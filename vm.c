#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <inttypes.h>

#include "vm.h"

void clear_memory(Memory* memory) {
  free(memory->data);
  free(memory);
}

void clear_sectors(VM* vm) {
  if (vm->num_sectors > 0) {
    free(vm->memory_map);
  }
}

VM* init_vm() {

  FILE *fp;

  fp = fopen("code.omg", "r");

  fseek(fp, 0L, SEEK_END);
  uint64_t fsize = ftell(fp);
  fseek(fp, 0L, SEEK_SET);

  Memory *memory = malloc(sizeof(Memory));

  memory->length = fsize/sizeof(uint64_t);
  memory->data = malloc(fsize);

  printf("File size: %" PRIu64 "\n", fsize);

  fread(memory->data, sizeof(uint64_t), fsize/sizeof(uint64_t), fp);

  Memory *external_memory = malloc(sizeof(Memory));

  // number of instructions is constant
  Memory *gas_map = malloc(sizeof(Memory));
  gas_map->data = malloc(sizeof(uint64_t) * I_INVALID);
  gas_map->length = I_INVALID;

  Sector* sector_pt;

  VM *vm = malloc(sizeof(VM));

  vm->mode = M_ROOT;
  vm->state = S_NRM,

  vm->ip = 0;
  vm->oldip = 0;

  vm->interrupt = 0;

  vm->memory = memory;
  vm->external_memory = external_memory;

  vm->gas = 0;
  vm->gas_map = gas_map;

  vm->num_sectors = 0;
  vm->memory_map = sector_pt;

  return vm;
}

uint64_t mmap_len(VM* vm) {
  uint64_t total = 0;
  for (int i = 0; i<vm->num_sectors;i++) {
    Sector sector = vm->memory_map[i];
    total += sector.length;
  }
  return total;
}

uint64_t get_offset(VM* vm, uint64_t virtual_address) {

  for (int i = 0; i<vm->num_sectors;i++) {
    Sector sector = vm->memory_map[i];
    if (virtual_address < sector.length) {
      return sector.start + virtual_address;
    } else {
      virtual_address -= sector.length;
    }
  }

  // TODO what to do on fail?

}

void print_memory(VM* vm) {
  printf("[");
  if (vm->mode == M_ROOT) {
    for (int i=0;i<vm->memory->length;i++) {
      printf("%" PRIu64, vm->memory->data[i]);
      if (i < vm->memory->length-1) {
        printf(",");
      }
    }
  } else {
    for (int i=0;i<mmap_len(vm);i++) {
      printf("%" PRIu64, vm->memory->data[get_offset(vm, i)]);
      if (i < mmap_len(vm)-1) {
        printf(",");
      }
    }
  }
  printf("]\n");
}

uint64_t mmap(VM* vm, uint64_t offset) {
  if (vm->mode == M_ROOT) {
    return offset;
  } else {
    return get_offset(vm, offset);
  }
}

uint64_t gmem(VM* vm, uint64_t offset) {
  //TODO check for memory access exception
  if (offset < vm->memory->length) {
    return vm->memory->data[mmap(vm, offset)];
  } else {

  }
}

uint64_t smem(VM* vm, uint64_t offset, uint64_t value) {
  if (offset < vm->memory->length) {
    vm->memory->data[mmap(vm, offset)] = value;
  } else {

  }
}

uint8_t valid_instruction(uint8_t mode, uint64_t instr) {
  if (mode == M_ROOT) {
    return 1;
  } else if (mode == M_CHILD && instr <= 6) {
    return 1;
  } else {
    return 0;
  }
}

uint64_t args(VM* vm, uint64_t arg) {
  return gmem(vm, vm->ip+1+arg);
}

void build_gmap(VM* vm, uint64_t offset) {
  for (int i=0;i<I_INVALID;i++) {
    vm->gas_map->data[i] = gmem(vm, offset+i);
  }
}

void build_mmap(VM* vm, uint64_t offset) {
  clear_sectors(vm);
  vm->num_sectors = gmem(vm, offset);
  printf("Creating %lu sectors at offset %lu\n", vm->num_sectors, offset);
  vm->memory_map = malloc(sizeof(Sector) * vm->num_sectors);
  for (int i=0;i<vm->num_sectors;i++) {
    vm->memory_map[i].start = gmem(vm, offset+1+2*i);
    vm->memory_map[i].length = gmem(vm, offset+1+2*i+1);
  }
}

void run(VM* vm, uint8_t debug) {
  printf("Running\n");

  while (1) {
    if (debug) {
      sleep(1);
      printf("IP: %" PRIu64 "\n", vm->ip);
      print_memory(vm);
    }

    uint8_t instr = gmem(vm, vm->ip);

    if (instr >= I_INVALID || !valid_instruction(vm->mode, instr)) {
      vm->mode = M_ROOT;
      vm->state = S_IIE;
      vm->oldip = vm->ip;
      vm->ip = 0;
      continue;
    }

    uint64_t instrcost = vm->gas_map->data[instr];

    if (debug) {
      //printf("INSTR: %" PRIu8 "\n", instr);
      printf("INSTR: %s\n", istrings[instr]);
    }

    if (vm->mode == M_CHILD && (uint64_t)(vm->gas) - instrcost < 0) {
      vm->mode = M_ROOT;
      vm->state = S_OOG;
      vm->ip = 0;
      continue;
    }

    if (vm->mode == M_CHILD) {
      vm->gas -= instrcost;
    }

    uint8_t jump = 0;

    //uint64_t* args =
    switch(instr) {
      case I_ADD:
        smem(vm, args(vm, 0), gmem(vm, args(vm, 0)) + gmem(vm, args(vm, 1)));
        break;
      case I_ADDI:
        smem(vm, args(vm, 0), gmem(vm, args(vm, 0)) + args(vm, 1));
        break;
      case I_MUL:
        smem(vm, args(vm, 0), gmem(vm, args(vm, 0)) * gmem(vm, args(vm, 1)));
        break;
      case I_MULI:
        smem(vm, args(vm, 0), gmem(vm, args(vm, 0)) * args(vm, 1));
        break;
      case I_JMP:
        vm->ip = args(vm, 0);
        jump = 1;
        break;
      case I_JLE:
        if (gmem(vm, args(vm, 1)) < gmem(vm, args(vm, 2))) {
          vm->ip = args(vm, 0);
          jump = 1;
        }
        break;
      case I_RUN:
        build_mmap(vm, args(vm, 0));
        vm->ip = gmem(vm, args(vm, 1));
        vm->mode = M_CHILD;
        jump = 1;
        break;
      case I_INT:
        vm->mode = M_ROOT;
        vm->oldip = vm->ip;
        vm->ip = 0;
        jump = 1;
        break;
      case I_LMT:
        build_gmap(vm, args(vm, 0));
        vm->gas = args(vm, 1);
        break;
      case I_JIT:
        if (vm->interrupt) {
          vm->interrupt = 0;
          vm->ip = args(vm, 0);
          jump = 1;
        }
        break;
      case I_REM:
        if (args(vm, 1) < vm->external_memory->length) {
          smem(vm, args(vm, 0), vm->external_memory->data[args(vm, 1)]);
        }
        break;
      case I_MLN:
        if (vm->mode == M_ROOT) {
          smem(vm, args(vm, 0), vm->memory->length);
        } else {
          smem(vm, args(vm, 0), mmap_len(vm));
        }
        break;
      case I_SET:
        smem(vm, args(vm, 0), args(vm, 1));
        break;
      case I_OLDIP:
        smem(vm, args(vm, 0), vm->oldip);
        break;
    }

    if (!jump) {
      // TODO check for out of bounds here?!
      vm->ip += 1 + INSTRUCTION_ARGS[instr];
    }
  }
}

int main() {
  printf("Hello, World!\n");
  VM* vm = init_vm();
  run(vm, 1);
  return 0;
}
