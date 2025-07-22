import logging
import sys
import os
from typing import Dict, List, Optional

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from models import resetForTesting
from main import main, OutputOrder

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
    outputOrderStrings: List[str] = preset["OutputOrder"].split(", ")
    outputOrder: List[OutputOrder] = [
        OutputOrder[order.strip().upper()] for order in outputOrderStrings
    ]
    existingOutputFileName: str = preset["ExistingOutputFilePath"]
    existingOutputFilePath: Optional[str] = (
        f'manualTests/{currentTestFileStart}/{existingOutputFileName}.json'
        if existingOutputFileName != "None" else None
    )
    main(
        inputFilePath, outputFilePath, clozeChoosingAlgorithm, 
        n, benefitShorterSentences, outputOrder, existingOutputFilePath
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
            "OutputOrder": "alphabetical",
            "ExistingOutputFilePath": "None"
        },
        {
            "FileStart": "punctuationBeforeFirstWord",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical",
            "ExistingOutputFilePath": "None"
        },
        {
            "FileStart": "alonePunctuationBeforeFirstWord",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical",
            "ExistingOutputFilePath": "None"
        },
        {
            "FileStart": "afterAndAlonePunctuationAfterLastWord",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical",
            "ExistingOutputFilePath": "None"
        },
        {
            "FileStart": "doubleAfterPunctuation",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical",
            "ExistingOutputFilePath": "None"
        },
        {
            "FileStart": "aloneAndBeforePunctuationMidSentence",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical",
            "ExistingOutputFilePath": "None"
        },
        {
            "FileStart": "noInputButExistingInUseOutput",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical",
            "ExistingOutputFilePath": "existingClozeFlashcards"
        },
        {
            "FileStart": "complexExistingSentenceParsedAndNotDupicatedByNewSentence",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical",
            "ExistingOutputFilePath": "existingClozeFlashcards"
        },
        {
            "FileStart": "multiWordExpressionInDifferentOrderGetGrouped",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "alphabetical",
            "ExistingOutputFilePath": "None"
        },
        
        {
            "FileStart": "multiWordExpressionInDifferentOrderGetGrouped",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "unused, alphabetical",
            "ExistingOutputFilePath": "None"
        },
    ]

    for preset in presets:
        resetForTesting()
        runTest(preset)