from time import sleep
from inp import anykey

# Word size of the VM
BITS = 64
# Used for computation of remainder of instructions that produce larger values
EXP = 2**BITS
# Maximum word value in unsigned representation
WORDMAX = EXP-1

# Number of instructions, their opcodes and names
NUMINSTR = 14
I_ADD, I_MUL, I_JMP, I_JLE, I_RUN, I_LMT, I_INT, I_JIT, I_REM, I_MLN, I_SET, I_ADDI, I_MULI, I_OLDIP = range(NUMINSTR)
INAMES = "I_ADD, I_MUL, I_JMP, I_JLE, I_RUN, I_LMT, I_INT, I_JIT, I_REM, I_MLN, I_SET, I_ADDI, I_MULI, I_OLDIP".replace("I_", "").split(", ")

# Number of argument words following each instruction
I_ARGS = [2,2,1,3,2,2,0,1,2,1,2,2,2,1]

# Arithmetic Instructions
II_ARITH = [I_ADD, I_MUL, I_SET, I_ADDI, I_MULI]

# Control Flow Instructions
II_CONTROL = [I_JMP, I_JLE]

# Virtual machine security modes (equivalent to ring protection on physical CPUs)
M_ROOT, M_CHILD = range(2)

# Groups of instructions that can be executed in each mode
II_CHILD = II_ARITH + II_CONTROL + [I_INT] + [I_MLN]
II_ROOT = II_CHILD + [I_RUN, I_LMT, I_JIT, I_REM, I_OLDIP]

# One group for each mode
III = [II_ROOT, II_CHILD]

# Number and codes of virtual machine states
# interrupt, out of gas, invalid memory access, invalid instruction executed
NUMSTATES = 4
S_INT, S_OOG, S_IMA, S_IIE = range(NUMSTATES)

def opcode(txt):
	"""Converts an opcode number to its text representation"""
	try:
		return INAMES.index(txt.upper())
	except ValueError:
		return None

class MemoryAccessException(Exception):
	pass

class VM:
	def __init__(self, memory):
		"""Initializes a virtual machine instance, which contains the complete runtime state of the computation"""
		self.memory = memory
		self.external_memory = []
		self.interrupt = False
		# memory layout: 0: first instruction

		# Stores the cost for each instruction in a list, with index=opcode
		self.gas_map = [0 for i in range(NUMINSTR)]

		self.memory_map = []#also in memory?

		self.state = None
		self.gas = 0
		self.mode = M_ROOT
		self.ip = 0
		self.oldip = 0




	def build_gmap(self, offset):
		"""Stores the root-process specified gas cost for each construction in an internal variable, self.gas_map"""
		self.gas_map = []
		for i in range(NUMINSTR):
			self.gas_map.append(self.gmem(offset+i))

	# only root mode can reserve memory

	# is this a temporary structure, cannot be modified from child, even if memory is mapped onto it
	def build_mmap(self, offset):
		"""Stores a memory map in an internal variable, self.memory_map, similar to a page table

		A memory map is a list of sectors. Each sector has a start address and a length in real memory.

		The root process provides a child process memory map when it transfers control to it
		"""
		# TODO force increasing, no overlap?
		self.memory_map = []

		mmaplen = self.gmem(offset)
		for i in range(mmaplen):
			sector_start = self.gmem(offset+1+i*2)
			sector_length = self.gmem(offset+1+i*2+1)
			self.memory_map.append([sector_start, sector_length])

	def get_offset(self, virtual_address):
		"""Maps a virtual address to a real address"""

		for sector_start, sector_length in self.memory_map:
			if virtual_address < sector_length:
				return sector_start + virtual_address
			else:
				virtual_address -= sector_length

	def mmap(self, offset, force_mmap=False):
		"""Mode-dependent memory mapping, real->real in root mode, virtual->real in child mode or if forced"""
		if self.mode == M_ROOT and not force_mmap:
			return offset
		else:
			return self.get_offset(offset)

	def mmap_len(self):
		"""Returns the total length of the virtual memory map"""
		return sum(sector[1] for sector in self.memory_map)

	def gmem(self, offset, force_mmap=False):
		"""Gets mode-dependent address, raises Exception on failure"""
		try:
			return self.memory[self.mmap(offset, force_mmap)]
		except (IndexError, TypeError):
			raise MemoryAccessException()

	def smem(self, offset, value, force_mmap=False):
		"""Sets mode-dependent address, raises Exception on failure"""
		try:
			self.memory[self.mmap(offset, force_mmap)] = value & WORDMAX
		except (IndexError, TypeError):
			raise MemoryAccessException()

	def print_memory(self):
		"""Prints all memory (in root mode) or virtual memory (child mode)"""
		if self.mode == M_ROOT:
			print(self.memory)
		else:
			print([self.gmem(offset) for offset in range(self.mmap_len())])

	def run(self, debug=False):
		"""Starts/continues VM execution from its current state
		Signals external events by an interrupt which transfers control to the root process, storing the old instruction pointer in self.oldip so the interrupted (child) process can be resumed later
		"""

		while True:

			key = anykey()
			if key:
				print("HIT", key)
				#if ord(key) == 27: # ESC
				#	exit(0)
				# TODO interrupting interrupt?
				self.external_memory = key
				self.mode = M_ROOT
				self.interrupt = 1
				self.state = S_INT
				self.oldip = self.ip
				self.ip = 0

			if debug:
				sleep(1)

			try:

				if debug:
					print("IP", self.ip)
					self.print_memory()

				instr = self.gmem(self.ip)#can fail

				# TODO enforce accurate length gasmap?!
				try:
					instrcost = self.gas_map[instr]
				except IndexError:
					self.mode = M_ROOT
					self.state = S_IIE
					self.ip = 0
					continue

				if self.mode == M_CHILD and self.gas >= 0 and self.gas - instrcost < 0:
					self.mode = M_ROOT
					self.state = S_OOG
					self.ip = 0
					continue

				if self.mode == M_CHILD:#XXX keep it like this?
					self.gas -= instrcost

				args = [self.gmem(self.ip+a) for a in range(1,1+I_ARGS[instr])]

				jump = False

				if instr not in III[self.mode]:
					# If an instruction is not allowed in this mode, switch to the root process
					self.mode = M_ROOT
					self.state = S_IIE
					self.oldip = self.ip
					self.ip = 0
					continue

				# Arithmetic instructions
				elif instr == I_ADD:
					# Add the values of two memory addresses and store the result in the first
					self.smem(args[0], self.gmem(args[0])+self.gmem(args[1]))
				elif instr == I_ADDI:
					# Add an immediate value to a memory address value and store it
					self.smem(args[0], self.gmem(args[0])+args[1])
				elif instr == I_MUL:
					# Multiply the values of two memory addresses and store the result in the first
					self.smem(args[0], self.gmem(args[0])*self.gmem(args[1]))
				elif instr == I_MULI:
					# Multiply an immediate value with a memory address value and store it
					self.smem(args[0], self.gmem(args[0])*args[1])

				# Control flow instructions
				elif instr == I_JMP:
					# Unconditionally jump to a instruction in memory
					self.ip = args[0]
					jump = True
				elif instr == I_JLE:
					# Conditionally jump to the instruction (first argument) if the memory value at the second argument (address) is strictly smaller than the third
					if self.gmem(args[1]) < self.gmem(args[2]):
						self.ip = args[0]
						jump = True
				elif instr == I_RUN:
					# Start a child process by providing a memory map and a starting instruction address within it, switch the vm to child mode
					# 0: real start address of memory map, +ip?
					self.build_mmap(args[0])
					self.ip = self.gmem(args[1])
					# have to do this in the end to not interfere with mmap calculations
					self.mode = M_CHILD
					jump = True
				elif instr == I_INT:
					# Software interrupt to real memory address 0
					self.mode = M_ROOT
					self.ip = 0
					jump = True
				elif instr == I_LMT:
					# Parameterized by the instruction gas map at address args[0], limit all following execution to args[1] gas
					self.build_gmap(args[0])
					self.gas = args[1]
				elif instr == I_JIT:#only in root mode?
					# Jump if an interrupt occured
					if self.interrupt:
						self.interrupt = 0
						self.ip = args[0]
						jump = True
				elif instr == I_REM:
					if args[1] < len(self.external_memory):
						self.smem(args[0], self.external_memory[args[1]])
				elif instr == I_MLN:
					# Saves either the real memory length in root mode or the virtual memory length at memory address args[0]
					if self.mode == M_ROOT:
						self.smem(args[0], len(self.memory))
					else:
						self.smem(args[0], self.mmap_len())

				# Memory load/store
				elif instr == I_SET:
					# Sets the value at memory address args[0] to immediate value args[1]
					self.smem(args[0], args[1])

				# Internal variable access
				elif instr == I_OLDIP:
					# Stores the old ip at args[0]
					self.smem(args[0], self.oldip)

				if not jump:
					# Increment the instruction pointer to the next instruction in memory
					self.ip += 1 + len(args)

				if debug:
					print("ip", self.ip, "mode", self.mode, "gas", self.gas, INAMES[instr], args)
			except MemoryAccessException as e:
				if debug:
					print(e)
				# If a memory access attempt is made to memory that does not exist, switch to root process
				self.state = S_IMA
				self.mode = M_ROOT
