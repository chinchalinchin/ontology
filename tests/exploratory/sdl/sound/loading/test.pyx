cdef extern from "SDL.h":
    int SDL_Init(int flags)
    void SDL_Quit()
    void SDL_Delay(int ms)
    const char* SDL_GetError()     # <--- Added to pull exact C-level error messages
    int SDL_INIT_AUDIO

cdef extern from "SDL_mixer.h":
    ctypedef struct Mix_Chunk:
        pass
    ctypedef struct Mix_Music:
        pass
        
    int Mix_OpenAudio(int frequency, unsigned short format, int channels, int chunksize)
    int Mix_Init(int flags)
    void Mix_CloseAudio()
    void Mix_Quit()
    
    Mix_Chunk* Mix_LoadWAV(const char* file)
    Mix_Music* Mix_LoadMUS(const char* file)
    
    int Mix_PlayChannel(int channel, Mix_Chunk* chunk, int loops)
    int Mix_PlayMusic(Mix_Music* music, int loops)
    
    int Mix_HaltChannel(int channel)   # <--- Added to stop sound effects
    int Mix_HaltMusic()                # <--- Added to stop music
    
    void Mix_FreeChunk(Mix_Chunk* chunk)
    void Mix_FreeMusic(Mix_Music* music)
    
    int MIX_INIT_MP3
    int MIX_DEFAULT_FREQUENCY
    unsigned short MIX_DEFAULT_FORMAT
    int MIX_DEFAULT_CHANNELS

def play_audio(bytes wav_file, bytes mp3_file):
    if SDL_Init(SDL_INIT_AUDIO) < 0:
        raise RuntimeError(f"SDL_Init failed: {SDL_GetError().decode('utf-8')}")

    if Mix_Init(MIX_INIT_MP3) & MIX_INIT_MP3 != MIX_INIT_MP3:
        raise RuntimeError(f"Mix_Init failed: {SDL_GetError().decode('utf-8')}")

    if Mix_OpenAudio(MIX_DEFAULT_FREQUENCY, MIX_DEFAULT_FORMAT, MIX_DEFAULT_CHANNELS, 2048) < 0:
        raise RuntimeError(f"Mix_OpenAudio failed: {SDL_GetError().decode('utf-8')}")

    cdef Mix_Chunk* wav_sound = Mix_LoadWAV(wav_file)
    if not wav_sound:
        raise RuntimeError(f"Failed to load WAV: {SDL_GetError().decode('utf-8')}")

    cdef Mix_Music* mp3_music = Mix_LoadMUS(mp3_file)
    if not mp3_music:
        raise RuntimeError(f"Failed to load MP3: {SDL_GetError().decode('utf-8')}")

    # Play WAV and explicitly check if it was routed to a valid channel
    if Mix_PlayChannel(-1, wav_sound, 0) == -1:
        print(f"WARNING - WAV failed to play: {SDL_GetError().decode('utf-8')}")

    # Play MP3
    if Mix_PlayMusic(mp3_music, -1) == -1:
        print(f"WARNING - MP3 failed to play: {SDL_GetError().decode('utf-8')}")

    # Block python thread to listen
    SDL_Delay(5000)

    # --- THE FIX ---
    # Halt all audio processing threads BEFORE destroying the memory!
    Mix_HaltChannel(-1) # -1 halts all active effect channels
    Mix_HaltMusic()

    # Cleanup
    Mix_FreeChunk(wav_sound)
    Mix_FreeMusic(mp3_music)
    Mix_CloseAudio()
    Mix_Quit()
    SDL_Quit()