from dataclasses import dataclass
import logging
from typing import Dict, List, Optional, Tuple
import json

from models import (
    MultiWordExpression,
    RawLine,
    RawWord,
    PunctuationlessWord,
    ClozeFlashcard,
    SimpleClozeFlashcard,
    removePunctuation
)

logger = logging.getLogger(__name__)

def findInvalidLines(lines: List[str]) -> List[str]:
    """
    Find invalid lines in a list of lines.
    A line is invalid if:
    - it has multiple spaces back to back,
    - it has leading or trailing whitespace (and not just a newline), or
    - it has characters that are not letters, numbers, ",", ".", "~", "?", "_" or " ".
    """
    invalidLines: List[str] = []

    for line in lines:
        # Check for multiple spaces, leading/trailing whitespace, and invalid characters
        if ('  ' in line or
            not all(c.isalpha() or c.isdigit() or c in '",.~?_' or c.isspace() for c in line)):
            invalidLines.append(line)

    return invalidLines

def printFoundInvalidLines(invalidLines: List[str]) -> None:
    """
    Print the found invalid lines.
    """
    for line in invalidLines:
        print(f"\"{line}\"")

def getInUseClozeFlashcards(
    existingClozeFlashcardsJsonFileString: Optional[str]
) -> Dict[str, List[ClozeFlashcard]]:
    """
    Parse the existing cloze flashcards JSON file string and return a dictionary
    of in-use cloze flashcards.
    """
    if existingClozeFlashcardsJsonFileString is None:
        return {}

    inUseClozeFlashcards : Dict[str, List[ClozeFlashcard]] = {}

    try:
        existingClozeFlashcards: Dict[str, List[Dict[str, str]]] = json.loads(
            existingClozeFlashcardsJsonFileString
        )
        for clozeFlashcard in [
            clozeFlashcard
            for clozeFlashcards in existingClozeFlashcards.values()
            for clozeFlashcard in clozeFlashcards
        ]:
            inUse = clozeFlashcard['inUse'] == "True"
            if not bool(inUse):
                continue

            # Create a ClozeFlashcard instance
            beforeClozeWordStrings = clozeFlashcard['beforeCloze'].split()
            afterClozeWordStrings = clozeFlashcard['afterCloze'].split()
            clozeWordString = clozeFlashcard['clozeWord']

            rawWordStrings: List[str] = (
                beforeClozeWordStrings + [clozeWordString] + afterClozeWordStrings
            )
            rawWords: List[RawWord] = [RawWord(word) for word in rawWordStrings]
            rawLine: RawLine = RawLine(rawWords)
            wordIndex: int = len(beforeClozeWordStrings)
            clozeFlashcardInstance: ClozeFlashcard = ClozeFlashcard(
                rawLine, wordIndex, inUse
            )

            # Add the cloze flashcard to the in-use cloze flashcards dictionary
            punctuationlessWord = removePunctuation(clozeWordString)
            if punctuationlessWord not in inUseClozeFlashcards:
                inUseClozeFlashcards[punctuationlessWord] = []
            inUseClozeFlashcards[punctuationlessWord].append(clozeFlashcardInstance)
    except json.JSONDecodeError:
        logger.error("Error decoding JSON from clozeFlashcards.json. Starting fresh.")

    return inUseClozeFlashcards

def addPunctuationlessWord(
    punctuationlessWordString: str,
    punctuationlessWords: Dict[str, PunctuationlessWord],
    rawWord: RawWord
) -> None:
    # If the punctuationless version of the word is not in the dictionary,
    # create a new PunctuationlessWord
    if punctuationlessWordString not in punctuationlessWords:
        # Create a new PunctuationlessWord
        punctuationlessWord: PunctuationlessWord = PunctuationlessWord(
            punctuationlessWordString, rawWord
        )
        # Store the PunctuationlessWord in the dictionary
        punctuationlessWords[punctuationlessWordString] = punctuationlessWord
    else:
        # If it exists, add the raw word ID to the existing PunctuationlessWord
        punctuationlessWords[punctuationlessWordString].referenceRawWords.append(rawWord)

@dataclass
class MultiWordExpressionIndexCounter:
    MWE: MultiWordExpression
    count: int = 0

def createPunctuationlessWordsFromSentences(
    sentenceLines: List[str]
) -> Dict[str, PunctuationlessWord]:
    """
    Create PunctuationlessWord objects from a list of sentence lines.
    Returns a dictionary of PunctuationlessWord objects.
    """
    # Dictionary to store PunctuationlessWord objects
    punctuationlessWords: Dict[str, PunctuationlessWord] = {}

    # Read the file and process each line
    for line in sentenceLines:
        wordsInLine: List[str] = line.split()
        currentRawWords: List[RawWord] = []
        currentMultiWordExpressions: Dict[str, MultiWordExpressionIndexCounter] = {}

        for rawWordString in wordsInLine:
            # Detect multi-word expressions
            multiWordExpressionInfo: Optional[Tuple['MultiWordExpression', int]] = None
            if '_' in rawWordString:
                parts: List[str] = rawWordString.split('_')
                rawWordString = parts[0]
                inSentenceMWEId = parts[1]
                if inSentenceMWEId not in currentMultiWordExpressions:
                    # Create a new MultiWordExpression
                    currentMultiWordExpressions[inSentenceMWEId] = MultiWordExpressionIndexCounter(MultiWordExpression())
                multiWordExpressionInfo = (
                    currentMultiWordExpressions[inSentenceMWEId].MWE,
                    currentMultiWordExpressions[inSentenceMWEId].count
                )
                currentMultiWordExpressions[inSentenceMWEId].count += 1

            rawWord: RawWord = RawWord(rawWordString, multiWordExpressionInfo)
            currentRawWords.append(rawWord)

            # If the raw word is a multi-word expression, append the raw word to the multi-word expression and
            # add it to the punctuationless words dictionary after the loop
            if multiWordExpressionInfo is not None:
                multiWordExpressionInfo[0].rawWords.append(rawWord)
                continue

            # Remove punctuation from the raw word
            punctuationlessWordString: str = removePunctuation(rawWordString)

            addPunctuationlessWord(
                punctuationlessWordString,
                punctuationlessWords,
                rawWord
            )

        # If there are multi-word expressions, add them to the punctuationless words dictionary
        for multiWordExpression in [counter.MWE for counter in currentMultiWordExpressions.values()]:
            addPunctuationlessWord(
                multiWordExpression.getPunctuationlessWordString(),
                punctuationlessWords,
                multiWordExpression.rawWords[0]
            )

        # Create a new RawLine instance which stores itself in the raw words
        RawLine(currentRawWords)

    # Log the number of unique words found
    logger.debug(f"{len(punctuationlessWords)} unique words found in the sentences.")

    # Sort the keys into alphabetical order
    punctuationlessWords = dict(sorted(punctuationlessWords.items(), key=lambda item: item[0]))

    return punctuationlessWords

def convertToJsonableFormat(
    wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]]
) -> Dict[str, List[Dict[str, str]]]:
    """
    Convert the word to SimpleClozeFlashcard dictionary to a JSON-serializable format.
    Returns a dictionary of words to lists of dictionaries representing SimpleClozeFlashcards.
    """
    wordToJsonableClozeFlashcards: Dict[str, List[Dict[str, str]]] = {}

    for word, simpleClozeFlashcards in wordToSimpleClozeFlashcards.items():
        jsonableFlashcards: List[Dict[str, str]] = []
        for simpleClozeFlashcard in simpleClozeFlashcards:
            jsonableFlashcards.append(simpleClozeFlashcard.toDict())
        wordToJsonableClozeFlashcards[word] = jsonableFlashcards

    return wordToJsonableClozeFlashcards

def createInitialClozeFlashcards(
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]]
) -> Dict[str, List[SimpleClozeFlashcard]]:
    wordToClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = {}

    for word in inUseClozeFlashcards:
        # If the word is already in use, add the cloze flashcards to the dictionary
        if word not in wordToClozeFlashcards:
            wordToClozeFlashcards[word] = []

        for clozeFlashcard in inUseClozeFlashcards[word]:
            # Get the SimpleClozeFlashcard representation of the ClozeFlashcard
            simpleClozeFlashcard = clozeFlashcard.GetSimpleClozeFlashcard()

            wordToClozeFlashcards[word].append(simpleClozeFlashcard)

    return wordToClozeFlashcards