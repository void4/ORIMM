from vm import VM, BITS
from assembler import translate, insert

with open("code.asm") as f:
    text = f.read()
    code = translate(text)

memory = code

import bz2
import ctypes

data = b"".join(v.to_bytes(8, byteorder="big") for v in memory)

compressed = bz2.compress(data)

print(len(data), "BYTES", len(compressed), "COMPRESSED")

#memory = [0 for i in range(100)]

#o = insert(memory, 0, code)
#insert(memory, o, standard_gas)

# memory map layout:
# 1 word: length of map, then 1 word offset, 1 word length pairs

# use segment:labels hierarchy, or allow arbitrary trees with indentation?
# more compact instruction set later!

print(memory)
print(len(memory), "words", len(memory)*BITS//8, "bytes")
#exit(1)
vm = VM(memory)
vm.run(debug=True)
