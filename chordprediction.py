import csv
from chord_trie import ChordTrie

def create_data():
    progressions = []
    with open("chord-porgressions-roman-numeral.csv", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            raw = row["Progression"]
            for dash in ['–', '—', '\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2015']:
                raw = raw.replace(dash, '-')
            progression = [chord.strip() for chord in raw.split('-') if chord.strip()]
            progressions.append(progression)
    return progressions

def main():
    progressions = create_data()
    trie = ChordTrie()
    for progression in progressions:
        trie.insert(progression)
    while True:
        trie.obtain_progression()
        again = input("\nDo you want to enter another progression? (y/n): ").lower()
        if again not in ("y", "yes"):
            break

if __name__ == "__main__":
    main()
