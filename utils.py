import logging
from typing import Dict, List, Optional
import json

from algorithms import (
    firstSentencesFirstAlgorithm,
    mostDifferentAlgorithm,
    highestProportionOfNewWordsAlgorithm
)
from models import (
    ClozeFlashcard,
    SimpleClozeFlashcard,
    Word
)
from readWrite import readJsonFile, writeJsonFile
from resources import (
    ClozeChoosingAlgorithm,
    OutputOrder
)
from configUtils import (
    getClozeChoosingAlgorithm,
    getOutputFilePath,
    getOutputOrder,
    getWordsToBury
)
from globalUtils import (
    getInUseClozeFlashcards,
    getUniqueWordIdToWordObjects
)

logger = logging.getLogger(__name__)

def printGeneratingClozeFlashcardsInfo(configFilePath: str) -> None:
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]] = (
        getInUseClozeFlashcards(configFilePath)
    )
    clozeChoosingAlgorithm: ClozeChoosingAlgorithm = getClozeChoosingAlgorithm(configFilePath)
    
    totalInUseClozeFlashcards: int = sum(
        len(flashcards) for flashcards in inUseClozeFlashcards.values()
    )
    logger.info(
        f"Generating cloze flashcards using the '{clozeChoosingAlgorithm}' algorithm "
        f"given {totalInUseClozeFlashcards} existing cloze flashcards..."
    )

def generateClozeFlashcards(configFilePath: str) -> Dict[str, List[SimpleClozeFlashcard]]:
    """
    Generate cloze flashcards based on the chosen algorithm.
    Returns a dictionary of words to lists of SimpleClozeFlashcard objects.
    """
    if logger.isEnabledFor(logging.INFO):
        printGeneratingClozeFlashcardsInfo(configFilePath)

    clozeChoosingAlgorithm: ClozeChoosingAlgorithm = getClozeChoosingAlgorithm(configFilePath)
    if clozeChoosingAlgorithm == ClozeChoosingAlgorithm.FIRST_SENTENCES_FIRST:
        return firstSentencesFirstAlgorithm(configFilePath)
    elif clozeChoosingAlgorithm == ClozeChoosingAlgorithm.MOST_DIFFERENT:
        return mostDifferentAlgorithm(configFilePath)
    elif clozeChoosingAlgorithm == ClozeChoosingAlgorithm.HIGHEST_PROPORTION_OF_NEW_WORDS:
        return highestProportionOfNewWordsAlgorithm(configFilePath)
    
    # If an unknown algorithm is specified, log an error and return an empty dictionary
    logger.error(
        f"Unknown cloze choosing algorithm '{clozeChoosingAlgorithm}' specified in the config file."
    )
    return {}

def ensureInUseClozeFlashcardsPersist(
    configFilePath: str,
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]]
) -> None:
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]] = (
        getInUseClozeFlashcards(configFilePath)
    )
    
    for word, clozeFlashcards in inUseClozeFlashcards.items():
        if word not in wordToSimpleClozeFlashcards:
            # If the word is not in the new cloze flashcards, 
            # a serious error has occurred
            logger.error(
                f"Word '{word}' from in-use cloze flashcards is not present "
                f"in the new cloze flashcards."
            )
            exit(1)

        for clozeFlashcard in clozeFlashcards:
            simpleClozeFlashcard = clozeFlashcard.GetSimpleClozeFlashcard()
            if simpleClozeFlashcard not in wordToSimpleClozeFlashcards[word]:
                # If the cloze flashcard is not in the new cloze flashcards,
                # a serious error has occurred
                logger.error(
                    f"Cloze flashcard '{simpleClozeFlashcard}' for word '{word}' "
                    f"from in-use cloze flashcards is not present in the new "
                    f"cloze flashcards."
                )
                exit(1)

def convertToJsonableFormat(
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]]
) -> Dict[str, List[Dict[str, str]]]:
    """
    Convert the word to SimpleClozeFlashcard dictionary to a JSON-serializable format.
    Returns a dictionary of words to lists of dictionaries 
    representing SimpleClozeFlashcards.
    """
    wordToJsonableClozeFlashcards: Dict[str, List[Dict[str, str]]] = {}

    for word, simpleClozeFlashcards in wordToSimpleClozeFlashcards.items():
        jsonableFlashcards: List[Dict[str, str]] = []
        for simpleClozeFlashcard in simpleClozeFlashcards:
            jsonableFlashcards.append(simpleClozeFlashcard.toJsonableDict())
        wordToJsonableClozeFlashcards[word] = jsonableFlashcards

    return wordToJsonableClozeFlashcards

def getOutputFileData(configFilePath: str) -> Dict[str, List[SimpleClozeFlashcard]]:
    """
    Get a mapping of words to their corresponding SimpleClozeFlashcard objects from the output file.
    """
    outputFilePath: str = getOutputFilePath(configFilePath)
    jsonDataString: Optional[str] = readJsonFile(outputFilePath)
    if jsonDataString is None:
        logger.error(f"Output file '{outputFilePath}' not found or empty.")
        return {}

    jsonData: Dict[str, List[Dict[str, str]]] = json.loads(jsonDataString)
    if not jsonData:
        logger.error(f"No data found in output file '{outputFilePath}'.")
        return {}

    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = {}
    for word, flashcards in jsonData.items():
        wordToSimpleClozeFlashcards[word] = [
            SimpleClozeFlashcard.fromJsonableDict(fc) for fc in flashcards
        ]

    return wordToSimpleClozeFlashcards

def storeWordToSimpleClozeFlashcards(
        configFilePath: str,
        wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]]
) -> None:
    # Ensure that the in use cloze flashcards are persisted
    ensureInUseClozeFlashcardsPersist(
        configFilePath,
        wordToSimpleClozeFlashcards
    )

    wordToJsonableClozeFlashcards: Dict[str, List[Dict[str, str]]] = (
        convertToJsonableFormat(wordToSimpleClozeFlashcards)
    )

    outputFilePath: str = getOutputFilePath(configFilePath)
    writeJsonFile(outputFilePath, wordToJsonableClozeFlashcards)

def sortSimpleClozeFlashcards(
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]],
    configFilePath: str
) -> Dict[str, List[SimpleClozeFlashcard]]:
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
    
    return wordToSimpleClozeFlashcards

def burySimpleClozeFlashcards(
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]],
    configFilePath: str
) -> Dict[str, List[SimpleClozeFlashcard]]:
    """
    Bury specified words in the SimpleClozeFlashcards.
    Returns a dictionary of words to lists of SimpleClozeFlashcard objects.
    """
    wordsToBury: List[str] = getWordsToBury(configFilePath)
    wordToSimpleClozeFlashcards = dict(
        sorted(
            wordToSimpleClozeFlashcards.items(),
            # Bury specified words
            key=lambda item: 1 if item[0] in wordsToBury else 0
        )
    )

    return wordToSimpleClozeFlashcards