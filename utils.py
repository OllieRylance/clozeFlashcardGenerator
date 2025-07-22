import logging
from typing import Dict, List, Optional, Tuple
import json
import re

from algorithms import mostDifferentAlgorithm
from models import (
    MultiWordExpression,
    Line,
    Word,
    Punctuation,
    PunctuationWordPosition,
    ClozeFlashcard,
    SimpleClozeFlashcard,
)
from readWrite import readJsonFile, readLines

logger = logging.getLogger(__name__)

def prepareSentenceLines(inputFilePath: str) -> List[str]:
    """
    Read sentences from a file and validate them.
    Returns a list of valid sentences.
    """
    logger.info(f"Reading sentences from '{inputFilePath}'...")
    sentenceLines: List[str] = readLines(inputFilePath)

    # Check for invalid lines in the sentences file
    logger.info(f"Checking for invalid lines in '{inputFilePath}'...")

    invalidLines: List[str] = findInvalidLines(sentenceLines)

    if invalidLines:
        logger.error("Invalid sentence lines found.")

        if logger.isEnabledFor(logging.DEBUG):
            printFoundInvalidLines(invalidLines)

        # Exit the program if invalid lines are found
        exit(1)

    logger.info("Sentence lines are valid.")
    return sentenceLines

def prepareInUseClozeFlashcards(outputFilePath: str) -> None:
    """
    Prepare the in-use cloze flashcards from the output file.
    Returns a dictionary of in-use cloze flashcards.
    """
    # Try to read existing cloze flashcards from the output file
    existingClozeFlashcardsJsonFileString: Optional[str] = readJsonFile(outputFilePath)
    if existingClozeFlashcardsJsonFileString is None:
        logger.info(
            f"No existing cloze flashcards found in '{outputFilePath}'. "
            f"Starting fresh."
        )

    makeInUseClozeFlashcards(existingClozeFlashcardsJsonFileString)

def printGeneratingClozeFlashcardsInfo(
    inUseClozeFlashcards: Dict[str, List[ClozeFlashcard]],
    clozeChoosingAlgorithm: str
) -> None:
    totalInUseClozeFlashcards: int = sum(
        len(flashcards) for flashcards in inUseClozeFlashcards.values()
    )
    logger.info(
        f"Generating cloze flashcards using the '{clozeChoosingAlgorithm}' algorithm "
        f"given {totalInUseClozeFlashcards} existing cloze flashcards..."
    )

def generateClozeFlashcards(
    clozeChoosingAlgorithm: str,
    n: int,
    benefitShorterSentences: bool
) -> None:
    """
    Generate cloze flashcards based on the chosen algorithm.
    Returns a dictionary of words to lists of SimpleClozeFlashcard objects.
    """
    if logger.isEnabledFor(logging.INFO):
        printGeneratingClozeFlashcardsInfo(
            ClozeFlashcard.inUseClozeFlashcards, clozeChoosingAlgorithm
        )

    createInitialClozeFlashcards()

    for uniqueWordId in Word.uniqueWordIdToWordObjects.keys():
        # If the word already has equal or more cloze flashcards than n, skip it
        if (
            uniqueWordId in SimpleClozeFlashcard.wordToFlashcards
            and len(SimpleClozeFlashcard.wordToFlashcards[uniqueWordId]) >= n
        ):
            continue

        if clozeChoosingAlgorithm == "mostDifferent":
            mostDifferentAlgorithm(
                uniqueWordId,
                n,
                benefitShorterSentences
            )

def ensureInUseClozeFlashcardsPersist() -> None:
    for word, clozeFlashcards in ClozeFlashcard.inUseClozeFlashcards.items():
        wordToSimpleClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = (
            SimpleClozeFlashcard.wordToFlashcards
        )

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

def findInvalidLines(lines: List[str]) -> List[str]:
    """
    Find invalid lines in a list of lines.
    A line is invalid if:
    - it has multiple spaces back to back,
    - it has leading or trailing whitespace (and not just a newline), or
    - it has characters that are not letters, numbers, ",", ".", "?", "_" or " ".
    """
    invalidLines: List[str] = []

    for line in lines:
        # Check for multiple spaces, leading/trailing whitespace, and invalid characters
        if ('  ' in line or
            not all(c.isalpha() or c.isdigit() or c in '",.?_' or c.isspace() 
                   for c in line)):
            invalidLines.append(line)

    return invalidLines

def printFoundInvalidLines(invalidLines: List[str]) -> None:
    """
    Print the found invalid lines.
    """
    for line in invalidLines:
        print(f"\"{line}\"")

def createClozeFlashcardFromSimpleJsonableDict(
    clozeFlashcard: Dict[str, str]
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

    line = parseSentenceLine(lineString, addWordsToClassDict=False)
    wordIndex: int = SimpleClozeFlashcard.wordsInString(clozeFlashcard['beforeCloze'])
    clozeFlashcardInstance = ClozeFlashcard(
        line, wordIndex, clozeFlashcard['inUse'] == "True"
    )

    return clozeFlashcardInstance

def makeInUseClozeFlashcards(
    existingClozeFlashcardsJsonFileString: Optional[str]
) -> None:
    """
    Parse the existing cloze flashcards JSON file string and return a dictionary
    of in-use cloze flashcards.
    """
    if existingClozeFlashcardsJsonFileString is None:
        return

    existingClozeFlashcards: Dict[str, List[Dict[str, str]]] = {}

    try:
        existingClozeFlashcards = json.loads(
            existingClozeFlashcardsJsonFileString
        )
    except json.JSONDecodeError:
        logger.error("Error decoding JSON from clozeFlashcards.json. Starting fresh.")

    # Log the number of unique words found
    logger.debug(
        f"{len(Word.uniqueWordIdToWordObjects)} unique words "
        f"(+ multi word expressions) found in the sentences."
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
        clozeFlashcardInstance: ClozeFlashcard = (
            createClozeFlashcardFromSimpleJsonableDict(clozeFlashcard)
        )

        # Add the cloze flashcard to the in-use cloze flashcards dictionary
        uniqueWordId: str = (
            clozeFlashcardInstance.GetFirstClozeWord().getUniqueWordId()
        )
        if uniqueWordId not in ClozeFlashcard.inUseClozeFlashcards:
            ClozeFlashcard.inUseClozeFlashcards[uniqueWordId] = []
        ClozeFlashcard.inUseClozeFlashcards[uniqueWordId].append(
            clozeFlashcardInstance
        )

def addWordToClassDict(word: Word) -> None:
    # If the unique word ID is not in the dictionary, add it
    uniqueWordId: str = word.getUniqueWordId()
    if uniqueWordId not in Word.uniqueWordIdToWordObjects:
        Word.uniqueWordIdToWordObjects[uniqueWordId] = []
    Word.uniqueWordIdToWordObjects[uniqueWordId].append(word)

def getWordStringAndId(wordString: str) -> Tuple[str, int]:
    """
    Split the raw word string into parts, e.g.,
    "word_1" -> "word" and 1
    """
    parts = wordString.split('_')
    if len(parts) != 2:
        logger.error(f"Invalid word string format: {wordString}")
        return wordString, 0
    if not parts[1].isdigit():
        logger.error(f"Invalid word ID in word string: {wordString}")
        return parts[0], 0
    return parts[0], int(parts[1])

def processPunctuation(
    subString: str,
    punctuationDict: Dict[int, List[Punctuation]],
    realIndex: int
) -> Tuple[str, bool]:
    # If the subString starts or ends with a string of punctuation
    # using regex to find punctuation at the start and end
    # punctuation to look for is ",?"
    # TODO : allow more punctuation characters
    match = re.match(r'([^\w\s]*)(.*?)([^\w\s]*)$', subString)
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

def processMultiWordExpression(
    wordString: str,
    multiWordExpressions: Dict[int, MultiWordExpression]
) -> Tuple[str, Optional[MultiWordExpression]]:
    """
    Process a word string to detect multi-word expressions.
    Returns a tuple of MultiWordExpression and its index if found, otherwise None.
    """
    if '_' in wordString:
        wordString, inSentenceMultiWordExpressionId = getWordStringAndId(wordString)
        if inSentenceMultiWordExpressionId not in multiWordExpressions:
            # Create a new MultiWordExpression
            multiWordExpressions[inSentenceMultiWordExpressionId] = (
                MultiWordExpression()
            )
        
        multiWordExpression = multiWordExpressions[inSentenceMultiWordExpressionId]
        return wordString, multiWordExpression
    return wordString, None

def parseSentenceLine(line: str, addWordsToClassDict: bool = True) -> Line:
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
        wordString, multiWordExpression = processMultiWordExpression(
            wordString, multiWordExpressions
        )
        
        word: Word = Word(wordString, multiWordExpression)
        words.append(word)

        # If the word is a multi-word expression, append the word to the 
        # multi-word expression and continue as multi-word expressions are 
        # handled after the loop
        if multiWordExpression is not None:
            multiWordExpression.words.append(word)
            continue
        
        if addWordsToClassDict:
            addWordToClassDict(word)

    if addWordsToClassDict:
        for multiWordExpression in [m for m in multiWordExpressions.values()]:
            addWordToClassDict(multiWordExpression.words[0])

    return Line(words, punctuationDict)

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

def createInitialClozeFlashcards() -> None:
    wordToClozeFlashcards: Dict[str, List[SimpleClozeFlashcard]] = {}

    for word in ClozeFlashcard.inUseClozeFlashcards:
        # If the word is already in use, add the cloze flashcards to the dictionary
        if word not in wordToClozeFlashcards:
            wordToClozeFlashcards[word] = []

        for clozeFlashcard in ClozeFlashcard.inUseClozeFlashcards[word]:
            simpleClozeFlashcard: SimpleClozeFlashcard = (
                clozeFlashcard.GetSimpleClozeFlashcard()
            )
            wordToClozeFlashcards[word].append(simpleClozeFlashcard)

    SimpleClozeFlashcard.wordToFlashcards = wordToClozeFlashcards