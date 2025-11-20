class ChordNode:
    """Chord Trie Node Class:
        Stores the name of the chord
        Stores children
        Stores a usage count
        Stores an end of progression boolean
    """

    def __init__(self):
        self.chord = str()
        self.count = 0
        self.is_end_of_progression = False
        self.children = {}

class ChordTrie:
    """Chord Trie Class:
        Stores the root node
        Methods to insert chords
        Predict next chords 
        Get children 
        Check for chord existence
    """

    def __init__(self):
        self.allchordsymbols = set()
        self.root = ChordNode()
        self.total_progressions = 0

    def insert(self, progression, target_node=None):
        for chord in progression: # Add all chords to the set
            self.allchordsymbols.add(chord)
        if target_node is None:
            target_node = self.root # Start at root if not recursing
        if progression == []:
            return
        if progression[0] not in target_node.children: # If chord not present, add it
            newchord = ChordNode()
            newchord.chord = progression[0]
            newchord.count += 1
            target_node.children[progression[0]] = newchord
            if len(progression) == 1: # Detect end of chord progression
                newchord.is_end_of_progression = True
                self.total_progressions += 1
            else:
                slicedprogression = progression[1:] # Slice progression for recursion
                self.insert(slicedprogression, newchord)
        else: # Chord already present, increment count and recurse
            slicedprogression = progression[1:] # Slice progression for recursion
            target_node.children[progression[0]].count += 1
            self.insert(slicedprogression, target_node.children[progression[0]])
                
    def predict_next(self, progression):
        if not progression:
            print("No progression provided for prediction.")
            return
        next_chord_counts = {}

        def traverse(node, path):
            if len(path) >= len(progression):
                if path[-len(progression):] == progression:
                    for child in node.children.values():
                        next_chord = child.chord
                        next_chord_counts[next_chord] = next_chord_counts.get(next_chord, 0) + 1
            for child in node.children.values():
                traverse(child, path + [child.chord])
        traverse(self.root, [])
        if not next_chord_counts:
            print("No next chord found for this progression.")
            return {}
        totalcount = sum(next_chord_counts.values())
        print("Predicted next chords with probabilities:")
        printdict = {chord: count / totalcount for chord, count in next_chord_counts.items()}
        sorted_predictions = sorted(printdict.items(), key=lambda x: x[1], reverse=True)
        for chord, probability in sorted_predictions:
            print(f"{chord}, Probability: {probability:.2f}")
        return printdict
    
    def count_subsequence(self, subsequence):
        def search(node, subseq):
            count = 0
            if not subseq:
                # If subsequence is empty, we've matched it
                count += 1
            for child in node.children.values():
                # If the current child matches the first of the subsequence, try to match the rest
                if subseq and child.chord == subseq[0]:
                    count += search(child, subseq[1:])
                # Always search for a new match starting from this child
                count += search(child, subseq)
            return count
        return search(self.root, subsequence)

    def obtain_progression(self):
        myprogression = []
        firstchord = input("Enter the first chord: ")
        myprogression.append(firstchord)
        while True:
            nextchord = input("Enter the next chord (or press enter to end): ")
            if nextchord == "":
                break
            elif nextchord not in self.allchordsymbols:
                print("Chord not recognized. Please try again.")
            else:
                myprogression.append(nextchord)
        print("You entered the progression: ", myprogression)
        print(" ")
        predictions = self.predict_next(myprogression)
        if not predictions:
            response = input("No predictions found for this progression. Would you like to predict based on only the last submitted chord? (yes/y) ")
            if response.lower() in ['yes', 'y']:
                self.predict_next([myprogression[-1]])
            else:
                print("No prediction made.")
        

    def get_children(self, chord, target_node=None):
        if target_node is None: # Set target to root if not recursing
            target_node = self.root
        nodechildren = target_node.children # Get children of the current node
        if chord in nodechildren: 
            return list(nodechildren[chord].children.keys())
        else: # Search recursively through children
            for child in nodechildren.values(): 
                result = self.get_children(chord, child)
                if result is not None:
                    return result
        return []

    def __contains__(self, chord, target_node=None):
        if target_node is None: # Set target to root if not recursing
            target_node = self.root
        if chord in target_node.children: # Check if chord is in children
            return True
        else:
            for child in target_node.children.values():
                if self.__contains__(chord, child): # Check recursively for chord
                    return True
        return False
        
    def find_progression(self, progression, target_node=None):
        if progression == []:
            return target_node 
        if target_node is None:
            target_node = self.root
        if progression[0] in target_node.children:
            slicedprogression = progression[1:]
            return self.find_progression(slicedprogression, target_node.children[progression[0]])
        else:
            return None
        

