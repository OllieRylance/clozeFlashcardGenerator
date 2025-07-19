import logging
from typing import Dict, List, Optional
import cProfile
import pstats
import io

from models import PunctuationlessWord, ClozeFlashcard, SimpleClozeFlashcard
from utils import (
    findInvalidLines,
    printFoundInvalidLines,
    getInUseClozeFlashcards,
    createPunctuationlessWordsFromSentences,
    convertToJsonableFormat,
    createInitialClozeFlashcards,
)
from algorithms import highestScoreAlgorithm, mostDifferentAlgorithm
from readWrite import readLines, readJsonFile, writeJsonFile

logger = logging.getLogger(__name__)

def prepareSentenceLines(inputFilePath: str) -> List[str]:
    """
    Read sentences from a file and validate them.
    Returns a list of valid sentences.
    """
    logger.info(f"Reading sentences from '{inputFilePath}'...")
    sentenceLines: List[str] = readLines(inputFilePath)

    if not sentenceLines:
        logger.error(f"No valid lines found in '{inputFilePath}'. Please check the file.")

        # Exit the program if no valid lines are found
        exit(1)

    # Check for invalid lines in the sentences file
    logger.info(f"Checking for invalid lines in '{inputFilePath}'...")

    invalidLines: List[str] = findInvalidLines(sentenceLines)

    if invalidLines:
        logger.error("Invalid sentence lines found.")

        if logger.isEnabledFor(logging.DEBUG):
            printFoundInvalidLines(invalidLines)

        # Exit the program if invalid lines are found
        exit(1)

    logger.info("Sentence lines are valid.")
    return sentenceLines

def prepareInUseClozeFlashcards(outputFilePath: str) -> Dict[str, List[ClozeFlashcard]]:
    """
    Prepare the in-use cloze flashcards from the output file.
    Returns a dictionary of in-use cloze flashcards.
    """
    # Try to read existing cloze flashcards from the output file
    existingClozeFlashcardsJsonFileString: Optional[str] = readJsonFile(outputFilePath)
    if existingClozeFlashcardsJsonFileString is None:
        logger.info(f"No existing cloze flashcards found in '{outputFilePath}'. Starting fresh.")

    logger.info(f"Found existing cloze flashcards data in '{outputFilePath}'.")

    # Return the dictionary that stores the in use cloze flashcards
    return getInUseClozeFlashcards(existingClozeFlashcardsJsonFileString)

def printGeneratingClozeFlashcardsInfo(
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]],
    clozeChoosingAlgorithm: str
) -> None:
    totalInUseClozeFlashcards: int = sum(
        len(flashcards) for flashcards in inUseClozeFlashcards.values()
    )
    logger.info(
        f"Generating cloze flashcards using the '{clozeChoosingAlgorithm}' algorithm "
        f"given {totalInUseClozeFlashcards} existing cloze flashcards..."
    )

def generateClozeFlashcards(
    clozeChoosingAlgorithm: str,
    n: int,
    punctuationlessWords: Dict[str, PunctuationlessWord],
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]],
    benefitShorterSentences: bool
) -> Optional[Dict[str, List[SimpleClozeFlashcard]]]:
    """
    Generate cloze flashcards based on the chosen algorithm.
    Returns a dictionary of words to lists of SimpleClozeFlashcard objects.
    """
    if logger.isEnabledFor(logging.INFO):
        printGeneratingClozeFlashcardsInfo(inUseClozeFlashcards, clozeChoosingAlgorithm)

    maxWordFrequency: Optional[int] = None
    if clozeChoosingAlgorithm == "highestScore":
        maxWordFrequency = max(len(flashcards) for flashcards in inUseClozeFlashcards.values())

    wordToClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = createInitialClozeFlashcards(
        inUseClozeFlashcards
    )

    for punctuationlessWord in punctuationlessWords.values():
        word: str = punctuationlessWord.word
        # If the word already has equal or more cloze flashcards than n, skip it
        if word in wordToClozeFlashcards and len(wordToClozeFlashcards[word]) >= n:
            continue

        if clozeChoosingAlgorithm == "highestScore":
            highestScoreAlgorithm(
                punctuationlessWord,
                wordToClozeFlashcards,
                punctuationlessWords,
                n,
                benefitShorterSentences,
                maxWordFrequency
            )
        elif clozeChoosingAlgorithm == "mostDifferent":
            mostDifferentAlgorithm(
                punctuationlessWord,
                wordToClozeFlashcards,
                punctuationlessWords,
                inUseClozeFlashcards,
                n,
                benefitShorterSentences
            )

    return wordToClozeFlashcards

def ensureInUseClozeFlashcardsPersist(
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]],
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]]
) -> None:
    for word, clozeFlashcards in inUseClozeFlashcards.items():
        if word not in wordToSimpleClozeFlashcards:
            # If the word is not in the new cloze flashcards, a serious error has occurred
            logger.error(
                f"Word '{word}' from in-use cloze flashcards is not present "
                f"in the new cloze flashcards."
            )
            exit(1)

        for clozeFlashcard in clozeFlashcards:
            simpleClozeFlashcard = clozeFlashcard.GetSimpleClozeFlashcard()
            if simpleClozeFlashcard not in wordToSimpleClozeFlashcards[word]:
                # If the cloze flashcard is not in the new cloze flashcards,
                # a serious error has occurred
                logger.error(
                    f"Cloze flashcard '{simpleClozeFlashcard}' for word '{word}' "
                    f"from in-use cloze flashcards is not present in the new cloze flashcards."
                )
                exit(1)

# Main Function
# Generates optimal cloze flashcards from a file of sentences
def main(
    inputFilePath: str,
    outputFilePath: str,
    clozeChoosingAlgorithm: str,
    n: int,
    benefitShorterSentences: bool
) -> None:
    # Try to get the lines from the input file
    if clozeChoosingAlgorithm not in ["highestScore", "mostDifferent"]:
        logger.error(f"Invalid cloze choosing algorithm: {clozeChoosingAlgorithm}.")
        exit(1)

    sentenceLines: List[str] = prepareSentenceLines(inputFilePath)
    punctuationlessWords: Dict[str, PunctuationlessWord] = createPunctuationlessWordsFromSentences(
        sentenceLines
    )

    # Try to read existing cloze flashcards from the output file
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]] = prepareInUseClozeFlashcards(
        outputFilePath
    )

    wordToSimpleClozeFlashcards: Optional[Dict[str, List[SimpleClozeFlashcard]]] = generateClozeFlashcards(
        clozeChoosingAlgorithm, n, punctuationlessWords, inUseClozeFlashcards, benefitShorterSentences
    )

    if wordToSimpleClozeFlashcards is None:
        logger.error(
            f"Failed to generate cloze flashcards using the '{clozeChoosingAlgorithm}' algorithm."
        )
        exit(1)

    # Ensure that that all of the past in use cloze flashcards are still in the output
    ensureInUseClozeFlashcardsPersist(inUseClozeFlashcards, wordToSimpleClozeFlashcards)

    wordToJsonableClozeFlashcards: Dict[str, List[Dict[str, str]]] = convertToJsonableFormat(
        wordToSimpleClozeFlashcards
    )

    writeJsonFile(outputFilePath, wordToJsonableClozeFlashcards)

# TODO: create test folders where different input and output set ups can be tested
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG, # Options are DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(levelname)s: %(message)s'
    )

    profiler = None

    # If the logger is set to DEBUG, create a profile to analyze performance
    if logger.isEnabledFor(logging.DEBUG):
        # Create profiler
        profiler = cProfile.Profile()

        # Start profiling
        profiler.enable()

    # Your code to profile
    inputFilePath: str = 'sentences.txt'
    outputFilePath: str = 'clozeFlashcards.json'
    clozeChoosingAlgorithm: str = "mostDifferent"
    n: int = 3
    benefitShorterSentences: bool = False
    # TODO : implement outputOrder and use it to sort the cloze flashcards
    outputOrder: str = "alphabetical" # options are "alphabetical", "frequency", "random", "firstComeFirstServed", "lastComeFirstServed"
    main(inputFilePath, outputFilePath, clozeChoosingAlgorithm, n, benefitShorterSentences)

    if profiler is not None:
        # Stop profiling
        profiler.disable()

        # Create a string buffer to capture output
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)

        # Sort by cumulative time and print top 20 functions
        ps.sort_stats('cumulative')
        ps.print_stats(20)

        # Print the results
        print(s.getvalue())

        # You can also save to file
        ps.dump_stats('profile_results.prof')