import logging
from typing import Dict, List, Optional, Tuple
from itertools import combinations

from models import RawLine, RawWord, PunctuationlessWord, ClozeFlashcard, SimpleClozeFlashcard

logger = logging.getLogger(__name__)

def highestScoreAlgorithm(
    currentPunctuationlessWord: PunctuationlessWord,
    wordToClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]],
    punctuationlessWords: Dict[str, PunctuationlessWord],
    n: int,
    benefitShorterSentences: bool,
    optionalMaxWordFrequency: Optional[int]
) -> None:
    if optionalMaxWordFrequency is None:
        logger.error("Max word frequency is None, cannot proceed with highest score algorithm.")
        exit(1)
    
    maxWordFrequency: int = optionalMaxWordFrequency

    # For each unique word, create cloze flashcards for the it's raw lines
    # with the top n highest scores
    # If there are already cloze flashcards in use for the word, use those as the start of the list
    word: str = currentPunctuationlessWord.word
    referenceRawWords: List[RawWord] = currentPunctuationlessWord.referenceRawWords
    sortedRawWordObjects: List[RawWord] = sorted(
        referenceRawWords,
        key=lambda x: x.getSentenceScore(
            punctuationlessWords, maxWordFrequency, benefitShorterSentences
        ),
        reverse=True
    )

    # Take the top n highest scoring raw lines
    topRawWordObjects: List[RawWord] = (
        sortedRawWordObjects[:n] if len(sortedRawWordObjects) > n
        else sortedRawWordObjects
    )

    for rawWord in topRawWordObjects:
        # Ensure that the wordToClozeFlashcards has not reached the limit
        # (from some preexisting in use and some new ones)
        if word in wordToClozeFlashcards and len(wordToClozeFlashcards[word]) >= n:
            break

        # If the raw line of the raw word is already in the dictionary, skip it
        if rawWord.rawLine in wordToClozeFlashcards.get(word, []):
            continue

        # Create a new SimpleClozeFlashcard instance for the raw word
        clozeFlashcard: SimpleClozeFlashcard = ClozeFlashcard(
            rawWord.rawLine, rawWord.wordIndex
        ).GetSimpleClozeFlashcard()

        # If the word is not in the dictionary, create a new list
        if word not in wordToClozeFlashcards:
            wordToClozeFlashcards[word] = []
        wordToClozeFlashcards[word].append(clozeFlashcard)

def mostDifferentAlgorithm(
    currentPunctuationlessWord: PunctuationlessWord,
    wordToClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]],
    punctuationlessWords: Dict[str, PunctuationlessWord],
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]],
    n: int,
    benefitShorterSentences: bool
) -> None:
    # For each unique word, create cloze flashcards for the it's raw lines
    # with the top n most different sentences
    # If there are already cloze flashcards in use for the word, use those as the start of the list
    word: str = currentPunctuationlessWord.word
    rawWords: List[RawWord] = currentPunctuationlessWord.referenceRawWords
    inUseClozeFlashcardsForWord: List[ClozeFlashcard] = inUseClozeFlashcards.get(word, [])

    # Create a list of the raw words that are not already in use
    unusedRawWords: List[RawWord] = []

    for rawWord in rawWords:
        if not rawWord.rawLine.inListOfOtherRawLines([
            clozeFlashcard.rawLine for clozeFlashcard in inUseClozeFlashcardsForWord
        ]):
            unusedRawWords.append(rawWord)

    # If the number of reference raw words plus the number of in use cloze flashcards
    # is less than or equal to n, create cloze flashcards for all the raw words
    if len(unusedRawWords) + len(inUseClozeFlashcardsForWord) <= n:
        for rawWord in unusedRawWords:
            simpleClozeFlashcard: SimpleClozeFlashcard = ClozeFlashcard(
                rawWord.rawLine, rawWord.wordIndex
            ).GetSimpleClozeFlashcard()

            if (word in inUseClozeFlashcards and
                simpleClozeFlashcard in inUseClozeFlashcardsForWord):
                # If the cloze flashcard is already in use, skip it
                continue

            if word not in wordToClozeFlashcards:
                wordToClozeFlashcards[word] = []
            wordToClozeFlashcards[word].append(simpleClozeFlashcard)

        return

    # Subtract the number of cloze flashcards already in use for the word from n
    n = n - len(inUseClozeFlashcardsForWord)

    # Create a dictionary that maps all of the relevant raw lines IDs to their objects
    rawLineIdToRawWord: Dict[int, RawWord] = {
        rawWord.rawLine.hashedRawLine: rawWord for rawWord in unusedRawWords
    }

    # Create a list of all the combinations of n raw lines
    rawLineIds: List[int] = list(rawLineIdToRawWord.keys())

    # Add the in-use cloze flashcards to the rawLineIdToRawWord
    for clozeFlashcard in inUseClozeFlashcardsForWord:
        rawLineId: int = clozeFlashcard.rawLine.hashedRawLine
        clozeRawWord: RawWord = clozeFlashcard.GetClozeRawWord()
        rawLineIdToRawWord[rawLineId] = clozeRawWord

    inUseIds: List[int] = [
        clozeFlashcard.rawLine.hashedRawLine for clozeFlashcard in inUseClozeFlashcardsForWord
    ]

    # Combination means combination of sentences, not words
    newCombinations: List[Tuple[int, ...]] = generateNewCombinations(
        rawLineIds, inUseIds, n
    )

    bestCombination: Optional[Tuple[int, ...]] = findMostDifferentCombination(
        newCombinations, rawLineIdToRawWord, punctuationlessWords, benefitShorterSentences
    )

    if bestCombination is None:
        logger.error(f"No valid combination found for word '{word}'.")
        return

    bestCombinationWithoutInUse: Tuple[int, ...] = removeInUseIds(bestCombination, inUseIds)

    for rawLineId in bestCombinationWithoutInUse:
        rawLine: RawLine = rawLineIdToRawWord[rawLineId].rawLine
        wordIndex: int = rawLineIdToRawWord[rawLineId].wordIndex
        newSimpleClozeFlashcard: SimpleClozeFlashcard = ClozeFlashcard(
            rawLine, wordIndex
        ).GetSimpleClozeFlashcard()
        if word not in wordToClozeFlashcards:
            wordToClozeFlashcards[word] = []
        wordToClozeFlashcards[word].append(newSimpleClozeFlashcard)

def generateNewCombinations(
    rawLineIds: List[int],
    inUseClozeFlashcardIds: List[int],
    n: int
) -> List[Tuple[int, ...]]:
    """
    Generate new combinations of raw line IDs that include the in-use cloze flashcards.
    """
    newCombinations: List[Tuple[int, ...]] = []

    # Generate all combinations of n raw lines
    for combination in combinations(rawLineIds, n):
        # Create a new combination that includes the in-use cloze flashcards
        newCombination: Tuple[int, ...] = tuple(inUseClozeFlashcardIds) + combination
        newCombinations.append(newCombination)

    return newCombinations

def findMostDifferentCombination(
    combinationsOfRawLines: List[Tuple[int, ...]],
    rawLineIdToRawWord: Dict[int, RawWord],
    punctuationlessWords: Dict[str, PunctuationlessWord],
    benefitShorterSentences: bool
) -> Optional[Tuple[int, ...]]:
    currentHighestCosDissimilarity: float = 0
    currentBestCombination: Optional[Tuple[int, ...]] = None

    # For each combination of raw lines work out the sum of the normalised dot products of
    # their word vectors and find the combination with the highest cosine dissimilarity
    for combination in combinationsOfRawLines:
        sumOfCosDissimilarities: float = 0
        for i in range(len(combination)):
            for j in range(i + 1, len(combination)):
                rawLine1: RawLine = rawLineIdToRawWord[combination[i]].rawLine
                rawLine2: RawLine = rawLineIdToRawWord[combination[j]].rawLine
                cosDissimilarity: float = rawLine1.getCosDissimilarity(
                    rawLine2, punctuationlessWords
                )

                if benefitShorterSentences:
                    cosDissimilarity *= (
                        rawLine1.getSentenceLengthScore() *
                        rawLine2.getSentenceLengthScore()
                    )

                sumOfCosDissimilarities += cosDissimilarity

        if sumOfCosDissimilarities > currentHighestCosDissimilarity:
            currentHighestCosDissimilarity = sumOfCosDissimilarities
            currentBestCombination = combination

    return currentBestCombination

def removeInUseIds(combination: Tuple[int, ...], inUseIds: List[int]) -> Tuple[int, ...]:
    """
    Remove the in-use IDs from the combination.
    """
    return tuple(id_ for id_ in combination if id_ not in inUseIds)