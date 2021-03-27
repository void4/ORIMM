from vm import VM, BITS
from assembler import translate, insert

standard_gas = [1,2,1,2,0,1,0]
code = translate("""
segment main:
lmt gasmap 1000
run memmap 0
jmp main

segment gasmap:
dw 1 2 1 2 0 1
segment memmap:
dw 1 child #child ;length of child segment
ds "this is a test"

segment child:
add 0 0
""")


memory = code

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
vm.run()
