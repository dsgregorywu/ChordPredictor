import csv
import numpy as np
import sounddevice as sd

class TheoryEngine:
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
    # The absolute semitone offsets for the two different modes
    MODES = {
        "Major": {
            'i': 0, 'I': 0, 'bii': 1, 'bII': 1, 'ii': 2, 'II': 2, 'biii': 3, 'bIII': 3,
            'iii': 4, 'III': 4, 'iv': 5, 'IV': 5, 'bv': 6, 'bV': 6, 'v': 7, 'V': 7,
            'bvi': 8, 'bVI': 8, 'vi': 9, 'VI': 9, 'bvii': 10, 'bVII': 10, 'vii': 11, 'VII': 11
        },
        "Minor": {
            'i': 0, 'I': 0, 'bii': 1, 'bII': 1, 'ii': 2, 'II': 2, 'iii': 3, 'III': 3,
            'iv': 5, 'IV': 5, 'v': 7, 'V': 7, 'vi': 8, 'VI': 8, 'vii': 10, 'VII': 10
        }
    }
    FREQUENCIES = {
        # Octave 3 (Low/Bass range)
        "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56,
        "E3": 164.81, "F3": 174.61, "F#3": 185.00, "G3": 196.00,
        "G#3": 207.65, "A3": 220.00, "A#3": 233.08, "B3": 246.94,

        # Octave 4 (Middle range / "Middle C")
        "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13,
        "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00,
        "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,

        # Octave 5 (High range)
        "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25,
        "E5": 659.25, "F5": 698.46, "F#5": 739.99, "G5": 783.99,
        "G#5": 830.61, "A5": 880.00, "A#5": 932.33, "B5": 987.77
    }


    @staticmethod
    def get_absolute_chord(key_root, symbol, quality="Major"):
        import re
        # Match the Roman numeral root (with optional b/♭) and the rest as flavor
        m = re.match(r"([b♭]?[iIvV]{1,3})(.*)", symbol)
        if not m:
            return symbol
        root_part, flavor = m.group(1), m.group(2)

        # Normalize flats to 'b'
        root_part = root_part.replace('♭', 'b')

        # Select the map based on the active project quality
        mode_map = TheoryEngine.MODES.get(quality, TheoryEngine.MODES["Major"])
        if root_part not in mode_map:
            return symbol

        # Clean up key root (handle flats if they come in as 'Bb' etc)
        key_root_fixed = key_root
        if key_root_fixed == "Bb": key_root_fixed = "A#"
        elif key_root_fixed == "Eb": key_root_fixed = "D#"
        elif key_root_fixed == "Ab": key_root_fixed = "G#"
        elif key_root_fixed == "Db": key_root_fixed = "C#"
        elif key_root_fixed == "Gb": key_root_fixed = "F#"
        # Accept both b and # for accidentals
        key_root_fixed = key_root_fixed.replace('b', 'b').replace('#', '#')

        try:
            start_idx = TheoryEngine.NOTES.index(key_root_fixed.upper())
            offset = mode_map[root_part]
            chord_note = TheoryEngine.NOTES[(start_idx + offset) % 12]
            # Only add 'm' if root is lowercase, flavor does not already start with 'm' or 'M', and not a diminished/aug chord
            if root_part[0].islower() and not (flavor.startswith('m') or flavor.startswith('M') or 'dim' in flavor or 'aug' in flavor):
                flavor = 'm' + flavor
            return f"{chord_note}{flavor}"
        except:
            return symbol

class ChordNode:
    def __init__(self, chord=str()):
        self.chord = chord
        self.count = 0
        self.children = {}
        self.genres = set()
        # Track if this node belongs to a Major or Minor sequence
        self.mode_counts = {"Major": 0, "Minor": 0}

class ChordTrie:
    def __init__(self):
        self.root = ChordNode()

    def insert(self, progression, genre="General"):
        # ALGORITHM CHANGE: Detect mode from the data itself
        # If the first chord is 'i', 'iv', or 'v', it's a Minor progression
        # If it's 'I', 'IV', or 'V', it's Major.
        first_chord = progression[0] if progression else "I"
        detected_mode = "Minor" if first_chord[0].islower() else "Major"

        node = self.root
        for chord in progression:
            if chord not in node.children:
                node.children[chord] = ChordNode(chord)
            node = node.children[chord]
            node.count += 1
            node.genres.add(genre)
            node.mode_counts[detected_mode] += 1

    def predict_next(self, progression, key="C", quality="Major", genre=None):
        # Try longest suffix to shortest, fallback to just last chord
        for start in range(len(progression)+1):
            node = self.root
            found = True
            for chord in progression[start:]:
                if chord in node.children:
                    node = node.children[chord]
                else:
                    found = False
                    break
            if found and node.children:
                # Found a node with children, use it
                results = []
                for sym, child in node.children.items():
                    if genre and genre not in child.genres:
                        continue
                    # Only suggest chords that have appeared in the current mode
                    mode_weight = child.mode_counts.get(quality, 0)
                    if mode_weight == 0:
                        continue
                    denom = sum(n.mode_counts[quality] for n in node.children.values() if n.mode_counts[quality] > 0)
                    prob = mode_weight / denom if denom > 0 else 0
                    display_name = TheoryEngine.get_absolute_chord(key, sym, quality)
                    results.append({
                        "symbol": sym,
                        "display": display_name,
                        "probability": round(prob, 2)
                    })
                if results:
                    return sorted(results, key=lambda x: x['probability'], reverse=True)
        # If nothing found, return empty
        return []
    
class BuiltChord:
    def __init__(self, root, quality, seventh=None):
        self.root = root
        self.quality = quality
        self.seventh = seventh
        self.display_name = TheoryEngine.get_absolute_chord(root, quality)
        self.notes = []
        self.frequencies = []

    def buildchord(self):
        if self.root:
            self.notes.append(self.root)
        else:
            self.notes.append("")
        if self.quality == "Major":
            self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 4) % 12])
            self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 7) % 12]) 
        elif self.quality == "Minor":
            self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 3) % 12]) 
            self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 7) % 12]) 
        elif self.quality == "Diminished":
            self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 3) % 12]) 
            self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 6) % 12]) 
        elif self.quality == "Augmented":
            self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 4) % 12])  
            self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 8) % 12])  
        # Add 7th if specified
        if self.seventh:
            if self.seventh == "Major":
                self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 11) % 12])
            elif self.seventh == "Minor":
                self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 10) % 12])
            elif self.seventh == "Diminished":
                self.notes.append(TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 9) % 12])
        return self.notes
    def build_frequencies(self, TheoryEngine):
        # Always put root in octave 4, stack other notes above
        octaves = []
        if not self.notes:
            return []
        start_octave = 4
        octaves.append(start_octave)
        prev_midi = TheoryEngine.NOTES.index(self.notes[0]) + 12 * start_octave
        for i, n in enumerate(self.notes[1:], 1):
            note_idx = TheoryEngine.NOTES.index(n)
            octave = start_octave
            # Always stack above previous note
            while note_idx + 12 * octave <= prev_midi:
                octave += 1
            octaves.append(octave)
            prev_midi = note_idx + 12 * octave
        self.frequencies = [TheoryEngine.FREQUENCIES.get(note + str(octave), 0) for note, octave in zip(self.notes, octaves)]
        return self.frequencies
    
    def play(self, duration=0.5):
        """
        Play the chord using sounddevice and numpy (sine waves for each note).
        duration: duration of each note in seconds
        """
        freqs = self.build_frequencies(TheoryEngine)
        samplerate = 44100
        t = np.linspace(0, duration, int(samplerate * duration), False)
        chord_wave = np.zeros_like(t)
        for freq in freqs:
            if freq > 0:
                chord_wave += 0.33 * np.sin(2 * np.pi * freq * t)
        chord_wave = chord_wave / np.max(np.abs(chord_wave))
        sd.play(chord_wave, samplerate)
        sd.wait()