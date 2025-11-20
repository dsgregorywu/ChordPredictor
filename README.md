# Chord-Predictor

Project Title and Description
This is my tree-based chord predictor! It uses a Trie to store existing chord progressions from a Kaggle dataset, then searches that tree based on the inputted beginning chords 
from the user. This program is designed for beginner composers who don't yet have a great understanding of music theory in order to give ideas for chord progressions. This is 
something I struggle with as a musician and arranger, and would love for this project to be something that I can use in the future for my compositions.

Team Members and Roles:
Derec Gregory (Everything)

Installation & Setup
The only required package for this is csv, as it reads in the chord progressions from a csv file. 
To use my program, follow these steps:
Step 1: Run the program
Step 2: Enter your existing chord(s)
Step 3: Pick one that is recommended to you!

Usage Guide
See above! It's very user friendly and designed to be simple. If you don't give it a correct chord, it will ask you to try again so no worries 
for non-musicians! You input a chord or chord progression when asked, then you are outputted some amount of potential next chords, ordered from most 
frequent to least frequent. Higher up chords are found more commonly in chord progressions and might be a better choice!

Screenshots/Demos
I have screenshots in the folder named Screenshots of some example interactions.

Screenshot 1. Testing to see if the common ii-V-I progression works. This progression is found commonly in jazz, as the ii chord is not popular in most mainstream music, 
so there aren't any other potential ending chords for an inputted ii-V.

Screenshot 2. Finding potential next chord based off of just a V chord. A V chord is found in almost every piece of music and loves to resolve to a I or i chord. 
I'm testing this to find the frequency of how often it resolves to I or i versus to a different chord.

Screenshot 3. Testing an uncommon chord progression (III-V-VI) and getting denied, then having it search based just on the last chord (VI). Since this chord 
progression is never used, this serves as a test to see how well the failsafe of searching just using the last chord works.

Tree Implementation Details

My Trie works by taking in chord progressions from the csv, loading the first as a subchild of the root node (which doesn't have a chord) if the first chord of the progression
is not already a subchild of the root node. It then goes its way through the chord progression, branching off to become a new branch if the chord progression does not yet exist.
The main function of predicting a chord is O(N x L) where N is the amount of nodes in the tree and L is the length of the progression. The space complexity is O(C) where C is the 
amount of possible next chords, and is typically between 1 and 8. Insertion of a progression has a time complexity of O(L) is the length of the progression, often between 1 and 5, 
so this is pretty much O(1). Insertion has a space complexity of O(N x L), which is the total amount of nodes times the length of the progression.

I implemented most of my functions recursively which works surprisingly well for this type of assignment due to the nature of finding bits and pieces of chord progressions. The 
ability to recursively go through each branch and quickly check for the inputted chord progression helps make this extremely efficient and would translate very well on a large scale.

Evolution of the Interface
I didn't originally have it as a loop, just as a one-time function. I wanted to make it into a loop as a way of efficiency, as well as if I was going to turn this project into a 
website or something, it would make it much more user-friendly. From this process, I learned to think from a user's perspective, where focusing on what is accessible for them is 
most important.

Challenges & Solutions
This was surprisingly difficult. Music (and chords especially) don't translate well to something as binary as computers. My main issue was getting data. I found a small Kaggle dataset
with chord progressions that I liked and have been using that, but added a few manually that it missed. What's tough about a project like this is that SO much modern music uses the same
10-15 chord progressions. I want my program to recommend what is best and most common, so the more data on different and unique chord progressions I give it, the less accurate the outputs
will be, which is not something I've ran into before. One solution I thought of would be some sort of "weight" to each chord progression based off of how common it is used in music, but 
there isn't really a subjective way to implement that, at least on this time frame. My actual solution is to leave it with a smaller dataset, so that way it doesn't overrecommend uncommon 
chord progressions while treating more obvious answers with less priority. Another difficult task was translating csv data into chord progressions I could use. Due to the sheer number 
of ways chords can be written, it was difficult to make it so that every format would load correctly without accidentally thinking there were extra characters at the end or beginning of a 
chord. This ties back into music not translating very well to computers, but it's something I love so I've been determined to make it work. My fix for that was unfortunately to go through 
all of the data I had and clean it myself, which on this small of a dataset didn't take very long, but on a larger scale I would use Posit Cloud or something to make it all cleaner 
and more readable in my program.

Future Enhancements

If I had more time, I would add SO many more chord progressions, as well as figure out a way to make the "weighting" system work. My brain went to taking in a midi file, detecting the 
chords, and turning them into chord symbols of as much music as I can find, and while my other Algorithms project might be able to help with that, getting chords from Midi files would
not be very accurate and it would likely end up giving false information. This again ties back into music just not translating well into computers unfortunately.
