import csv
from flask import Flask, json, request, jsonify
from flask_cors import CORS  # You'll need: pip install flask-cors
import glob
import os

SONGS_FOLDER = "songs"
if not os.path.exists(SONGS_FOLDER):
    os.makedirs(SONGS_FOLDER)


app = Flask(__name__)
CORS(app) # This allows your frontend to talk to this backend

# --- MUSIC THEORY & TRIE LOGIC ---

class TheoryEngine:
    NOTES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    SCALE_MAP = {
        'i': 0, 'I': 0, 'bii': 1, 'bII': 1, 'ii': 2, 'II': 2, 'biii': 3, 'bIII': 3,
        'iii': 4, 'III': 4, 'iv': 5, 'IV': 5, 'bv': 6, 'bV': 6, 'v': 7, 'V': 7,
        'bvi': 8, 'bVI': 8, 'vi': 9, 'VI': 9, 'bvii': 10, 'bVII': 10, 'vii': 11, 'VII': 11
    }

    @staticmethod
    def get_absolute_chord(key_root, symbol):
        root_part = ""
        for char in symbol:
            if char in "ibIIVVb": root_part += char
            else: break
        flavor = symbol[len(root_part):]
        
        if root_part not in TheoryEngine.SCALE_MAP:
            return symbol
            
        start_idx = TheoryEngine.NOTES.index(key_root.upper())
        offset = TheoryEngine.SCALE_MAP[root_part]
        chord_note = TheoryEngine.NOTES[(start_idx + offset) % 12]
        
        if root_part[0].islower() and "m" not in flavor:
            flavor = "m" + flavor
        return f"{chord_note}{flavor}"

class ChordNode:
    def __init__(self, chord=""):
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
        for chord in progression:
            if chord in node.children:
                node = node.children[chord]
            else:
                return []

        total = sum(child.count for child in node.children.values())
        results = []
        for sym, child in node.children.items():
            if genre and genre.lower() != "all" and genre not in child.genres:
                continue
            
            prob = child.count / total
            display_name = TheoryEngine.get_absolute_chord(key, sym)
            results.append({
                "symbol": sym, 
                "display": display_name, 
                "probability": round(prob, 2)
            })
        return sorted(results, key=lambda x: x['probability'], reverse=True)

# --- GLOBAL DATA INITIALIZATION ---

trie = ChordTrie()

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
    # Expecting: { "progression": ["I", "V"], "key": "G", "genre": "Rock" }
    prog = data.get('progression', [])
    key = data.get('key', 'C')
    genre = data.get('genre', None)
    
    predictions = trie.predict_next(prog, key=key, genre=genre)
    return jsonify(predictions)

import os

# Define the folder name
SONGS_FOLDER = "songs"

# Create the folder if it doesn't exist yet
if not os.path.exists(SONGS_FOLDER):
    os.makedirs(SONGS_FOLDER)

@app.route('/save_project', methods=['POST'])
def save_project():
    project_data = request.json
    project_id = project_data.get('id')
    
    # Save inside the 'songs' folder
    filename = os.path.join(SONGS_FOLDER, f"project_{project_id}.json")
    
    with open(filename, 'w') as f:
        json.dump(project_data, f, indent=4)
        
    return jsonify({"status": "success", "message": "Project saved to folder!"})

@app.route('/list_projects', methods=['GET'])
def list_projects():
    projects = []
    # Only look inside the 'songs' folder
    for filename in os.listdir(SONGS_FOLDER):
        if filename.endswith(".json"):
            path = os.path.join(SONGS_FOLDER, filename)
            with open(path, 'r') as f:
                data = json.load(f)
                projects.append({
                    "title": data.get('title', 'Untitled'),
                    "filename": filename # Still need the filename to load it later
                })
    return jsonify(projects)

@app.route('/load_project/<filename>', methods=['GET'])
def load_project(filename):
    # Load from the 'songs' folder
    path = os.path.join(SONGS_FOLDER, filename)
    with open(path, 'r') as f:
        return jsonify(json.load(f))
    
if __name__ == '__main__':
    print("--- Starting ChordTrie Server ---")
    
    # Check if the folder exists
    if not os.path.exists(SONGS_FOLDER):
        print(f"Creating folder: {SONGS_FOLDER}")
        os.makedirs(SONGS_FOLDER)
    else:
        print(f"Found existing folder: {SONGS_FOLDER}")

    print("Checking for Trie data...")
    init_data() # Make sure this function doesn't have an infinite loop!
    
    print("Attempting to launch Flask on Port 8000...")
    app.run(debug=True, port=8000)