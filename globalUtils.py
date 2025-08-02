from typing import Dict, List, Optional, Tuple
import logging
import json
import re

from models import (
    Word, ClozeFlashcard, SimpleClozeFlashcard, Line,
    Punctuation, MultiWordExpression
)
from configUtils import getInputFilePath, getOutputFilePath
from readWrite import readLines, readJsonFile
from resources import Resources, PunctuationWordPosition

logger = logging.getLogger(__name__)

def getUniqueWordIdToWordObjects(configFilePath: str) -> Dict[str, List[Word]]:
    """
    Get a mapping of unique word IDs to their corresponding Word objects.
    """
    inputFilePath: str = getInputFilePath(configFilePath)
    sentenceLines: Optional[List[str]] = prepareSentenceLines(inputFilePath)

    if sentenceLines is None:
        return {}

    uniqueWordIdToWordObjects: Dict[str, List[Word]] = {}

    for line in sentenceLines:
        parseSentenceLine(
            line,
            uniqueWordIdToWordObjects
        )

    return uniqueWordIdToWordObjects

def createInitialClozeFlashcards(
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]]
) -> Dict[str, List[SimpleClozeFlashcard]]:
    wordToClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = {}

    for word in inUseClozeFlashcards:
        # If the word is already in use, add the cloze flashcards to the dictionary
        if word not in wordToClozeFlashcards:
            wordToClozeFlashcards[word] = []

        for clozeFlashcard in inUseClozeFlashcards[word]:
            simpleClozeFlashcard: SimpleClozeFlashcard = (
                clozeFlashcard.getSimpleClozeFlashcard()
            )
            wordToClozeFlashcards[word].append(simpleClozeFlashcard)

    return wordToClozeFlashcards

def getInUseClozeFlashcards(configFilePath: str) -> Dict[str, List[ClozeFlashcard]]:
    """
    Get a mapping of unique word IDs to their corresponding in-use ClozeFlashcard objects.
    """
    outputFilePath: str = getOutputFilePath(configFilePath)

    # Try to read existing cloze flashcards from the output file
    existingClozeFlashcardsJsonFileString: Optional[str] = readJsonFile(outputFilePath)
    if existingClozeFlashcardsJsonFileString is None:
        logger.info(
            "No existing cloze flashcards found in '%s'. "
            "Starting fresh.",
            outputFilePath
        )
        return {}

    return makeInUseClozeFlashcards(
        configFilePath,
        existingClozeFlashcardsJsonFileString,
    )

def prepareSentenceLines(inputFilePath: str) -> Optional[List[str]]:
    """
    Read sentences from a file and validate them.
    Returns a list of valid sentences.
    """
    logger.info("Reading sentences from '%s'...", inputFilePath)
    sentenceLines: List[str] = readLines(inputFilePath)

    # Check for invalid lines in the sentences file
    logger.info("Checking for invalid lines in '%s'...", inputFilePath)

    invalidLines: List[str] = findInvalidLines(sentenceLines)

    if invalidLines:
        logger.error("Invalid sentence lines found.")

        if logger.isEnabledFor(logging.DEBUG):
            printFoundInvalidLines(invalidLines)

        return None

    logger.info("Sentence lines are valid.")
    return sentenceLines

def parseSentenceLine(
        line: str,
        uniqueWordIdToWordObjects: Dict[str, List[Word]],
        addWordsToClassDict: bool = True
    ) -> Line:
    subStrings: List[str] = line.split()
    words: List[Word] = []
    punctuationDict: Dict[int, List[Punctuation]] = {}
    alonePunctuation: int = 0
    multiWordExpressions: Dict[int, MultiWordExpression] = {}
    for index, subString in enumerate(subStrings):
        realIndex = index - alonePunctuation
        # Deal with punctuation
        wordString, alonePunctuationFound = processPunctuation(
            subString, punctuationDict, realIndex
        )
        if alonePunctuationFound:
            alonePunctuation += 1
            continue

        # Detect multi-word expressions
        wordString, multiWordExpression = processMultiWordExpressions(
            wordString, multiWordExpressions
        )

        word: Word = Word(wordString, multiWordExpression)
        words.append(word)

        multiWordExpression.words.append(word)

    if addWordsToClassDict:
        for multiWordExpression in list(multiWordExpressions.values()):
            addWordToClassDict(
                multiWordExpression.words[0], uniqueWordIdToWordObjects
            )

    return Line(words, punctuationDict)

def findInvalidLines(lines: List[str]) -> List[str]:
    """
    Find invalid lines in a list of lines.
    A line is invalid if:
    - it has no words,
    - it has multiple spaces back to back,
    - it has leading or trailing whitespace (and not just a newline), or
    - it has characters that are not letters, numbers, " ", "_", or valid
      punctuation in the punctuation characters resource.
    """
    invalidLines: List[str] = []

    for line in lines:
        # Check for multiple spaces, leading/trailing whitespace, and invalid characters
        if (not any(c.isalpha() for c in line) or
            '  ' in line or
            not all(c.isalpha() or c.isdigit() or c.isspace() or c == "_"
                   or c in Resources.punctuationChars for c in line)):
            invalidLines.append(line)

    return invalidLines

def printFoundInvalidLines(invalidLines: List[str]) -> None:
    """
    Print the found invalid lines.
    """
    for line in invalidLines:
        print(f"\"{line}\"")

def makeInUseClozeFlashcards(
    configFilePath: str,
    existingClozeFlashcardsJsonFileString: str
) -> Dict[str, List[ClozeFlashcard]]:
    """
    Parse the existing cloze flashcards JSON file string and return a dictionary
    of in-use cloze flashcards.
    """
    existingClozeFlashcards: Dict[str, List[Dict[str, str]]] = {}

    try:
        existingClozeFlashcards = json.loads(
            existingClozeFlashcardsJsonFileString
        )
    except json.JSONDecodeError:
        logger.error("Error decoding JSON from clozeFlashcards.json. Starting fresh.")

    uniqueWordIdToWordObjects: Dict[str, List[Word]] = (
        getUniqueWordIdToWordObjects(configFilePath)
    )

    # Log the number of unique words found
    logger.debug(
        "%d unique words "
        "(+ multi word expressions) found in the sentences.",
        len(uniqueWordIdToWordObjects)
    )

    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]] = {}

    for clozeFlashcard in [
        clozeFlashcard
        for clozeFlashcards in existingClozeFlashcards.values()
        for clozeFlashcard in clozeFlashcards
    ]:
        inUse = clozeFlashcard['inUse'] == "True"
        if not bool(inUse):
            continue

        # Create a ClozeFlashcard instance
        clozeFlashcardInstance: ClozeFlashcard = (
            createClozeFlashcardFromSimpleJsonableDict(
                clozeFlashcard,
                uniqueWordIdToWordObjects
            )
        )

        # Add the cloze flashcard to the in-use cloze flashcards dictionary
        uniqueWordId: str = (
            clozeFlashcardInstance.getFirstClozeWord().getUniqueWordId()
        )
        if uniqueWordId not in inUseClozeFlashcards:
            inUseClozeFlashcards[uniqueWordId] = []
        inUseClozeFlashcards[uniqueWordId].append(
            clozeFlashcardInstance
        )

    return inUseClozeFlashcards

def processPunctuation(
    subString: str,
    punctuationDict: Dict[int, List[Punctuation]],
    realIndex: int
) -> Tuple[str, bool]:
    # If the subString starts or ends with a string of punctuation
    # using regex to find punctuation at the start and end
    # punctuation to look for is in the punctuation characters resource
    allowedPunctuation = Resources.punctuationChars
    pattern = f"([{re.escape(allowedPunctuation)}]*)(.*?)([{re.escape(allowedPunctuation)}]*)$"
    match = re.match(pattern, subString)
    if not match:
        return subString, False

    if realIndex not in punctuationDict:
        punctuationDict[realIndex] = []
    if match.group(2) == "":
        # If the word is just punctuation, treat it as alone punctuation
        punctuationDict[realIndex].append(
            Punctuation(
                match.group(1) + match.group(3),
                PunctuationWordPosition.ALONE
            )
        )
        return "", True
    wordString = match.group(2)
    if match.group(1):
        # If there is punctuation at the start, add it before the word
        punctuationDict[realIndex].append(
            Punctuation(match.group(1), PunctuationWordPosition.BEFORE)
        )
    if match.group(3):
        # If there is punctuation at the end, add it after the word
        punctuationDict[realIndex].append(
            Punctuation(match.group(3), PunctuationWordPosition.AFTER)
        )

    return wordString, False

def processMultiWordExpressions(
    wordString: str,
    multiWordExpressions: Dict[int, MultiWordExpression]
) -> Tuple[str, MultiWordExpression]:
    """
    Process a word string to detect multi-word expressions.
    Returns a tuple of MultiWordExpression and its index if found, otherwise None.
    """

    inSentenceMultiWordExpressionId: int = -1
    if '_' in wordString:
        wordString, inSentenceMultiWordExpressionId = getWordStringAndId(wordString)
    else:
        currentLowestExpressionId = min(
            multiWordExpressions.keys(),
            default=1
        )
        if currentLowestExpressionId < 0:
            inSentenceMultiWordExpressionId = currentLowestExpressionId - 1
        else:
            inSentenceMultiWordExpressionId = -1

    if inSentenceMultiWordExpressionId not in multiWordExpressions:
        # Create a new MultiWordExpression
        multiWordExpressions[inSentenceMultiWordExpressionId] = (
            MultiWordExpression()
        )

    multiWordExpression = multiWordExpressions[inSentenceMultiWordExpressionId]
    return wordString, multiWordExpression

def addWordToClassDict(
        word: Word,
        uniqueWordIdToWordObjects: Dict[str, List[Word]]
    ) -> None:
    # If the unique word ID is not in the dictionary, add it
    uniqueWordId: str = word.getUniqueWordId()
    if uniqueWordId not in uniqueWordIdToWordObjects:
        uniqueWordIdToWordObjects[uniqueWordId] = []
    uniqueWordIdToWordObjects[uniqueWordId].append(word)

def createClozeFlashcardFromSimpleJsonableDict(
    clozeFlashcard: Dict[str, str],
    uniqueWordIdToWordObjects: Dict[str, List[Word]]
) -> ClozeFlashcard:
    """
    Create a ClozeFlashcard from a simple JSON-serializable dictionary.
    """
    clozeWordsPart1: List[str] = [
        Word.addClozeIdToString(word, 1)
        for word in clozeFlashcard['clozeWordPart1'].split()
    ]
    clozeWordsPart2: List[str] = [
        Word.addClozeIdToString(word, 1)
        for word in clozeFlashcard['clozeWordPart2'].split()
    ]
    lineString: str = (
        clozeFlashcard['beforeCloze']
        + ' '.join(clozeWordsPart1)
        + clozeFlashcard['midCloze']
        + ' '.join(clozeWordsPart2)
        + clozeFlashcard['afterCloze']
    )

    line = parseSentenceLine(lineString, uniqueWordIdToWordObjects, addWordsToClassDict=False)
    wordIndex: int = SimpleClozeFlashcard.wordsInString(clozeFlashcard['beforeCloze'])
    clozeFlashcardInstance = ClozeFlashcard(
        line, wordIndex, clozeFlashcard['inUse'] == "True"
    )

    return clozeFlashcardInstance

def getWordStringAndId(wordString: str) -> Tuple[str, int]:
    """
    Split the word string into parts, e.g.,
    "word_1" -> "word" and 1
    """
    parts = wordString.split('_')
    if len(parts) != 2:
        logger.error("Invalid word string format: %s", wordString)
        return wordString, 0
    if not parts[1].isdigit():
        logger.error("Invalid word ID in word string: %s", wordString)
        return parts[0], 0
    return parts[0], int(parts[1])
