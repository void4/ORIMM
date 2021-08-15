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
# default labels like start? - well, segment name is already offset

# TODO use relative addressing

# also use external_memory for comms between os and processes?

code = translate("""
segment@0 main:

jit inthandler

mln main:data



lmt gasmap 100
run memmap oldip
jmp main

inthandler:
oldip oldip

jmp main

oldip:
dw 0

register:
dw 0

allocate_memory:
add allocated register

allocate_node:
;set register 16
;todo check memory size first
addi allocated 16

data:
dw 42;real memlen

allocated:
dw free

segment gasmap:
;I_ADD, I_MUL, I_JMP, I_JLE, I_RUN, I_LMT, I_INT, I_JIT, I_REM, I_MLN, I_SET, I_ADDI, I_MULI, I_OLDIP
dw 1 1 1 1 1 1 1 1 1 1 1 1 1 1
segment memmap:
dw 1 child #child ;length of child segment

segment data:
ds "this is a test"

segment osdata:
dw 0;capindex

segment childnode:
dw 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16;address of next node + 16 keys
;next, memory

segment child:
start:
add 0 0
add 1 1
add 2 2
mln child:data
jmp child:start

data:
dw 1;virtual memlen

segment free:
dzw 100
""")


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
