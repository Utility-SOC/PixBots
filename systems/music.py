# pixbots_enhanced/systems/music.py
# MERGED VERSION: JSON Instruments + Dissonance/Biome Logic

import pygame
import numpy
import threading
import time
import random
import logging
import json
import os

logger = logging.getLogger(__name__)

# --- Audio Synthesis Constants ---
SAMPLE_RATE = 44100
BUFFER_SIZE = 2048

class Instrument:
    """Defines the timbre of a sound using waveform and envelope."""
    def __init__(self, name, waveform="sine", attack=0.01, decay=0.1, sustain=0.7, release=0.2, volume=1.0, harmonics=None, effects=None, fm_ratio=2.0, fm_index=1.0):
        self.name = name
        self.waveform = waveform
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release
        self.volume = volume
        self.harmonics = harmonics if harmonics else [1.0]
        self.effects = effects if effects else []
        self.fm_ratio = fm_ratio
        self.fm_index = fm_index
        self.cache = {} # Key: (frequency, duration) -> numpy array

    def get_wave(self, frequency, duration):
        """Retrieves wave from cache or generates it."""
        key = (int(frequency), round(duration, 2))
        
        if key in self.cache:
            return self.cache[key].copy()
            
        wave = self.generate_wave_raw(frequency, duration)
        
        if self.waveform not in ["karplus_strong"]:
             wave = self.apply_envelope(wave, duration)
             
        wave = self.apply_effects(wave, duration)
        
        # Safety: Remove NaNs/Infs
        wave = numpy.nan_to_num(wave)
        
        # Store in cache
        if len(self.cache) > 100: # Simple LRU-ish
            self.cache.pop(next(iter(self.cache)))
        self.cache[key] = wave
        
        return wave.copy()

    def generate_wave_raw(self, frequency, duration):
        """Generates the raw waveform array."""
        num_samples = int(SAMPLE_RATE * duration)
        t = numpy.linspace(0., duration, num_samples, endpoint=False)
        
        if self.waveform == "karplus_strong":
            return self.generate_karplus_strong(frequency, num_samples)
            
        elif self.waveform == "fm":
            return self.generate_fm(frequency, t)
        
        elif self.waveform == "sine" or self.waveform == "custom":
            wave = numpy.zeros(num_samples)
            for i, amp in enumerate(self.harmonics):
                if amp > 0:
                    wave += amp * numpy.sin(2. * numpy.pi * (frequency * (i + 1)) * t)
            max_val = numpy.max(numpy.abs(wave))
            if max_val > 0: wave /= max_val
            return wave
            
        elif self.waveform == "square":
            return numpy.sign(numpy.sin(2. * numpy.pi * frequency * t))
            
        elif self.waveform == "sawtooth":
            return 2.0 * (t * frequency - numpy.floor(t * frequency + 0.5))
            
        elif self.waveform == "triangle":
            return 2.0 * numpy.abs(2.0 * (t * frequency - numpy.floor(t * frequency + 0.5))) - 1.0
            
        elif self.waveform == "noise":
            return numpy.random.uniform(-1, 1, num_samples)
            
        elif self.waveform == "snare":
            noise = numpy.random.uniform(-1, 1, num_samples)
            tone = numpy.sin(2. * numpy.pi * frequency * t) * numpy.exp(-5 * t)
            return noise * 0.8 + tone * 0.2
            
        elif self.waveform == "kick":
            freq_env = numpy.linspace(frequency, frequency * 0.1, num_samples)
            phase = numpy.cumsum(freq_env) / SAMPLE_RATE
            wave = numpy.sin(2. * numpy.pi * phase)
            return numpy.clip(wave * 1.5, -1, 1)
            
        else:
            return numpy.sin(2. * numpy.pi * frequency * t)

    def generate_karplus_strong(self, frequency, num_samples):
        """Simulates a plucked string using Karplus-Strong algorithm."""
        N = int(SAMPLE_RATE / frequency)
        if N <= 0: N = 1
        
        burst = numpy.random.uniform(-1, 1, N)
        wave = numpy.zeros(num_samples)
        wave[:min(N, num_samples)] = burst[:min(N, num_samples)]
        
        cursor = N
        while cursor < num_samples:
            block_len = min(N, num_samples - cursor)
            source = wave[cursor-N : cursor-N+block_len]
            
            # Lowpass: average with previous sample
            source_shifted = numpy.roll(source, 1)
            if cursor-N-1 >= 0:
                source_shifted[0] = wave[cursor-N-1]
            
            new_block = 0.5 * (source + source_shifted) * 0.994
            wave[cursor : cursor+block_len] = new_block
            cursor += block_len
            
        return wave

    def generate_fm(self, frequency, t):
        """Generates Frequency Modulation synthesis."""
        modulator = self.fm_index * numpy.sin(2. * numpy.pi * (frequency * self.fm_ratio) * t)
        carrier = numpy.sin(2. * numpy.pi * frequency * t + modulator)
        return carrier

    def apply_effects(self, wave, duration):
        """Applies configured audio effects to the wave."""
        num_samples = len(wave)
        t = numpy.linspace(0., duration, num_samples, endpoint=False)

        for effect in self.effects:
            if effect["type"] == "distortion":
                drive = effect.get("drive", 0.5)
                wave = numpy.tanh(wave * (1.0 + drive * 5.0))
                max_val = numpy.max(numpy.abs(wave))
                if max_val > 0: wave /= max_val

            elif effect["type"] == "tremolo":
                rate = effect.get("rate", 5.0)
                depth = effect.get("depth", 0.5)
                mod = (1.0 - depth) + depth * numpy.sin(2. * numpy.pi * rate * t)
                wave *= mod

            elif effect["type"] == "delay":
                delay_time = effect.get("time", 0.2)
                feedback = effect.get("feedback", 0.4)
                delay_samples = int(delay_time * SAMPLE_RATE)
                
                if delay_samples < num_samples:
                    delayed_signal = numpy.zeros_like(wave)
                    delayed_signal[delay_samples:] = wave[:-delay_samples]
                    wave += delayed_signal * feedback

        return wave

    def apply_envelope(self, wave, duration):
        """Applies ADSR envelope to the wave."""
        num_samples = len(wave)
        attack_len = int(SAMPLE_RATE * self.attack)
        decay_len = int(SAMPLE_RATE * self.decay)
        release_len = int(SAMPLE_RATE * self.release)
        
        total_len = attack_len + decay_len + release_len
        if total_len > num_samples:
            scale = num_samples / total_len
            attack_len = int(attack_len * scale)
            decay_len = int(decay_len * scale)
            release_len = int(release_len * scale)

        sustain_len = num_samples - attack_len - decay_len - release_len
        if sustain_len < 0: sustain_len = 0 

        attack_env = numpy.linspace(0., 1., attack_len)
        decay_env = numpy.linspace(1., self.sustain, decay_len)
        sustain_env = numpy.full(sustain_len, self.sustain)
        release_env = numpy.linspace(self.sustain, 0., release_len)
        
        envelope = numpy.concatenate((attack_env, decay_env, sustain_env, release_env))
        
        if len(envelope) > len(wave):
            envelope = envelope[:len(wave)]
        elif len(envelope) < len(wave):
            envelope = numpy.pad(envelope, (0, len(wave) - len(envelope)), 'constant')
            
        wave = wave * envelope
        return wave

class Note:
    """Represents a musical note and its generated sound."""
    def __init__(self, pitch, duration_beats, instrument: Instrument, velocity=100):
        self.pitch = pitch
        self.duration_beats = duration_beats
        self.velocity = velocity
        self.instrument = instrument
        self.sound = self.generate_sound()

    @staticmethod
    def midi_to_freq(midi_note):
        if midi_note <= 0: return 0
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    def generate_sound(self):
        try:
            init_conf = pygame.mixer.get_init()
            channels = init_conf[2] if init_conf else 2
        except:
            channels = 2

        frequency = self.midi_to_freq(self.pitch)
        
        if frequency == 0:
            num_samples = int(self.duration_beats * SAMPLE_RATE)
            arr = numpy.zeros((num_samples, channels) if channels > 1 else (num_samples,), dtype=numpy.int16)
            return pygame.sndarray.make_sound(arr)

        wave = self.instrument.get_wave(frequency, self.duration_beats)
        amplitude = (self.velocity / 127.0) * self.instrument.volume * 16383 
        wave = (wave * amplitude).astype(numpy.int16)

        if channels == 1:
            sound_array = numpy.ascontiguousarray(wave)
        else:
            sound_array = numpy.ascontiguousarray(numpy.tile(wave[:, numpy.newaxis], (1, channels)))

        try:
            return pygame.sndarray.make_sound(sound_array)
        except ValueError:
            # Fallback to stereo
            wave_stereo = numpy.ascontiguousarray(numpy.vstack((wave, wave)).T)
            return pygame.sndarray.make_sound(wave_stereo)

class MusicGenerator:
    """Generates procedural music and synthesizes it into audio."""
    
    def __init__(self):
        self.initialized = False
        self.playing = False
        self.thread = None
        self.stop_flag = False
        self.biome = "grassland"
        self.reset_flag = False
        self.instruments = {}
        self.load_instruments()
        
        # --- SCALES ---
        self.scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "pentatonic": [0, 3, 5, 7, 10],
            "phrygian": [0, 1, 4, 5, 7, 8, 10],
            "diminished": [0, 3, 6, 9],
            "chromatic": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
        }
        
        # --- BIOME CONFIG (Merged) ---
        self.biomes = {
            "grassland": { "bpm": 100, "scale": "major", "root": 64, "voice": "flute", "perc": "woodblock", "rhythm": "basic", "dissonance": 0.0 },
            "plains": { "bpm": 100, "scale": "major", "root": 64, "voice": "flute", "perc": "woodblock", "rhythm": "basic", "dissonance": 0.0 },
            "island": { "bpm": 90, "scale": "major", "root": 60, "voice": "marimba", "perc": "reggaeton_snare", "rhythm": "reggae", "dissonance": 0.05 },
            "beach": { "bpm": 160, "scale": "major", "root": 52, "voice": "surf_guitar", "perc": "drum_snare", "rhythm": "surf", "dissonance": 0.1 },
            "mountains": { "bpm": 85, "scale": "pentatonic", "root": 57, "voice": "pizzicato", "perc": "drum_kick", "rhythm": "basic", "dissonance": 0.2 },
            "mountain": { "bpm": 85, "scale": "pentatonic", "root": 57, "voice": "pizzicato", "perc": "drum_kick", "rhythm": "basic", "dissonance": 0.2 },
            "desert": { "bpm": 100, "scale": "phrygian", "root": 50, "voice": "duduk", "perc": "shaker", "rhythm": "basic", "dissonance": 0.3 },
            "volcano": { "bpm": 150, "scale": "diminished", "root": 36, "voice": "crunchy_bass", "perc": "drum_kick", "rhythm": "panic", "dissonance": 0.8 },
            "volcanic": { "bpm": 150, "scale": "diminished", "root": 36, "voice": "crunchy_bass", "perc": "drum_kick", "rhythm": "panic", "dissonance": 0.8 },
            "tundra": { "bpm": 80, "scale": "pentatonic", "root": 72, "voice": "bell", "perc": "drum_hihat", "rhythm": "basic", "dissonance": 0.0 },
            "snow": { "bpm": 80, "scale": "pentatonic", "root": 72, "voice": "bell", "perc": "drum_hihat", "rhythm": "basic", "dissonance": 0.0 },
            "forest": { "bpm": 100, "scale": "pentatonic", "root": 58, "voice": "pad", "perc": "drum_snare", "rhythm": "basic", "dissonance": 0.0 },
        }

    def load_instruments(self):
        try:
            with open(os.path.join("data", "instruments.json"), "r") as f:
                data = json.load(f)
                for name, props in data.items():
                    self.instruments[name] = Instrument(name, **props)
            logger.info(f"Loaded {len(self.instruments)} instruments from JSON.")
        except Exception as e:
            logger.error(f"Failed to load instruments.json: {e}")
            self.instruments["flute"] = Instrument("Flute")

    def init(self):
        try:
            # if pygame.mixer.get_init():
            #     pygame.mixer.quit()
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, BUFFER_SIZE)
                pygame.mixer.init()
                pygame.mixer.set_num_channels(32)
            self.initialized = True
            logger.info("Procedural Synthesizer initialized.")
        except pygame.error as e:
            logger.error(f"Failed to initialize mixer: {e}")

    def shutdown(self):
        self.stop_music()
        if self.initialized:
            pygame.mixer.quit()
            self.initialized = False

    def set_biome(self, biome_name):
        biome_name = biome_name.lower()
        if biome_name in self.biomes:
            if self.biome != biome_name:
                self.biome = biome_name
                self.reset_flag = True
                logger.info(f"Music biome changed to: {biome_name}")

    def start_music(self):
        if not self.initialized: return
        if self.thread and self.thread.is_alive():
            return # Already playing
            
        self.playing = True
        self.stop_flag = False
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop_music(self):
        self.playing = False
        self.stop_flag = True
        if self.thread:
            self.thread.join(timeout=1.0)
        pygame.mixer.stop()

    def _loop(self):
        next_mel = next_rhy = time.time()
        mel_q, rhy_q = [], []
        
        while not self.stop_flag:
            now = time.time()
            if self.reset_flag:
                pygame.mixer.stop()
                mel_q.clear(); rhy_q.clear()
                next_mel = next_rhy = now
                self.reset_flag = False

            cfg = self.biomes.get(self.biome, self.biomes["grassland"])
            beat = 60.0 / cfg["bpm"]

            # Melody
            if now >= next_mel:
                if not mel_q:
                    mel_q = self._gen_melody(cfg)
                if mel_q:
                    n = mel_q.pop(0)
                    if n.pitch > 0: n.sound.play()
                    next_mel = now + (n.duration_beats * beat)

            # Rhythm
            if now >= next_rhy:
                if not rhy_q:
                    rhy_q = self._gen_rhythm(cfg)
                if rhy_q:
                    n = rhy_q.pop(0)
                    if n.pitch > 0: n.sound.play()
                    next_rhy = now + (n.duration_beats * beat)
            
            time.sleep(0.005)

    def _gen_melody(self, cfg):
        notes = []
        inst_name = cfg["voice"]
        inst = self.instruments.get(inst_name, self.instruments.get("flute"))
        if not inst: return []
        
        scale = self.scales[cfg["scale"]]
        root = cfg["root"]
        dissonance = cfg["dissonance"]
        
        num = 16 if cfg["rhythm"] == "surf" else 8
        idx = 0
        
        for _ in range(num):
            idx += random.choice([-1, 0, 1, 2, -2])
            
            if random.random() < dissonance:
                pitch = root + scale[idx % len(scale)] + (idx // len(scale))*12 + 1 
            else:
                pitch = root + scale[idx % len(scale)] + (idx // len(scale))*12
            
            dur = 0.5
            if cfg["rhythm"] == "surf": 
                dur = 0.25 
            elif cfg["rhythm"] == "reggae":
                dur = random.choice([0.5, 1.0])

            play = True
            if cfg["rhythm"] == "panic": play = True
            elif random.random() < 0.2: play = False

            notes.append(Note(pitch if play else 0, dur, inst))
        return notes

    def _gen_rhythm(self, cfg):
        notes = []
        k = self.instruments.get("drum_kick")
        s = self.instruments.get("drum_snare")
        h = self.instruments.get("shaker")
        
        # Fallback
        if not k: k = self.instruments.get(cfg["perc"])
        if not s: s = self.instruments.get(cfg["perc"])
        if not h: h = self.instruments.get(cfg["perc"])
        
        if not k: return [] # No instruments

        style = cfg["rhythm"]

        if style == "surf":
            notes = [Note(60, 1.0, k), Note(60, 1.0, s), Note(60, 1.0, k), Note(60, 1.0, s)]
            
        elif style == "reggae":
            notes = [Note(0, 1.0, k), Note(60, 1.0, s), Note(0, 1.0, k), Note(60, 1.0, s)]
            
        elif style == "panic":
            notes = [Note(60, 0.5, k), Note(60, 0.5, k), Note(60, 0.5, s), Note(60, 0.5, k)]
            
        else: # Basic
            notes = [Note(60, 1.0, k), Note(60, 1.0, h), Note(60, 1.0, s), Note(60, 1.0, h)]
            
        return notes

# --- Singleton and Control Functions ---
music_system = MusicGenerator()

def init():
    music_system.init()

def shutdown():
    music_system.shutdown()

def play_music(biome_name: str):
    music_system.set_biome(biome_name)
    music_system.start_music()

def stop_music():
    music_system.stop_music()
