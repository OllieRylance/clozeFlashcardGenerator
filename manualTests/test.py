import logging
import sys
import os
from typing import Dict, List

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from models import resetForTesting
from clozeFlashcardGenerator import main

logger = logging.getLogger(__name__)

def runTest(preset: Dict[str, str]) -> None:
    """
    Run the test with the given preset.
    
    :param preset: A dictionary containing the test configuration.
    """
    currentTestFileStart: str = preset["FileStart"]
    inputFilePath: str = f'manualTests/{currentTestFileStart}/sentences.txt'
    outputFilePath: str = f'manualTests/{currentTestFileStart}/clozeFlashcards.json'
    clozeChoosingAlgorithm: str = preset["Algorithm"]
    n: int = int(preset["n"])
    benefitShorterSentences: bool = preset["BenefitShorterSentences"] == "True"
    # outputOrder: str = preset["OutputOrder"]
    main(
        inputFilePath, outputFilePath, clozeChoosingAlgorithm, 
        n, benefitShorterSentences
    )

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.CRITICAL, # Options are DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(levelname)s: %(message)s'
    )

    presets: List[Dict[str, str]] = [
        {
            "FileStart": "alonePunctuationMidCloze",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical"
        },
        {
            "FileStart": "punctuationBeforeFirstWordWhichIsCloze",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical"
        },
        {
            "FileStart": "aloneWordBeforeFirstWordWhichIsCloze",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical"
        },
        {
            "FileStart": "afterAndAlonePunctuationAfterLastWordWhichIsCloze",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical"
        },
        {
            "FileStart": "doubleAfterPunctuation",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical"
        },
    ]

    for preset in presets:
        resetForTesting()
        runTest(preset)