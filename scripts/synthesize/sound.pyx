# cython: language_level=3
from libc.stdint cimport uint8_t, uint16_t, uint32_t
from libc.math cimport sin, exp, M_PI
from libc.stdlib cimport malloc, free

DEF MAX_VOICES = 32

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

cdef struct NoteEvent:
    int start_sample
    int total_samples
    float freq

cdef struct Voice:
    int active
    float freq
    int sample_pos
    int total_samples
    double phase1
    double phase2
    double phase3

cdef struct SynthState:
    int sample_rate
    NoteEvent *events
    int total_events
    int next_event_idx
    int current_sample
    Voice voices[MAX_VOICES]
    int finished

cdef void audio_callback(void *userdata, Uint8 *stream, int len) noexcept nogil:
    cdef SynthState *synth = <SynthState *>userdata
    cdef float *buffer = <float *>stream
    cdef int num_samples = len // sizeof(float)
    cdef int i, v, slot
    cdef float freq, t, env, v_sample, mix_sample
    cdef int active_count

    for i in range(num_samples):
        # Spawn pending note events that match the current sample
        while synth.next_event_idx < synth.total_events and synth.events[synth.next_event_idx].start_sample <= synth.current_sample:
            if synth.events[synth.next_event_idx].freq > 0.0:
                slot = -1
                for v in range(MAX_VOICES):
                    if not synth.voices[v].active:
                        slot = v
                        break
                if slot != -1:
                    synth.voices[slot].active = 1
                    synth.voices[slot].freq = synth.events[synth.next_event_idx].freq
                    synth.voices[slot].sample_pos = 0
                    synth.voices[slot].total_samples = synth.events[synth.next_event_idx].total_samples
                    synth.voices[slot].phase1 = 0.0
                    synth.voices[slot].phase2 = 0.0
                    synth.voices[slot].phase3 = 0.0
            synth.next_event_idx += 1

        mix_sample = 0.0
        active_count = 0

        # Synthesize and accumulate all active voices
        for v in range(MAX_VOICES):
            if not synth.voices[v].active:
                continue

            active_count += 1
            freq = synth.voices[v].freq
            t = <float>synth.voices[v].sample_pos / <float>synth.sample_rate

            # 4ms attack ramp + exponential release
            if t < 0.004:
                env = t / 0.004
            else:
                env = exp(-2.8 * (t / (<float>synth.voices[v].total_samples / <float>synth.sample_rate)))

            synth.voices[v].phase1 += (2.0 * M_PI * freq) / synth.sample_rate
            if synth.voices[v].phase1 > 2.0 * M_PI:
                synth.voices[v].phase1 -= 2.0 * M_PI

            synth.voices[v].phase2 += (2.0 * M_PI * (freq * 2.0)) / synth.sample_rate
            if synth.voices[v].phase2 > 2.0 * M_PI:
                synth.voices[v].phase2 -= 2.0 * M_PI

            synth.voices[v].phase3 += (2.0 * M_PI * (freq * 3.0)) / synth.sample_rate
            if synth.voices[v].phase3 > 2.0 * M_PI:
                synth.voices[v].phase3 -= 2.0 * M_PI

            v_sample = (0.70 * sin(synth.voices[v].phase1) +
                        0.22 * sin(synth.voices[v].phase2) +
                        0.08 * sin(synth.voices[v].phase3)) * env
            mix_sample += v_sample

            synth.voices[v].sample_pos += 1
            if synth.voices[v].sample_pos >= synth.voices[v].total_samples:
                synth.voices[v].active = 0

        # Soft compression headroom scaling
        if active_count > 1:
            mix_sample *= (0.35 / (1.0 + 0.35 * (active_count - 1)))
        else:
            mix_sample *= 0.35

        buffer[i] = mix_sample
        synth.current_sample += 1

    if synth.next_event_idx >= synth.total_events and active_count == 0:
        synth.finished = 1

def play(list event_seq):
    cdef int total = len(event_seq)
    if total == 0:
        return

    cdef NoteEvent *event_buf = <NoteEvent *>malloc(total * sizeof(NoteEvent))
    if event_buf == NULL:
        raise MemoryError("Failed to allocate event buffer.")

    cdef int i
    cdef int sample_rate = 48000
    for i in range(total):
        event_buf[i].start_sample = <int>(event_seq[i][0] * sample_rate)
        event_buf[i].freq = <float>event_seq[i][1]
        event_buf[i].total_samples = <int>(event_seq[i][2] * sample_rate)

    if SDL_Init(SDL_INIT_AUDIO) < 0:
        free(event_buf)
        raise RuntimeError(f"Failed to initialize SDL: {SDL_GetError().decode('utf-8')}")

    cdef SynthState *synth = <SynthState *>malloc(sizeof(SynthState))
    if synth == NULL:
        free(event_buf)
        SDL_Quit()
        raise MemoryError("Failed to allocate synth state.")

    synth.sample_rate = sample_rate
    synth.events = event_buf
    synth.total_events = total
    synth.next_event_idx = 0
    synth.current_sample = 0
    synth.finished = 0

    for i in range(MAX_VOICES):
        synth.voices[i].active = 0

    cdef SDL_AudioSpec desired
    cdef SDL_AudioSpec obtained

    desired.freq = sample_rate
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
        free(event_buf)
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
        free(event_buf)
        SDL_Quit()