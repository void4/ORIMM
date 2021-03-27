BITS = 64
EXP = 2**BITS
WORDMAX = EXP-1


NUMINSTR = 7
I_ADD, I_MUL, I_JMP, I_JLE, I_RUN, I_INT, I_LMT = range(NUMINSTR)

II_ARITH = [I_ADD, I_MUL]
II_CONTROL = [I_JMP, I_JLE]

II_ROOT = II_ARITH + II_CONTROL + [I_RUN, I_LMT]
II_CHILD = II_ARITH + II_CONTROL + [I_INT]

III = [II_ROOT, II_CHILD]

INAMES = "I_ADD, I_MUL, I_JMP, I_JLE, I_RUN, I_INT, I_LMT".replace("I_", "").split(", ")

I_ARGS = [2,2,1,3,2,0,2]

M_ROOT, M_CHILD = range(2)

# interrupt, out of gas, invalid memory access
S_INT, S_OOG, S_IMA = range(3)

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

	def mmap(self, offset):
		if self.mode == M_ROOT:
			return offset
		else:
			return self.get_offset(offset)

	def gmem(self, offset):
		try:
			return self.memory[self.mmap(offset)]
		except IndexError:
			raise MemoryAccessException()

	def smem(self, offset, value):
		try:
			self.memory[self.mmap(offset)] = value
		except IndexError:
			raise MemoryAccessException()

	def run(self):
		TOTAL_INSTR = 0

		while True:

			try:
				TOTAL_INSTR += 1

				#if TOTAL_INSTR == 10:
				#	break

				instr = self.gmem(self.ip)#can fail

				instrcost = self.gas_map[instr]

				if self.gas >= 0 and self.gas - instrcost < 0:
					self.mode = M_ROOT
					self.state = S_OOG
					self.ip = 0
					self.gas = 0
					continue

				args = [self.gmem(self.ip+a) for a in range(1,1+I_ARGS[instr])]

				jump = False

				if instr not in III[self.mode]:
					pass
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
				elif instr == I_INT:
					self.mode = M_ROOT
					self.ip = 0
					self.gas = None
				elif instr == I_LMT:
					self.build_gmap(args[0])
					self.gas = args[1]

				if not jump:
					self.ip += 1 + len(args)

				print(self.ip, self.mode, INAMES[instr], args)
			except MemoryAccessException:
				print("mae")
				self.state = S_IMA
				self.mode = M_ROOT
				self.ip = 0
