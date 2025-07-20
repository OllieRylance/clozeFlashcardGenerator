import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import math
from enum import Enum
import re

logger = logging.getLogger(__name__)

# Line Class
class Line:
    calculatedCosDissimilarities: Dict[Tuple[int, int], float] = {}
    calculatedSentenceLengthScores: Dict[int, float] = {}

    def __init__(
        self, words: List['Word'], 
        punctuationDict: Dict[int, List['Punctuation']]
    ) -> None:
        for index, word in enumerate(words):
            word.appendReferenceLine(self, index)
        self.words: List['Word'] = words
        self.punctuationDict: Dict[int, List['Punctuation']] = punctuationDict

        self.asString: Optional[str] = None
        self.id: int = hash(str(self))
        # self.score: Optional[float] = None
        self.wordVector: Optional[np.ndarray] = None

    def __str__(self) -> str:
        if self.asString is None:
            self.asString = Line.stringifyWordsAndPunctuation(
                self.words, self.punctuationDict
            )

        return self.asString

    def __eq__(self, other: object) -> bool:
        """Check if two Lines have equal hashes."""
        if not isinstance(other, Line):
            return NotImplemented
        return self.id == other.id

    def GetLastIndex(self) -> int:
        """
        Get the last index of the line.
        This is used to determine if the line has any words after a certain index.
        """
        highestWordIndex: int = len(self.words) - 1
        highestPunctuationIndex: int = max(self.punctuationDict.keys())
        return max(highestWordIndex, highestPunctuationIndex)  

    # def inListOfOtherRawLines(self, otherRawLines: List['RawLine']) -> bool:
    #     """
    #     Check if this raw line is in the list of other raw lines.
    #     """
    #     return any(self == otherRawLine for otherRawLine in otherRawLines)

    # def getScore(
    #     self,
    #     punctuationlessWords: Dict[str, 'PunctuationlessWord'],
    #     maxWordFrequency: int,
    #     benefitShorterSentences: bool
    # ) -> float:
    #     """
    #     Score a sentence based on how useful it is for clozing.
    #     """
    #     if self.score is not None:
    #         return self.score

    #     score: float = 0.0

    #     # Calculate the score based on the rarity of the words in the sentence
    #     for rawWord in self.rawWords:
    #         wordString: str = rawWord.punctuationlessWordString
    #         rarity: float = getWordRarityScore(wordString, punctuationlessWords, maxWordFrequency)
    #         score += rarity

    #     # Penalize long sentences if shorter sentences are preferred
    #     if benefitShorterSentences:
    #         lengthPenalty: float = len(self.rawWords) ** 0.8
    #         score = score / lengthPenalty

    #     self.score = score
    #     return score

    def getUniqueWordIdVector(self) -> np.ndarray:
        """
        Generate a word vector for the raw line.
        """
        if self.wordVector is not None:
            return self.wordVector

        # Initialize the word vector as a dictionary
        # where keys are the punctuationless words and values are their counts
        wordCounts: Dict[str, int] = {
            uniqueWordId: 0 
            for uniqueWordId in Word.uniqueWordIdToWordObjects.keys()
        }

        # Iterate through the words and update the word vector
        for word in self.words:
            uniqueWordId: str = word.getUniqueWordId()
            if uniqueWordId in wordCounts:
                wordCounts[uniqueWordId] += 1

        # Convert the dictionary to a numpy array for easier manipulation
        self.wordVector = np.array(list(wordCounts.values()), dtype=float)

        return self.wordVector

    def getCosDissimilarity(self, otherLine: 'Line') -> float:
        """
        Calculate the cosine dissimilarity between this raw line and another raw line.
        """
        # Check if the cosine dissimilarity has already been calculated
        if (self.id, otherLine.id) in self.calculatedCosDissimilarities:
            return self.calculatedCosDissimilarities[(self.id, otherLine.id)]

        vector1: np.ndarray = self.getUniqueWordIdVector()
        vector2: np.ndarray = otherLine.getUniqueWordIdVector()

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
            self.id,
            otherLine.id
        )] = cosineDissimilarity

        return cosineDissimilarity

    def getSentenceLengthScore(self) -> float:
        """
        Calculate a score based on the length of the sentence.
        Shorter sentences get a higher score with a reciprocal of exponential curve.
        """
        length = len(self.words)

        if self.calculatedSentenceLengthScores.get(length) is not None:
            return self.calculatedSentenceLengthScores[length]

        sentenceLengthScore = 1 / (math.exp((4 * length / 25) ** 4))
        self.calculatedSentenceLengthScores[length] = sentenceLengthScore
        return sentenceLengthScore
    
    @staticmethod
    def stringifyWordsAndPunctuation(
        words: List['Word'],
        punctuationDict: Dict[int, List['Punctuation']]
    ) -> str:
        """
        Convert a list of words and punctuation into a single string.
        """
        result: str = ""
        alonePunctuation: List['Punctuation'] = []
        for index, word in enumerate(words):
            if index > 0:
                result += " "
            relevantPunctuation: Optional[List[Punctuation]] = (
                punctuationDict.get(index)
            )
            wordString: str = word.thisWordString
            if relevantPunctuation:
                alonePunctuation = [
                    p for p in relevantPunctuation 
                    if p.wordPosition == PunctuationWordPosition.ALONE
                ]
                if alonePunctuation:
                    result += f"{alonePunctuation[0].character} "
                beforePunctuation: List[Punctuation] = [
                    p for p in relevantPunctuation 
                    if p.wordPosition == PunctuationWordPosition.BEFORE
                ]
                if beforePunctuation:
                    wordString = beforePunctuation[0].character + wordString
                afterPunctuation: List[Punctuation] = [
                    p for p in relevantPunctuation 
                    if p.wordPosition == PunctuationWordPosition.AFTER
                ]
                if afterPunctuation:
                    wordString += afterPunctuation[0].character
            result += wordString
        
        # Add any punctuation that is alone at the end of the sentence
        indexAfterWords = len(words)
        if indexAfterWords in punctuationDict:
            alonePunctuation = [
                p for p in punctuationDict[indexAfterWords] 
                if p.wordPosition == PunctuationWordPosition.ALONE
            ]
            if alonePunctuation:
                result += f"{alonePunctuation[0].character} "
            
        return result

# Simple Cloze Flashcard Class
# Contains the before and after cloze words and the cloze word
class SimpleClozeFlashcard:
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
    
    wordToFlashcards: Dict[str, List['SimpleClozeFlashcard']] = {}

    def __init__(
        self,
        beforeCloze: str,
        midCloze: str,
        afterCloze: str,
        clozePart1: str,
        clozePart2: str,
        inUse: bool = False
    ) -> None:
        self.beforeCloze: str = beforeCloze
        self.midCloze: str = midCloze
        self.afterCloze: str = afterCloze
        self.clozePart1: str = clozePart1
        self.clozePart2: str = clozePart2
        self.inUse: bool = inUse

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SimpleClozeFlashcard):
            return NotImplemented
        return (
            self.beforeCloze == other.beforeCloze and
            self.midCloze == other.midCloze and
            self.afterCloze == other.afterCloze and
            self.clozePart1 == other.clozePart1 and
            self.clozePart2 == other.clozePart2
        )

    def toJsonableDict(self) -> Dict[str, str]:
        """Convert SimpleClozeFlashcard to dictionary for JSON serialization."""
        return {
            'beforeCloze': self.beforeCloze,
            'midCloze': self.midCloze,
            'afterCloze': self.afterCloze,
            'clozeWordPart1': self.clozePart1,
            'clozeWordPart2': self.clozePart2,
            'inUse': str(self.inUse)
        }
    
    @staticmethod
    def wordsInString(string: str) -> int:
        words: List[str] = string.split()
        # Ignore words that are just punctuation
        return sum(1 for word in words if not re.match(r'^[^\w\s]+$', word))

# Cloze Flashcard Class
# Contains a raw line and the index of the word to be clozed
class ClozeFlashcard:
    inUseClozeFlashcards: Dict[str, List['ClozeFlashcard']] = {}

    def __init__(self, line: Line, wordIndex: int, inUse: bool = False) -> None:
        self.line: Line = line
        self.wordIndex: int = wordIndex
        self.inUse: bool = inUse

        self.simpleClozeFlashcard: Optional[SimpleClozeFlashcard] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ClozeFlashcard):
            return NotImplemented
        return self.simpleClozeFlashcard == other.simpleClozeFlashcard

    # def __str__(self) -> str:
    #     wordsBeforeCloze: str = self.GetWordsBeforeCloze()
    #     clozeWord: str = self.rawLine.rawWords[self.wordIndex].word
    #     wordsAfterCloze: str = self.GetWordsAfterCloze()
    #     return f"{wordsBeforeCloze} *{clozeWord}* {wordsAfterCloze}"

    def GetSimpleClozeFlashcard(self) -> SimpleClozeFlashcard:
        if self.simpleClozeFlashcard is not None:
            return self.simpleClozeFlashcard

        currentStartWordIndex: int = 0
        currentNextWordIndex: int = self.wordIndex
        beforeCloze: str = self.GetStringOfWordsAndPunctuation(
            currentStartWordIndex,
            currentNextWordIndex,
            # trailingSpace=True
        )
        currentStartWordIndex = currentNextWordIndex

        # If the cloze word is not part of a multi-word expression,
        clozePart1: str = ""
        midCloze: str = ""
        clozePart2: str = ""
        afterCloze: str = ""

        multiWordExpression: Optional[MultiWordExpression] = (
            self.GetFirstClozeWord().multiWordExpression
        )
        if multiWordExpression is None:
            currentNextWordIndex += 1
            clozePart1 = self.GetStringOfWordsAndPunctuation(
                currentStartWordIndex,
                currentNextWordIndex,
                isCloze=True
            )
            currentStartWordIndex = currentNextWordIndex
            currentNextWordIndex = len(self.getWords())
            afterCloze = (
                self.GetStringOfWordsAndPunctuation(
                    currentStartWordIndex,
                    currentNextWordIndex,
                    # leadingSpace=currentStartWordIndex != currentNextWordIndex
                ) 
                if (currentStartWordIndex != currentNextWordIndex 
                    or currentNextWordIndex in self.line.punctuationDict) 
                else afterCloze
            )
        else:
            currentNextWordIndex += multiWordExpression.getNumWordsBeforeSplitInCloze()
            clozePart1 = self.GetStringOfWordsAndPunctuation(
                currentStartWordIndex,
                currentNextWordIndex,
                isCloze=True
            ) if currentStartWordIndex != currentNextWordIndex else clozePart1
            currentStartWordIndex = currentNextWordIndex
            currentNextWordIndex += multiWordExpression.getNumWordsInSplitOfCloze()
            midCloze = (
                self.GetStringOfWordsAndPunctuation(
                    currentStartWordIndex,
                    currentNextWordIndex,
                    # leadingSpace=True,
                    # trailingSpace=True
                ) if currentStartWordIndex != currentNextWordIndex else midCloze
            )
            currentStartWordIndex = currentNextWordIndex
            currentNextWordIndex += multiWordExpression.getNumWordsAfterSplitInCloze()
            clozePart2 = (
                self.GetStringOfWordsAndPunctuation(
                    currentStartWordIndex,
                    currentNextWordIndex,
                    isCloze=True
                ) if currentStartWordIndex != currentNextWordIndex else clozePart2
            )
            currentStartWordIndex = currentNextWordIndex
            currentNextWordIndex = len(self.getWords())
            afterCloze = (
                self.GetStringOfWordsAndPunctuation(
                    currentStartWordIndex,
                    currentNextWordIndex,
                    # leadingSpace=currentStartWordIndex != currentNextWordIndex
                ) 
                if (currentStartWordIndex != currentNextWordIndex 
                    or currentNextWordIndex in self.line.punctuationDict) 
                else afterCloze
            )

        self.simpleClozeFlashcard = SimpleClozeFlashcard(
            beforeCloze, midCloze, afterCloze, clozePart1, clozePart2, self.inUse
        )

        return self.simpleClozeFlashcard

        # lastIndex: int = self.line.GetLastIndex()

        # multiWordExpressionId: int = word.multiWordExpressionInfo[0].id
        # wordsBeforeCloze: List[Word] = []
        # punctuationBeforeCloze: List[Punctuation] = []
        # wordsMidCloze: List[Word] = []
        # punctuationMidCloze: List[Punctuation] = []
        # wordsAfterCloze: List[Word] = []
        # punctuationAfterCloze: List[Punctuation] = []
        # clozeWordsPart1: List[Word] = []
        # clozePunctuationPart1: List[Punctuation] = []
        # clozeWordsPart2: List[Word] = []
        # clozePunctuationPart2: List[Punctuation] = []

        # for rawWord in self.rawLine.rawWords:
        #     if rawWord.multiWordExpressionInfo is not None and \
        #         rawWord.multiWordExpressionInfo[0].id == multiWordExpressionId:
        #         if len(wordsMidCloze) == 0:
        #             clozeWordsPart1.append(rawWord.word)
        #         else:
        #             clozeWordsPart2.append(rawWord.word)
        #     else:
        #         if len(clozeWordsPart1) == 0:
        #             wordsBeforeCloze.append(rawWord.word)
        #         elif len(clozeWordsPart2) == 0:
        #             wordsMidCloze.append(rawWord.word)
        #         else:
        #             wordsAfterCloze.append(rawWord.word)
        
        # self.simpleClozeFlashcard = SimpleClozeFlashcard(
        #     ' '.join(wordsBeforeCloze),
        #     ' '.join(wordsMidCloze),
        #     " ".join(wordsAfterCloze),
        #     " ".join(clozePart1),
        #     " ".join(clozePart2),
        #     self.inUse
        # )
        # return self.simpleClozeFlashcard

    def hasMultiWordExpression(self) -> bool:
        """
        Check if the cloze word is part of a multi-word expression.
        """
        if self.GetFirstClozeWord().multiWordExpression is not None:
            return True
        return False

    def GetStringOfWordsAndPunctuation(
        self,
        firstIndex: int,
        nextIndex: int,
        isCloze: bool = False,
        leadingSpace: bool = False,
        trailingSpace: bool = False
    ) -> str:
        words: List[Word] = self.line.words
        punctuationDict: Dict[int, List['Punctuation']] = self.line.punctuationDict
        result = ""
        if leadingSpace:
            result += " "
        for i in range(firstIndex, nextIndex):
            # Add alone punctuation before the word is not clozed
            wordString: str = words[i].thisWordString
            if i in punctuationDict:
                for punctuation in punctuationDict[i]:
                    if (punctuation.wordPosition == PunctuationWordPosition.ALONE 
                        and not isCloze):
                        result += punctuation.character + " "
                    elif punctuation.wordPosition == PunctuationWordPosition.BEFORE:
                        wordString = punctuation.character + wordString
                    elif punctuation.wordPosition == PunctuationWordPosition.AFTER:
                        wordString += punctuation.character
            result += wordString
            if i < nextIndex - 1:
                result += " "

        # Add alone punctuation after the word if it is not clozed
        if not isCloze and nextIndex in punctuationDict:
            for punctuation in punctuationDict[nextIndex]:
                if punctuation.wordPosition == PunctuationWordPosition.ALONE:
                    result += " " + punctuation.character

        if trailingSpace:
            result += " "

        return result

    def getWords(self) -> List['Word']:
        """
        Get the words in the line.
        """
        return self.line.words

    # def GetWordsBeforeCloze(self) -> str:
    #     """Get the words before the cloze word."""
    #     return ' '.join([rawWord.word for rawWord in self.rawLine.rawWords[:self.wordIndex]])

    def GetFirstClozeWord(self) -> 'Word':
        """Get the word that is clozed."""
        return self.line.words[self.wordIndex]

    # def GetWordsAfterCloze(self) -> str:
    #     """Get the words after the cloze word."""
    #     if self.wordIndex + 1 >= len(self.rawLine.rawWords):
    #         return ''

    #     return ' '.join([rawWord.word for rawWord in self.rawLine.rawWords[self.wordIndex + 1:]])

    # def GetPunctuationlessClozeString(self) -> str:
    #     clozeFirstRawWord: RawWord = self.GetClozeWord()
        
    #     return clozeFirstRawWord.GetUniquePunctuationlessWordString()

# Word Class
class Word:
    uniqueWordIdToWordObjects: Dict[str, List['Word']] = {}

    def __init__(
        self, wordString: str, 
        multiWordExpression: Optional['MultiWordExpression'] = None
    ) -> None:
        self.thisWordString: str = wordString
        self.line: Optional['Line'] = None
        self.index: Optional[int] = None
        self.uniqueWordId: Optional[str] = None

        self.multiWordExpression: Optional['MultiWordExpression'] = multiWordExpression

    # def getSentenceScore(
    #     self,
    #     punctuationlessWords: Dict[str, PunctuationlessWord],
    #     maxWordFrequency: int,
    #     benefitShorterSentences: bool
    # ) -> float:
    #     return self.rawLine.getScore(
    #         punctuationlessWords, maxWordFrequency, benefitShorterSentences
    #     )
    
    def getUniqueWordId(self) -> str:
        """
        Get a unique identifier for the word (and the rest of its 
        multi-word expression).
        """
        if self.uniqueWordId is not None:
            return self.uniqueWordId

        if self.multiWordExpression is None:
            self.uniqueWordId = self.thisWordString
            return self.uniqueWordId
        
        # If the word is part of a multi-word expression
        multiWordExpression: 'MultiWordExpression' = self.multiWordExpression
        self.uniqueWordId = multiWordExpression.getUniqueWordId()
        return self.uniqueWordId
    
    def thisInstanceInClozeFlashcards(
        self, clozeFlashcards: List['ClozeFlashcard']
    ) -> bool:
        """
        Check if this instance of the word is in the list of cloze flashcards.
        """
        for clozeFlashcard in clozeFlashcards:
            if (clozeFlashcard.line == self.line 
                and clozeFlashcard.wordIndex == self.index):
                return True
        return False

    @staticmethod
    def addClozeIdToString(
        wordString: str, multiWordExpressionIndex: int
    ) -> str:
        # Using regex, separate any punctuation at the end of the word
        # Punctuation at the end of a word can be "?"
        match = re.match(r'(.*?)([^\w\s]*)$', wordString)
        if match:
            return f"{match.group(1)}_{multiWordExpressionIndex}{match.group(2)}"
        return f"{wordString}_{multiWordExpressionIndex}"

    # def GetUniquePunctuationlessWordString(self) -> str:
    #     if self.uniquePunctuationlessWordString is not None:
    #         return self.uniquePunctuationlessWordString

    #     if self.multiWordExpressionInfo is None:
    #         self.uniquePunctuationlessWordString = removePunctuation(self.word)
    #         return self.uniquePunctuationlessWordString

    #     # If the word is part of a multi-word expression
    #     multiWordExpression: 'MultiWordExpression' = self.multiWordExpressionInfo[0]
    #     self.uniquePunctuationlessWordString = multiWordExpression.getUniquePunctuationlessWordString()
    #     return self.uniquePunctuationlessWordString

    def appendReferenceLine(self, line: Line, index: int) -> None:
        """Add a reference to the line and index of this word."""
        self.line = line
        self.index = index
        # if self.getUniqueWordId() not in Word.uniqueWordIdToWordObjects:
        #     Word.uniqueWordIdToWordObjects[self.getUniqueWordId()] = []
        # Word.uniqueWordIdToWordObjects[self.getUniqueWordId()].append(self)

class PunctuationWordPosition(Enum):
    BEFORE = 1
    AFTER = 2
    ALONE = 3

class Punctuation:
    def __init__(self, character: str, wordPosition: PunctuationWordPosition) -> None:
        self.character: str = character
        self.wordPosition: PunctuationWordPosition = wordPosition

class MultiWordExpression:
    multiWordExpressionCount: int = 0

    def __init__(self) -> None:
        self.id: int = MultiWordExpression.multiWordExpressionCount
        MultiWordExpression.multiWordExpressionCount += 1
        self.words: List[Word] = []

        self.uniqueWordId: Optional[str] = None
        self.numWordsBeforeSplitInCloze: Optional[int] = None
    
    def __str__(self) -> str:
        return " ".join([word.thisWordString for word in self.words])

    def getUniqueWordId(self) -> str:
        """
        Get the unique punctuationless word string for the multi-word expression.
        Combines the raw words in alphabetical order.
        """
        if self.uniqueWordId is not None:
            return self.uniqueWordId
        
        self.uniqueWordId = ' '.join([word.thisWordString for word in self.words])
        return self.uniqueWordId

    def getNumWordsBeforeSplitInCloze(self) -> int:
        if self.numWordsBeforeSplitInCloze is not None:
            return self.numWordsBeforeSplitInCloze
        
        currentIndex: int = self.getFirstIndex()
        currentIndex -= 1
        for wordNumber, word in enumerate(self.words):
            if word.index is None:
                self.handleMissingIndexError(word)
                continue
            if word.index != currentIndex + 1:
                return wordNumber
            currentIndex = word.index
        return len(self.words)

    def getNumWordsInSplitOfCloze(self) -> int:
        firstWordIndex: int = self.getFirstIndex()
        lastWordIndex: int = self.getLastIndex()
        return (lastWordIndex - firstWordIndex + 1) - len(self.words)
    
    def getNumWordsAfterSplitInCloze(self) -> int:
        return len(self.words) - self.getNumWordsBeforeSplitInCloze()
    
    def getFirstIndex(self) -> int:
        firstWordIndex: Optional[int] = self.words[0].index
        if firstWordIndex is None:
            self.handleMissingIndexError(self.words[0])
            return -1
        return firstWordIndex
    
    def getLastIndex(self) -> int:
        lastWordIndex: Optional[int] = self.words[-1].index
        if lastWordIndex is None:
            self.handleMissingIndexError(self.words[-1])
            return -1
        return lastWordIndex

    def handleMissingIndexError(self, word: Word) -> None:
        """
        Handle the case where a word in the multi-word expression has no index.
        """
        logger.error(
            f"Word '{word.thisWordString}' in multi-word expression "
            f"'{self.getUniqueWordId()}' has no index."
        )
        exit(1) 

    # example sentence a b word c d more words
    # 0       1        2 3 4    5 6 7    8