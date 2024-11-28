#include <stdint.h>

const uint8_t DMX_MAGIC[4] = {0x44, 0x4D, 0x58, 0x20};

typedef struct __attribute__((packed)) {
    uint8_t magic[4];
    uint8_t __padding[2];
    uint16_t universe;
    uint32_t elementAmount;
    uint32_t duration;  // in milliseconds
} dmxHeader;

typedef struct __attribute__((packed)) {
    uint32_t timestamp;  // in milliseconds
    uint16_t valueAmount;
} dmxElement;

typedef struct {
    uint16_t channel;
    uint8_t value;
} dmxValue;
