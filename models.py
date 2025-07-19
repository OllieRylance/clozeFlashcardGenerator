import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import math

logger = logging.getLogger(__name__)

def removePunctuation(word: str) -> str:
    """Remove punctuation from the word, keeping only letters."""
    return ''.join(char if char.isalpha() else '' for char in word)

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
            score = score / lengthPenalty

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
    # TODO : reformat the outputs to with the following changes:
    #   current:
    #   {
    #       "beforeCloze": "words",
    #       "midCloze": "words",
    #       "afterCloze": "",
    #       "clozeWordPart1": "words,",
    #       "clozeWordPart2": "words?",
    #       "inUse": "False"
    #   }
    #   desired:
    #   {
    #       "beforeCloze": "words ",
    #       "midCloze": ", words",
    #       "afterCloze": "?",
    #       "clozeWordPart1": "words",
    #       "clozeWordPart2": "words",
    #       "inUse": "False"
    #   }
    #   The changes include taking the punctuation out of the cloze words and including the spaces
    #   between the rest of the words and the clozes
    #   This may require adding a punctuation class and separating the punctuation from the words
    #   so that if puncuation is after the last which is the cloze word, it is included in the
    #   afterCloze 
    
    def __init__(
        self,
        beforeCloze: str,
        midCloze: str,
        afterCloze: str,
        clozeWordPart1: str,
        clozeWordPart2: str,
        inUse: bool = False
    ) -> None:
        self.beforeCloze: str = beforeCloze
        self.midCloze: str = midCloze
        self.afterCloze: str = afterCloze
        self.clozeWordPart1: str = clozeWordPart1
        self.clozeWordPart2: str = clozeWordPart2
        self.inUse: bool = inUse

    def toDict(self) -> Dict[str, str]:
        """Convert SimpleClozeFlashcard to dictionary for JSON serialization."""
        return {
            'beforeCloze': self.beforeCloze,
            'midCloze': self.midCloze,
            'afterCloze': self.afterCloze,
            'clozeWordPart1': self.clozeWordPart1,
            'clozeWordPart2': self.clozeWordPart2,
            'inUse': str(self.inUse)
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
        if self.simpleClozeFlashcard is not None:
            return self.simpleClozeFlashcard

        clozeRawWord: RawWord = self.rawLine.rawWords[self.wordIndex]
        
        if clozeRawWord.multiWordExpressionInfo is None:
            clozeWord = clozeRawWord.word
            beforeCloze: str = self.GetWordsBeforeCloze()
            afterCloze: str = self.GetWordsAfterCloze()
            self.simpleClozeFlashcard = SimpleClozeFlashcard(
                beforeCloze, "", afterCloze, clozeWord, "", self.inUse
            )
            return self.simpleClozeFlashcard
        
        # If the cloze word is part of a multi-word expression
        multiWordExpressionId: int = clozeRawWord.multiWordExpressionInfo[0].id
        wordsBeforeCloze: List[str] = []
        wordsMidCloze: List[str] = []
        wordsAfterCloze: List[str] = []
        clozePart1: List[str] = []
        clozePart2: List[str] = []
        
        for rawWord in self.rawLine.rawWords:
            if rawWord.multiWordExpressionInfo is not None and \
                rawWord.multiWordExpressionInfo[0].id == multiWordExpressionId:
                if len(wordsMidCloze) == 0:
                    clozePart1.append(rawWord.word)
                else:
                    clozePart2.append(rawWord.word)
            else:
                if len(clozePart1) == 0:
                    wordsBeforeCloze.append(rawWord.word)
                elif len(clozePart2) == 0:
                    wordsMidCloze.append(rawWord.word)
                else:
                    wordsAfterCloze.append(rawWord.word)
        
        self.simpleClozeFlashcard = SimpleClozeFlashcard(
            ' '.join(wordsBeforeCloze),
            ' '.join(wordsMidCloze),
            " ".join(wordsAfterCloze),
            " ".join(clozePart1),
            " ".join(clozePart2),
            self.inUse
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

    def GetPunctuationlessClozeString(self) -> str:
        clozeFirstRawWord: RawWord = self.GetClozeRawWord()
        
        return clozeFirstRawWord.GetUniquePunctuationlessWordString()

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
        self.uniquePunctuationlessWordString: Optional[str] = None

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
    
    def GetUniquePunctuationlessWordString(self) -> str:
        if self.uniquePunctuationlessWordString is not None:
            return self.uniquePunctuationlessWordString

        if self.multiWordExpressionInfo is None:
            self.uniquePunctuationlessWordString = removePunctuation(self.word)
            return self.uniquePunctuationlessWordString

        # If the word is part of a multi-word expression
        multiWordExpression: 'MultiWordExpression' = self.multiWordExpressionInfo[0]
        self.uniquePunctuationlessWordString = multiWordExpression.getUniquePunctuationlessWordString()
        return self.uniquePunctuationlessWordString

class MultiWordExpression:
    # TODO : distinguish between whether a word is in the middle
    # of a multi-word expression because Anki does not support storing them in the same place
    MWECount: int = 0

    def __init__(self) -> None:
        self.id: int = MultiWordExpression.MWECount
        MultiWordExpression.MWECount += 1
        self.rawWords: List[RawWord] = []

        self.punctuationlessWordString: Optional[str] = None
    
    def getUniquePunctuationlessWordString(self) -> str:
        """
        Get the unique punctuationless word string for the multi-word expression.
        Combines the raw words in alphabetical order.
        """
        if self.punctuationlessWordString is not None:
            return self.punctuationlessWordString

        rawWordStrings: List[str] = [rawWord.word for rawWord in self.rawWords]
        self.punctuationlessWordString = ' '.join([removePunctuation(word) for word in rawWordStrings])
        return self.punctuationlessWordString