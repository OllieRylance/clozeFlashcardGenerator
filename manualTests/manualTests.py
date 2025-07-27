import logging
import sys
import os
from typing import List

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, root_dir)

from main import main

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.CRITICAL, # Options are DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(levelname)s: %(message)s'
    )

    configFilePaths: List[str] = [
        "manualTests/afterAndAlonePunctuationAfterLastWord/config.json",
        "manualTests/aloneAndBeforePunctuationMidSentence/config.json",
        "manualTests/alonePunctuationBeforeFirstWord/config.json",
        "manualTests/alonePunctuationMidCloze/config.json",
        "manualTests/buryWord/config.json",
        "manualTests/complexExistingSentenceParsedAndNotDupicatedByNewSentence/config.json",
        "manualTests/doubleAfterPunctuation/config.json",
        "manualTests/doubleSpace/config.json",
        "manualTests/invalidPunctuation/config.json",
        "manualTests/leastInUsedSentenceFirst/config.json",
        "manualTests/multiWordExpressionInDifferentOrderGetGrouped/config.json",
        "manualTests/punctuationBeforeFirstWord/config.json",
        "manualTests/sortUnusedFirstThenAlphabetical/config.json",
        "manualTests/sortUnusedFirstThenFrequency/config.json",
        "manualTests/wordlessSentence/config.json"
    ]

    for configFilePath in configFilePaths:
        main(configFilePath)