import logging
from typing import Dict, List

from configUtils import getOutputFilePath
from models import ClozeFlashcard, SimpleClozeFlashcard, Word
from readWrite import writeJsonFile
from utils import (
    convertToJsonableFormat,
    ensureInUseClozeFlashcardsPersist,
    generateClozeFlashcards,
    getUniqueWordIdToWordObjects,
    getInUseClozeFlashcards
)
from resources import (
    OutputOrder
)
from configUtils import (
    getOutputOrder,
    getWordsToBury
)

logger = logging.getLogger(__name__)

# Main Function
# Generates optimal cloze flashcards from a file of sentences
def main(configFilePath: str) -> None:
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = (
        generateClozeFlashcards(
            configFilePath
        )
    )

    # Ensure that the in use cloze flashcards are persisted
    ensureInUseClozeFlashcardsPersist(
        configFilePath,
        wordToSimpleClozeFlashcards
    )

    # TODO : complete seperate sorting logic so that it can be used
    # with and without rerunning the algorithm

    outputOrder: List[OutputOrder] = getOutputOrder(configFilePath)
    outputOrder.reverse()
    for order in outputOrder:
        if order == OutputOrder.ALPHABETICAL:
            wordToSimpleClozeFlashcards = dict(
                sorted(
                    wordToSimpleClozeFlashcards.items(),
                    key=lambda item: item[0] # Sort by word (key)
                )
            )
        elif order == OutputOrder.FREQUENCY:
            uniqueWordIdToWordObjects: Dict[str, List[Word]] = (
                getUniqueWordIdToWordObjects(configFilePath)
            )            
            frequencies: Dict[str, int] = {}
            for word, references in uniqueWordIdToWordObjects.items():
                frequencies[word] = len(references)
            wordToSimpleClozeFlashcards = dict(
                sorted(
                    wordToSimpleClozeFlashcards.items(),
                    # Sort by frequency
                    key=lambda item: frequencies[item[0]],
                    # Most frequent first
                    reverse=True
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
                    # Sort by used count
                    key=lambda item: usedCounts[item[0]],
                )
            )
        elif order == OutputOrder.LEAST_IN_USED_SENTENCES_FIRST:
            inUseCounts: Dict[str, int] = {}
            for word in wordToSimpleClozeFlashcards.keys():
                inUseCounts[word] = 0

            inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]] = (
                getInUseClozeFlashcards(configFilePath)
            )
            for word in (word for flashcards in inUseClozeFlashcards.values() 
                         for flashcard in flashcards 
                         for word in flashcard.getWords()):
                if word.isFirstWordInMultiWordExpression():
                    uniqueWordId: str = word.getUniqueWordId()
                    if uniqueWordId not in inUseCounts:
                        inUseCounts[uniqueWordId] = 0
                    inUseCounts[uniqueWordId] += 1
            wordToSimpleClozeFlashcards = dict(
                sorted(
                    wordToSimpleClozeFlashcards.items(),
                    # Sort by in use count
                    key=lambda item: inUseCounts[item[0]],
                )
            )

    wordsToBury: List[str] = getWordsToBury(configFilePath)
    wordToSimpleClozeFlashcards = dict(
        sorted(
            wordToSimpleClozeFlashcards.items(),
            # Bury specified words
            key=lambda item: 1 if item[0] in wordsToBury else 0
        )
    )

    wordToJsonableClozeFlashcards: Dict[str, List[Dict[str, str]]] = (
        convertToJsonableFormat(wordToSimpleClozeFlashcards)
    )

    # Ensure that the in use cloze flashcards are persisted
    ensureInUseClozeFlashcardsPersist(
        configFilePath,
        wordToSimpleClozeFlashcards
    )

    outputFilePath: str = getOutputFilePath(configFilePath)
    writeJsonFile(outputFilePath, wordToJsonableClozeFlashcards)