import csv
import numpy as np
import sounddevice as sd

class TheoryEngine:
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]    
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
        "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56,
        "E3": 164.81, "F3": 174.61, "F#3": 185.00, "G3": 196.00,
        "G#3": 207.65, "A3": 220.00, "A#3": 233.08, "B3": 246.94,

        "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13,
        "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00,
        "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,

        "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25,
        "E5": 659.25, "F5": 698.46, "F#5": 739.99, "G5": 783.99,
        "G#5": 830.61, "A5": 880.00, "A#5": 932.33, "B5": 987.77
    }


    @staticmethod
    def get_absolute_chord(key_root, symbol, quality="Major"):
        import re
        # Accept sharps/flats in root and roman, and pass through all extensions
        m = re.match(r"([b#♭♯]?((?:i{1,3})|iv|vii|vi|v|IV|VII|VI|V|I{1,3}))(.*)", symbol, re.IGNORECASE)
        if not m:
            return symbol
        root_part, flavor = m.group(1), m.group(3)
        root_part = root_part.replace('♭', 'b').replace('♯', '#')
        key_root_fixed = key_root.replace('♭', 'b').replace('♯', '#')
        if key_root_fixed == "Bb": key_root_fixed = "A#"
        elif key_root_fixed == "Eb": key_root_fixed = "D#"
        elif key_root_fixed == "Ab": key_root_fixed = "G#"
        elif key_root_fixed == "Db": key_root_fixed = "C#"
        elif key_root_fixed == "Gb": key_root_fixed = "F#"
        try:
            start_idx = TheoryEngine.NOTES.index(key_root_fixed.upper())
            mode_map = TheoryEngine.MODES.get(quality, TheoryEngine.MODES["Major"])
            # Special handling for bI and #I (chromatic root alterations)
            if root_part.lower() == 'bi':
                chord_note = TheoryEngine.NOTES[(start_idx - 1) % 12]
            elif root_part.lower() == '#i':
                chord_note = TheoryEngine.NOTES[(start_idx + 1) % 12]
            else:
                offset = mode_map[root_part]
                chord_note = TheoryEngine.NOTES[(start_idx + offset) % 12]
            # Diatonic quality
            roman = root_part.replace('b','').replace('#','')
            diatonic_qualities = {
                'Major': {
                    'I': '', 'ii': 'm', 'iii': 'm', 'IV': '', 'V': '', 'vi': 'm', 'vii': 'dim',
                    'bII': '', 'bIII': '', 'bVI': '', 'bVII': '', 'bV': '', 'bvii': 'dim', 'bv': '',
                },
                'Minor': {
                    'i': 'm', 'ii': 'dim', 'III': '', 'iv': 'm', 'v': 'm', 'VI': '', 'VII': '',
                    'bII': '', 'bIII': '', 'bVI': '', 'bVII': '', 'bV': '', 'bvii': 'dim', 'bv': '',
                }
            }
            qmap = diatonic_qualities['Minor' if quality=="Minor" else 'Major']
            # If flavor doesn't specify m, dim, aug, 7, etc, use diatonic
            if not flavor or not (flavor.startswith('m') or 'dim' in flavor or 'aug' in flavor):
                if roman in qmap and qmap[roman]:
                    flavor = qmap[roman] + flavor
            if 'dim' in flavor and not flavor.startswith('dim'):
                flavor = 'dim' + flavor.replace('dim','')
            # Pass through all extensions (including b9/#9)
            return f"{chord_note}{flavor}"
        except Exception:
            return symbol

class ChordNode:
    def __init__(self, chord=str()):
        self.chord = chord
        self.count = 0
        self.children = {}
        self.genres = set()
        self.mode_counts = {"Major": 0, "Minor": 0}

class ChordTrie:
    def __init__(self):
        self.root = ChordNode()

    def insert(self, progression, genre="General", quality="Major"):
        node = self.root
        for chord in progression:
            if chord not in node.children:
                node.children[chord] = ChordNode(chord)
            node = node.children[chord]
            node.count += 1
            node.genres.add(genre)
            # Use the provided quality as the mode
            if quality in node.mode_counts:
                node.mode_counts[quality] += 1
            else:
                node.mode_counts[quality] = 1

    def predict_next(self, progression, key="C", quality="Major", genre=None):
        if not progression:
            # Only suggest chords that exist in the trie as first chords, weighted by actual frequency
            first_chord_counts = {}
            for child in self.root.children.values():
                for mode in child.mode_counts:
                    if quality == mode and child.mode_counts[mode] > 0:
                        first_chord_counts[child.chord] = child.mode_counts[mode]
            total = sum(first_chord_counts.values())
            results = []
            for sym, count in first_chord_counts.items():
                display_name = TheoryEngine.get_absolute_chord(key, sym, quality)
                prob = count / total if total > 0 else 0
                results.append({
                    "symbol": sym,
                    "display": display_name,
                    "probability": round(prob, 2)
                })
            return sorted(results, key=lambda x: x['probability'], reverse=True)
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
    def __init__(self, root, flavor):
        self.root = root
        self.flavor = flavor.lower() if flavor else ''
        # Parse quality and seventh for compatibility
        if 'dim' in self.flavor and 'dim7' not in self.flavor:
            self.quality = 'Diminished'
        elif 'aug' in self.flavor:
            self.quality = 'Augmented'
        elif 'm' in self.flavor and not self.flavor.startswith('M'):
            self.quality = 'Minor'
        else:
            self.quality = 'Major'
        self.display_name = root + flavor if flavor else root
        self.notes = []
        self.frequencies = []

    def buildchord(self):
        # Always start with the root
        if self.root:
            self.notes.append(self.root)
        else:
            self.notes.append("")

        def interval(semitones):
            return TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + semitones) % 12]

        # Parse extensions from self.display_name or self.seventh
        ext = self.display_name.lower() if hasattr(self, 'display_name') else ''
        # Parse for all allowed extensions in order of musical priority
        # 1. sus2/sus4/sus24
        sus2 = 'sus2' in ext
        sus4 = 'sus4' in ext
        sus24 = 'sus24' in ext or 'sus2sus4' in ext
        # 2. triad base
        if 'dim' in ext and 'dim7' not in ext:
            third = interval(3)
            fifth = interval(6)
        elif 'aug' in ext:
            third = interval(4)
            fifth = interval(8)
        elif 'm' in ext and not sus2 and not sus4 and not sus24:
            third = interval(3)
            fifth = interval(7)
        else:
            third = interval(4)
            fifth = interval(7)
        # sus overrides third
        if sus24:
            third = interval(2)
            self.notes.append(third)
            self.notes.append(interval(5))
        elif sus2:
            third = interval(2)
            self.notes.append(third)
        elif sus4:
            third = interval(5)
            self.notes.append(third)
        else:
            self.notes.append(third)
        self.notes.append(fifth)

        # 3. 6th, 7th, 9th, 11th, 13th, add9, etc.
        if '6/9' in ext:
            self.notes.append(interval(9))
            self.notes.append(interval(14))
        elif '6' in ext and '13' not in ext:
            self.notes.append(interval(9))
        if 'maj7' in ext or 'Δ7' in ext:
            self.notes.append(interval(11))
        elif 'm7' in ext or 'min7' in ext or (self.quality == "Minor" and '7' in ext):
            self.notes.append(interval(10))
        elif '7' in ext and 'dim7' not in ext and 'maj7' not in ext:
            self.notes.append(interval(10))
        elif 'dim7' in ext or 'o7' in ext:
            self.notes.append(interval(9))
        # 9th: always a major 9th above the root, not relative to the key
        if '9' in ext and 'add9' not in ext:
            ninth = TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 2) % 12]  # major 9th = root + 2 semitones (octave up)
            self.notes.append(ninth)
        elif 'add9' in ext:
            ninth = TheoryEngine.NOTES[(TheoryEngine.NOTES.index(self.root) + 2) % 12]
            self.notes.append(ninth)
        if '11' in ext:
            self.notes.append(interval(17))
        if '13' in ext:
            self.notes.append(interval(21))

        # 4. b5/#5, b9/#9, b13/#11
        if 'b5' in ext:
            self.notes[2] = interval(6)
        if '#5' in ext:
            self.notes[2] = interval(8)
        if 'b9' in ext:
            self.notes.append(interval(13))
        if '#9' in ext:
            self.notes.append(interval(15))
        if 'b13' in ext:
            self.notes.append(interval(20))
        if '#11' in ext:
            self.notes.append(interval(18))

        # 5. no5/no3
        if 'no5' in ext and len(self.notes) > 2:
            self.notes.pop(2)
        if 'no3' in ext and len(self.notes) > 1:
            self.notes.pop(1)

        # 6. alt (altered dominant: b5, #5, b9, #9, #11, b13)
        if 'alt' in ext:
            self.notes[2] = interval(6)  # b5
            self.notes.append(interval(8))  # #5
            self.notes.append(interval(13)) # b9
            self.notes.append(interval(15)) # #9
            self.notes.append(interval(18)) # #11
            self.notes.append(interval(20)) # b13

        # Remove duplicates, preserve order
        seen = set()
        out = []
        for n in self.notes:
            if n not in seen:
                out.append(n)
                seen.add(n)
        self.notes = out
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