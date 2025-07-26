import logging
import sys
import os
from typing import Dict, List, Optional

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from main import main, OutputOrder, ClozeChoosingAlgorithm

logger = logging.getLogger(__name__)

def runTest(config: Dict[str, str]) -> None:
    """
    Run the test with the given config.
    
    :param config: A dictionary containing the test configuration.
    """
    currentTestFileStart: str = config["FileStart"]
    inputFilePath: str = f'manualTests/{currentTestFileStart}sentences.txt'
    outputFilePath: str = f'manualTests/{currentTestFileStart}clozeFlashcards.json'
    clozeChoosingAlgorithm: ClozeChoosingAlgorithm = ClozeChoosingAlgorithm[config["Algorithm"].upper()]
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
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "punctuationBeforeFirstWord/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "alonePunctuationBeforeFirstWord/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "afterAndAlonePunctuationAfterLastWord/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "doubleAfterPunctuation/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "aloneAndBeforePunctuationMidSentence/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "noInputButExistingInUseOutput/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "existingClozeFlashcards"
        },
        {
            "FileStart": "complexExistingSentenceParsedAndNotDupicatedByNewSentence/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "existingClozeFlashcards"
        },
        {
            "FileStart": "multiWordExpressionInDifferentOrderGetGrouped/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "sortUnusedFirstThenAlphabetical/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "LEAST_USED_AS_CLOZE_FIRST, ALPHABETICAL",
            "ExistingOutputFileName": "existingClozeFlashcards"
        },
        {
            "FileStart": "invalidPunctuation/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "wordlessSentence/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "doubleSpace/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "ALPHABETICAL",
            "ExistingOutputFileName": "None"
        },
        {
            "FileStart": "sortUnusedFirstThenFrequency/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "LEAST_USED_AS_CLOZE_FIRST, FREQUENCY",
            "ExistingOutputFileName": "existingClozeFlashcards"
        },
        {
            "FileStart": "leastInUsedSentenceFirst/",
            "Algorithm": "MOST_DIFFERENT",
            "n": "3",
            "BenefitShorterSentences": "False",
            "OutputOrder": "LEAST_IN_USED_SENTENCES_FIRST, ALPHABETICAL",
            "ExistingOutputFileName": "existingClozeFlashcards"
        }
    ]

    for config in configs:
        runTest(config)