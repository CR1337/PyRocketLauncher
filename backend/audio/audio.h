#ifndef __AUDIO_H__
#define __AUDIO_H__

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <pthread.h>
#include <alsa/asoundlib.h>

/**
 * @brief This represents the type of an audio error.
*/
enum AudioErrorType {
    // info
    AUDIO_ERROR_NO_ERROR,  /* No error occurred. */

    // warnings
    AUDIO_WARNING_ALREADY_PLAYING,  /* The audio is already playing. */
    AUDIO_WARNING_ALREADY_PAUSED,  /* The audio is already paused. */
    AUDIO_WARNING_JUMPED_BEYOND_END,  /* The given time is beyond the end of the audio. */

    // errors
    // reading riff file
    AUDIO_ERROR_FILE_TOO_SMALL,  /* The file is too small. */
    AUDIO_ERROR_INVALID_RIFF_MAGIC_NUMBER,  /* The RIFF magic number is invalid. */
    AUDIO_ERROR_INVALID_WAVE_MAGIC_NUMBER,  /* The WAVE magic number is invalid. */
    AUDIO_ERROR_INVALID_FILE_SIZE,  /* The file size is invalid. */
    AUDIO_ERROR_IMVALID_FMT_MAGIC_NUMBER,  /* The fmt magic number is invalid. */
    AUDIO_ERROR_INVALID_FMT_SIZE,  /* The fmt size is invalid. */
    AUDIO_ERROR_NO_PCM_FORMAT,  /* The audio is not in PCM format. */
    AUDIO_ERROR_INVALID_BYTE_RATE,  /* The byte rate is invalid. */
    AUDIO_ERROR_INVALID_BLOCK_ALIGN,  /* The block align is invalid. */
    AUDIO_ERROR_DATA_CHUNK_NOT_FOUND,  /* The data chunk was not found. */
    AUDIO_ERROR_INVALID_DATA_MAGIC_NUMBER,  /* The data magic number is invalid. */
    AUDIO_ERROR_INVALID_DATA_SIZE,  /* The data size is invalid. */
    AUDIO_ERROR_INVALID_FACT_MAGIC_NUMBER,  /* The fact magic number is invalid. */
    AUDIO_ERROR_INVALID_FACT_SIZE,  /* The fact size is invalid. */
    AUDIO_ERROR_INVALID_NON_PCM_EXTENSION_SIZE,  /* The non-PCM extension size is invalid. */
    AUDIO_ERROR_INVALID_EXTENSIBLE_EXTENSION_SIZE,  /* The extensible extension size is invalid. */
    AUDIO_ERROR_INVALID_EXTENSIBLE_AUDIO_FORMAT,  /* The extensible audio format is invalid. */
    AUDIO_ERROR_INVALID_EXTENSIBLE_GUID,  /* The extensible GUID is invalid. */
    AUDIO_ERROR_INVALID_SAMPLES_PER_CHANNEL,  /* The samples per channel is invalid. */
    AUDIO_UNSUPPORTED_FORMAT,  /* The format is not supported. */
    // alsa
    AUDIO_ERROR_ALSA_ERROR,  /* An ALSA error occurred. */
    AUDIO_ERROR_MIXER_ELEMENT_NOT_FOUND,  /* The mixer element was not found. */
    // other
    AUDIO_ERROR_MEMORY_ALLOCATION_FAILED,  /* Memory allocation failed. */
    AUDIO_UNSUPPORTED_BITS_PER_SAMPLE  /* The bits per sample are not supported. */
};

/**
 * @brief This represents the severity level of an audio error.
*/
enum AudioErrorLevel {
    AUDIO_ERROR_LEVEL_INFO = 0,  /* Just informational. */
    AUDIO_ERROR_LEVEL_WARNING = 1,  /* A warning. Everything works fine. */
    AUDIO_ERROR_LEVEL_ERROR = 2  /* An unrecoverable error. */
};

/**
 * @brief his represents an audio error.
*/
typedef struct {
    enum AudioErrorType type;  /* The type of the error. */
    enum AudioErrorLevel level;  /* The severity level of the error. */
    int alsaErrorNumber;  /* The ALSA error number if the error occured in the ALSA library. */
} AudioError;

/**
 * @brief This represents the configuration of the audio object.
 * 
 * The time resolution determines every how many milliseconds commands
 * like audioPlay() or audioPause() are processed.
*/
typedef struct {
    void *rawData;  /* The raw audio data as found in a WAV file. */
    size_t rawDataSize;  /* The size of the raw audio data. */
    char *soundDeviceName;  /* The name of the sound device to use. */
    size_t soundDeviceNameSize;  /* The size of the sound device name. */
    uint32_t timeResolution;  /* The time resolution in milliseconds. */
} AudioConfiguration;

/**
 * @brief This represents an opaque audio object. 
 * */ 
typedef void* AudioObject;

/**
 * Initializes the audio object with the given configuration.
 * 
 * Only if the initial memory allocation failed this function returns NULL.
 * Otherwise an AudioObject is returned. Therefore make sure to call
 * audioGetError() afterwards to check if the initialization was successful.
 * In any case (except when NULL is returned) audioDestroy() must be called
 * to free the resources.
 * 
 * @param configuration The configuration to use.
 * @return The audio object or NULL.
 * */
AudioObject * audioInit(AudioConfiguration *configuration);
/**
 * Frees the resources of the audio object.
 * 
 * @param self The audio object.
*/
void audioDestroy(AudioObject self);

/**
 * Plays the audio.
 * 
 * You can pass a barrier to wait on. This is useful if you want to synchronize
 * the audio with other threads. If you don't want to wait pass NULL.
 * 
 * If you call audioGetError() after this function you might get a 
 * WARNING_ALREADY_PLAYING error if the audio is already playing.
 * 
 * @param self The audio object.
 * @param barrier An optional barrier to wait on.
*/
bool audioPlay(AudioObject self, pthread_barrier_t *barrier);
/**
 * Pauses the audio.
 * 
 * You can pass a barrier to wait on. This is useful if you want to synchronize
 * the audio with other threads. If you don't want to wait pass NULL.
 * 
 * If you call audioGetError() after this function you might get a 
 * WARNING_ALREADY_PAUSED error if the audio is already paused.
 * 
 * @param self The audio object.
 * @param barrier An optional barrier to wait on.
*/
bool audioPause(AudioObject self, pthread_barrier_t *barrier);
/**
 * Stops the audio.
 * 
 * You can pass a barrier to wait on. This is useful if you want to synchronize
 * the audio with other threads. If you don't want to wait pass NULL.
 * 
 * If the audio is already stopped this function does nothing.
 * 
 * @param self The audio object.
 * @param barrier An optional barrier to wait on.
*/
void audioStop(AudioObject self, pthread_barrier_t *barrier);
/**
 * Jumps to the given time in milliseconds.
 * 
 * You can pass a barrier to wait on. This is useful if you want to synchronize
 * the audio with other threads. If you don't want to wait pass NULL.
 * 
 * If you call audioGetError() after this function you might get a 
 * WARNING_JUMPED_BEYOND_END error if the given time is beyond the end of the
 * audio. In that case the audio will be stopped.
 * 
 * @param self The audio object.
 * @param barrier An optional barrier to wait on.
 * @param milliseconds The time to jump to in milliseconds.
*/
bool audioJump(
    AudioObject self, pthread_barrier_t *barrier, uint32_t milliseconds
);

/**
 * Returns whether the audio is playing.
 * 
 * @param self The audio object.
 * @return Whether the audio is playing.
*/
bool audioGetIsPlaying(AudioObject self);
/**
 * Returns whether the audio is paused.
 * 
 * @param self The audio object.
 * @return Whether the audio is paused.
*/
bool audioGetIsPaused(AudioObject self);
/**
 * Returns the current time of the audio in milliseconds.
 * 
 * @param self The audio object.
*/
uint32_t audioGetCurrentTime(AudioObject self);
/**
 * Returns the total duration of the audio in milliseconds.
 * 
 * @param self The audio object.
*/
uint32_t audioGetTotalDuration(AudioObject self);

/**
 * Sets the master volume.
 * 
 * Values larger than 100 will be clamped to 100.
 * 
 * @param self The audio object.
 * @param volume The volume to set. Must be between 0 and 100.
*/
bool audioSetVolume(AudioObject self, uint8_t volume);
/**
 * Returns the master volume between 0 and 100.
 * 
 * @param self The audio object.
*/
uint8_t audioGetVolume(AudioObject self);

/**
 * Returns the last error that occurred.
 * 
 * @param self The audio object.
*/
AudioError * audioGetError(AudioObject self);
/**
 * Returns a string representation of the given error.
 * 
 * @param error The error.
*/
const char * audioGetErrorString(AudioError *error);

#endif // __AUDIO_H__
