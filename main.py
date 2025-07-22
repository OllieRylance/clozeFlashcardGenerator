from enum import Enum
import logging
from typing import Dict, List, Optional
import cProfile
import pstats
import io

from models import SimpleClozeFlashcard, Word

from readWrite import writeJsonFile
from utils import (
    convertToJsonableFormat,
    ensureInUseClozeFlashcardsPersist,
    generateClozeFlashcards,
    parseSentenceLine,
    prepareInUseClozeFlashcards,
    prepareSentenceLines
)

logger = logging.getLogger(__name__)

class OutputOrder(Enum):
    ALPHABETICAL = 1
    FREQUENCY = 2
    RANDOM = 3
    LEAST_USED_FIRST = 4

# Main Function
# Generates optimal cloze flashcards from a file of sentences
def main(
    inputFilePath: str,
    outputFilePath: str,
    clozeChoosingAlgorithm: str,
    n: int,
    benefitShorterSentences: bool,
    outputOrder: List[OutputOrder] = [OutputOrder.ALPHABETICAL],
    existingOutputFilePath: Optional[str] = "Same",
) -> None:
    # Try to get the lines from the input file
    if clozeChoosingAlgorithm not in ["mostDifferent"]:
        logger.error(f"Invalid cloze choosing algorithm: {clozeChoosingAlgorithm}.")
        exit(1)

    sentenceLines: List[str] = prepareSentenceLines(inputFilePath)
    for line in sentenceLines:
        parseSentenceLine(line)

    # Determine which file to use for existing cloze flashcards
    if existingOutputFilePath is None:
        # User wants to ignore any existing files - start fresh
        logger.info("Ignoring any existing cloze flashcards - starting fresh")
    elif existingOutputFilePath == "Same":
        # Use the same file as output (default behavior)
        prepareInUseClozeFlashcards(outputFilePath)
    else:
        # Use the specified existing file
        prepareInUseClozeFlashcards(existingOutputFilePath)

    generateClozeFlashcards(
        clozeChoosingAlgorithm, n, benefitShorterSentences
    )

    # Ensure that that all of the past in use cloze flashcards are still in the output
    ensureInUseClozeFlashcardsPersist()

    # TODO : investigate adding more output order options
    # firstly, the option to put words without used cloze flashcards at the start
    # and then most frequent words at the beginning
    # Output order could be a list with most important sort first, etc. And the list
    # gets iterated through backwards permorming the sorts one by one (or all in same
    # run though using lambda if possible)
    outputOrder.reverse()
    for order in outputOrder:
        if order == OutputOrder.ALPHABETICAL:
            SimpleClozeFlashcard.wordToFlashcards = dict(
                sorted(
                    SimpleClozeFlashcard.wordToFlashcards.items(),
                    key=lambda item: item[0]  # Sort by word (key)
                )
            )
        elif order == OutputOrder.FREQUENCY:
            frequencies: Dict[str, int] = {}
            for word, references in Word.uniqueWordIdToWordObjects.items():
                frequencies[word] = len(references)
            SimpleClozeFlashcard.wordToFlashcards = dict(
                sorted(
                    SimpleClozeFlashcard.wordToFlashcards.items(),
                    key=lambda item: frequencies[item[0]],  # Sort by frequency
                    reverse=True  # Most frequent first
                )
            )
        elif order == OutputOrder.RANDOM:
            import random
            items = list(SimpleClozeFlashcard.wordToFlashcards.items())
            random.shuffle(items)
            SimpleClozeFlashcard.wordToFlashcards = dict(items)
        elif order == OutputOrder.LEAST_USED_FIRST:
            usedCounts: Dict[str, int] = {}
            for word, flashcards in SimpleClozeFlashcard.wordToFlashcards.items():
                usedCounts[word] = sum(1 for fc in flashcards if fc.inUse)
            SimpleClozeFlashcard.wordToFlashcards = dict(
                sorted(
                    SimpleClozeFlashcard.wordToFlashcards.items(),
                    key=lambda item: usedCounts[item[0]],  # Sort by used count
                )
            )

    wordToJsonableClozeFlashcards: Dict[str, List[Dict[str, str]]] = (
        convertToJsonableFormat(SimpleClozeFlashcard.wordToFlashcards)
    )

    writeJsonFile(outputFilePath, wordToJsonableClozeFlashcards)

# TODO : come up with and stick to naming convention
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
    outputOrder: List[OutputOrder] = [OutputOrder.ALPHABETICAL]
    main(
        inputFilePath, outputFilePath, clozeChoosingAlgorithm, 
        n, benefitShorterSentences, outputOrder
    )

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