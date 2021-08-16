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
