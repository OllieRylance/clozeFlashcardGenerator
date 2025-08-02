import logging
from typing import Dict, List

from models import SimpleClozeFlashcard
from utils import (
    generateClozeFlashcards,
    getOutputFileData,
    storeWordToSimpleClozeFlashcards,
    sortSimpleClozeFlashcards,
    burySimpleClozeFlashcards
)

logger = logging.getLogger(__name__)

# Main Function
# Generates optimal cloze flashcards from a file of sentences
def main(configFilePath: str) -> None:
    applyAlgorithm(configFilePath)
    sortOutputWords(configFilePath)
    buryOutputWords(configFilePath)

def applyAlgorithm(configFilePath: str) -> None:
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = (
        generateClozeFlashcards(
            configFilePath
        )
    )

    storeWordToSimpleClozeFlashcards(
        configFilePath,
        wordToSimpleClozeFlashcards
    )

def sortOutputWords(configFilePath: str) -> None:
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = (
        getOutputFileData(configFilePath)
    )

    wordToSimpleClozeFlashcards = sortSimpleClozeFlashcards(
        wordToSimpleClozeFlashcards,
        configFilePath
    )

    storeWordToSimpleClozeFlashcards(
        configFilePath,
        wordToSimpleClozeFlashcards
    )

def buryOutputWords(configFilePath: str) -> None:
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = (
        getOutputFileData(configFilePath)
    )

    wordToSimpleClozeFlashcards = burySimpleClozeFlashcards(
        wordToSimpleClozeFlashcards,
        configFilePath
    )

    storeWordToSimpleClozeFlashcards(
        configFilePath,
        wordToSimpleClozeFlashcards
    )
