#define M_ROOT 0
#define M_CHILD 1

#define S_NRM 0
#define S_INT 1
#define S_OOG 2
#define S_IMA 3
#define S_IIE 4

#define I_ADD 0
#define I_ADDI 1

#define I_MUL 2
#define I_MULI 3

#define I_SET 4

#define I_JMP 5
#define I_JLE 6

#define I_INT 7
#define I_JIT 8

#define I_MLN 9
#define I_REM 10

#define I_RUN 11
#define I_LMT 12

#define I_OLDIP 13

#define I_INVALID 14

#define INSTRUCTION_ARGS {2,2, 2,2, 2, 1,2, 0,1, 1,1, 2,2, 1}

typedef struct {
  uint64_t start;
  uint64_t length;
} Sector;

typedef struct {
  uint64_t length;
  uint64_t* data;
} Memory;

typedef struct {
  uint8_t mode;
  uint8_t state;

  uint64_t ip;
  uint64_t oldip;

  uint8_t interrupt;

  Memory* memory;
  Memory* external_memory;

  uint64_t gas;
  Memory* gas_map;

  uint64_t num_sectors;
  Sector* memory_map;
} VM;
