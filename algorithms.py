import logging
from typing import Dict, List, Optional, Tuple
from itertools import combinations

from models import Line, ClozeFlashcard, SimpleClozeFlashcard, Word

logger = logging.getLogger(__name__)

# def highestScoreAlgorithm(
#     currentPunctuationlessWord: PunctuationlessWord,
#     wordToClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]],
#     punctuationlessWords: Dict[str, PunctuationlessWord],
#     n: int,
#     benefitShorterSentences: bool,
#     optionalMaxWordFrequency: Optional[int]
# ) -> None:
#     if optionalMaxWordFrequency is None:
#         logger.error("Max word frequency is None, cannot proceed with highest score algorithm.")
#         exit(1)
    
#     maxWordFrequency: int = optionalMaxWordFrequency

#     # For each unique word, create cloze flashcards for the it's raw lines
#     # with the top n highest scores
#     # If there are already cloze flashcards in use for the word, use those as the start of the list
#     word: str = currentPunctuationlessWord.word
#     referenceRawWords: List[RawWord] = currentPunctuationlessWord.referenceRawWords
#     sortedRawWordObjects: List[RawWord] = sorted(
#         referenceRawWords,
#         key=lambda x: x.getSentenceScore(
#             punctuationlessWords, maxWordFrequency, benefitShorterSentences
#         ),
#         reverse=True
#     )

#     # Take the top n highest scoring raw lines
#     topRawWordObjects: List[RawWord] = (
#         sortedRawWordObjects[:n] if len(sortedRawWordObjects) > n
#         else sortedRawWordObjects
#     )

#     for rawWord in topRawWordObjects:
#         # Ensure that the wordToClozeFlashcards has not reached the limit
#         # (from some preexisting in use and some new ones)
#         if word in wordToClozeFlashcards and len(wordToClozeFlashcards[word]) >= n:
#             break

#         # Create a new SimpleClozeFlashcard instance for the raw word
#         clozeFlashcard: SimpleClozeFlashcard = ClozeFlashcard(
#             rawWord.rawLine, rawWord.wordIndex
#         ).GetSimpleClozeFlashcard()

#         # If the simple flashcard for the raw word is already in the dictionary, skip it
#         if clozeFlashcard in wordToClozeFlashcards.get(word, []):
#             continue

#         # If the word is not in the dictionary, create a new list
#         if word not in wordToClozeFlashcards:
#             wordToClozeFlashcards[word] = []
#         wordToClozeFlashcards[word].append(clozeFlashcard)

def mostDifferentAlgorithm(
    uniqueWordId: str,
    n: int,
    benefitShorterSentences: bool
) -> None:
    # For each unique word, create cloze flashcards for the it's raw lines
    # with the top n most different sentences
    # If there are already cloze flashcards in use for the word, 
    # use those as the start of the list
    words: List[Word] = Word.uniqueWordIdToWordObjects[uniqueWordId]
    inUseClozeFlashcardsForWord: List[ClozeFlashcard] = (
        ClozeFlashcard.inUseClozeFlashcards.get(uniqueWordId, [])
    )

    # Create a list of the raw words that are not already in use
    unusedWords: List[Word] = []

    for word in words:
        if not word.thisInstanceInClozeFlashcards(inUseClozeFlashcardsForWord):
            unusedWords.append(word)

    # If the number of reference words plus the number of in use cloze flashcards
    # is less than or equal to n, create cloze flashcards for all the words
    if len(unusedWords) + len(inUseClozeFlashcardsForWord) <= n:
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

            if (currentUniqueWordId in ClozeFlashcard.inUseClozeFlashcards and
                simpleClozeFlashcard in inUseClozeFlashcardsForWord):
                # If the cloze flashcard is already in use, skip it
                continue

            if currentUniqueWordId not in SimpleClozeFlashcard.wordToFlashcards:
                SimpleClozeFlashcard.wordToFlashcards[currentUniqueWordId] = []
            SimpleClozeFlashcard.wordToFlashcards[currentUniqueWordId].append(
                simpleClozeFlashcard
            )

        return

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
    newSentenceNum = n - len(inUseClozeFlashcardsForWord)

    # Combination means combination of sentences, not words
    newCombinations: List[Tuple[int, ...]] = generateNewCombinations(
        lineIds, inUseIds, newSentenceNum
    )

    bestCombination: Optional[Tuple[int, ...]] = findMostDifferentCombination(
        newCombinations, lineIdToWord, benefitShorterSentences
    )

    if bestCombination is None:
        logger.error(f"No valid combination found for word '{uniqueWordId}'.")
        return

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
        if uniqueWordId not in SimpleClozeFlashcard.wordToFlashcards:
            SimpleClozeFlashcard.wordToFlashcards[uniqueWordId] = []
        SimpleClozeFlashcard.wordToFlashcards[uniqueWordId].append(
            newSimpleClozeFlashcard
        )

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
    combinationsOfRawLines: List[Tuple[int, ...]],
    lineIdToWord: Dict[int, Word],
    benefitShorterSentences: bool
) -> Optional[Tuple[int, ...]]:
    currentHighestCosDissimilarity: float = 0
    currentBestCombination: Optional[Tuple[int, ...]] = None

    # For each combination of raw lines work out the sum of the normalised 
    # dot products of their word vectors and find the combination with the 
    # highest cosine dissimilarity
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
                    line2
                )

                if benefitShorterSentences:
                    cosDissimilarity *= (
                        line1.getSentenceLengthScore() *
                        line2.getSentenceLengthScore()
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