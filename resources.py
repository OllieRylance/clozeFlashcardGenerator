from typing import List
from matplotlib.pylab import Enum

class Resources:
    """
    A class to hold various resources used in the application.
    """
    punctuationChars: str = "\",.?_"

class OutputOrder(Enum):
    ALPHABETICAL = "alphabetical"
    FREQUENCY = "frequency"
    RANDOM = "random"
    LEAST_USED_AS_CLOZE_FIRST = "leastUsedAsClozeFirst"
    LEAST_IN_USED_SENTENCES_FIRST = "leastInUsedSentencesFirst"

# TODO : add an algorithm which prioritises sentences with the 
# highest proportion of words that are either:
# - not anywhere in existing flashcards
# - not cloze words in existing flashcards
class ClozeChoosingAlgorithm(Enum):
    MOST_DIFFERENT = "mostDifferent"

class sentencePart(Enum):
    BEFORE_CLOZE = "beforeCloze"
    MID_CLOZE = "midCloze"
    AFTER_CLOZE = "afterCloze"
    CLOZE_PART_1 = "clozePart1"
    CLOZE_PART_2 = "clozePart2"

class PunctuationWordPosition(Enum):
    BEFORE = "before"
    AFTER = "after"
    ALONE = "alone"

class algorithmConfigDefaults:
    """
    Default values for the algorithm configuration.
    """
    inputFilePath: str = "defaultData/sentences.txt"
    outputFilePath: str = "defaultData/clozeFlashcards.json"
    clozeChoosingAlgorithm: ClozeChoosingAlgorithm = ClozeChoosingAlgorithm.MOST_DIFFERENT
    numFlashcardsPerWord: int = 3
    benefitShorterSentences: bool = False
    outputOrder: List[OutputOrder] = []
    wordsToBury: List[str] = []
    # TODO : add option that allows words that are already used
    # as cloze words to just output those flashcards for (save
    # processing time)
    # onlyInUseForWordsWithClozeFlashcards: bool = True

class algorithmConfigMapping:
    requiredKeys: List[str] = [
        "name",
        "file"
    ]