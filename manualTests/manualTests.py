import logging
import sys
import os
from typing import Dict, List, Optional

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from models import resetForTesting
from main import main, OutputOrder

logger = logging.getLogger(__name__)

def runTest(config: Dict[str, str]) -> None:
    """
    Run the test with the given config.
    
    :param config: A dictionary containing the test configuration.
    """
    currentTestFileStart: str = config["FileStart"]
    inputFilePath: str = f'manualTests/{currentTestFileStart}sentences.txt'
    outputFilePath: str = f'manualTests/{currentTestFileStart}clozeFlashcards.json'
    clozeChoosingAlgorithm: str = config["Algorithm"]
    n: int = int(config["n"])
    benefitShorterSentences: bool = config["BenefitShorterSentences"] == "True"
    outputOrderStrings: List[str] = config["OutputOrder"].split(", ")
    outputOrder: List[OutputOrder] = [
        OutputOrder[order.strip().upper()] for order in outputOrderStrings
    ]
    existingOutputFileName: str = config["ExistingOutputFileName"]
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

    configs: List[Dict[str, str]] = [
        {
            "FileStart": "alonePunctuationMidCloze/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "punctuationBeforeFirstWord/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "alonePunctuationBeforeFirstWord/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "afterAndAlonePunctuationAfterLastWord/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "doubleAfterPunctuation/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "aloneAndBeforePunctuationMidSentence/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "noInputButExistingInUseOutput/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "existingClozeFlashcards"
        },
        {
            "FileStart": "complexExistingSentenceParsedAndNotDupicatedByNewSentence/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "existingClozeFlashcards"
        },
        {
            "FileStart": "multiWordExpressionInDifferentOrderGetGrouped/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "sortUnusedFirstThenAlphabetical/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "LEAST_USED_FIRST, ALPHABETICAL",
            "ExistingOutputFileName": "existingClozeFlashcards"
        },
        {
            "FileStart": "invalidPunctuationTest/",
            "Algorithm": "mostDifferent",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        
    ]

    for config in configs:
        resetForTesting()
        runTest(config)