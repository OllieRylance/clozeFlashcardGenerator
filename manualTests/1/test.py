import logging
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, root_dir)

from clozeFlashcardGenerator import main

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG, # Options are DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(levelname)s: %(message)s'
    )

    inputFilePath: str = 'manualTests/1/testSentences.txt'
    outputFilePath: str = 'manualTests/1/testClozeFlashcards.json'
    clozeChoosingAlgorithm: str = "mostDifferent"
    n: int = 3
    benefitShorterSentences: bool = False
    outputOrder: str = "alphabetical"
    main(
        inputFilePath, outputFilePath, clozeChoosingAlgorithm, 
        n, benefitShorterSentences
    )