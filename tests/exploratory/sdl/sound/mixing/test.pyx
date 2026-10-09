# cython: language_level=3
from libc.stdint cimport uint8_t, uint16_t, uint32_t
from libc.math cimport sin, exp, M_PI
from libc.stdlib cimport malloc, free

cdef extern from "SDL2/SDL.h" nogil:
    ctypedef uint32_t Uint32
    ctypedef uint16_t Uint16
    ctypedef uint8_t Uint8
    ctypedef Uint32 SDL_AudioDeviceID
    ctypedef Uint16 SDL_AudioFormat

    cdef Uint32 SDL_INIT_AUDIO
    cdef SDL_AudioFormat AUDIO_F32SYS

    ctypedef void (*SDL_AudioCallback)(void *userdata, Uint8 *stream, int len) noexcept nogil

    cdef struct SDL_AudioSpec:
        int freq
        SDL_AudioFormat format
        Uint8 channels
        Uint8 silence
        Uint16 samples
        Uint32 size
        SDL_AudioCallback callback
        void *userdata

    int SDL_Init(Uint32 flags)
    void SDL_Quit()
    SDL_AudioDeviceID SDL_OpenAudioDevice(
        const char *device,
        int iscapture,
        const SDL_AudioSpec *desired,
        SDL_AudioSpec *obtained,
        int allowed_changes
    )
    void SDL_PauseAudioDevice(SDL_AudioDeviceID dev, int pause_on)
    void SDL_CloseAudioDevice(SDL_AudioDeviceID dev)
    void SDL_Delay(Uint32 ms)
    const char *SDL_GetError()

cdef struct Note:
    float freq
    float duration

# Melodic definition for the opening motif of Für Elise
cdef Note SCORE[27]
SCORE[0]  = Note(659.25, 0.16)  # E5
SCORE[1]  = Note(622.25, 0.16)  # D#5
SCORE[2]  = Note(659.25, 0.16)  # E5
SCORE[3]  = Note(622.25, 0.16)  # D#5
SCORE[4]  = Note(659.25, 0.16)  # E5
SCORE[5]  = Note(493.88, 0.16)  # B4
SCORE[6]  = Note(587.33, 0.16)  # D5
SCORE[7]  = Note(523.25, 0.16)  # C5
SCORE[8]  = Note(440.00, 0.40)  # A4
SCORE[9]  = Note(261.63, 0.16)  # C4
SCORE[10] = Note(329.63, 0.16)  # E4
SCORE[11] = Note(440.00, 0.16)  # A4
SCORE[12] = Note(493.88, 0.40)  # B4
SCORE[13] = Note(329.63, 0.16)  # E4
SCORE[14] = Note(415.30, 0.16)  # G#4
SCORE[15] = Note(493.88, 0.16)  # B4
SCORE[16] = Note(523.25, 0.40)  # C5
SCORE[17] = Note(329.63, 0.16)  # E4
SCORE[18] = Note(659.25, 0.16)  # E5
SCORE[19] = Note(622.25, 0.16)  # D#5
SCORE[20] = Note(659.25, 0.16)  # E5
SCORE[21] = Note(622.25, 0.16)  # D#5
SCORE[22] = Note(659.25, 0.16)  # E5
SCORE[23] = Note(493.88, 0.16)  # B4
SCORE[24] = Note(587.33, 0.16)  # D5
SCORE[25] = Note(523.25, 0.16)  # C5
SCORE[26] = Note(440.00, 0.60)  # A4

cdef struct SynthState:
    int sample_rate
    const Note *score
    int total_notes
    int current_note_idx
    int note_sample_pos
    int note_total_samples
    double phase1
    double phase2
    double phase3
    int finished

cdef void audio_callback(void *userdata, Uint8 *stream, int len) noexcept nogil:
    cdef SynthState *synth = <SynthState *>userdata
    cdef float *buffer = <float *>stream
    cdef int num_samples = len // sizeof(float)
    cdef int i
    cdef float freq, t, env, sample
    cdef const Note *note

    for i in range(num_samples):
        if synth.current_note_idx >= synth.total_notes:
            buffer[i] = 0.0
            synth.finished = 1
            continue

        note = &synth.score[synth.current_note_idx]
        freq = note.freq
        t = <float>synth.note_sample_pos / <float>synth.sample_rate

        # Exponential decay envelope with 5ms linear attack
        if t < 0.005:
            env = t / 0.005
        else:
            env = exp(-3.2 * (t / note.duration))

        # Phase accumulation across fundamental and harmonics
        synth.phase1 += (2.0 * M_PI * freq) / synth.sample_rate
        if synth.phase1 > 2.0 * M_PI:
            synth.phase1 -= 2.0 * M_PI

        synth.phase2 += (2.0 * M_PI * (freq * 2.0)) / synth.sample_rate
        if synth.phase2 > 2.0 * M_PI:
            synth.phase2 -= 2.0 * M_PI

        synth.phase3 += (2.0 * M_PI * (freq * 3.0)) / synth.sample_rate
        if synth.phase3 > 2.0 * M_PI:
            synth.phase3 -= 2.0 * M_PI

        # Additive synthesis with decaying harmonic weights
        sample = (0.65 * sin(synth.phase1) +
                  0.25 * sin(synth.phase2) +
                  0.10 * sin(synth.phase3)) * env * 0.35

        buffer[i] = sample
        synth.note_sample_pos += 1

        if synth.note_sample_pos >= synth.note_total_samples:
            synth.current_note_idx += 1
            synth.note_sample_pos = 0
            synth.phase1 = 0.0
            synth.phase2 = 0.0
            synth.phase3 = 0.0
            if synth.current_note_idx < synth.total_notes:
                synth.note_total_samples = <int>(synth.score[synth.current_note_idx].duration * synth.sample_rate)

def play():
    if SDL_Init(SDL_INIT_AUDIO) < 0:
        raise RuntimeError(f"Failed to initialize SDL: {SDL_GetError().decode('utf-8')}")

    cdef SynthState *synth = <SynthState *>malloc(sizeof(SynthState))
    if synth == NULL:
        SDL_Quit()
        raise MemoryError("Failed to allocate synthesizer state.")

    synth.sample_rate = 48000
    synth.score = SCORE
    synth.total_notes = sizeof(SCORE) // sizeof(Note)
    synth.current_note_idx = 0
    synth.note_sample_pos = 0
    synth.note_total_samples = <int>(SCORE[0].duration * synth.sample_rate)
    synth.phase1 = 0.0
    synth.phase2 = 0.0
    synth.phase3 = 0.0
    synth.finished = 0

    cdef SDL_AudioSpec desired
    cdef SDL_AudioSpec obtained

    desired.freq = synth.sample_rate
    desired.format = AUDIO_F32SYS
    desired.channels = 1
    desired.samples = 1024
    desired.callback = audio_callback
    desired.userdata = synth

    cdef SDL_AudioDeviceID dev = SDL_OpenAudioDevice(
        NULL, 0, &desired, &obtained, 0
    )

    if dev == 0:
        free(synth)
        err = SDL_GetError().decode('utf-8')
        SDL_Quit()
        raise RuntimeError(f"Failed to open audio device: {err}")

    SDL_PauseAudioDevice(dev, 0)

    try:
        while not synth.finished:
            SDL_Delay(50)
    finally:
        SDL_PauseAudioDevice(dev, 1)
        SDL_CloseAudioDevice(dev)
        free(synth)
        SDL_Quit()