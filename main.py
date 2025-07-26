import logging
from typing import Dict, List, Optional
import cProfile
import pstats
import io

from models import ClozeFlashcard, SimpleClozeFlashcard, Word
from readWrite import writeJsonFile
from utils import (
    convertToJsonableFormat,
    ensureInUseClozeFlashcardsPersist,
    generateClozeFlashcards,
    parseSentenceLine,
    prepareInUseClozeFlashcards,
    prepareSentenceLines
)
from resources import (
    ClozeChoosingAlgorithm,
    OutputOrder
)

logger = logging.getLogger(__name__)

# Main Function
# Generates optimal cloze flashcards from a file of sentences
def main(
    inputFilePath: str,
    outputFilePath: str,
    clozeChoosingAlgorithm: ClozeChoosingAlgorithm,
    n: int,
    benefitShorterSentences: bool,
    outputOrder: List[OutputOrder] = [OutputOrder.ALPHABETICAL],
    existingOutputFilePath: Optional[str] = "Same",
) -> None:
    sentenceLines: Optional[List[str]] = prepareSentenceLines(inputFilePath)

    if sentenceLines is None: return

    uniqueWordIdToWordObjects: Dict[str, List[Word]] = {}

    for line in sentenceLines:
        parseSentenceLine(
            line,
            uniqueWordIdToWordObjects
        )

    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]] = {}

    # Determine which file to use for existing cloze flashcards
    if existingOutputFilePath is None:
        # User wants to ignore any existing files - start fresh
        logger.info("Ignoring any existing cloze flashcards - starting fresh")
    elif existingOutputFilePath == "Same":
        # Use the same file as output (default behavior)
        prepareInUseClozeFlashcards(
            outputFilePath,
            uniqueWordIdToWordObjects,
            inUseClozeFlashcards
        )
    else:
        # Use the specified existing file
        prepareInUseClozeFlashcards(
            existingOutputFilePath,
            uniqueWordIdToWordObjects,
            inUseClozeFlashcards
        )

    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = {}

    generateClozeFlashcards(
        clozeChoosingAlgorithm, n, benefitShorterSentences,
        inUseClozeFlashcards, uniqueWordIdToWordObjects,
        wordToSimpleClozeFlashcards
    )

    # Ensure that that all of the past in use cloze flashcards are still in the output
    ensureInUseClozeFlashcardsPersist(
        inUseClozeFlashcards, wordToSimpleClozeFlashcards
    )

    outputOrder.reverse()
    for order in outputOrder:
        if order == OutputOrder.ALPHABETICAL:
            wordToSimpleClozeFlashcards = dict(
                sorted(
                    wordToSimpleClozeFlashcards.items(),
                    key=lambda item: item[0]  # Sort by word (key)
                )
            )
        elif order == OutputOrder.FREQUENCY:
            frequencies: Dict[str, int] = {}
            for word, references in uniqueWordIdToWordObjects.items():
                frequencies[word] = len(references)
            wordToSimpleClozeFlashcards = dict(
                sorted(
                    wordToSimpleClozeFlashcards.items(),
                    key=lambda item: frequencies[item[0]],  # Sort by frequency
                    reverse=True  # Most frequent first
                )
            )
        elif order == OutputOrder.RANDOM:
            import random
            items = list(wordToSimpleClozeFlashcards.items())
            random.shuffle(items)
            wordToSimpleClozeFlashcards = dict(items)
        elif order == OutputOrder.LEAST_USED_AS_CLOZE_FIRST:
            usedCounts: Dict[str, int] = {}
            for word, flashcards in wordToSimpleClozeFlashcards.items():
                usedCounts[word] = sum(1 for fc in flashcards if fc.inUse)
            wordToSimpleClozeFlashcards = dict(
                sorted(
                    wordToSimpleClozeFlashcards.items(),
                    key=lambda item: usedCounts[item[0]],  # Sort by used count
                )
            )

    wordToJsonableClozeFlashcards: Dict[str, List[Dict[str, str]]] = (
        convertToJsonableFormat(wordToSimpleClozeFlashcards)
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
    clozeChoosingAlgorithm: ClozeChoosingAlgorithm = ClozeChoosingAlgorithm.MOST_DIFFERENT
    n: int = 3
    benefitShorterSentences: bool = True
    # TODO : Add not in any in use cloze flashcards first to output order (LEAST_IN_USED_SENTENCES_FIRST)
    outputOrder: List[OutputOrder] = [OutputOrder.LEAST_USED_AS_CLOZE_FIRST, OutputOrder.FREQUENCY, OutputOrder.ALPHABETICAL]
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