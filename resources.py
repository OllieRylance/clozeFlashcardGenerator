from matplotlib.pylab import Enum

class Resources:
    """
    A class to hold various resources used in the application.
    """
    punctuationChars = "\",.?_"

class OutputOrder(Enum):
    ALPHABETICAL = "alphabetical"
    FREQUENCY = "frequency"
    RANDOM = "random"
    LEAST_USED_FIRST = "leastUsedFirst"

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