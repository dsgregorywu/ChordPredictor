import csv
from chord_trie import ChordTrie

def load_data(trie):
    with open("chord-porgressions-roman-numeral.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            genre = row.get("Style", "Popular")
            raw = row["Progression"]
            # Your dash cleaning logic
            for dash in ['–', '—', '\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2015']:
                raw = raw.replace(dash, '-')
            
            progression = [c.strip() for c in raw.split('-') if c.strip()]
            trie.insert(progression, genre=genre)

def main():
    trie = ChordTrie()
    load_data(trie)
    
    print("Welcome to the Chord Planner!")
    user_key = input("Enter your song key (e.g., D): ")
    current_prog = []
    
    while True:
        print(f"\nCurrent Progression: {' -> '.join(current_prog)}")
        preds = trie.predict_next(current_prog, key=user_key)
        
        if preds:
            print("Suggestions:")
            for i, p in enumerate(preds[:3]):
                print(f"{i+1}. {p['display']} ({p['symbol']}) - {int(p['probability']*100)}%")
        
        next_val = input("\nEnter next Roman Numeral (or 'exit'): ")
        if next_val.lower() == 'exit': break
        current_prog.append(next_val)

if __name__ == "__main__":
    main()