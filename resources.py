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
    LEAST_USED_AS_CLOZE_FIRST = "least-used-as-cloze-first"
    LEAST_IN_USED_SENTENCES_FIRST = "least-in-used-sentences-first"

    @staticmethod
    def getTerminalOptions() -> List[str]:
        """
        Returns a list of terminal options for the output order.
        """
        return [order.value for order in OutputOrder]

class ClozeChoosingAlgorithm(Enum):
    FIRST_SENTENCES_FIRST = "first-sentences-first"
    MOST_DIFFERENT = "most-different"
    HIGHEST_PROPORTION_OF_NEW_WORDS = "highest-proportion-of-new-words"

    @staticmethod
    def getTerminalOptions() -> List[str]:
        """
        Returns a list of terminal options for the cloze choosing algorithm.
        """
        return [algorithm.value for algorithm in ClozeChoosingAlgorithm]

class SentencePart(Enum):
    BEFORE_CLOZE = "beforeCloze"
    MID_CLOZE = "midCloze"
    AFTER_CLOZE = "afterCloze"
    CLOZE_PART_1 = "clozePart1"
    CLOZE_PART_2 = "clozePart2"

class PunctuationWordPosition(Enum):
    BEFORE = "before"
    AFTER = "after"
    ALONE = "alone"

class GeneratorConfigDefaults:
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

class GeneratorConfigMapping:
    requiredKeys: List[str] = [
        "name",
        "file"
    ]
