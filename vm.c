#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <unistd.h>
#include <inttypes.h>

#include "vm.h"

VM* init_vm() {

  Sector* sector_pt;

  Memory *memory = malloc(sizeof(Memory));
  Memory *external_memory = malloc(sizeof(Memory));
  Memory *gas_map = malloc(sizeof(Memory));

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

void build_gmap(VM* vm, uint64_t offset) {

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
  if (vm->mode == M_ROOT) {
    for (int i=0;i<vm->memory->length;i++) {
      printf("%" PRIu64, vm->memory->data[i]);
    }
  } else {
    for (int i=0;i<mmap_len(vm);i++) {
      printf("%" PRIu64, vm->memory->data[get_offset(vm, i)]);
    }
  }
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

void run(VM* vm, uint8_t debug) {
  printf("Running\n");

  while (1) {
    if (debug) {
      sleep(1);
      printf("IP: %" PRIu64 "\n", vm->ip);
      print_memory(vm);
    }

    uint8_t instr = gmem(vm, vm->ip);
  }
}

int main() {
  printf("Hello, World!\n");
  VM* vm = init_vm();
  run(vm, 1);
  return 0;
}
