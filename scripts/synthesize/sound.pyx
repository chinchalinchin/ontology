# cython: language_level=3
from libc.stdint cimport uint8_t, uint16_t, uint32_t
from libc.math cimport sin, exp, powf, M_PI
from libc.stdlib cimport malloc, free

DEF MAX_VOICES = 32
DEF MAX_HARMONICS = 8

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
    float velocity
    float attack
    float decay
    int num_harmonics
    float harmonics[MAX_HARMONICS]

cdef struct Voice:
    int active
    float freq
    int sample_pos
    int total_samples
    float base_amp
    float attack_samples
    float decay_coeff
    int num_harmonics
    float harmonics[MAX_HARMONICS]
    double phases[MAX_HARMONICS]

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
    cdef int i, v, slot, h, nh
    cdef float freq, env, v_sample, mix_sample, vel, base_amp, brightness
    cdef int active_count

    for i in range(num_samples):
        # Dispatch pending note events scheduled for the current sample
        while synth.next_event_idx < synth.total_events and synth.events[synth.next_event_idx].start_sample <= synth.current_sample:
            if synth.events[synth.next_event_idx].freq > 0.0:
                slot = -1
                for v in range(MAX_VOICES):
                    if not synth.voices[v].active:
                        slot = v
                        break
                if slot != -1:
                    vel = synth.events[synth.next_event_idx].velocity
                    if vel < 0.01:
                        vel = 0.01
                    elif vel > 1.0:
                        vel = 1.0

                    # Stevens' power law amplitude: A = v^1.8
                    base_amp = powf(vel, 1.8)
                    # Dynamic brightness factor: higher harmonics scale with velocity
                    brightness = powf(vel, 0.5)

                    synth.voices[slot].active = 1
                    synth.voices[slot].freq = synth.events[synth.next_event_idx].freq
                    synth.voices[slot].sample_pos = 0
                    synth.voices[slot].total_samples = synth.events[synth.next_event_idx].total_samples
                    synth.voices[slot].base_amp = base_amp
                    synth.voices[slot].attack_samples = synth.events[synth.next_event_idx].attack * <float>synth.sample_rate
                    if synth.voices[slot].attack_samples < 1.0:
                        synth.voices[slot].attack_samples = 1.0
                    synth.voices[slot].decay_coeff = synth.events[synth.next_event_idx].decay

                    nh = synth.events[synth.next_event_idx].num_harmonics
                    synth.voices[slot].num_harmonics = nh
                    for h in range(nh):
                        # Precalculate scaled harmonic weights w_h * (v^0.5)^h
                        synth.voices[slot].harmonics[h] = synth.events[synth.next_event_idx].harmonics[h] * powf(brightness, <float>h)
                        synth.voices[slot].phases[h] = 0.0

            synth.next_event_idx += 1

        mix_sample = 0.0
        active_count = 0

        # Accumulate and synthesize active voices
        for v in range(MAX_VOICES):
            if not synth.voices[v].active:
                continue

            active_count += 1
            freq = synth.voices[v].freq

            # Envelope evaluation (linear attack ramp + exponential decay)
            if <float>synth.voices[v].sample_pos < synth.voices[v].attack_samples:
                env = <float>synth.voices[v].sample_pos / synth.voices[v].attack_samples
            else:
                env = exp(-synth.voices[v].decay_coeff * (<float>synth.voices[v].sample_pos / <float>synth.voices[v].total_samples))

            v_sample = 0.0
            for h in range(synth.voices[v].num_harmonics):
                # Update phase for each overtone partial
                synth.voices[v].phases[h] += (2.0 * M_PI * (freq * <float>(h + 1))) / synth.sample_rate
                if synth.voices[v].phases[h] > 2.0 * M_PI:
                    synth.voices[v].phases[h] -= 2.0 * M_PI
                v_sample += synth.voices[v].harmonics[h] * sin(synth.voices[v].phases[h])

            v_sample *= (synth.voices[v].base_amp * env)
            mix_sample += v_sample

            synth.voices[v].sample_pos += 1
            if synth.voices[v].sample_pos >= synth.voices[v].total_samples:
                synth.voices[v].active = 0

        # Headroom scaling to prevent distortion across polyphony
        if active_count > 1:
            mix_sample *= (0.35 / (1.0 + 0.35 * (active_count - 1)))
        else:
            mix_sample *= 0.35

        buffer[i] = mix_sample
        synth.current_sample += 1

    if synth.next_event_idx >= synth.total_events and active_count == 0:
        synth.finished = 1

def play(list event_seq):
    """Play a sequence of note events using SDL2 streaming audio."""
    cdef int total = len(event_seq)
    if total == 0:
        return

    cdef NoteEvent *event_buf = <NoteEvent *>malloc(total * sizeof(NoteEvent))
    if event_buf == NULL:
        raise MemoryError("Failed to allocate event buffer.")

    cdef int i, h, nh
    cdef int sample_rate = 48000
    cdef tuple tup
    cdef list harm_list

    for i in range(total):
        tup = <tuple>event_seq[i]
        event_buf[i].start_sample = <int>(<float>tup[0] * sample_rate)
        event_buf[i].freq = <float>tup[1]
        event_buf[i].total_samples = <int>(<float>tup[2] * sample_rate)
        event_buf[i].velocity = <float>tup[3]
        event_buf[i].attack = <float>tup[4]
        event_buf[i].decay = <float>tup[5]

        harm_list = <list>tup[6]
        nh = len(harm_list)
        if nh > MAX_HARMONICS:
            nh = MAX_HARMONICS
        event_buf[i].num_harmonics = nh
        for h in range(nh):
            event_buf[i].harmonics[h] = <float>harm_list[h]

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