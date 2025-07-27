import logging
from typing import List

from configUtils import (
    getBenefitShorterSentences,
    getClozeChoosingAlgorithm,
    getInputFilePath,
    getNumFlashcardsPerWord,
    getOutputFilePath,
    getOutputOrder,
    getWordsToBury
)
from resources import ClozeChoosingAlgorithm, OutputOrder
from main import main

logger = logging.getLogger(__name__)

def runAlgorithm(configFilePath: str) -> None:
    """
    Runs the algorithm with the configuration specified in the config file.
    """
    inputFilePath: str = getInputFilePath(configFilePath)
    outputFilePath: str = getOutputFilePath(configFilePath)
    clozeChoosingAlgorithm: ClozeChoosingAlgorithm = getClozeChoosingAlgorithm(configFilePath)
    numFlashcardsPerWord: int = getNumFlashcardsPerWord(configFilePath)
    benefitShorterSentences: bool = getBenefitShorterSentences(configFilePath)
    outputOrder: List[OutputOrder] = getOutputOrder(configFilePath)
    wordsToBury: List[str] = getWordsToBury(configFilePath)

    main(
        inputFilePath,
        outputFilePath,
        clozeChoosingAlgorithm,
        numFlashcardsPerWord,
        benefitShorterSentences,
        outputOrder,
        wordsToBury
    )