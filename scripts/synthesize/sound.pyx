# cython: language_level=3
from libc.stdint cimport uint8_t, uint16_t, uint32_t
from libc.math cimport sin, exp, M_PI
from libc.stdlib cimport malloc, free

DEF MAX_VOICES = 8

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

cdef struct Chord:
    float freqs[MAX_VOICES]
    int voice_count
    float duration

cdef struct VoiceState:
    double phase1
    double phase2
    double phase3

cdef struct SynthState:
    int sample_rate
    Chord *score
    int total_chords
    int current_chord_idx
    int chord_sample_pos
    int chord_total_samples
    VoiceState voices[MAX_VOICES]
    int finished

cdef void audio_callback(void *userdata, Uint8 *stream, int len) noexcept nogil:
    cdef SynthState *synth = <SynthState *>userdata
    cdef float *buffer = <float *>stream
    cdef int num_samples = len // sizeof(float)
    cdef int i, v
    cdef float freq, t, env, mix_sample, v_sample
    cdef Chord *chord

    for i in range(num_samples):
        if synth.current_chord_idx >= synth.total_chords:
            buffer[i] = 0.0
            synth.finished = 1
            continue

        chord = &synth.score[synth.current_chord_idx]
        t = <float>synth.chord_sample_pos / <float>synth.sample_rate

        # Exponential decay envelope with 5ms click-suppression attack
        if t < 0.005:
            env = t / 0.005
        else:
            env = exp(-3.0 * (t / chord.duration))

        mix_sample = 0.0

        # Synthesize and mix each active voice in the chord
        for v in range(chord.voice_count):
            freq = chord.freqs[v]
            if freq <= 0.0:
                continue

            synth.voices[v].phase1 += (2.0 * M_PI * freq) / synth.sample_rate
            if synth.voices[v].phase1 > 2.0 * M_PI:
                synth.voices[v].phase1 -= 2.0 * M_PI

            synth.voices[v].phase2 += (2.0 * M_PI * (freq * 2.0)) / synth.sample_rate
            if synth.voices[v].phase2 > 2.0 * M_PI:
                synth.voices[v].phase2 -= 2.0 * M_PI

            synth.voices[v].phase3 += (2.0 * M_PI * (freq * 3.0)) / synth.sample_rate
            if synth.voices[v].phase3 > 2.0 * M_PI:
                synth.voices[v].phase3 -= 2.0 * M_PI

            v_sample = (0.65 * sin(synth.voices[v].phase1) +
                        0.25 * sin(synth.voices[v].phase2) +
                        0.10 * sin(synth.voices[v].phase3)) * env
            mix_sample += v_sample

        # Headroom attenuation to prevent saturation clipping
        if chord.voice_count > 1:
            mix_sample *= (0.35 / (1.0 + 0.45 * (chord.voice_count - 1)))
        else:
            mix_sample *= 0.35

        buffer[i] = mix_sample
        synth.chord_sample_pos += 1

        if synth.chord_sample_pos >= synth.chord_total_samples:
            synth.current_chord_idx += 1
            synth.chord_sample_pos = 0
            for v in range(MAX_VOICES):
                synth.voices[v].phase1 = 0.0
                synth.voices[v].phase2 = 0.0
                synth.voices[v].phase3 = 0.0
            if synth.current_chord_idx < synth.total_chords:
                synth.chord_total_samples = <int>(synth.score[synth.current_chord_idx].duration * synth.sample_rate)

def play(list chord_seq):
    cdef int total = len(chord_seq)
    if total == 0:
        return

    cdef Chord *score_buf = <Chord *>malloc(total * sizeof(Chord))
    if score_buf == NULL:
        raise MemoryError("Failed to allocate chord buffer.")

    cdef int i, j, v_count
    cdef list freqs
    for i in range(total):
        freqs = chord_seq[i][0]
        v_count = len(freqs)
        if v_count > MAX_VOICES:
            v_count = MAX_VOICES
        score_buf[i].voice_count = v_count
        score_buf[i].duration = <float>chord_seq[i][1]
        for j in range(v_count):
            score_buf[i].freqs[j] = <float>freqs[j]
        for j in range(v_count, MAX_VOICES):
            score_buf[i].freqs[j] = 0.0

    if SDL_Init(SDL_INIT_AUDIO) < 0:
        free(score_buf)
        raise RuntimeError(f"Failed to initialize SDL: {SDL_GetError().decode('utf-8')}")

    cdef SynthState *synth = <SynthState *>malloc(sizeof(SynthState))
    if synth == NULL:
        free(score_buf)
        SDL_Quit()
        raise MemoryError("Failed to allocate synth state.")

    synth.sample_rate = 48000
    synth.score = score_buf
    synth.total_chords = total
    synth.current_chord_idx = 0
    synth.chord_sample_pos = 0
    synth.chord_total_samples = <int>(score_buf[0].duration * synth.sample_rate)
    synth.finished = 0

    for j in range(MAX_VOICES):
        synth.voices[j].phase1 = 0.0
        synth.voices[j].phase2 = 0.0
        synth.voices[j].phase3 = 0.0

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
        free(score_buf)
        err = SDL_GetError().decode('utf-8')
        SDL_Quit()
        raise RuntimeError(f"Failed to open audio device: {err}")

    SDL_PauseAudioDevice(dev, 0)

    try:
        while not synth.finished:
            SDL_Delay(20)
    finally:
        SDL_PauseAudioDevice(dev, 1)
        SDL_CloseAudioDevice(dev)
        free(synth)
        free(score_buf)
        SDL_Quit()