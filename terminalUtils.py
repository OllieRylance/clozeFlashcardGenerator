import logging

from main import main

logger = logging.getLogger(__name__)

def runAlgorithm(configFilePath: str) -> None:
    """
    Runs the algorithm with the configuration specified in the config file.
    """
    main(
        configFilePath
    )