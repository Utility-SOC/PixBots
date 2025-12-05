# pixbots_enhanced/systems/music.py
# NEW VERSION: Procedural synthesizer with JSON Instruments and Sequencer.

import pygame
import numpy
import threading
import time
import random
import logging
import math
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
        # Quantize duration to avoid cache misses on tiny float diffs?
        # For now, exact match.
        key = (int(frequency), round(duration, 2))
        
        if key in self.cache:
            return self.cache[key].copy() # Return copy so effects don't mutate cache
            
        wave = self.generate_wave_raw(frequency, duration)
        
        # Apply envelope/effects here?
        # If we cache here, we cache the RAW wave.
        # K-S is naturally decayed, so envelope might be redundant or just for cleanup.
        # FM needs envelope.
        
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
        # 1. Generate noise burst
        N = int(SAMPLE_RATE / frequency)
        if N <= 0: N = 1
        
        # Initial burst (pluck)
        burst = numpy.random.uniform(-1, 1, N)
        
        # Output buffer
        wave = numpy.zeros(num_samples)
        
        # Fill start
        wave[:min(N, num_samples)] = burst[:min(N, num_samples)]
        
        # Feedback loop (Vectorized block copy)
        # y[i] = 0.5 * (y[i-N] + y[i-N-1])
        # We can approximate this by copying the previous block and applying a low-pass decay
        
        cursor = N
        prev_block = burst
        
        while cursor < num_samples:
            # Low-pass filter the previous block: average adjacent samples
            # Simple average: (x[i] + x[i+1]) / 2
            # We can use numpy roll for this
            
            # Decay factor (string damping)
            decay = 0.990 
            
            # Filter
            # shift = numpy.roll(prev_block, 1) # Circular, but we want linear?
            # Actually, for K-S, the circular buffer is key.
            # Let's just average the block with its shifted self.
            
            block_len = min(N, num_samples - cursor)
            source = wave[cursor-N : cursor-N+block_len]
            
            # Simple decay copy
            # wave[cursor : cursor+block_len] = source * decay
            
            # Better: Lowpass
            # y[n] = 0.5(y[n-N] + y[n-N-1])
            # This means the new block is the average of the old block and the old block shifted by 1.
            
            # Create shifted version of source (using previous sample for continuity)
            source_shifted = numpy.roll(source, 1)
            source_shifted[0] = wave[cursor-N-1] if cursor-N-1 >= 0 else 0
            
            new_block = 0.5 * (source + source_shifted) * decay
            
            wave[cursor : cursor+block_len] = new_block
            
            cursor += block_len
            
        return wave

    def generate_fm(self, frequency, t):
        """Generates Frequency Modulation synthesis."""
        # Carrier and Modulator
        # f_c = frequency
        # f_m = frequency * ratio
        # y = sin(2pi * f_c * t + index * sin(2pi * f_m * t))
        
        modulator = self.fm_index * numpy.sin(2. * numpy.pi * (frequency * self.fm_ratio) * t)
        carrier = numpy.sin(2. * numpy.pi * frequency * t + modulator)
        return carrier

    def generate_fm(self, frequency, t):
        """Generates Frequency Modulation synthesis."""
        # Carrier and Modulator
        # f_c = frequency
        # f_m = frequency * ratio
        # y = sin(2pi * f_c * t + index * sin(2pi * f_m * t))
        
        modulator = self.fm_index * numpy.sin(2. * numpy.pi * (frequency * self.fm_ratio) * t)
        carrier = numpy.sin(2. * numpy.pi * frequency * t + modulator)
        return carrier

    def apply_effects(self, wave, duration):
        """Applies configured audio effects to the wave."""
        num_samples = len(wave)
        t = numpy.linspace(0., duration, num_samples, endpoint=False)

        if self.effects:
            logger.debug(f"Applying effects for {self.name}: {[e['type'] for e in self.effects]}")

        for effect in self.effects:
            if effect["type"] == "distortion":
                # Soft clipping
                drive = effect.get("drive", 0.5)
                logger.debug(f"  - Distortion: drive={drive}")
                wave = numpy.tanh(wave * (1.0 + drive * 5.0))
                # Normalize after distortion to prevent blowout
                max_val = numpy.max(numpy.abs(wave))
                if max_val > 0: wave /= max_val

            elif effect["type"] == "tremolo":
                # Amplitude Modulation
                rate = effect.get("rate", 5.0) # Hz
                depth = effect.get("depth", 0.5)
                logger.debug(f"  - Tremolo: rate={rate}, depth={depth}")
                mod = (1.0 - depth) + depth * numpy.sin(2. * numpy.pi * rate * t)
                wave *= mod

            elif effect["type"] == "delay":
                # Simple echo
                delay_time = effect.get("time", 0.2) # Seconds
                feedback = effect.get("feedback", 0.4)
                logger.debug(f"  - Delay: time={delay_time}, feedback={feedback}")
                delay_samples = int(delay_time * SAMPLE_RATE)
                
                if delay_samples < num_samples:
                    delayed_signal = numpy.zeros_like(wave)
                    delayed_signal[delay_samples:] = wave[:-delay_samples]
                    wave += delayed_signal * feedback

        return wave

    def apply_envelope(self, wave, duration):
        """Applies ADSR envelope to the wave."""
        # Apply effects BEFORE envelope so tails get cut naturally? 
        # Or AFTER? Usually effects like Delay happen AFTER envelope.
        # But for simple synthesis, let's apply effects first (like distortion) 
        # then envelope to shape the final sound.
        # Wait, Delay should be AFTER envelope to hear the echo tail.
        # Distortion should be BEFORE envelope (usually).
        # Let's split them? Or just apply all before for simplicity?
        # If we apply Delay before envelope, the echo will be cut off by the release.
        # So we should apply Envelope FIRST, then Effects.
        
        num_samples = len(wave)
        attack_len = int(SAMPLE_RATE * self.attack)
        decay_len = int(SAMPLE_RATE * self.decay)
        release_len = int(SAMPLE_RATE * self.release)
        
        # Adjust lengths if note is too short
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
        
        # Trim or pad to match wave length exactly
        if len(envelope) > len(wave):
            envelope = envelope[:len(wave)]
        elif len(envelope) < len(wave):
            envelope = numpy.pad(envelope, (0, len(wave) - len(envelope)), 'constant')
            
        wave = wave * envelope
        
        # Apply Effects AFTER envelope (especially for Delay/Reverb simulation)
        wave = self.apply_effects(wave, duration)
        
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
        """Converts a MIDI note number to a frequency in Hz."""
        if midi_note <= 0: return 0
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

    def generate_sound(self):
        """Generates a pygame.Sound object for this note."""
        # Check mixer channels
        try:
            init_conf = pygame.mixer.get_init()
            if init_conf:
                channels = init_conf[2]
            else:
                channels = 2 # Default
        except:
            channels = 2

        frequency = self.midi_to_freq(self.pitch)
        
        if frequency == 0:
            # Silence
            num_samples = int(self.duration_beats * SAMPLE_RATE)
            if channels == 1:
                arr = numpy.zeros((num_samples,), dtype=numpy.int16)
            else:
                arr = numpy.zeros((num_samples, channels), dtype=numpy.int16)
            return pygame.sndarray.make_sound(arr)

        # Use cached wave generation
        wave = self.instrument.get_wave(frequency, self.duration_beats)

        # Scale to 16-bit integer range and apply velocity and instrument volume
        amplitude = (self.velocity / 127.0) * self.instrument.volume * 16383 
        wave = (wave * amplitude).astype(numpy.int16)

        # Explicitly log mixer state for debugging
        init_conf = pygame.mixer.get_init()
        channels = 2
        if init_conf:
            channels = init_conf[2]
        
        # Prepare sound array based on channel count
        if channels == 1:
            sound_array = numpy.ascontiguousarray(wave)
        else:
            # Duplicate the wave for each channel (works for Stereo, Quad, 5.1, 7.1, etc.)
            # wave is 1D (N,) -> (N, 1) -> (N, channels)
            sound_array = numpy.ascontiguousarray(numpy.tile(wave[:, numpy.newaxis], (1, channels)))

        try:
            return pygame.sndarray.make_sound(sound_array)
        except ValueError as e:
            logger.error(f"Audio Error! Mixer: {init_conf}, Channels: {channels}, Array: {sound_array.shape}. Error: {e}")
            
            # Emergency Fallback: Try Stereo (2 channels) as a last resort if N-channel fails
            # Some drivers might report 8 but accept 2?
            try:
                logger.info("Retrying with Stereo (2 channels)...")
                wave_stereo = numpy.ascontiguousarray(numpy.vstack((wave, wave)).T)
                return pygame.sndarray.make_sound(wave_stereo)
            except ValueError as e2:
                logger.error(f"Fallback failed: {e2}")
                return pygame.sndarray.make_sound(numpy.zeros((int(self.duration_beats * SAMPLE_RATE), 2), dtype=numpy.int16))

class MusicGenerator:
    """Generates procedural music and synthesizes it into audio."""
    
    def __init__(self):
        self.initialized = False
        self.currently_playing = False
        self.thread = None
        self.should_stop = False
        self.current_biome = "grassland"
        self.force_reset = False # Flag for hard switch
        self.instruments = {}
        self.load_instruments()
        
        # Musical parameters
        self.scales = {
            "major": [0, 2, 4, 5, 7, 9, 11],
            "minor": [0, 2, 3, 5, 7, 8, 10],
            "pentatonic": [0, 2, 4, 7, 9],
            "chromatic": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
            "harmonic_minor": [0, 2, 3, 5, 7, 8, 11],
            "phrygian": [0, 1, 3, 5, 7, 8, 10],
            "whole_tone": [0, 2, 4, 6, 8, 10]
        }
        
        self.biome_params = {
            "grassland": {"base_pitch": 60, "scale": "major", "tempo": 110, "melody_inst": "flute", "rhythm_inst": "woodblock", "rhythm_pattern": "basic"},
            "plains": {"base_pitch": 60, "scale": "major", "tempo": 110, "melody_inst": "flute", "rhythm_inst": "woodblock", "rhythm_pattern": "basic"},
            "desert": {"base_pitch": 55, "scale": "harmonic_minor", "tempo": 90, "melody_inst": "duduk", "rhythm_inst": "shaker", "rhythm_pattern": "basic"},
            "tundra": {"base_pitch": 72, "scale": "pentatonic", "tempo": 80, "melody_inst": "bell", "rhythm_inst": "drum_hihat", "rhythm_pattern": "basic"},
            "snow": {"base_pitch": 72, "scale": "pentatonic", "tempo": 80, "melody_inst": "bell", "rhythm_inst": "drum_hihat", "rhythm_pattern": "basic"},
            "forest": {"base_pitch": 58, "scale": "pentatonic", "tempo": 100, "melody_inst": "pad", "rhythm_inst": "drum_snare", "rhythm_pattern": "basic"},
            "volcano": {"base_pitch": 40, "scale": "chromatic", "tempo": 130, "melody_inst": "crunchy_bass", "rhythm_inst": "drum_kick", "rhythm_pattern": "aggressive"},
            "volcanic": {"base_pitch": 40, "scale": "chromatic", "tempo": 130, "melody_inst": "crunchy_bass", "rhythm_inst": "drum_kick", "rhythm_pattern": "aggressive"},
            "island": {"base_pitch": 64, "scale": "major", "tempo": 95, "melody_inst": "marimba", "rhythm_inst": "reggaeton_snare", "rhythm_pattern": "reggaeton"},
            "beach": {"base_pitch": 60, "scale": "phrygian", "tempo": 160, "melody_inst": "surf_guitar", "rhythm_inst": "drum_snare", "rhythm_pattern": "rock"},
            "mountainous": {"base_pitch": 48, "scale": "minor", "tempo": 110, "melody_inst": "pizzicato", "rhythm_inst": "drum_kick", "rhythm_pattern": "basic", "motif": [0, 1, 2, 3, 4, 2, 4]},
            "mountain": {"base_pitch": 48, "scale": "minor", "tempo": 110, "melody_inst": "pizzicato", "rhythm_inst": "drum_kick", "rhythm_pattern": "basic", "motif": [0, 1, 2, 3, 4, 2, 4]},
        }

    def load_instruments(self):
        try:
            with open(os.path.join("data", "instruments.json"), "r") as f:
                data = json.load(f)
                for name, props in data.items():
                    self.instruments[name] = Instrument(
                        name, 
                        waveform=props.get("waveform", "sine"),
                        attack=props.get("attack", 0.01),
                        decay=props.get("decay", 0.1),
                        sustain=props.get("sustain", 0.7),
                        release=props.get("release", 0.2),
                        volume=props.get("volume", 1.0),
                        harmonics=props.get("harmonics", None),
                        effects=props.get("effects", None),
                        fm_ratio=props.get("fm_ratio", 2.0),
                        fm_index=props.get("fm_index", 1.0)
                    )
            logger.info(f"Loaded {len(self.instruments)} instruments from JSON.")
        except Exception as e:
            logger.error(f"Failed to load instruments.json: {e}")
            # Fallback
            self.instruments["flute"] = Instrument("Flute")

    def init(self):
        try:
            # Force re-initialization to ensure our settings (stereo, 44.1k) are used
            if pygame.mixer.get_init():
                pygame.mixer.quit()
                
            pygame.mixer.pre_init(SAMPLE_RATE, -16, 2, BUFFER_SIZE)
            pygame.mixer.init()
            pygame.mixer.set_num_channels(32) # More channels for polyphony
            self.initialized = True
            logger.info("Procedural Synthesizer initialized.")
        except pygame.error as e:
            logger.error(f"Failed to initialize mixer: {e}")

    def shutdown(self):
        self.stop_music()
        if self.initialized:
            pygame.mixer.quit()
            self.initialized = False

    def start_music(self):
        if not self.initialized: return
        if self.currently_playing: self.stop_music()
        
        self.should_stop = False
        self.currently_playing = True
        self.thread = threading.Thread(target=self.sequencer_thread, daemon=True)
        self.thread.start()

    def stop_music(self):
        if self.currently_playing:
            self.should_stop = True
            if self.thread:
                self.thread.join(timeout=1.0)
            pygame.mixer.stop()
            self.currently_playing = False

    def set_biome(self, biome_name):
        biome_name = biome_name.lower()
        if biome_name in self.biome_params:
            if self.current_biome != biome_name:
                self.current_biome = biome_name
                self.force_reset = True # Trigger hard switch
                logger.info(f"Music biome changed to: {biome_name}")

    def sequencer_thread(self):
        """Main loop that schedules notes for both melody and rhythm."""
        next_melody_time = time.time()
        next_rhythm_time = time.time()
        
        melody_queue = []
        rhythm_queue = []
        
        while not self.should_stop:
            try:
                current_time = time.time()
                
                # Hard Switch Logic
                if self.force_reset:
                    pygame.mixer.stop() # Stop all currently playing sounds
                    melody_queue.clear()
                    rhythm_queue.clear()
                    next_melody_time = current_time
                    next_rhythm_time = current_time
                    self.force_reset = False
                    logger.info("Music sequencer reset for new biome.")
                
                params = self.biome_params.get(self.current_biome, self.biome_params["grassland"])
                tempo = params["tempo"]
                beat_duration = 60.0 / tempo
                if current_time >= next_melody_time:
                    if not melody_queue:
                        scale = self.scales.get(params["scale"], self.scales["major"])
                        inst_name = params.get("melody_inst", "flute")
                        instrument = self.instruments.get(inst_name, self.instruments.get("flute"))
                        if instrument:
                            melody_queue = self.generate_melody(params["base_pitch"], scale, 8, instrument, params.get("motif"))

                    if melody_queue:
                        note = melody_queue.pop(0)
                        if note.pitch > 0:
                            note.sound.play()
                        next_melody_time = current_time + (note.duration_beats * beat_duration)

                if current_time >= next_rhythm_time:
                    if not rhythm_queue:
                        inst_name = params.get("rhythm_inst", "drum_snare")
                        instrument = self.instruments.get(inst_name, self.instruments.get("flute"))
                        pattern = params.get("rhythm_pattern", "basic")
                        if instrument:
                            rhythm_queue = self.generate_rhythm(4, instrument, pattern)
                    
                    if rhythm_queue:
                        note = rhythm_queue.pop(0)
                        if note.pitch > 0:
                             note.sound.play()
                        next_rhythm_time = current_time + (note.duration_beats * beat_duration)

                time.sleep(0.01) # Small sleep to prevent CPU hogging

            except Exception as e:
                logger.error(f"Error in sequencer thread: {e}", exc_info=True)
                time.sleep(1)

    def generate_melody(self, base_pitch, scale, num_notes, instrument, motif=None):
        melody = []
        
        if motif:
            # Use motif pattern
            for scale_degree in motif:
                scale_idx = scale_degree % len(scale)
                octave_offset = (scale_degree // len(scale)) * 12
                pitch = base_pitch + scale[scale_idx] + octave_offset
                duration = 0.5 
                melody.append(Note(pitch, duration, instrument))
        else:
            # Random walk
            pitch_index = 0
            for _ in range(num_notes):
                step = random.choice([-1, 0, 1, 1])
                pitch_index += step
                scale_idx = pitch_index % len(scale)
                octave_offset = (pitch_index // len(scale)) * 12
                pitch = base_pitch + scale[scale_idx] + octave_offset
                duration = random.choice([0.5, 0.5, 1.0]) 
                if random.random() < 0.1: pitch = 0 
                melody.append(Note(pitch, duration, instrument))
                
        return melody

    def generate_surf_melody(self, base_pitch, scale, num_notes, instrument):
        """Generates fast, tremolo-picking style melody."""
        melody = []
        # Surf rock often uses Phrygian Dominant or Major scale with chromaticism
        # We'll use rapid 16th notes on the same pitch (tremolo picking) then move
        
        pitch_index = 0
        notes_generated = 0
        
        while notes_generated < num_notes:
            # Pick a target note
            step = random.choice([-2, -1, 0, 1, 2])
            pitch_index += step
            scale_idx = pitch_index % len(scale)
            octave_offset = (pitch_index // len(scale)) * 12
            pitch = base_pitch + scale[scale_idx] + octave_offset
            
            # Tremolo pick it (4 times = 1 beat)
            repeats = 4
            for _ in range(repeats):
                # Slight velocity variation
                vel = random.randint(100, 127)
                melody.append(Note(pitch, 0.25, instrument, vel))
                notes_generated += 1
                if notes_generated >= num_notes: break
                
        return melody

    def generate_rhythm(self, num_beats, instrument, pattern="basic"):
        """Generates a rhythmic pattern."""
        rhythm = []
        pitch = 60 # Fixed pitch for percussion usually
        
        if pattern == "rock":
            # Standard Rock Beat: Kick on 1, 3. Snare on 2, 4.
            # We only have one instrument passed in (Snare usually for rhythm_inst)
            # But we need Kick too.
            # Let's cheat and grab the Kick instrument directly if possible, or just use pitch diff?
            # Instruments are stored in self.instruments.
            kick = self.instruments.get("drum_kick")
            snare = self.instruments.get("drum_snare")
            hihat = self.instruments.get("drum_hihat")
            
            if not kick or not snare:
                # Fallback
                kick = instrument
                snare = instrument
            
            for i in range(num_beats):
                # Beat i (0, 1, 2, 3)
                # 1 (0): Kick + HiHat
                # 2 (1): Snare + HiHat
                # 3 (2): Kick + HiHat
                # 4 (3): Snare + HiHat
                
                # We can't play multiple notes at once in this simple list structure easily 
                # unless we return a list of lists or manage polyphony in sequencer.
                # But our sequencer just pops one note.
                # Wait, Note object generates a Sound. We can just play the Sound.
                # But the sequencer waits for duration.
                # To do polyphony (Kick+HiHat), we need to mix them into one Sound or play them simultaneously.
                # The sequencer logic: note.sound.play(), then wait.
                # If we want simultaneous, we can return a "Chord" object?
                # Or just play the Kick, and have the HiHat be part of the sound? No.
                # Let's just alternate for now to keep it simple but driving.
                # Kick - Snare - Kick - Snare (Driving)
                
                if i % 2 == 0:
                    # Kick
                    rhythm.append(Note(60, 1.0, kick, 127))
                else:
                    # Snare
                    rhythm.append(Note(60, 1.0, snare, 127))
                    
        elif pattern == "reggaeton":
            # Dembow beat: Kick on 1, 2, 3, 4. Snare on 1.75, 2.5, 3.75, 4.5
            # We are generating 'num_beats' worth of notes.
            # To do this simply with our Note class (which has duration), we need to sequence durations.
            # 1 beat = 1.0. 
            # Pattern loop (1 bar = 4 beats):
            # Hit (Kick) at 0.0 -> Duration 0.75
            # Hit (Snare) at 0.75 -> Duration 0.25
            # Hit (Snare) at 1.0 -> Duration 1.0 (Wait, Dembow is Kick on 1, 2, 3, 4)
            # Let's simplify:
            # Beat 1: Kick (0.0), Snare (0.75)
            # Beat 2: Kick (1.0), Snare (1.5) -> Wait, classic is 3-3-2 rhythm (Tresillo)
            # Let's do: 
            # Note 1: 0.75 duration (dotted 8th)
            # Note 2: 0.25 duration (16th)
            # Note 3: 0.5 duration (8th)
            # Note 4: 0.5 duration (8th)
            # Total: 2.0 beats. Repeat for 4 beats.
            
            # Actually, let's just use the instrument provided (which is snare for Island)
            # And assume there's a backing kick (we don't support multi-instrument rhythm yet in this simple function)
            # So we play the "Snare" part of Reggaeton.
            # Snare hits on: 0.75, 1.5, 2.75, 3.5?
            # Let's try: 0.75 (rest), 0.25 (hit), 0.5 (rest), 0.5 (hit)
            
            # Sequence of (duration, velocity)
            # 1. Rest 0.75
            # 2. Hit 0.25
            # 3. Rest 0.5
            # 4. Hit 0.5
            # Total 2.0 beats.
            
            for _ in range(num_beats // 2):
                rhythm.append(Note(0, 0.75, instrument, 0)) # Rest
                rhythm.append(Note(pitch, 0.25, instrument, 110)) # Hit
                rhythm.append(Note(0, 0.5, instrument, 0)) # Rest
                rhythm.append(Note(pitch, 0.5, instrument, 100)) # Hit
                
        elif pattern == "aggressive":
            # Fast hits
            for _ in range(num_beats * 2): # 8th notes
                velocity = 120 if random.random() > 0.3 else 0
                rhythm.append(Note(pitch if velocity > 0 else 0, 0.5, instrument, velocity))
                
        else: # Basic
            for i in range(num_beats):
                if i % 2 == 0: velocity = 120
                else: velocity = 80 if random.random() > 0.5 else 0
                rhythm.append(Note(pitch if velocity > 0 else 0, 1.0, instrument, velocity))
                
        return rhythm

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
