from time import sleep
from inp import anykey

BITS = 64
EXP = 2**BITS
WORDMAX = EXP-1

# TODO floating point instructions?
NUMINSTR = 9
I_ADD, I_MUL, I_JMP, I_JLE, I_RUN, I_LMT, I_INT, I_JIT, I_REM = range(NUMINSTR)

II_ARITH = [I_ADD, I_MUL]
II_CONTROL = [I_JMP, I_JLE]

II_ROOT = II_ARITH + II_CONTROL + [I_RUN, I_LMT, I_JIT, I_REM]
II_CHILD = II_ARITH + II_CONTROL + [I_INT]

III = [II_ROOT, II_CHILD]

INAMES = "I_ADD, I_MUL, I_JMP, I_JLE, I_RUN, I_LMT, I_INT, I_JIT, I_REM".replace("I_", "").split(", ")

I_ARGS = [2,2,1,3,2,2,0,1,2]

M_ROOT, M_CHILD = range(2)

# interrupt, out of gas, invalid memory access, invalid instruction executed
S_INT, S_OOG, S_IMA, S_IIE = range(4)

def opcode(txt):
	try:
		return INAMES.index(txt.upper())
	except ValueError:
		return None

class MemoryAccessException(Exception):
	pass

class VM:
	def __init__(self, memory):
		self.memory = memory
		self.external_memory = []
		self.interrupt = False
		# memory layout: 0: first instruction

		self.gas_map = [0 for i in range(NUMINSTR)]

		self.memory_map = []#also in memory?

		self.state = None
		self.gas = 0
		self.mode = M_ROOT
		self.ip = 0




	def build_gmap(self, offset):
		self.gas_map = []
		for i in range(NUMINSTR):
			self.gas_map.append(self.gmem(offset+i))

	# only root mode can reserve memory

	# is this a temporary structure, cannot be modified from child, even if memory is mapped onto it
	def build_mmap(self, offset):
		self.memory_map = []

		mmaplen = self.gmem(offset)
		for i in range(mmaplen):
			sector_start = self.gmem(offset+1+i*2)
			sector_length = self.gmem(offset+1+i*2+1)
			self.memory_map.append([sector_start, sector_length])

	def get_offset(self, ip):
		total = 0
		for mem, ln in self.memory_map:
			if ip < ln:
				return mem+ip
			else:
				ip -= ln

	def mmap(self, offset, force_mmap=False):
		if self.mode == M_ROOT and not force_mmap:
			return offset
		else:
			return self.get_offset(offset)

	def gmem(self, offset, force_mmap=False):
		try:
			return self.memory[self.mmap(offset, force_mmap)]
		except (IndexError, TypeError):
			raise MemoryAccessException()

	def smem(self, offset, value, force_mmap=False):
		try:
			self.memory[self.mmap(offset, force_mmap)] = value
		except (IndexError, TypeError):
			raise MemoryAccessException()

	def run(self):
		TOTAL_INSTR = 0

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
				self.ip = 0

			sleep(0.1)

			try:
				TOTAL_INSTR += 1

				#if TOTAL_INSTR == 10:
				#	break
				print("IP", self.ip)
				instr = self.gmem(self.ip)#can fail

				instrcost = self.gas_map[instr]

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
					self.mode = M_ROOT
					self.state = S_IIE
					self.ip = 0
					continue
				elif instr == I_ADD:
					self.smem(args[0], self.gmem(args[0])+self.gmem(args[1]))
				elif instr == I_MUL:
					self.smem(args[0], self.gmem(args[0])*self.gmem(args[1]))
				elif instr == I_JMP:
					self.ip = args[0]
					jump = True
				elif instr == I_JLE:
					if self.gmem(args[1]) < self.gmem(args[2]):
						self.ip = args[0]
						jump = True
				elif instr == I_RUN:
					# 0: real start address of memory map, +ip?
					self.build_mmap(args[0])
					self.ip = args[1]
					# have to do this in the end to not interfere with mmap calculations
					self.mode = M_CHILD
					jump = True
				elif instr == I_INT:
					self.mode = M_ROOT
					self.ip = 0
					jump = True
				elif instr == I_LMT:
					self.build_gmap(args[0])
					self.gas = args[1]
				elif instr == I_JIT:#only in root mode?
					if self.interrupt:
						self.interrupt = 0
						self.ip = args[0]
						jump = True
				elif instr == I_REM:
					if args[1] < len(self.external_memory):
						self.smem(args[0], self.external_memory[args[1]])

				if not jump:
					self.ip += 1 + len(args)

				print("ip", self.ip, "mode", self.mode, "gas", self.gas, INAMES[instr], args)
			except MemoryAccessException:
				print("mae")
				self.state = S_IMA
				self.mode = M_ROOT
