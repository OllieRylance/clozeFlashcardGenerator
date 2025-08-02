import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import math
import re
import hashlib

from resources import (
    PunctuationWordPosition,
    sentencePart
)

logger = logging.getLogger(__name__)

# def resetForTesting() -> None:
#     Line.calculatedCosDissimilarities.clear()
#     Line.calculatedSentenceLengthScores.clear()
#     Word.uniqueWordIdToWordObjects.clear()
#     SimpleClozeFlashcard.wordToFlashcards.clear()
#     ClozeFlashcard.inUseClozeFlashcards.clear()

class Word:
    # uniqueWordIdToWordObjects: Dict[str, List['Word']] = {}

    def __init__(
        self, wordString: str, 
        multiWordExpression: 'MultiWordExpression'
    ) -> None:
        self.thisWordString: str = wordString
        self.line: Optional['Line'] = None
        self.index: Optional[int] = None
        self.uniqueWordId: Optional[str] = None
        self.firstWordInMultiWordExpression: Optional[bool] = None

        self.multiWordExpression: 'MultiWordExpression' = multiWordExpression
    
    def getUniqueWordId(self) -> str:
        """
        Get a unique identifier for the word (and the rest of its 
        multi-word expression).
        """
        if self.uniqueWordId is not None:
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

    def appendReferenceLine(self, line: 'Line', index: int) -> None:
        """Add a reference to the line and index of this word."""
        self.line = line
        self.index = index
    
    def isFirstWordInMultiWordExpression(self) -> bool:
        """
        Check if this word is the first word in its multi-word expression.
        """
        if self.firstWordInMultiWordExpression is not None:
            return self.firstWordInMultiWordExpression
        
        self.firstWordInMultiWordExpression = (
            self.multiWordExpression.getFirstIndex() == self.index
        )
        return self.firstWordInMultiWordExpression
    
    def getSentenceNewWordProportion(
        self, 
        seenWords: List[str],
        calculatedSentenceProportions: Dict[int, float]
    ) -> float:
        if self.line is None:
            logger.error(
                f"Word '{self.thisWordString}' has no associated line."
            )
            return 0.0

        line = self.line
        lineId: int = line.id
        if lineId in calculatedSentenceProportions:
            return calculatedSentenceProportions[lineId]
        
        totalFirstWords: int = 0
        totalUnseenWords: int = 0

        for word in line.words:
            if word.isFirstWordInMultiWordExpression():
                totalFirstWords += 1
                if word.getUniqueWordId() not in seenWords:
                    totalUnseenWords += 1

        if totalFirstWords == 0:
            logger.error(
                f"Line '{line}' has no first words in multi-word expressions."
            )

            calculatedSentenceProportions[lineId] = 0.0
            return 0.0

        proportion: float = totalUnseenWords / totalFirstWords
        calculatedSentenceProportions[lineId] = proportion
        return proportion

class MultiWordExpression:
    def __init__(self) -> None:
        self.words: List[Word] = []

        self.uniqueWordId: Optional[str] = None
        self.numWordsBeforeSplitInCloze: Optional[int] = None
    
    def __str__(self) -> str:
        return " ".join([word.thisWordString for word in self.words])

    def getUniqueWordId(self) -> str:
        """
        Get the unique punctuationless word string for the multi-word expression.
        Combines the words in alphabetical order.
        """
        if self.uniqueWordId is not None:
            return self.uniqueWordId
        
        self.uniqueWordId = ' '.join(
            sorted([word.thisWordString for word in self.words])
        )
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

class Punctuation:
    def __init__(self, character: str, wordPosition: 'PunctuationWordPosition') -> None:
        self.character: str = character
        self.wordPosition: PunctuationWordPosition = wordPosition

class Line:
    # calculatedCosDissimilarities: Dict[Tuple[int, int], float] = {}
    # calculatedSentenceLengthScores: Dict[int, float] = {}

    def __init__(
        self, words: List['Word'], 
        punctuationDict: Dict[int, List['Punctuation']]
    ) -> None:
        for index, word in enumerate(words):
            word.appendReferenceLine(self, index)
        self.words: List['Word'] = words
        self.punctuationDict: Dict[int, List['Punctuation']] = punctuationDict

        self.asString: Optional[str] = None
        self.id: int = int(hashlib.sha256(str(self).encode()).hexdigest()[:8], 16)
        self.wordVector: Optional[np.ndarray] = None

    def __str__(self) -> str:
        if self.asString is None:
            self.asString = Line.stringifyWordsAndPunctuation(
                self.words, self.punctuationDict
            )

        return self.asString

    def __eq__(self, other: object) -> bool:
        """Check if two Lines have equal ids."""
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

    def getUniqueWordIdVector(self, uniqueWordIdToWordObjects: Dict[str, List['Word']]) -> np.ndarray:
        """
        Generate a word vector for the line.
        """
        if self.wordVector is not None:
            return self.wordVector

        # Initialize the word vector as a dictionary
        # where keys are the punctuationless words and values are their counts
        wordCounts: Dict[str, int] = {
            uniqueWordId: 0 
            for uniqueWordId in uniqueWordIdToWordObjects.keys()
        }

        # Iterate through the words and update the word vector
        for word in self.words:
            uniqueWordId: str = word.getUniqueWordId()
            if uniqueWordId in wordCounts:
                wordCounts[uniqueWordId] += 1

        # Convert the dictionary to a numpy array for easier manipulation
        self.wordVector = np.array(list(wordCounts.values()), dtype=float)

        return self.wordVector

    def getCosDissimilarity(
            self,
            otherLine: 'Line',
            calculatedCosDissimilarities: Dict[Tuple[int, int], float],
            uniqueWordIdToWordObjects: Dict[str, List['Word']]
        ) -> float:
        """
        Calculate the cosine dissimilarity between this line and another line.
        """
        # Check if the cosine dissimilarity has already been calculated
        if (self.id, otherLine.id) in calculatedCosDissimilarities:
            return calculatedCosDissimilarities[(self.id, otherLine.id)]

        vector1: np.ndarray = self.getUniqueWordIdVector(
            uniqueWordIdToWordObjects
        )
        vector2: np.ndarray = otherLine.getUniqueWordIdVector(
            uniqueWordIdToWordObjects
        )

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
        calculatedCosDissimilarities[(
            self.id,
            otherLine.id
        )] = cosineDissimilarity

        return cosineDissimilarity

    def getSentenceLengthScore(self, calculatedSentenceLengthScores: Dict[int, float]) -> float:
        """
        Calculate a score based on the length of the sentence.
        Shorter sentences get a higher score with a reciprocal of exponential curve.
        """
        length = len(self.words)

        if calculatedSentenceLengthScores.get(length) is not None:
            return calculatedSentenceLengthScores[length]

        sentenceLengthScore = 1 / (math.exp((3 * length / 25) ** 2))
        calculatedSentenceLengthScores[length] = sentenceLengthScore
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

class ClozeFlashcard:
    # inUseClozeFlashcards: Dict[str, List['ClozeFlashcard']] = {}

    def __init__(self, line: Line, wordIndex: int, inUse: bool = False) -> None:
        self.line: Line = line
        self.wordIndex: int = wordIndex
        self.inUse: bool = inUse

        self.simpleClozeFlashcard: Optional[SimpleClozeFlashcard] = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ClozeFlashcard):
            return NotImplemented
        return self.simpleClozeFlashcard == other.simpleClozeFlashcard

    def GetSimpleClozeFlashcard(self) -> 'SimpleClozeFlashcard':
        if self.simpleClozeFlashcard is not None:
            return self.simpleClozeFlashcard

        beforeCloze: str = self.GetStringOfSentencePart(
            sentencePart.BEFORE_CLOZE
        )
        midCloze: str = self.GetStringOfSentencePart(
            sentencePart.MID_CLOZE
        )
        afterCloze: str = self.GetStringOfSentencePart(
            sentencePart.AFTER_CLOZE
        )
        clozePart1: str = self.GetStringOfSentencePart(
            sentencePart.CLOZE_PART_1
        )
        clozePart2: str = self.GetStringOfSentencePart(
            sentencePart.CLOZE_PART_2
        )

        self.simpleClozeFlashcard = SimpleClozeFlashcard(
            beforeCloze, midCloze, afterCloze, clozePart1, clozePart2, self.inUse
        )

        return self.simpleClozeFlashcard

    def GetStringOfSentencePart(
        self,
        part: 'sentencePart'
    ) -> str:
        leadingSpace: bool = False
        trailingSpace: bool = False
        getLeadingAndTrailingPunctuation: bool = True
        firstIndex: int = 0
        nextIndex: int = 0
        firstClozeWord: 'Word' = self.GetFirstClozeWord()
        multiWordExpression: Optional['MultiWordExpression'] = (
            firstClozeWord.multiWordExpression
        )
        words: List[Word] = self.line.words
        
        if part == sentencePart.BEFORE_CLOZE:
            trailingSpace = True
            firstIndex = 0
            nextIndex = self.wordIndex
        elif part == sentencePart.CLOZE_PART_1:
            getLeadingAndTrailingPunctuation = False
            firstIndex = self.wordIndex
            nextIndex = (
                self.wordIndex
                + multiWordExpression.getNumWordsBeforeSplitInCloze()
            )
        elif part == sentencePart.MID_CLOZE:
            leadingSpace = True
            trailingSpace = True
            firstIndex = (
                self.wordIndex
                + multiWordExpression.getNumWordsBeforeSplitInCloze()
            )
            nextIndex = (
                self.wordIndex 
                + multiWordExpression.getNumWordsBeforeSplitInCloze()
                + multiWordExpression.getNumWordsInSplitOfCloze()
            )
        elif part == sentencePart.CLOZE_PART_2:
            getLeadingAndTrailingPunctuation = False
            firstIndex = (
                self.wordIndex 
                + multiWordExpression.getNumWordsBeforeSplitInCloze()
                + multiWordExpression.getNumWordsInSplitOfCloze()
            )
            nextIndex = (
                self.wordIndex 
                + multiWordExpression.getNumWordsBeforeSplitInCloze()
                + multiWordExpression.getNumWordsInSplitOfCloze()
                + multiWordExpression.getNumWordsAfterSplitInCloze()
            )
        elif part == sentencePart.AFTER_CLOZE:
            leadingSpace = True
            firstIndex = (
                self.wordIndex 
                + multiWordExpression.getNumWordsBeforeSplitInCloze()
                + multiWordExpression.getNumWordsInSplitOfCloze()
                + multiWordExpression.getNumWordsAfterSplitInCloze()
            )
            nextIndex = len(words)

        return self.GenerateSentencePart(
            leadingSpace,
            trailingSpace,
            getLeadingAndTrailingPunctuation,
            firstIndex,
            nextIndex,
            words,
            self.line.punctuationDict
        )

    @staticmethod
    def GenerateSentencePart(
        leadingSpace: bool,
        trailingSpace: bool,
        getLeadingAndTrailingPunctuation: bool,
        firstIndex: int,
        nextIndex: int,
        words: List['Word'],
        punctuationDict: Dict[int, List['Punctuation']]
    ) -> str:
        # If the first index is the same as the next index, return an empty string
        previousIndex: int = firstIndex - 1
        
        # If this part has no words
        if firstIndex == nextIndex:
            if not getLeadingAndTrailingPunctuation:
                return ""
            # Before cloze
            elif not leadingSpace and trailingSpace:
                if nextIndex in punctuationDict:
                    punctuationsBeforeTheFirstWord: str = ""
                    for punctuation in punctuationDict[nextIndex]:
                        if punctuation.wordPosition == PunctuationWordPosition.ALONE:
                            punctuationsBeforeTheFirstWord += punctuation.character + " "
                        elif punctuation.wordPosition == PunctuationWordPosition.BEFORE:
                            punctuationsBeforeTheFirstWord += punctuation.character
                    return punctuationsBeforeTheFirstWord
            # Mid cloze
            elif leadingSpace and trailingSpace:
                return ""
            # After cloze
            elif leadingSpace and not trailingSpace:
                punctuationAfterTheLastWord: str = ""
                if previousIndex in punctuationDict:
                    for punctuation in punctuationDict[previousIndex]:
                        if punctuation.wordPosition == PunctuationWordPosition.AFTER:
                            punctuationAfterTheLastWord += punctuation.character
                if firstIndex in punctuationDict:
                    for punctuation in punctuationDict[firstIndex]:
                        if punctuation.wordPosition == PunctuationWordPosition.ALONE:
                            punctuationAfterTheLastWord += " " + punctuation.character
                return punctuationAfterTheLastWord

        result: str = ""

        # Deal with punctuation before the first word if it is not clozed
        previousPunctuationFound: bool = False
        if getLeadingAndTrailingPunctuation:
            if previousIndex in punctuationDict:
                for punctuation in punctuationDict[previousIndex]:
                    if punctuation.wordPosition == PunctuationWordPosition.AFTER:
                        result += punctuation.character
                        previousPunctuationFound = True

        if previousPunctuationFound or leadingSpace:
            result += " "
        
        # Add the words and punctuation in the range from firstIndex to nextIndex
        lastIndex: int = nextIndex - 1
        for i in range(firstIndex, nextIndex):
            addAlonePunctuation: bool = (
                getLeadingAndTrailingPunctuation 
                or i != firstIndex
            )
            addBeforePunctuation: bool = addAlonePunctuation
            addAfterPunctuation: bool = (
                getLeadingAndTrailingPunctuation
                or i != lastIndex
            )

            wordString: str = words[i].thisWordString
            if i in punctuationDict:
                for punctuation in punctuationDict[i]:
                    if (punctuation.wordPosition == PunctuationWordPosition.ALONE 
                        and addAlonePunctuation):
                        result += punctuation.character + " "
                    elif (punctuation.wordPosition == PunctuationWordPosition.BEFORE
                          and addBeforePunctuation):
                        wordString = punctuation.character + wordString
                    elif (punctuation.wordPosition == PunctuationWordPosition.AFTER
                          and addAfterPunctuation):
                        wordString += punctuation.character
            result += wordString
            if i < lastIndex:
                result += " "

        # Add trailing punctuation
        nextWordBeforePunctuation: str = ""
        if getLeadingAndTrailingPunctuation and nextIndex in punctuationDict:
            for punctuation in punctuationDict[nextIndex]:
                if punctuation.wordPosition == PunctuationWordPosition.ALONE:
                    result += " " + punctuation.character
                elif punctuation.wordPosition == PunctuationWordPosition.BEFORE:
                    nextWordBeforePunctuation += punctuation.character

        if trailingSpace:
            result += " " + nextWordBeforePunctuation

        return result

    def getWords(self) -> List['Word']:
        """
        Get the words in the line.
        """
        return self.line.words

    def GetFirstClozeWord(self) -> 'Word':
        """Get the word that is clozed."""
        return self.line.words[self.wordIndex]

class SimpleClozeFlashcard:
    # wordToFlashcards: Dict[str, List['SimpleClozeFlashcard']] = {}

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
        # TODO: polymorphic json so that flashcards without mid or part 2 dont need extra lines
        return {
            'beforeCloze': self.beforeCloze,
            'clozeWordPart1': self.clozePart1,
            'afterCloze': self.afterCloze,
            'midCloze': self.midCloze,
            'clozeWordPart2': self.clozePart2,
            'inUse': str(self.inUse)
        }
    
    @staticmethod
    def fromJsonableDict(
        jsonableDict: Dict[str, str]
    ) -> 'SimpleClozeFlashcard':
        """
        Create a SimpleClozeFlashcard from a JSON-serializable dictionary.
        """
        return SimpleClozeFlashcard(
            beforeCloze=jsonableDict['beforeCloze'],
            midCloze=jsonableDict['midCloze'],
            afterCloze=jsonableDict['afterCloze'],
            clozePart1=jsonableDict['clozeWordPart1'],
            clozePart2=jsonableDict['clozeWordPart2'],
            inUse=jsonableDict['inUse'] == 'True'
        )

    @staticmethod
    def wordsInString(string: str) -> int:
        words: List[str] = string.split()
        # Ignore words that are just punctuation
        return sum(1 for word in words if not re.match(r'^[^\w\s]+$', word))
