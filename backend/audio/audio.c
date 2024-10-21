#include "audio.h"

#include <stdio.h>
#include <unistd.h>

#include <errno.h>

#define HALF(x) ((x) / 2)

typedef uint8_t Bool8;

#define RIFF_MAGIC (uint8_t[4]){'R', 'I', 'F', 'F'}
#define WAVE_MAGIC (uint8_t[4]){'W', 'A', 'V', 'E'}
#define FMT_MAGIC  (uint8_t[4]){'f', 'm', 't', ' '}
#define FACT_MAGIC (uint8_t[4]){'f', 'a', 'c', 't'}
#define DATA_MAGIC (uint8_t[4]){'d', 'a', 't', 'a'}
#define MAGIC_SIZE (4)

#define FMT_CHUNK_SIZE_PCM (sizeof(AudioFmtChunk))
#define FMT_CHUNK_SIZE_NON_PCM (sizeof(AudioFmtChunk) \
    + sizeof(AudioNonPcmFmtChunkExtension))
#define FMT_CHUNK_SIZE_EXTENSIBLE (sizeof(AudioFmtChunk) \
    + sizeof(AudioExtensibleFmtChunkExtension))

#define FMT_CHUNK_SIZE_OFFSET (8)
#define EXTENSIBLE_FMT_CHUNK_EXTRA_SIZE (22)

#define EXTENSIBLE_GUID (uint8_t[14]){ \
    0x00, 0x00, 0x00, 0x00, 0x10, 0x00, 0x80,  \
    0x00, 0x00, 0xAA, 0x00, 0x38, 0x9B, 0x71 \
}
#define EXTENSIBLE_GUID_SIZE (14)

#define WAVE_FORMAT_PCM (0x0001)
#define WAVE_FORMAT_IEEE_FLOAT (0x0003)
#define WAVE_FORMAT_ALAW (0x0006)
#define WAVE_FORMAT_MULAW (0x0007)
#define WAVE_FORMAT_EXTENSIBLE (0xFFFE)

#define CHANNEL_POSITION_COUNT (18)
#define CHANNEL_MASK_18 (0b111111111111111111)
const static enum snd_pcm_chmap_position all_channel_positions[CHANNEL_POSITION_COUNT] = {
    SND_CHMAP_FL,
    SND_CHMAP_FR,
    SND_CHMAP_FC,
    SND_CHMAP_LFE,
    SND_CHMAP_RL,
    SND_CHMAP_RR,
    SND_CHMAP_FLC,
    SND_CHMAP_FRC,
    SND_CHMAP_BC,
    SND_CHMAP_SL,
    SND_CHMAP_SR,
    SND_CHMAP_TC,
    SND_CHMAP_TFL,
    SND_CHMAP_TFC,
    SND_CHMAP_TFR,
    SND_CHMAP_TRL,
    SND_CHMAP_TRC,
    SND_CHMAP_TRR,
};

#define PCM_BLOCK_MODE (0)
#define PCM_SEARCH_DIRECTION_NEAR (0)

#define MAX_VOLUME (100)

#define MAX_VOLUME (100)

#define DEFAULT_SOUND_DEVICE_NAME ("default")

#define MICROSECONDS_PER_MILLISECOND (1000)
#define MILLISECONDS_PER_SECOND (1000)
#define BITS_PER_BYTE (8)

#define BUFFER_SIZE_FACTOR (8)
#define INTERNAL_BARRIER_COUNT (2)

// The following 6 structs define the structure of a WAV file.

/**
 * @brief The RIFF header of a WAV file
*/
typedef struct __attribute__((packed)) {
    uint8_t riffMagic[4];
    uint32_t fileSize;
    uint8_t waveMagic[4];
} AudioRiffHeader;

/**
 * @brief The Fmt Chunk of a PCM WAV file
*/
typedef struct __attribute__((packed)) {
    uint8_t fmtMagic[4];
    uint32_t fmtSize;
    uint16_t audioFormat;
    uint16_t numChannels;
    uint32_t sampleRate;
    uint32_t byteRate;
    uint16_t blockAlign;
    uint16_t bitsPerSample;
} AudioFmtChunk;

/**
 * @brief The Fmt Chunk of a non-PCM WAV file
*/
typedef struct __attribute__((packed)) {
    uint16_t extraSize;
} AudioNonPcmFmtChunkExtension;

/**
 * @brief The Fmt Chunk of an extensible WAV file
*/
typedef struct __attribute__((packed)) {
    uint16_t extraSize;
    uint16_t validBitsPerSample;
    uint32_t channelMask;
    uint16_t audioFormat;
    uint8_t guid[14];
} AudioExtensibleFmtChunkExtension;

/**
 * @brief The Fact Chunk of a WAV file
*/
typedef struct __attribute__((packed)) {
    uint8_t factMagic[4];
    uint32_t factSize;
    uint32_t samplesPerChannel;
} AudioFactChunk;

/**
 * @brief The DATA chunk of a WAV file
 * 
 * This is followed by the audio data.
*/
typedef struct __attribute__((packed)) {
    uint8_t dataMagic[4];
    uint32_t dataSize;
} AudioDataChunk;

/**
 * @brief This represents the data necessary to play the audio.
*/
typedef struct {
    uint32_t audioLength;  /* The length of the audio in milliseconds */
    uint32_t sampleRate;  /* The sample rate in frames/second */
    uint32_t byteRate;  /* How many bytes are "played" per second */
    uint32_t dataSize;  /* The amount of audio data in bytes */
    uint32_t channelMap;  /* The mapping from channel to speaker */
    uint32_t samplesPerChannel;  /* The amount of samples per channel */
    uint16_t channelAmount;  /* The amount of channels, 1 is mono, 2 is stereo */
    uint16_t blockAlign;  /* Amount of bytes per sample */
    uint16_t bitsPerSample;  /* The amount of bits per sample */
    uint16_t format;  /* The format of the audio data */
    uint8_t *data;  /* A pointer to the audio data */
    uint8_t __align[3];
} AudioRiffData;

/**
 * @brief This is the entire audio object given to the user as an opaque pointer.
*/
typedef struct {
    AudioRiffData riffData;  /* The data necessary to play the audio */
    snd_pcm_t *pcmHandle;  /* The ALSA pcm handle */
    pthread_t *thread;  /* The thread that plays the audio */
    pthread_barrier_t *externalBarrier;  /* A barrier to synchronize with potential other threads created by the user */
    pthread_barrier_t *internalBarrier;  /* A barrier to synchronize the user thread with the audio thread */
    pthread_mutex_t *actionLock;  /* A lock to prevent multiple actions at the same time */
    AudioError *error;  /* An error object to communicate errors to the user */
    char *soundDeviceName;  /* The name of the sound device */
    uint32_t jumpTarget;  /* The target time to jump to in milliseconds */
    uint32_t currentFrame;  /* The current frame being played */
    uint32_t lastFrame;  /* The last frame that can be played */
    uint32_t timeResolution;  /* The time resolution in milliseconds */
    uint32_t alsaBufferSize;  /* The size of the ALSA buffer in frames */
    Bool8 soundDeviceNameSetByUser;  /* Whether the sound device name was set by the user */
    Bool8 useExternalBarrier;  /* Whether an external barrier is used */
    Bool8 isPlaying;  /* Whether the audio is playing */
    Bool8 isPaused;  /* Whether the audio is paused */
    Bool8 playFlag;  /* Whether the audio should be played */
    Bool8 pauseFlag;  /* Whether the audio should be paused */
    Bool8 stopFlag;  /* Whether the audio should be stopped */
    Bool8 haltFlag;  /* Whether the audio thread should be stopped */
    Bool8 jumpFlag;  /* Whether the audio should jump to a specific time */
    uint8_t __align[7];
} _AudioObject;

void _resetError(_AudioObject *_self) {
    ((_AudioObject*)_self)->error->type = AUDIO_ERROR_NO_ERROR;
    ((_AudioObject*)_self)->error->level = AUDIO_ERROR_LEVEL_INFO;
    ((_AudioObject*)_self)->error->alsaErrorNumber = 0;
}

void _waitForBarriers(_AudioObject *_self) {
    pthread_barrier_wait(_self->internalBarrier);
    if (_self->externalBarrier != NULL) {
        pthread_barrier_wait(_self->externalBarrier);
        _self->externalBarrier = NULL;
    }
}

void _play(_AudioObject *_self) {
    _self->playFlag = false;
    _self->isPlaying = true;
    _self->isPaused = false;
}

void _pause(_AudioObject *_self) {
    _self->pauseFlag = false;
    _self->isPlaying = false;
    _self->isPaused = true;
    
    // How much not played frames are in the buffer?
    snd_pcm_sframes_t delay; 
    snd_pcm_delay(_self->pcmHandle, &delay);

    // Remove them from the buffer
    _self->currentFrame -= delay;
    if (_self->currentFrame < 0) _self->currentFrame = 0;
    snd_pcm_drop(_self->pcmHandle);
    snd_pcm_prepare(_self->pcmHandle);
}

void _stop(_AudioObject *_self) {
    _self->stopFlag = false;
    _self->isPlaying = false;
    _self->isPaused = true;

    // Clear buffer
    _self->currentFrame = 0;
    snd_pcm_drop(_self->pcmHandle);
    snd_pcm_prepare(_self->pcmHandle);
}

void _jump(_AudioObject *_self) {
    _self->jumpFlag = false;

    // Calculate new current frame and check for overrun
    _self->currentFrame = (_self->jumpTarget * _self->riffData.sampleRate) 
        / MILLISECONDS_PER_SECOND;
    if (_self->currentFrame > _self->lastFrame) {
        _self->currentFrame = _self->lastFrame;
    }

    // Clear buffer
    snd_pcm_drop(_self->pcmHandle);
    snd_pcm_prepare(_self->pcmHandle);
}

snd_pcm_uframes_t _getFramesAvailable(_AudioObject *_self) {
    // Get the amount of frames that can be written to the buffer
    snd_pcm_status_t *status;
    snd_pcm_status_malloc(&status);
    snd_pcm_status(_self->pcmHandle, status);
    snd_pcm_uframes_t framesAvailable = snd_pcm_status_get_avail(status);
    snd_pcm_status_free(status);
    return framesAvailable;
}

snd_pcm_uframes_t _getFramesToWrite(
    _AudioObject *_self, snd_pcm_uframes_t framesAvailable, bool *endReached
) {
    // Compute the actual amount of frames to be written considering 
    // possible overrun.
    snd_pcm_uframes_t framesToWrite = framesAvailable;
    *endReached = false;
    if (_self->currentFrame + framesToWrite > _self->lastFrame) {
        framesToWrite = _self->lastFrame - _self->currentFrame;
        *endReached = true;
    }
    return framesToWrite;
}

void * _mainloop(void *self) {
    _AudioObject *_self = (_AudioObject*)self;
    _self->isPaused = true;

    while (!_self->haltFlag) {
        // Handle set command flags.
        if (_self->playFlag) {
            _play(_self);
            _waitForBarriers(_self);
        } else if (_self->pauseFlag) {
            _pause(_self);
            _waitForBarriers(_self);
        } else if (_self->stopFlag) {
            _stop(_self);
            _waitForBarriers(_self);
        } else if (_self->jumpFlag) {
            _jump(_self);
            _waitForBarriers(_self);
        }

        // Wait a bit and if paused don't do anything.
        usleep(_self->timeResolution * MICROSECONDS_PER_MILLISECOND);
        if (_self->isPaused) continue;

        // Determine how many frames could be written.
        snd_pcm_uframes_t framesAvailable = _getFramesAvailable(_self);

        // If buffer is half empty write frames
        if (framesAvailable > HALF(_self->alsaBufferSize)) {
            // Determine the amount of frames to write and check if
            // the end is reached afterwards.
            bool endReached = false;
            snd_pcm_uframes_t framesToWrite = _getFramesToWrite(
                _self, framesAvailable, &endReached
            );

            // Calculate the offset in the pcm data.
            size_t pcm_offset = _self->currentFrame 
                * _self->riffData.blockAlign;

            // Write the frames
            if (snd_pcm_writei(
                _self->pcmHandle, 
                (void*)(_self->riffData.data + pcm_offset), 
                framesToWrite
            ) == -EPIPE) {
                snd_pcm_prepare(_self->pcmHandle);
            }

            // Stop if end is reached.
            if (endReached) {
                _stop(_self);
            } else {
                _self->currentFrame += framesToWrite;
            }
        }
    }

    pthread_exit(NULL);
    return NULL;
}

bool _readFactCunk(_AudioObject *_self, AudioFactChunk *factChunk) {
    if (memcmp(factChunk->factMagic, FACT_MAGIC, MAGIC_SIZE)) {
        _self->error->type = AUDIO_ERROR_INVALID_FACT_MAGIC_NUMBER;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    if (factChunk->factSize != 4) {
        _self->error->type = AUDIO_ERROR_INVALID_FACT_SIZE;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    // The fact chunk contains the amount of samples per channel
    _self->riffData.samplesPerChannel = factChunk->samplesPerChannel;
    return true;
}

bool _readNonPcmFmtChunkExtension(
    _AudioObject *_self, AudioNonPcmFmtChunkExtension *nonPcmExtension
) {
    // non-PCM extensions that are not extensible have size 0
    if (nonPcmExtension->extraSize != 0) {
        _self->error->type = AUDIO_ERROR_INVALID_NON_PCM_EXTENSION_SIZE;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    // every non-PCM extension must have a fact chunk
    AudioFactChunk *factChunk = (AudioFactChunk*)(
        (uint8_t*)nonPcmExtension + sizeof(AudioNonPcmFmtChunkExtension)
    );
    if (!_readFactCunk(_self, factChunk)) {
        return false;
    }
    return true;
}

bool _readExtensibleFmtChunkExtension(
    _AudioObject *_self, AudioExtensibleFmtChunkExtension *extensibleExtension
) {
    // extensible fmt extensions have a fixed size
    if (
        extensibleExtension->extraSize 
        != EXTENSIBLE_FMT_CHUNK_EXTRA_SIZE
    ) {
        _self->error->type = AUDIO_ERROR_INVALID_EXTENSIBLE_EXTENSION_SIZE;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    // the extension conatains the actual audio format
    switch (extensibleExtension->audioFormat) {
        case WAVE_FORMAT_PCM:
        case WAVE_FORMAT_IEEE_FLOAT:
        case WAVE_FORMAT_ALAW:
        case WAVE_FORMAT_MULAW:
            _self->riffData.format = extensibleExtension->audioFormat;
            break;
        default:
            _self->error->type = AUDIO_ERROR_INVALID_EXTENSIBLE_AUDIO_FORMAT;
            _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
            return false;
            break;
    }
    // There is a fixed guid in the extension
    if (memcmp(
        extensibleExtension->guid, EXTENSIBLE_GUID, EXTENSIBLE_GUID_SIZE
    )) {
        _self->error->type = AUDIO_ERROR_INVALID_EXTENSIBLE_GUID;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    // The channel mask is used to map channels to speakers
    _self->riffData.channelMap = extensibleExtension->channelMask;
    // Every extensible fmt chunk must have a fact chunk
    AudioFactChunk *factChunk = (AudioFactChunk*)(
        (uint8_t*)extensibleExtension 
        + sizeof(AudioExtensibleFmtChunkExtension)
    );
    if (!_readFactCunk(_self, factChunk)) {
        return false;
    }
    return true;
}

bool _readFmtChunk(_AudioObject *_self, AudioFmtChunk *fmtChunk) {
    if (memcmp(fmtChunk->fmtMagic, FMT_MAGIC, MAGIC_SIZE)) {
        _self->error->type = AUDIO_ERROR_IMVALID_FMT_MAGIC_NUMBER;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }

    // Check if the fmt chunk has the right size
    _self->riffData.format = fmtChunk->audioFormat;
    size_t expectedFmtSize = 0;
    switch (_self->riffData.format) {
        case WAVE_FORMAT_PCM:
            expectedFmtSize = FMT_CHUNK_SIZE_PCM - FMT_CHUNK_SIZE_OFFSET;
            break;

        case WAVE_FORMAT_IEEE_FLOAT:
        case WAVE_FORMAT_ALAW:
        case WAVE_FORMAT_MULAW:
            expectedFmtSize = FMT_CHUNK_SIZE_NON_PCM - FMT_CHUNK_SIZE_OFFSET;
            break;

        case WAVE_FORMAT_EXTENSIBLE:
            expectedFmtSize = FMT_CHUNK_SIZE_EXTENSIBLE - FMT_CHUNK_SIZE_OFFSET;
            break;

        default:
            _self->error->type = AUDIO_ERROR_NO_PCM_FORMAT;
            _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
            return false;
            break;
    }
    if (fmtChunk->fmtSize != expectedFmtSize) {
        _self->error->type = AUDIO_ERROR_INVALID_FMT_SIZE;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }

    // Read the fmt chunk extension based on the format
    switch (_self->riffData.format) {
        case WAVE_FORMAT_IEEE_FLOAT:
        case WAVE_FORMAT_ALAW:
        case WAVE_FORMAT_MULAW:
            AudioNonPcmFmtChunkExtension *nonPcmExtension = 
            (AudioNonPcmFmtChunkExtension*)(
                (uint8_t*)fmtChunk + sizeof(AudioFmtChunk)
            );
            if (!_readNonPcmFmtChunkExtension(_self, nonPcmExtension)) {
                return false;
            }
            break;

        case WAVE_FORMAT_EXTENSIBLE:
            AudioExtensibleFmtChunkExtension *extensibleExtension = 
            (AudioExtensibleFmtChunkExtension*)(
                (uint8_t*)fmtChunk + sizeof(AudioFmtChunk)
            );
            if (!_readExtensibleFmtChunkExtension(_self, extensibleExtension)) {
                return false;
            }
            break;

        case WAVE_FORMAT_PCM:
            // PCM has no extension
            break;

        default:
            assert(false && "This should never happen.");
    }

    // Read the rest of the fmt chunk and check if all invariants hold true.
    _self->riffData.channelAmount = fmtChunk->numChannels;
    _self->riffData.channelAmount = fmtChunk->numChannels;
    _self->riffData.sampleRate = fmtChunk->sampleRate;
    _self->riffData.byteRate = fmtChunk->byteRate;
    _self->riffData.blockAlign = fmtChunk->blockAlign;
    _self->riffData.bitsPerSample = fmtChunk->bitsPerSample;
    if (
        _self->riffData.byteRate 
        != _self->riffData.sampleRate 
            * _self->riffData.channelAmount 
            * _self->riffData.bitsPerSample / BITS_PER_BYTE
    ) {
        _self->error->type = AUDIO_ERROR_INVALID_BYTE_RATE;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    if (
        _self->riffData.blockAlign 
        != _self->riffData.channelAmount 
            * _self->riffData.bitsPerSample / BITS_PER_BYTE
    ) {
        _self->error->type = AUDIO_ERROR_INVALID_BLOCK_ALIGN;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    return true;
}

bool _readRiffFile(_AudioObject *_self, void *rawData, size_t rawDataSize) {
    // Read entire WAV file and check if all invariants hold true.

    // check RIFF header
    AudioRiffHeader *riffHeader = (AudioRiffHeader*)rawData;
    if (memcmp(riffHeader->riffMagic, RIFF_MAGIC, MAGIC_SIZE)) {
        _self->error->type = AUDIO_ERROR_INVALID_RIFF_MAGIC_NUMBER;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    if (memcmp(riffHeader->waveMagic, WAVE_MAGIC, MAGIC_SIZE)) {
        _self->error->type = AUDIO_ERROR_INVALID_WAVE_MAGIC_NUMBER;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    if (
        riffHeader->fileSize 
        != rawDataSize - (riffHeader->waveMagic - (uint8_t*)riffHeader)
    ) {
        _self->error->type = AUDIO_ERROR_INVALID_FILE_SIZE;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }

    // check and read fmt chunk
    AudioFmtChunk *fmtChunk = (AudioFmtChunk*)(
        (uint8_t*)rawData + sizeof(AudioRiffHeader)
    );
    if (!_readFmtChunk(_self, fmtChunk)) {
        return false;
    }

    // look for begin of data chunk
    size_t dataChunkOffset = sizeof(AudioRiffHeader) + sizeof(AudioFmtChunk);
    while (memcmp(
        (uint8_t*)rawData + dataChunkOffset, DATA_MAGIC, MAGIC_SIZE
    )) {
        dataChunkOffset++;
        if (dataChunkOffset >= rawDataSize) {
            _self->error->type = AUDIO_ERROR_DATA_CHUNK_NOT_FOUND;
            _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
            return false;
        }
    }

    // check and read data chunk
    AudioDataChunk *dataChunk = (AudioDataChunk*)(
        (uint8_t*)rawData + dataChunkOffset
    );
    if (memcmp(dataChunk->dataMagic, DATA_MAGIC, MAGIC_SIZE)) {
        _self->error->type = AUDIO_ERROR_INVALID_DATA_MAGIC_NUMBER;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    _self->riffData.dataSize = dataChunk->dataSize;
    if (
        _self->riffData.dataSize 
        != rawDataSize 
            - dataChunkOffset
            - sizeof(AudioDataChunk)
        ) {
        _self->error->type = AUDIO_ERROR_INVALID_DATA_SIZE;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }

    // This is the pointer to the audio data itself.
    _self->riffData.data = (uint8_t*)rawData 
        + sizeof(AudioRiffHeader) 
        + sizeof(AudioFmtChunk) 
        + dataChunkOffset
        + sizeof(AudioDataChunk);

    // Compute the length of the entire audio in milliseconds
    _self->riffData.audioLength = (uint32_t)(_self->riffData.dataSize)
        * MILLISECONDS_PER_SECOND 
        / (uint64_t)(_self->riffData.byteRate);

    // Check if the amount of samples per channel is correct
    if (
        _self->riffData.samplesPerChannel 
        != (_self->riffData.sampleRate 
            * _self->riffData.audioLength) / MILLISECONDS_PER_SECOND
        && _self->riffData.format != WAVE_FORMAT_PCM
    ) {
        _self->error->type = AUDIO_ERROR_INVALID_SAMPLES_PER_CHANNEL;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }

    return true;
}

bool _setSoundDeviceName(
    _AudioObject *audioObject, AudioConfiguration *configuration
) {
    /* This function determines the name of the audio device used
    * to play the audio. It can be specifed by the user. If the user
    * passes NULL it is set to the default device. */
    if (configuration->soundDeviceName == NULL) {
        // Use the default name and remember that it was not set by the user.
        audioObject->soundDeviceName = DEFAULT_SOUND_DEVICE_NAME;
        audioObject->soundDeviceNameSetByUser = false;
    } else {
        // Allocate memory for the device name
        audioObject->soundDeviceName = (char*)calloc(
            configuration->soundDeviceNameSize + 1, sizeof(char)
        );
        // Fail if allocation failed
        if (audioObject->soundDeviceName == NULL) {
            audioObject->error->type = AUDIO_ERROR_MEMORY_ALLOCATION_FAILED;
            audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
            return false;
        }
        // Copy the name to the allocatec memory
        memcpy(
            audioObject->soundDeviceName, 
            configuration->soundDeviceName, 
            configuration->soundDeviceNameSize
        );
        // Remember that it was set to free the allocated memory later.
        audioObject->soundDeviceNameSetByUser = true;
    }
    return true;
}

bool _setChannelMap(_AudioObject *audioObject) {
    // Create a new channel map instance and set the amount of channels.
    snd_pcm_chmap_t *channelMap = (snd_pcm_chmap_t*)calloc(
        1, 
        sizeof(snd_pcm_chmap_t) 
            + audioObject->riffData.channelAmount 
            * sizeof(unsigned int)
    );
    if (channelMap == NULL) {
        audioObject->error->type = AUDIO_ERROR_MEMORY_ALLOCATION_FAILED;
        audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    channelMap->channels = audioObject->riffData.channelAmount;

    // Set the channel positions based on the channel map.
    if ((audioObject->riffData.channelMap & CHANNEL_MASK_18) == 0) {
        // If the channel map is 0, use the default channel positions.
        for (int i = 0; i < audioObject->riffData.channelAmount; ++i) {
            channelMap->pos[i] = all_channel_positions[i];
        }
    } else {
        for (int i = 0, j = 0; i < CHANNEL_POSITION_COUNT; ++i) {
            if (audioObject->riffData.channelMap & (1 << i)) {
                channelMap->pos[j++] = all_channel_positions[i];
                if (j >= audioObject->riffData.channelAmount) break;
            }
        }
    }
    int error = snd_pcm_set_chmap(audioObject->pcmHandle, channelMap);
    free(channelMap);
    // ENXIO means that the device does not support channel mapping.
    // We don't want to fail in this case.
    if (error && error != -ENXIO) {  
        audioObject->error->type = AUDIO_ERROR_ALSA_ERROR;
        audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
        audioObject->error->alsaErrorNumber = error;
        return false;
    }
    return true;
}

AudioObject * audioInit(AudioConfiguration *configuration) {
    _AudioObject *audioObject = (_AudioObject*)calloc(1, sizeof(_AudioObject));
    if (audioObject == NULL) { return NULL; }

    // Initialize the error object
    audioObject->error = (AudioError*)calloc(1, sizeof(AudioError));
    if (audioObject->error == NULL) { 
        free(audioObject);
        return NULL; 
    }
    _resetError(audioObject);

    // Read the input file. From here on in case of an error an incomplete
    // audioObject is returned containing a error object describing
    // what went wrong.
    if (!_readRiffFile(
        audioObject, configuration->rawData, configuration->rawDataSize
    )) {
        return (AudioObject*)audioObject;
    }

    if (!_setSoundDeviceName(audioObject, configuration)) {
        return (AudioObject*)audioObject;
    }

    // Initialize an ALSA pcm object
    if ((audioObject->error->alsaErrorNumber = snd_pcm_open(
        &audioObject->pcmHandle, 
        audioObject->soundDeviceName, 
        SND_PCM_STREAM_PLAYBACK, 
        PCM_BLOCK_MODE
    )) < 0) {
        audioObject->error->type = AUDIO_ERROR_ALSA_ERROR;
        audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return (AudioObject*)audioObject;
    }

    // Set the channel map
    if (!_setChannelMap(audioObject)) {
        return (AudioObject*)audioObject;
    }

    // Allocate space for pcm hardware parameters and initialize them.
    snd_pcm_hw_params_t *hardwareParameters;
    snd_pcm_hw_params_alloca(&hardwareParameters);

    if ((audioObject->error->alsaErrorNumber = snd_pcm_hw_params_any(
        audioObject->pcmHandle, hardwareParameters
    )) < 0) {
        audioObject->error->type = AUDIO_ERROR_ALSA_ERROR;
        audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return (AudioObject*)audioObject;
    }

    // Tell ALSA that the channels are stored in an interleaved format
    if ((audioObject->error->alsaErrorNumber = snd_pcm_hw_params_set_access(
        audioObject->pcmHandle, 
        hardwareParameters, 
        SND_PCM_ACCESS_RW_INTERLEAVED
    )) < 0) {
        audioObject->error->type = AUDIO_ERROR_ALSA_ERROR;
        audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return (AudioObject*)audioObject;
    }

    // Determine the pcm format from the WAV format and the bits per sample
    snd_pcm_format_t format;
    switch (audioObject->riffData.format) {
        case WAVE_FORMAT_PCM:
            switch (audioObject->riffData.bitsPerSample) {
                case 8:  format = SND_PCM_FORMAT_U8;         break;
                case 16: format = SND_PCM_FORMAT_S16_LE;     break;
                case 24: format = SND_PCM_FORMAT_S24_3LE;    break;
                case 32: format = SND_PCM_FORMAT_S32_LE;     break;
                default:
                    audioObject->error->type = AUDIO_UNSUPPORTED_BITS_PER_SAMPLE;
                    audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
                    return (AudioObject*)audioObject;
            }
            break;

        case WAVE_FORMAT_IEEE_FLOAT:
            switch (audioObject->riffData.bitsPerSample) {
                case 32: format = SND_PCM_FORMAT_FLOAT_LE; break;
                case 64: format = SND_PCM_FORMAT_FLOAT64_LE; break;
                default:
                    audioObject->error->type = AUDIO_UNSUPPORTED_BITS_PER_SAMPLE;
                    audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
                    return (AudioObject*)audioObject;
            }
            break;

        case WAVE_FORMAT_ALAW:
            switch (audioObject->riffData.bitsPerSample) {
                case 8: format = SND_PCM_FORMAT_A_LAW; break;
                default:
                    audioObject->error->type = AUDIO_UNSUPPORTED_BITS_PER_SAMPLE;
                    audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
                    return (AudioObject*)audioObject;
            }
            break;

        case WAVE_FORMAT_MULAW:
            switch (audioObject->riffData.bitsPerSample) {
                case 8: format = SND_PCM_FORMAT_MU_LAW; break;
                default:
                    audioObject->error->type = AUDIO_UNSUPPORTED_BITS_PER_SAMPLE;
                    audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
                    return (AudioObject*)audioObject;
            }
            break;

        default:
            audioObject->error->type = AUDIO_UNSUPPORTED_FORMAT;
            audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
            return (AudioObject*)audioObject;
            break;
    }

    if ((audioObject->error->alsaErrorNumber = snd_pcm_hw_params_set_format(
        audioObject->pcmHandle, hardwareParameters, format
    )) < 0) {
        audioObject->error->type = AUDIO_ERROR_ALSA_ERROR;
        audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return (AudioObject*)audioObject;
    }

    // Set the amount of channels (1 in mono, 2 is stereo, ...)
    if ((audioObject->error->alsaErrorNumber = snd_pcm_hw_params_set_channels(
        audioObject->pcmHandle, 
        hardwareParameters, 
        audioObject->riffData.channelAmount
    )) < 0) {
        audioObject->error->type = AUDIO_ERROR_ALSA_ERROR;
        audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return (AudioObject*)audioObject;
    }

    // Set the sample rate
    if ((audioObject->error->alsaErrorNumber = snd_pcm_hw_params_set_rate(
        audioObject->pcmHandle, 
        hardwareParameters, 
        audioObject->riffData.sampleRate, 
        PCM_SEARCH_DIRECTION_NEAR
    )) < 0) {
        audioObject->error->type = AUDIO_ERROR_ALSA_ERROR;
        audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return (AudioObject*)audioObject;
    }

    // Set the ALSA ring buffer size
    snd_pcm_uframes_t bufferSizeInSamples = audioObject->riffData.sampleRate 
        * BUFFER_SIZE_FACTOR
        * configuration->timeResolution
        / MILLISECONDS_PER_SECOND;
    audioObject->alsaBufferSize = bufferSizeInSamples;
    if ((audioObject->error->alsaErrorNumber = snd_pcm_hw_params_set_buffer_size(
        audioObject->pcmHandle, hardwareParameters, bufferSizeInSamples
    )) < 0) {
        audioObject->error->type = AUDIO_ERROR_ALSA_ERROR;
        audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return (AudioObject*)audioObject;
    }

    // Put the parameters into the pcm object
    if ((audioObject->error->alsaErrorNumber = snd_pcm_hw_params(
        audioObject->pcmHandle, hardwareParameters
    )) < 0) {
        audioObject->error->type = AUDIO_ERROR_ALSA_ERROR;
        audioObject->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return (AudioObject*)audioObject;
    }

    // Set the remaining members of the audioObject. For explanation see
    // the type definition.

    audioObject->timeResolution = configuration->timeResolution;
    audioObject->currentFrame = 0;
    audioObject->lastFrame = audioObject->riffData.dataSize 
        / audioObject->riffData.blockAlign;

    audioObject->thread = (pthread_t*)calloc(1, sizeof(pthread_t));
    audioObject->externalBarrier = NULL;
    audioObject->internalBarrier = (pthread_barrier_t*)calloc(
        1, sizeof(pthread_barrier_t)
    );
    audioObject->actionLock = (pthread_mutex_t*)calloc(
        1, sizeof(pthread_mutex_t)
    );
    pthread_mutex_init(audioObject->actionLock, NULL);

    audioObject->isPlaying = false;
    audioObject->isPaused = false;

    audioObject->playFlag = false;
    audioObject->pauseFlag = false;
    audioObject->stopFlag = false;
    audioObject->haltFlag = false;
    audioObject->jumpFlag = false;
    audioObject->jumpTarget = 0;

    // Start the audio thread and return the assembled object
    pthread_create(audioObject->thread, NULL, _mainloop, (void*)audioObject);
    return (AudioObject)audioObject;
}

void audioDestroy(AudioObject self) {
    _AudioObject *_self = (_AudioObject*)self;

    _self->haltFlag = true;
    if (_self->thread) {
        pthread_join(*(_self->thread), NULL);
        free(_self->thread);
    }
    
    if (_self->pcmHandle) {
        snd_pcm_drop(_self->pcmHandle);
        snd_pcm_close(_self->pcmHandle);
    }

    if (_self->externalBarrier) {
        pthread_barrier_destroy(_self->externalBarrier);
        free(_self->externalBarrier);
    }
    if (_self->actionLock) {
        pthread_mutex_destroy(_self->actionLock);
        free(_self->actionLock);
    }

    if (_self->soundDeviceNameSetByUser) free(_self->soundDeviceName);
    if (_self->error) free(_self->error);

    free(_self);
}

/**
 * @brief This function locks the action lock and checks if the action is allowed.
*/
bool _lockAction(
    _AudioObject *_self, pthread_barrier_t *barrier, bool predicate
) {
    // This lock prevents any other action from being processed while
    // the current action is being processed.
    pthread_mutex_lock(_self->actionLock);

    // If the predicate is false the action is not allowed.
    if (!predicate) {
        pthread_mutex_unlock(_self->actionLock);
        return false;
    }

    // If an external barrier is used, wait for it.
    _self->externalBarrier = barrier;
    pthread_barrier_init(
        _self->internalBarrier, NULL, INTERNAL_BARRIER_COUNT
    );

    return true;
}

/**
 * @brief This function unlocks the action lock and waits for the audio thread to process the action.
*/
void _unlockAction(_AudioObject *_self) {
    // wait for the audio thread to process the action
    pthread_barrier_wait(_self->internalBarrier);
    pthread_barrier_destroy(_self->internalBarrier);

    pthread_mutex_unlock(_self->actionLock);
}

bool audioPlay(AudioObject self, pthread_barrier_t *barrier) {
    _AudioObject *_self = (_AudioObject*)self;
    _resetError(_self);
    if (!_lockAction(
        _self, barrier, 
        !_self->isPlaying  // Only allow playing if not already playing
    )) {
        _self->error->type = AUDIO_WARNING_ALREADY_PLAYING;
        _self->error->level = AUDIO_ERROR_LEVEL_WARNING;
        return false;
    }

    _self->playFlag = true;

    _unlockAction(_self);
    return true;
}

bool audioPause(AudioObject self, pthread_barrier_t *barrier) {
    _AudioObject *_self = (_AudioObject*)self;
    _resetError(_self);
    if (!_lockAction(
        _self, barrier, 
        _self->isPlaying  // Only allow pausing if playing
    )) {
        _self->error->type = AUDIO_WARNING_ALREADY_PAUSED;
        _self->error->level = AUDIO_ERROR_LEVEL_WARNING;
        return false;
    }

    _self->pauseFlag = true;

    _unlockAction(_self);
    return true;
}

void audioStop(AudioObject self, pthread_barrier_t *barrier) {
    _AudioObject *_self = (_AudioObject*)self;
    _resetError(_self);
    _lockAction(_self, barrier, true);

    _self->stopFlag = true;

    _unlockAction(_self);
}

bool audioJump(
    AudioObject self, pthread_barrier_t *barrier, uint32_t milliseconds
) {
    _AudioObject *_self = (_AudioObject*)self;
    _resetError(_self);
    _lockAction(_self, barrier, true);

    _self->jumpFlag = true;
    if (milliseconds > _self->riffData.audioLength) {
        _self->error->type = AUDIO_WARNING_JUMPED_BEYOND_END;
        _self->error->level = AUDIO_ERROR_LEVEL_WARNING;
        return false;
    }
    _self->jumpTarget = milliseconds;

    _unlockAction(_self);
    return true;
}

bool audioGetIsPlaying(AudioObject self) { 
    _AudioObject *_self = (_AudioObject*)self;
    _resetError(_self);
    return _self->isPlaying; 
}

bool audioGetIsPaused(AudioObject self) { 
    _AudioObject *_self = (_AudioObject*)self;
    _resetError(_self);
    return _self->isPaused; 
}

uint32_t audioGetCurrentTime(AudioObject self) {
    _AudioObject *_self = (_AudioObject*)self;
    _resetError(_self);
    return (uint32_t)(_self->currentFrame)
        * MILLISECONDS_PER_SECOND
        / (uint32_t)(_self->riffData.sampleRate);
}

uint32_t audioGetTotalDuration(AudioObject self) { 
    _AudioObject *_self = (_AudioObject*)self;
    _resetError(_self);
    return _self->riffData.audioLength; 
}

bool _getMixerMasterElement(
    _AudioObject *_self, 
    snd_mixer_t **mixerHandle, snd_mixer_elem_t **masterElement
) {
    // Open mixer
    if ((_self->error->alsaErrorNumber = snd_mixer_open(mixerHandle, 0)) < 0) {
        _self->error->type = AUDIO_ERROR_ALSA_ERROR;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    if (
        (_self->error->alsaErrorNumber = snd_mixer_attach(
            *mixerHandle, _self->soundDeviceName
    )) < 0) {
        snd_mixer_close(*mixerHandle);
        _self->error->type = AUDIO_ERROR_ALSA_ERROR;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    if ((_self->error->alsaErrorNumber = snd_mixer_selem_register(
        *mixerHandle, NULL, NULL
    )) < 0) {
        snd_mixer_close(*mixerHandle);
        _self->error->type = AUDIO_ERROR_ALSA_ERROR;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }
    if ((_self->error->alsaErrorNumber = snd_mixer_load(*mixerHandle)) < 0) {
        snd_mixer_close(*mixerHandle);
        _self->error->type = AUDIO_ERROR_ALSA_ERROR;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }

    // Open the master element
    snd_mixer_selem_id_t *elementId;
    snd_mixer_selem_id_alloca(&elementId);
    snd_mixer_selem_id_set_index(elementId, 0);
    snd_mixer_selem_id_set_name(elementId, "Master");
    if ((*masterElement = snd_mixer_find_selem(*mixerHandle, elementId)) == NULL) {
        snd_mixer_close(*mixerHandle);
        _self->error->type = AUDIO_ERROR_MIXER_ELEMENT_NOT_FOUND;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }

    return true;
}

uint8_t audioGetVolume(AudioObject self) {
    _AudioObject *_self = (_AudioObject*)self;

    snd_mixer_t *mixerHandle;
    snd_mixer_elem_t *masterElement;
    if (!_getMixerMasterElement(_self, &mixerHandle, &masterElement)) {
        return 0;
    }

    // Get the volume
    long minVolume, maxVolume, volume;
    snd_mixer_selem_get_playback_volume_range(masterElement, &minVolume, &maxVolume);  
    if ((_self->error->alsaErrorNumber = snd_mixer_selem_get_playback_volume(
        masterElement, SND_MIXER_SCHN_MONO, &volume
    )) < 0) {
        snd_mixer_close(mixerHandle);
        _self->error->type = AUDIO_ERROR_ALSA_ERROR;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return 0;
    }

    snd_mixer_close(mixerHandle);
    return (uint8_t)(volume * MAX_VOLUME / maxVolume);
}

bool audioSetVolume(AudioObject self, uint8_t volume) {
    _AudioObject *_self = (_AudioObject*)self;

    if (volume > MAX_VOLUME) volume = MAX_VOLUME;

    snd_mixer_t *mixerHandle;
    snd_mixer_elem_t *masterElement;
    if (!_getMixerMasterElement(_self, &mixerHandle, &masterElement)) {
        return false;
    }

    // Set the volume
    long minVolume, maxVolume;
    snd_mixer_selem_get_playback_volume_range(masterElement, &minVolume, &maxVolume);
    if ((_self->error->alsaErrorNumber = snd_mixer_selem_set_playback_volume_all(
        masterElement, (volume * maxVolume) / MAX_VOLUME
    )) < 0) {
        snd_mixer_close(mixerHandle);
        _self->error->type = AUDIO_ERROR_ALSA_ERROR;
        _self->error->level = AUDIO_ERROR_LEVEL_ERROR;
        return false;
    }

    snd_mixer_close(mixerHandle);

    return true;
}

AudioError * audioGetError(AudioObject self) {
    _AudioObject *_self = (_AudioObject*)self;
    return _self->error;
}

const char * audioGetErrorString(AudioError *error) {
    switch (error->type) {
        // info
        case AUDIO_ERROR_NO_ERROR:
            return "No error";
            
        // warnings
        case AUDIO_WARNING_ALREADY_PLAYING:
            return "Audio is already playing";

        case AUDIO_WARNING_ALREADY_PAUSED:
            return "Audio is already paused";

        case AUDIO_WARNING_JUMPED_BEYOND_END:
            return "Jumped beyond end of audio";

        // errors
        // reading riff file
        case AUDIO_ERROR_FILE_TOO_SMALL:
            return "RIFF file is too small";

        case AUDIO_ERROR_INVALID_RIFF_MAGIC_NUMBER:
            return "RIFF magic is invalid";

        case AUDIO_ERROR_INVALID_WAVE_MAGIC_NUMBER:
            return "WAVE magic is invalid";

        case AUDIO_ERROR_INVALID_FILE_SIZE:
            return "RIFF file size is invalid";

        case AUDIO_ERROR_IMVALID_FMT_MAGIC_NUMBER:
            return "FMT magic is invalid";

        case AUDIO_ERROR_INVALID_FMT_SIZE:
            return "FMT size is invalid";

        case AUDIO_ERROR_NO_PCM_FORMAT:
            return "Audio format is not PCM";

        case AUDIO_ERROR_INVALID_BYTE_RATE:
            return "Byte rate is invalid";

        case AUDIO_ERROR_INVALID_BLOCK_ALIGN:
            return "Block align is invalid";

        case AUDIO_ERROR_DATA_CHUNK_NOT_FOUND:
            return "DATA chunk not found";

        case AUDIO_ERROR_INVALID_DATA_MAGIC_NUMBER:
            return "DATA magic is invalid";

        case AUDIO_ERROR_INVALID_DATA_SIZE:
            return "DATA size is invalid";

        case AUDIO_ERROR_INVALID_FACT_MAGIC_NUMBER:
            return "FACT magic is invalid";

        case AUDIO_ERROR_INVALID_FACT_SIZE:
            return "FACT size is invalid";

        case AUDIO_ERROR_INVALID_NON_PCM_EXTENSION_SIZE:
            return "Non PCM extension size is invalid";

        case AUDIO_ERROR_INVALID_EXTENSIBLE_EXTENSION_SIZE:
            return "Extensible extension size is invalid";

        case AUDIO_ERROR_INVALID_EXTENSIBLE_AUDIO_FORMAT:
            return "Extensible audio format is invalid";

        case AUDIO_ERROR_INVALID_EXTENSIBLE_GUID:
            return "Extensible GUID is invalid";

        case AUDIO_ERROR_INVALID_SAMPLES_PER_CHANNEL:
            return "Samples per channel is invalid";

        case AUDIO_UNSUPPORTED_FORMAT:
            return "Unsupported format";

        // alsa
        case AUDIO_ERROR_ALSA_ERROR:
            return snd_strerror(error->alsaErrorNumber);

        case AUDIO_ERROR_MIXER_ELEMENT_NOT_FOUND:
            return "Mixer element not found";

        // other
        case AUDIO_ERROR_MEMORY_ALLOCATION_FAILED:
            return "Memory allocation failed";

        case AUDIO_UNSUPPORTED_BITS_PER_SAMPLE:
            return "Unsupported bits per sample";

        default:
            return "Unknown error";
    }
}
