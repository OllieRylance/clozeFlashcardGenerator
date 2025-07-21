import logging
import sys
import os

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from clozeFlashcardGenerator import main

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.CRITICAL, # Options are DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(levelname)s: %(message)s'
    )

    fileStartDict = {
        1: "test"
    }

    currentTestFileStart = fileStartDict[1]

    inputFilePath: str = f'manualTests/{currentTestFileStart}Sentences.txt'
    outputFilePath: str = f'manualTests/{currentTestFileStart}ClozeFlashcards.json'
    clozeChoosingAlgorithm: str = "mostDifferent"
    n: int = 3
    benefitShorterSentences: bool = False
    outputOrder: str = "alphabetical"
    main(
        inputFilePath, outputFilePath, clozeChoosingAlgorithm, 
        n, benefitShorterSentences
    )