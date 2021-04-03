from vm import VM, BITS
from assembler import translate, insert

# Problem: lmt and run shouldn't be zero because otherwise child may use resources that way
# wouldn't be necessary if these instruction raised an exception

# Problem: syscall message passing: have to translate virtual to real memory
# pages aren't fixed size, so message may be weirdly distributed across real pages, even same real address on several virtual addresses
# first page of process fixed size, say 16 words: ret data + 15 keys

# add relative jump instruction

# allow interrupts?
# memory mapped io?

# how to recover gas and ip?

# save interrupt data address in 16 word process root node

# use certain memory regions as registers, passing data to OS?
# just one?
# def need some workspace

# give run a return value address parameter?
# TODO all label names should be segment-relative
# default labels like start?

code = translate("""
segment@0 main:

jit inthandler

lmt gasmap 1000
run memmap 0
jmp main

inthandler:

jmp main

allocate_memory:

allocate_node:

segment gasmap:
dw 1 2 1 2 0 0 5
segment memmap:
dw 1 child #child ;length of child segment

segment data:
ds "this is a test"

segment child:
start:
add 0 0
add 1 1
add 2 2
jmp child:start

segment free:
dzw 1000
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
