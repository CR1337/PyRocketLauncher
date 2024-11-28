#include <stdint.h>

enum IldxFormatCode {
    ILDX_FORMAT_CODE_3D_INDEXED = 0,
    ILDX_FORMAT_CODE_2D_INDEXED = 1,
    ILDX_FORMAT_CODE_COLOR_PALETTE = 2,
    ILDX_FORMAT_CODE_3D_TRUE_COLOR = 4,
    ILDX_FORMAT_CODE_2D_TRUE_COLOR = 5
};

const uint8_t ILDX_MAGIC[4] = {0x49, 0x4C, 0x44, 0x58};
const uint8_t ILDX_STATUS_CODE_LAST_POINT_MASK = 0b10000000;
const uint8_t ILDX_STATUS_CODE_BLANKING_MASK = 0b01000000;

typedef struct __attribute__((packed)) {
    uint8_t ildxMagic[4];
    uint8_t startTimestamp[3];
    uint8_t formatCode;
    uint8_t frameOrPaletteName[8];
    uint8_t companyName[8];
    uint16_t numberOfRecords;
    uint16_t frameOrPaletteNumber;
    uint16_t totalFrames;
    uint8_t projectorNumber;
    uint8_t framesPerSecondOrFrameAmount;
} ildxHeader;

typedef struct __attribute__((packed)) {
    uint16_t x;
    uint16_t y;
    uint16_t z;
    uint8_t statusCode;
    uint8_t colorIndex;
} ildx3dIndexedRecord;

typedef struct __attribute__((packed)) {
    uint16_t x;
    uint16_t y;
    uint8_t statusCode;
    uint8_t colorIndex;
} ildx2dIndexedRecord;

typedef struct __attribute__((packed)) {
    uint8_t r;
    uint8_t g;
    uint8_t b;
} ildxColorPlatteRecord;

typedef struct __attribute__((packed)) {
    uint16_t x;
    uint16_t y;
    uint16_t z;
    uint8_t statusCode;
    uint8_t r;
    uint8_t g;
    uint8_t b;
} ildx3dTrueColorRecord;

typedef struct __attribute__((packed)) {
    uint16_t x;
    uint16_t y;
    uint8_t statusCode;
    uint8_t r;
    uint8_t g;
    uint8_t b;
} ildx2dTrueColorRecord;
