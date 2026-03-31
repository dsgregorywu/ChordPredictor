import csv
from flask import Flask, json, request, jsonify
import importlib.util
from flask_cors import CORS 
import glob
import os
import sounddevice as sd

SONGS_FOLDER = "songs"
if not os.path.exists(SONGS_FOLDER):
    os.makedirs(SONGS_FOLDER)


app = Flask(__name__)
CORS(app)

# Import BuiltChord from chord_trie.py with error handling
import sys
chord_trie_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "chord_trie.py"))
spec = importlib.util.spec_from_file_location("chord_trie", chord_trie_path)
if spec is None or spec.loader is None:
    raise ImportError(f"Could not load chord_trie.py from {chord_trie_path}")
chord_trie = importlib.util.module_from_spec(spec)
spec.loader.exec_module(chord_trie)
@app.route('/play_section', methods=['POST'])
def play_section():
    data = request.json
    progression = data.get('progression', [])
    key = data.get('key', 'C')
    quality = data.get('quality', 'Major')
    duration = data.get('duration', 0.7)
    # Play each chord in the progression
    for symbol in progression:
        abs_chord = chord_trie.TheoryEngine.get_absolute_chord(key, symbol, quality)
        # Extract root and quality from abs_chord (e.g., 'C#m7' -> root='C#', quality='Minor')
        import re
        m = re.match(r"([A-G]#?)(.*)", abs_chord)
        if not m:
            continue
        root, flavor = m.group(1), m.group(2)
        # Determine chord quality
        if 'dim' in flavor:
            q = 'Diminished'
        elif 'aug' in flavor:
            q = 'Augmented'
        elif 'm' in flavor and not flavor.startswith('M'):
            q = 'Minor'
        else:
            q = 'Major'
        # Detect 7th type
        seventh = None
        if 'maj7' in flavor or 'M7' in flavor:
            seventh = 'Major'
        elif '7' in flavor and not 'maj7' in flavor and not 'M7' in flavor and not 'dim7' in flavor:
            seventh = 'Minor'  # Dominant 7th (b7)
        elif 'm7' in flavor:
            seventh = 'Minor'
        elif 'dim7' in flavor:
            seventh = 'Diminished'
        chord = chord_trie.BuiltChord(root, q, seventh)
        chord.buildchord()
        chord.play(duration=duration)
    return jsonify({'status': 'ok'})

# --- MUSIC THEORY & TRIE LOGIC ---

class TheoryEngine:
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    
    # Standard Major: I(0), ii(2), iii(4), IV(5), V(7), vi(9), vii(11)
    MAJOR_MAP = {
        'i': 0, 'I': 0, 'bii': 1, 'bII': 1, 'ii': 2, 'II': 2, 'biii': 3, 'bIII': 3,
        'iii': 4, 'III': 4, 'iv': 5, 'IV': 5, 'bv': 6, 'bV': 6, 'v': 7, 'V': 7,
        'bvi': 8, 'bVI': 8, 'vi': 9, 'VI': 9, 'bvii': 10, 'bVII': 10, 'vii': 11, 'VII': 11
    }

    # Standard Minor: i(0), ii(2), III(3), iv(5), v(7), VI(8), VII(10)
    # This ensures that "III" in A Minor is C Major (3 semitones), not C#
    MINOR_MAP = {
        'i': 0, 'I': 0, 'bii': 1, 'bII': 1, 'ii': 2, 'II': 2, 'iii': 3, 'III': 3,
        'iv': 5, 'IV': 5, 'v': 7, 'V': 7, 'vi': 8, 'VI': 8, 'vii': 10, 'VII': 10
    }

    @staticmethod
    def get_absolute_chord(key_root, symbol, quality="Major"):
        import re
        m = re.match(r"([b♭]?[iIvV]{1,3})(.*)", symbol)
        if not m:
            return symbol
        root_part, flavor = m.group(1), m.group(2)
        root_part = root_part.replace('♭', 'b')
        # Use MAJOR_MAP or MINOR_MAP based on the SONG quality, not the chord's case
        if quality == "Minor":
            current_map = TheoryEngine.MINOR_MAP
        else:
            current_map = TheoryEngine.MAJOR_MAP
        if root_part not in current_map:
            return symbol
        key_root_fixed = key_root.replace('b', '#')
        if key_root_fixed == "Bb": key_root_fixed = "A#"
        if key_root_fixed == "Eb": key_root_fixed = "D#"
        if key_root_fixed == "Ab": key_root_fixed = "G#"
        if key_root_fixed == "Db": key_root_fixed = "C#"
        if key_root_fixed == "Gb": key_root_fixed = "F#"
        try:
            start_idx = TheoryEngine.NOTES.index(key_root_fixed.upper())
            offset = current_map[root_part]
            chord_note = TheoryEngine.NOTES[(start_idx + offset) % 12]
            # Explicitly set flavor for major/minor if not present, based on roman numeral case
            if root_part[0].islower():
                if not (flavor.startswith('m') or flavor.startswith('M') or 'dim' in flavor or 'aug' in flavor):
                    flavor = 'm' + flavor
            else:
                if flavor.startswith('m') or flavor.startswith('M'):
                    pass  # already minor
                elif 'dim' in flavor or 'aug' in flavor:
                    pass  # already special
                else:
                    flavor = '' + flavor  # ensure major is explicit (no 'm')
            return f"{chord_note}{flavor}"
        except:
            return symbol

class ChordNode:
    def __init__(self, chord=""):
        self.chord = chord
        self.count = 0
        self.children = {}
        self.genres = set()
        self.mode_counts = {"Major": 0, "Minor": 0}

class ChordTrie:
    def __init__(self):
        self.root = ChordNode()

    def insert(self, progression, genre="General"):
        # Detect mode from the data itself
        first_chord = progression[0] if progression else "I"
        detected_mode = "Minor" if first_chord[0].islower() else "Major"
        node = self.root
        for symbol in progression:
            key = node
            quality = detected_mode
            abs_chord = chord_trie.TheoryEngine.get_absolute_chord(key, symbol, quality)
            import re
            m = re.match(r"([A-G]#?)(.*)", abs_chord)
            if not m:
                continue
            root, flavor = m.group(1), m.group(2)
            # Use the original roman numeral case to determine quality
            roman_match = re.match(r"([b♭]?[iIvV]{1,3})", symbol)
            if roman_match and roman_match.group(1)[0].islower():
                q = 'Minor'
            else:
                q = 'Major'
            if 'dim' in flavor:
                q = 'Diminished'
            elif 'aug' in flavor:
                q = 'Augmented'
            elif 'm' in flavor and not flavor.startswith('M'):
                q = 'Minor'
            elif flavor == '':
                pass  # keep q as set by roman numeral
            # Detect 7th type
            seventh = None
            if 'maj7' in flavor or 'M7' in flavor:
                seventh = 'Major'
            elif '7' in flavor and not 'maj7' in flavor and not 'M7' in flavor and not 'dim7' in flavor:
                seventh = 'Minor'  # Dominant 7th (b7)
            elif 'm7' in flavor:
                seventh = 'Minor'
            elif 'dim7' in flavor:
                seventh = 'Diminished'
            chord = chord_trie.BuiltChord(root, q, seventh)
            chord.buildchord()
            chord.play(duration=.8)
            results = []
            for sym, child in node.children.items():
                if genre and genre.lower() != "all" and genre not in child.genres:
                    continue
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
        return []

# --- GLOBAL DATA INITIALIZATION ---

trie = chord_trie.ChordTrie()

def init_data():
    try:
        with open("chord-porgressions-roman-numeral.csv", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                genre = row.get("Style", "Popular")
                raw = row["Progression"]
                for dash in ['–', '—', '\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2015']:
                    raw = raw.replace(dash, '-')
                progression = [c.strip() for c in raw.split('-') if c.strip()]
                trie.insert(progression, genre=genre)
        print("Trie initialized successfully.")
    except FileNotFoundError:
        print("Error: CSV file not found.")

# --- API ROUTES ---

@app.route('/predict', methods=['POST'])
def predict():
    data = request.json
    prog = data.get('progression', [])
    key = data.get('key', 'C')
    quality = data.get('quality', 'Major')
    genre = data.get('genre', None)
    
    predictions = trie.predict_next(prog, key=key, quality=quality, genre=genre)
    return jsonify(predictions)

@app.route('/save_project', methods=['POST'])
def save_project():
    project_data = request.json
    project_id = project_data.get('id')
    filename = os.path.join(SONGS_FOLDER, f"project_{project_id}.json")
    with open(filename, 'w') as f:
        json.dump(project_data, f, indent=4)
    return jsonify({"status": "success", "message": "Project saved to folder!"})

@app.route('/list_projects', methods=['GET'])
def list_projects():
    projects = []
    for filename in os.listdir(SONGS_FOLDER):
        if filename.endswith(".json"):
            path = os.path.join(SONGS_FOLDER, filename)
            with open(path, 'r') as f:
                data = json.load(f)
                projects.append({
                    "title": data.get('title', 'Untitled'),
                    "filename": filename 
                })
    return jsonify(projects)

@app.route('/load_project/<filename>', methods=['GET'])
def load_project(filename):
    path = os.path.join(SONGS_FOLDER, filename)
    with open(path, 'r') as f:
        return jsonify(json.load(f))
    
@app.route('/delete_project/<filename>', methods=['DELETE'])
def delete_project(filename):
    try:
        file_path = os.path.join(SONGS_FOLDER, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"status": "success", "message": "Project deleted!"})
        else:
            return jsonify({"status": "error", "message": "File not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/play_chord', methods=['POST'])
def play_chord():
    data = request.json
    symbol = data.get('chord')
    key = data.get('key', 'C')
    quality = data.get('quality', 'Major')
    duration = data.get('duration', 1.5)
    abs_chord = chord_trie.TheoryEngine.get_absolute_chord(key, symbol, quality)
    import re
    m = re.match(r"([A-G]#?)(.*)", abs_chord)
    if not m:
        return jsonify({'status': 'error', 'message': 'Invalid chord'}), 400
    root, flavor = m.group(1), m.group(2)
    roman_match = re.match(r"([b♭]?[iIvV]{1,3})", symbol)
    if roman_match and roman_match.group(1)[0].islower():
        q = 'Minor'
    else:
        q = 'Major'
    if 'dim' in flavor:
        q = 'Diminished'
    elif 'aug' in flavor:
        q = 'Augmented'
    elif 'm' in flavor and not flavor.startswith('M'):
        q = 'Minor'
    else:
        q = 'Major'
    seventh = None
    if 'maj7' in flavor or 'M7' in flavor:
        seventh = 'Major'
    elif '7' in flavor and not 'maj7' in flavor and not 'M7' in flavor and not 'dim7' in flavor:
        seventh = 'Minor'
    elif 'm7' in flavor:
        seventh = 'Minor'
    elif 'dim7' in flavor:
        seventh = 'Diminished'
    chord = chord_trie.BuiltChord(root, q, seventh)
    chord.buildchord()
    chord.play(duration=duration)
    return jsonify({'status': 'ok'})

@app.route('/get_chord_notes', methods=['POST'])
def get_chord_notes():
    data = request.get_json()
    symbol = data.get('chord')
    key = data.get('key', 'C')
    quality = data.get('quality', 'Major')
    abs_chord = chord_trie.TheoryEngine.get_absolute_chord(key, symbol, quality)
    import re
    m = re.match(r"([A-G]#?)(.*)", abs_chord)
    if not m:
        return jsonify({'notes': []})
    root, flavor = m.group(1), m.group(2)
    if 'dim' in flavor:
        q = 'Diminished'
    elif 'aug' in flavor:
        q = 'Augmented'
    elif 'm' in flavor and not flavor.startswith('M'):
        q = 'Minor'
    else:
        q = 'Major'
    seventh = None
    if 'maj7' in flavor or 'M7' in flavor:
        seventh = 'Major'
    elif '7' in flavor and not 'maj7' in flavor and not 'M7' in flavor and not 'dim7' in flavor:
        seventh = 'Minor'
    elif 'm7' in flavor:
        seventh = 'Minor'
    elif 'dim7' in flavor:
        seventh = 'Diminished'
    chord = chord_trie.BuiltChord(root, q, seventh)
    chord.buildchord()
    octaves = []
    if not chord.notes:
        return jsonify({'notes': []})
    root_note = chord.notes[0]
    if chord_trie.TheoryEngine.NOTES.index(root_note) > chord_trie.TheoryEngine.NOTES.index("G"):
        start_octave = 3
    else:
        start_octave = 4
    octaves.append(start_octave)
    prev_midi = chord_trie.TheoryEngine.NOTES.index(chord.notes[0]) + 12 * start_octave
    for n in chord.notes[1:]:
        note_idx = chord_trie.TheoryEngine.NOTES.index(n)
        octave = start_octave
        while note_idx + 12 * octave <= prev_midi:
            octave += 1
        octaves.append(octave)
        prev_midi = note_idx + 12 * octave
    notes = [note + str(octave) for note, octave in zip(chord.notes, octaves)]
    return jsonify({'notes': notes})

if __name__ == '__main__':
    init_data()
    app.run(debug=True, port=8000)