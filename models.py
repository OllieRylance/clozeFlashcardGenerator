import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import math

logger = logging.getLogger(__name__)

def removePunctuation(word: str) -> str:
    """Remove punctuation from the word, keeping only letters and '~'."""
    return ''.join(char if char.isalpha() or char == '~' else '' for char in word)

def getWordRarityScore(
    word: str,
    punctuationlessWords: Dict[str, 'PunctuationlessWord'],
    maxWordFrequency: int
) -> float:
    """Calculate the rarity score of a word based on its frequency."""
    punctuationlessWord: Optional['PunctuationlessWord'] = punctuationlessWords.get(word)
    if punctuationlessWord is None:
        frequency: int = 0
    else:
        frequency = len(punctuationlessWord.referenceRawWords)

    normalized: float = frequency / maxWordFrequency
    # Exponential decay with tunable steepness
    return math.exp(-5 * normalized)

# Raw Line Class
# Contains an ID and a list of raw words
class RawLine:
    calculatedCosDissimilarities: Dict[Tuple[int, int], float] = {}
    calculatedSentenceLengthScores: Dict[int, float] = {}

    def __init__(self, rawWords: List['RawWord']) -> None:
        self.hashedRawLine: int = hash(" ".join(rawWord.word for rawWord in rawWords))

        for index, rawWord in enumerate(rawWords):
            rawWord.assignRawLine(self, index)
        self.rawWords: List['RawWord'] = rawWords
        self.score: Optional[float] = None
        self.wordVector: Optional[np.ndarray] = None

    def __str__(self) -> str:
        return ' '.join([rawWord.word for rawWord in self.rawWords])

    def __eq__(self, other: object) -> bool:
        """Check if two RawLines have equal hashes."""
        if not isinstance(other, RawLine):
            return NotImplemented
        return self.hashedRawLine == other.hashedRawLine

    def inListOfOtherRawLines(self, otherRawLines: List['RawLine']) -> bool:
        """
        Check if this raw line is in the list of other raw lines.
        """
        return any(self == otherRawLine for otherRawLine in otherRawLines)

    def getScore(
        self,
        punctuationlessWords: Dict[str, 'PunctuationlessWord'],
        maxWordFrequency: int,
        benefitShorterSentences: bool
    ) -> float:
        """
        Score a sentence based on how useful it is for clozing.
        """
        if self.score is not None:
            return self.score

        score: float = 0.0

        # Calculate the score based on the rarity of the words in the sentence
        for rawWord in self.rawWords:
            wordString: str = rawWord.punctuationlessWordString
            rarity: float = getWordRarityScore(wordString, punctuationlessWords, maxWordFrequency)
            score += rarity

        # Penalize long sentences if shorter sentences are preferred
        if benefitShorterSentences:
            lengthPenalty: float = len(self.rawWords) ** 0.8
            score: float = score / lengthPenalty

        self.score = score
        return score

    def getWordVector(self, punctuationlessWords: Dict[str, 'PunctuationlessWord']) -> np.ndarray:
        """
        Generate a word vector for the raw line.
        """
        if self.wordVector is not None:
            return self.wordVector

        # Initialize the word vector as a dictionary
        # where keys are the punctuationless words and values are their counts
        wordCounts: Dict[str, int] = {word: 0 for word in punctuationlessWords.keys()}

        # Iterate through the raw words and update the word vector
        for rawWord in self.rawWords:
            word: str = rawWord.punctuationlessWordString
            if word in wordCounts:
                wordCounts[word] += 1

        # Convert the dictionary to a numpy array for easier manipulation
        self.wordVector = np.array(list(wordCounts.values()), dtype=float)

        return self.wordVector

    def getCosDissimilarity(
        self,
        otherRawLine: 'RawLine',
        punctuationlessWords: Dict[str, 'PunctuationlessWord']
    ) -> float:
        """
        Calculate the cosine dissimilarity between this raw line and another raw line.
        """
        # Check if the cosine dissimilarity has already been calculated
        if (self.hashedRawLine, otherRawLine.hashedRawLine) in self.calculatedCosDissimilarities:
            return self.calculatedCosDissimilarities[(self.hashedRawLine, otherRawLine.hashedRawLine)]

        vector1: np.ndarray = self.getWordVector(punctuationlessWords)
        vector2: np.ndarray = otherRawLine.getWordVector(punctuationlessWords)

        # Calculate the dot product
        dotProduct: float = np.dot(vector1, vector2)
        # Calculate the magnitudes of the vectors
        magnitude1: float = float(np.linalg.norm(vector1))
        magnitude2: float = float(np.linalg.norm(vector2))
        # Calculate the normalized dot product
        if magnitude1 == 0 or magnitude2 == 0:
            normalisedDotProduct: float = 0
        else:
            normalisedDotProduct = dotProduct / (magnitude1 * magnitude2)

        # Calculate the cosine dissimilarity
        cosineDissimilarity: float = 1 - normalisedDotProduct

        # Store the calculated dissimilarity for future use
        self.calculatedCosDissimilarities[(
            self.hashedRawLine,
            otherRawLine.hashedRawLine
        )] = cosineDissimilarity

        return cosineDissimilarity

    def getSentenceLengthScore(self) -> float:
        """
        Calculate a score based on the length of the sentence.
        Shorter sentences get a higher score with a reciprocal of exponential curve.
        """
        if self.calculatedSentenceLengthScores.get(len(self.rawWords)) is not None:
            return self.calculatedSentenceLengthScores[len(self.rawWords)]

        sentenceLengthScore = 1 / (math.exp((4 * len(self.rawWords) / 25) ** 4))
        self.calculatedSentenceLengthScores[len(self.rawWords)] = sentenceLengthScore
        return sentenceLengthScore

# Simple Cloze Flashcard Class
# Contains the before and after cloze words and the cloze word
class SimpleClozeFlashcard:
    # TODO : alter this so that it can store separated multi-word expressions
    def __init__(
        self,
        beforeCloze: str,
        afterCloze: str,
        clozeWord: str,
        inUse: bool = False
    ) -> None:
        self.beforeCloze: str = beforeCloze
        self.afterCloze: str = afterCloze
        self.clozeWord: str = clozeWord
        self.inUse: bool = inUse

    def __eq__(self, other: object) -> bool:
        """Check if two SimpleClozeFlashcards are equal."""
        if not isinstance(other, SimpleClozeFlashcard):
            return NotImplemented
        return (self.beforeCloze == other.beforeCloze and
                self.afterCloze == other.afterCloze and
                self.clozeWord == other.clozeWord and
                self.inUse == other.inUse)

    def toDict(self) -> Dict[str, str]:
        """Convert SimpleClozeFlashcard to dictionary for JSON serialization."""
        return {
            "beforeCloze": self.beforeCloze,
            "afterCloze": self.afterCloze,
            "clozeWord": self.clozeWord,
            "inUse": str(self.inUse)
        }

# Cloze Flashcard Class
# Contains a raw line and the index of the word to be clozed
class ClozeFlashcard:
    def __init__(self, rawLine: RawLine, wordIndex: int, inUse: bool = False) -> None:
        self.rawLine: RawLine = rawLine
        self.wordIndex: int = wordIndex
        self.inUse: bool = inUse

        self.simpleClozeFlashcard: Optional[SimpleClozeFlashcard] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ClozeFlashcard):
            return NotImplemented
        return self.simpleClozeFlashcard == other.simpleClozeFlashcard

    def __str__(self) -> str:
        wordsBeforeCloze: str = self.GetWordsBeforeCloze()
        clozeWord: str = self.rawLine.rawWords[self.wordIndex].word
        wordsAfterCloze: str = self.GetWordsAfterCloze()
        return f"{wordsBeforeCloze} *{clozeWord}* {wordsAfterCloze}"

    # TODO : alter this so that the Simple flashcard takes MWE into account
    def GetSimpleClozeFlashcard(self) -> SimpleClozeFlashcard:
        if self.simpleClozeFlashcard is None:
            wordsBeforeCloze: str = self.GetWordsBeforeCloze()
            clozeWord: str = self.rawLine.rawWords[self.wordIndex].word
            wordsAfterCloze: str = self.GetWordsAfterCloze()
            self.simpleClozeFlashcard = SimpleClozeFlashcard(
                wordsBeforeCloze, wordsAfterCloze, clozeWord, self.inUse
            )

        return self.simpleClozeFlashcard

    def GetWordsBeforeCloze(self) -> str:
        """Get the words before the cloze word."""
        return ' '.join([rawWord.word for rawWord in self.rawLine.rawWords[:self.wordIndex]])

    def GetClozeRawWord(self) -> 'RawWord':
        """Get the raw word that is clozed."""
        return self.rawLine.rawWords[self.wordIndex]

    def GetWordsAfterCloze(self) -> str:
        """Get the words after the cloze word."""
        if self.wordIndex + 1 >= len(self.rawLine.rawWords):
            return ''

        return ' '.join([rawWord.word for rawWord in self.rawLine.rawWords[self.wordIndex + 1:]])

# Punctuationless Word Class
# Contains a word with punctuation removed and references to raw words
class PunctuationlessWord:
    def __init__(self, word: str, rawWord: 'RawWord') -> None:
        self.word: str = word
        self.referenceRawWords: List['RawWord'] = [rawWord]

    def appendRawWord(self, rawWord: 'RawWord') -> None:
        """Add a raw word to the list of reference raw words."""
        self.referenceRawWords.append(rawWord)

# Raw Word Class
class RawWord:
    def __init__(self, word: str, multiWordExpressionInfo: Optional[Tuple['MultiWordExpression', int]] = None) -> None:
        self.word: str = word
        self.punctuationlessWordString: str = removePunctuation(word)

        # Attribute to hold the MultiWordExpression and this word's index in it
        self.multiWordExpressionInfo: Optional[Tuple['MultiWordExpression', int]] = multiWordExpressionInfo

    def __str__(self) -> str:
        return self.word

    def assignRawLine(self, rawLine: RawLine, wordIndex: int) -> None:
        self.rawLine: RawLine = rawLine
        self.wordIndex: int = wordIndex

    def getSentenceScore(
        self,
        punctuationlessWords: Dict[str, PunctuationlessWord],
        maxWordFrequency: int,
        benefitShorterSentences: bool
    ) -> float:
        return self.rawLine.getScore(
            punctuationlessWords, maxWordFrequency, benefitShorterSentences
        )

class MultiWordExpression:
    MWECount: int = 0

    def __init__(self) -> None:
        self.id: int = MultiWordExpression.MWECount
        MultiWordExpression.MWECount += 1
        self.rawWords: List[RawWord] = []

        self.punctuationlessWordString: Optional[str] = None
    
    def getPunctuationlessWordString(self) -> str:
        """
        Get the punctuationless word string for the multi-word expression.
        Combines the raw words in alphabetical order.
        """
        if self.punctuationlessWordString is not None:
            return self.punctuationlessWordString

        rawWordStrings: List[str] = sorted(rawWord.word for rawWord in self.rawWords)
        self.punctuationlessWordString = removePunctuation('~'.join(rawWordStrings))
        return self.punctuationlessWordString