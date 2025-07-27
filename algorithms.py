import logging
from typing import Dict, List, Optional, Tuple
from itertools import combinations

from configUtils import getBenefitShorterSentences, getNumFlashcardsPerWord
from models import Line, ClozeFlashcard, SimpleClozeFlashcard, Word
from globalUtils import (
    getUniqueWordIdToWordObjects,
    getInUseClozeFlashcards,
    createInitialClozeFlashcards
)

logger = logging.getLogger(__name__)

def preAlgorithmChecks(
    uniqueWordId: str,
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]],
    numFlashcardsPerWord: int,
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]],
    unusedWords: List[Word]
) -> Tuple[Dict[str, List[SimpleClozeFlashcard]], bool]:
    # If the word already has equal or more cloze flashcards than numFlashcardsPerWord, skip it
    if (
        uniqueWordId in wordToSimpleClozeFlashcards
        and len(wordToSimpleClozeFlashcards[uniqueWordId]) >= numFlashcardsPerWord
    ):
        return wordToSimpleClozeFlashcards, True

    inUseClozeFlashcardsForWord: List[ClozeFlashcard] = (
        inUseClozeFlashcards.get(uniqueWordId, [])
    )

    # If the number of reference words plus the number of in use cloze flashcards
    # is less than or equal to n, create cloze flashcards for all the words
    if len(unusedWords) + len(inUseClozeFlashcardsForWord) <= numFlashcardsPerWord:
        for word in unusedWords:
            currentUniqueWordId: str = word.getUniqueWordId()

            if word.line is None or word.index is None:
                logger.error(
                    f"Word '{currentUniqueWordId}' has no line or word index, "
                    f"cannot create cloze flashcard."
                )
                continue

            simpleClozeFlashcard: SimpleClozeFlashcard = ClozeFlashcard(
                word.line, word.index
            ).GetSimpleClozeFlashcard()

            if (currentUniqueWordId in inUseClozeFlashcards and
                simpleClozeFlashcard in inUseClozeFlashcardsForWord):
                # If the cloze flashcard is already in use, skip it
                continue

            if currentUniqueWordId not in wordToSimpleClozeFlashcards:
                wordToSimpleClozeFlashcards[currentUniqueWordId] = []
            wordToSimpleClozeFlashcards[currentUniqueWordId].append(
                simpleClozeFlashcard
            )

        return wordToSimpleClozeFlashcards, True
    
    return wordToSimpleClozeFlashcards, False

def mostDifferentAlgorithm(
    configFilePath: str
) -> Dict[str, List[SimpleClozeFlashcard]]:
    # For each unique word, create cloze flashcards for the it's raw lines
    # with the top n most different sentences
    # If there are already cloze flashcards in use for the word, 
    # use those as the start of the list
    
    uniqueWordIdToWordObjects: Dict[str, List[Word]] = (
        getUniqueWordIdToWordObjects(configFilePath)
    )
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]] = (
        getInUseClozeFlashcards(configFilePath)
    )
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = (
        createInitialClozeFlashcards(inUseClozeFlashcards)
    )
    numFlashcardsPerWord: int = getNumFlashcardsPerWord(configFilePath)

    calculatedCosDissimilarities: Dict[Tuple[int, int], float] = {}
    calculatedSentenceLengthScores: Dict[int, float] = {}    

    for uniqueWordId in uniqueWordIdToWordObjects.keys():
        # TODO : remove all mention of "raw"
        # Create a list of the raw words that are not already in use
        unusedWords: List[Word] = []

        words: List[Word] = uniqueWordIdToWordObjects[uniqueWordId]
        inUseClozeFlashcardsForWord: List[ClozeFlashcard] = (
            inUseClozeFlashcards.get(uniqueWordId, [])
        )
        for word in words:
            if not word.thisInstanceInClozeFlashcards(inUseClozeFlashcardsForWord):
                unusedWords.append(word)

        wordToSimpleClozeFlashcards, toContinue = (
            preAlgorithmChecks(
                uniqueWordId,
                wordToSimpleClozeFlashcards,
                numFlashcardsPerWord,
                inUseClozeFlashcards,
                unusedWords
            )
        )
        if toContinue:
            continue

        # Create a dictionary that maps all of the relevant raw lines IDs to their objects
        lineIdToWord: Dict[int, Word] = {
            word.line.id: word for word in unusedWords if word.line is not None
        }

        # Create a list of all the combinations of n raw lines
        lineIds: List[int] = list(lineIdToWord.keys())

        # Add the in-use cloze flashcards to the lineIdToWord
        for clozeFlashcard in inUseClozeFlashcardsForWord:
            lineId: int = clozeFlashcard.line.id
            clozeWord: Word = clozeFlashcard.GetFirstClozeWord()
            lineIdToWord[lineId] = clozeWord

        inUseIds: List[int] = [
            clozeFlashcard.line.id for clozeFlashcard in inUseClozeFlashcardsForWord
        ]

        # Subtract the number of cloze flashcards already in use for the word from n
        newSentenceNum = numFlashcardsPerWord - len(inUseClozeFlashcardsForWord)

        # Combination means combination of sentences, not words
        newCombinations: List[Tuple[int, ...]] = generateNewCombinations(
            lineIds, inUseIds, newSentenceNum
        )

        bestCombination: Optional[Tuple[int, ...]] = findMostDifferentCombination(
            configFilePath,
            newCombinations,
            lineIdToWord,
            calculatedCosDissimilarities,
            uniqueWordIdToWordObjects,
            calculatedSentenceLengthScores
        )

        if bestCombination is None:
            logger.error(f"No valid combination found for word '{uniqueWordId}'.")
            continue

        bestCombinationWithoutInUse: Tuple[int, ...] = removeInUseIds(
            bestCombination, inUseIds
        )

        for lineId in bestCombinationWithoutInUse:
            if lineId not in lineIdToWord:
                logger.error(
                    f"Line ID {lineId} not found in lineIdToWord mapping "
                    f"for word '{uniqueWordId}'."
                )
                continue

            line: Optional[Line] = lineIdToWord[lineId].line
            wordIndex: Optional[int] = lineIdToWord[lineId].index
            if line is None or wordIndex is None:
                logger.error(
                    f"Word '{uniqueWordId}' has no line or word index, "
                    f"cannot create cloze flashcard."
                )
                continue
            newSimpleClozeFlashcard: SimpleClozeFlashcard = ClozeFlashcard(
                line, wordIndex
            ).GetSimpleClozeFlashcard()
            if uniqueWordId not in wordToSimpleClozeFlashcards:
                wordToSimpleClozeFlashcards[uniqueWordId] = []
            wordToSimpleClozeFlashcards[uniqueWordId].append(
                newSimpleClozeFlashcard
            )
    
    return wordToSimpleClozeFlashcards

def generateNewCombinations(
    lineIds: List[int],
    inUseIds: List[int],
    n: int
) -> List[Tuple[int, ...]]:
    """
    Generate new combinations of raw line IDs that include the in-use cloze flashcards.
    """
    newCombinations: List[Tuple[int, ...]] = []

    # Generate all combinations of n raw lines
    for combination in combinations(lineIds, n):
        # Create a new combination that includes the in-use cloze flashcards
        newCombination: Tuple[int, ...] = tuple(inUseIds) + combination
        newCombinations.append(newCombination)

    return newCombinations

def findMostDifferentCombination(
    configFilePath: str,
    combinationsOfRawLines: List[Tuple[int, ...]],
    lineIdToWord: Dict[int, Word],
    calculatedCosDissimilarities: Dict[Tuple[int, int], float],
    uniqueWordIdToWordObjects: Dict[str, List[Word]],
    calculatedSentenceLengthScores: Dict[int, float]
) -> Optional[Tuple[int, ...]]:
    currentHighestCosDissimilarity: float = 0
    currentBestCombination: Optional[Tuple[int, ...]] = None

    benefitShorterSentences: bool = getBenefitShorterSentences(configFilePath)

    # For each combination of raw lines work out the sum of the normalised 
    # dot products of their word vectors and find the combination with the 
    # highest cosine dissimilarity
    # TODO : add progress bar
    for combination in combinationsOfRawLines:
        sumOfCosDissimilarities: float = 0
        for i in range(len(combination)):
            for j in range(i + 1, len(combination)):
                line1: Optional[Line] = lineIdToWord[combination[i]].line
                line2: Optional[Line] = lineIdToWord[combination[j]].line
                if line1 is None or line2 is None:
                    logger.error(
                        f"One of the lines for combination {combination} is None."
                    )
                    continue
                cosDissimilarity: float = line1.getCosDissimilarity(
                    line2,
                    calculatedCosDissimilarities,
                    uniqueWordIdToWordObjects
                )

                if benefitShorterSentences:
                    cosDissimilarity *= (
                        line1.getSentenceLengthScore(
                            calculatedSentenceLengthScores
                        ) *
                        line2.getSentenceLengthScore(
                            calculatedSentenceLengthScores
                        )
                    )

                sumOfCosDissimilarities += cosDissimilarity

        if sumOfCosDissimilarities > currentHighestCosDissimilarity:
            currentHighestCosDissimilarity = sumOfCosDissimilarities
            currentBestCombination = combination

    return currentBestCombination

def removeInUseIds(
    combination: Tuple[int, ...], inUseIds: List[int]
) -> Tuple[int, ...]:
    """
    Remove the in-use IDs from the combination.
    """
    return tuple(id_ for id_ in combination if id_ not in inUseIds)

def highestProportionOfNewWordsAlgorithm(
    configFilePath: str
) -> Dict[str, List[SimpleClozeFlashcard]]:
    uniqueWordIdToWordObjects: Dict[str, List[Word]] = (
        getUniqueWordIdToWordObjects(configFilePath)
    )
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]] = (
        getInUseClozeFlashcards(configFilePath)
    )
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = (
        createInitialClozeFlashcards(inUseClozeFlashcards)
    )
    numFlashcardsPerWord: int = getNumFlashcardsPerWord(configFilePath)

    # List of words that have been used in any used cloze flashcards
    seenWords: List[str] = []

    for word in (word for flashcards in inUseClozeFlashcards.values() 
                 for flashcard in flashcards 
                 for word in flashcard.getWords()):
        uniqueWordId: str = word.getUniqueWordId()
        if uniqueWordId not in seenWords:
            seenWords.append(uniqueWordId)

    calculatedSentenceProportions: Dict[int, float] = {}

    for uniqueWordId in uniqueWordIdToWordObjects.keys():
        # Create a list of the raw words that are not already in use
        unusedWords: List[Word] = []

        words: List[Word] = uniqueWordIdToWordObjects[uniqueWordId]
        inUseClozeFlashcardsForWord: List[ClozeFlashcard] = (
            inUseClozeFlashcards.get(uniqueWordId, [])
        )
        for word in words:
            if not word.thisInstanceInClozeFlashcards(inUseClozeFlashcardsForWord):
                unusedWords.append(word)

        wordToSimpleClozeFlashcards, toContinue = (
            preAlgorithmChecks(
                uniqueWordId,
                wordToSimpleClozeFlashcards,
                numFlashcardsPerWord,
                inUseClozeFlashcards,
                unusedWords
            )
        )
        if toContinue:
            continue
    
        unusedWords.sort(
            key=lambda w: (
                w.getSentenceNewWordProportion(seenWords, calculatedSentenceProportions),
                w.getUniqueWordId()
            ),
            reverse=True
        )

        for word in unusedWords[:numFlashcardsPerWord]:
            if word.line is None or word.index is None:
                logger.error(
                    f"Word '{word.getUniqueWordId()}' has no line or word index, "
                    f"cannot create cloze flashcard."
                )
                continue

            simpleClozeFlashcard: SimpleClozeFlashcard = ClozeFlashcard(
                word.line, word.index
            ).GetSimpleClozeFlashcard()

            if word.getUniqueWordId() not in wordToSimpleClozeFlashcards:
                wordToSimpleClozeFlashcards[word.getUniqueWordId()] = []
            wordToSimpleClozeFlashcards[word.getUniqueWordId()].append(
                simpleClozeFlashcard
            )

    return wordToSimpleClozeFlashcards