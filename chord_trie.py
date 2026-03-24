import csv

class TheoryEngine:
    """Handles translation from Roman Numerals (I, ii, bVII) to Notes."""
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
    # Mapping symbols to semitone offsets
    # Lowercase = minor, Uppercase = Major (standard notation)
    SCALE_MAP = {
        'i': 0, 'I': 0,
        'bii': 1, 'bII': 1,
        'ii': 2, 'II': 2,
        'biii': 3, 'bIII': 3,
        'iii': 4, 'III': 4,
        'iv': 5, 'IV': 5,
        'bv': 6, 'bV': 6,
        'v': 7, 'V': 7,
        'bvi': 8, 'bVI': 8,
        'vi': 9, 'VI': 9,
        'bvii': 10, 'bVII': 10,
        'vii': 11, 'VII': 11
    }

    @staticmethod
    def get_absolute_chord(key_root, symbol):
        # Extract accidental/number (e.g., 'bVII') from flavor (e.g., 'm7')
        # This is a simplified parser for your CSV format
        root_part = ""
        for char in symbol:
            if char in "ibIIVVb": root_part += char
            else: break
        
        flavor = symbol[len(root_part):]
        
        if root_part not in TheoryEngine.SCALE_MAP:
            return symbol # Return original if we can't parse it
            
        start_idx = TheoryEngine.NOTES.index(key_root.upper())
        offset = TheoryEngine.SCALE_MAP[root_part]
        chord_note = TheoryEngine.NOTES[(start_idx + offset) % 12]
        
        # Basic rule: if the Roman Numeral is lowercase, it's a minor chord
        if root_part[0].islower() and "m" not in flavor:
            flavor = "m" + flavor
            
        return f"{chord_note}{flavor}"

class ChordNode:
    def __init__(self, chord=str()):
        self.chord = chord
        self.count = 0
        self.children = {}
        self.genres = set()

class ChordTrie:
    def __init__(self):
        self.root = ChordNode()

    def insert(self, progression, genre="General"):
        node = self.root
        for chord in progression:
            if chord not in node.children:
                node.children[chord] = ChordNode(chord)
            node = node.children[chord]
            node.count += 1
            node.genres.add(genre)

    def predict_next(self, progression, key="C", genre=None):
        node = self.root
        # Navigate to the current spot
        for chord in progression:
            if chord in node.children:
                node = node.children[chord]
            else:
                return []

        # Calculate probabilities for children
        total = sum(child.count for child in node.children.values())
        results = []
        for sym, child in node.children.items():
            if genre and genre not in child.genres:
                continue
            
            prob = child.count / total
            display_name = TheoryEngine.get_absolute_chord(key, sym)
            
            results.append({
                "symbol": sym, 
                "display": display_name, 
                "probability": round(prob, 2)
            })
            
        return sorted(results, key=lambda x: x['probability'], reverse=True)