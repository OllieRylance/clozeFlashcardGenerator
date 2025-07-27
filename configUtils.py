import logging
import json
import os
from typing import Any, List, Optional

from readWrite import readJsonFile, writeJsonFile
from resources import ClozeChoosingAlgorithm, OutputOrder, algorithmConfigDefaults
from main import main

logger = logging.getLogger(__name__)

def validateConfigObject(config: Any) -> bool:
    """
    Validates the configuration object.
    """
    requiredKeys = [
        "name",
        "file"
    ]
    return all(
        config.get(key) is not None for key in requiredKeys
    )

def getConfigList() -> List[str]:
    """
    Returns a list of configuration file names.
    """
    appConfigJson = getAppConfigJson()
    return [
        config.get("name")
        for config in appConfigJson.get("configs", [])
        if validateConfigObject(config)
    ]

def getCurrentConfigName() -> str:
    """
    Returns the name of the currently active configuration.
    """
    appConfigJson = getAppConfigJson()
    currentConfigIndex = appConfigJson.get("currentConfigIndex", 0)
    configs = appConfigJson.get("configs", [])
    if 0 <= currentConfigIndex < len(configs):
        return configs[currentConfigIndex].get("name", "unknown")
    # TODO : make the currentConfigIndex the first config if there is a
    # first config. else, create a default config amd set it as current
    return "error: invalid currentConfigIndex"

def getAppConfigJson() -> Any:
    appConfigJsonString: Optional[str] = readJsonFile("appConfig.json")
    if appConfigJsonString is None:
        #TODO : create an appConfig.json file with a default config
        return "error: appConfig.json not found"
    
    return json.loads(appConfigJsonString)

def getConfigFilePath(configName: str) -> str:
    appConfigJson = getAppConfigJson()
    configs = appConfigJson.get("configs", [])
    if not configs:
        return "error: no configs available"
    for config in configs:
        if config.get("name") == configName:
            configFileName: Optional[str] = config.get("file")
            if not configFileName:
                return "error: config file name not found"
            return os.path.join("algorithmConfigs", configFileName)
    return "error: current config file not found"

def getCurrentConfigFilePath() -> str:
    """
    Returns the file path of the currently active configuration.
    """
    currentConfigName: str = getCurrentConfigName()
    return getConfigFilePath(currentConfigName)

def setCurrentConfig(name: str) -> None:
    """
    Sets the currently active configuration by name.
    """
    appConfigJson = getAppConfigJson()
    configs = appConfigJson.get("configs", [])
    if not configs:
        logger.error("No configs available")
        return
    
    for index, config in enumerate(configs):
        if config.get("name") == name:
            appConfigJson["currentConfigIndex"] = index
            writeJsonFile("appConfig.json", appConfigJson)
            logger.info(f"Current config set to: {name}")
            return
    logger.error(f"Config '{name}' not found")

def getAlgorithmConfig(configFilePath: str) -> Any:
    """
    Returns the algorithm configuration from the specified file.
    """
    configJsonString: Optional[str] = readJsonFile(configFilePath)
    if configJsonString is None:
        logger.error(f"Config file {configFilePath} not found")
        return getAlgorithmConfig(getConfigFilePath("default"))
    
    try:
        configJson = json.loads(configJsonString)
        return configJson
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse config file {configFilePath}: {e}")
        return None

def getInputFilePath(configFilePath: str) -> str:
    """
    Returns the input file path from the configuration file.
    """
    algorithmConfig = getAlgorithmConfig(configFilePath)
    if algorithmConfig is None:
        return algorithmConfigDefaults.inputFilePath
    return algorithmConfig.get("inputFilePath", algorithmConfigDefaults.inputFilePath)

def getOutputFilePath(configFilePath: str) -> str:
    """
    Returns the output file path from the configuration file.
    """
    algorithmConfig = getAlgorithmConfig(configFilePath)
    if algorithmConfig is None:
        return algorithmConfigDefaults.outputFilePath
    return algorithmConfig.get("outputFilePath", algorithmConfigDefaults.outputFilePath)

def getClozeChoosingAlgorithm(configFilePath: str) -> ClozeChoosingAlgorithm:
    """
    Returns the cloze choosing algorithm from the configuration file.
    """
    algorithmConfig = getAlgorithmConfig(configFilePath)
    if algorithmConfig is None:
        return algorithmConfigDefaults.clozeChoosingAlgorithm
    clozeChoosingAlgorithmString: Optional[str] = algorithmConfig.get("clozeChoosingAlgorithm")
    return (
        ClozeChoosingAlgorithm(clozeChoosingAlgorithmString)
        if clozeChoosingAlgorithmString else algorithmConfigDefaults.clozeChoosingAlgorithm
    )

def getNumFlashcardsPerWord(configFilePath: str) -> int:
    """
    Returns the number of flashcards per word from the configuration file.
    """
    algorithmConfig = getAlgorithmConfig(configFilePath)
    if algorithmConfig is None:
        return algorithmConfigDefaults.numFlashcardsPerWord
    return algorithmConfig.get("numFlashcardsPerWord", algorithmConfigDefaults.numFlashcardsPerWord)

def getBenefitShorterSentences(configFilePath: str) -> bool:
    """
    Returns whether to benefit shorter sentences from the configuration file.
    """
    algorithmConfig = getAlgorithmConfig(configFilePath)
    if algorithmConfig is None:
        return algorithmConfigDefaults.benefitShorterSentences
    return algorithmConfig.get("benefitShorterSentences", algorithmConfigDefaults.benefitShorterSentences)

def getOutputOrder(configFilePath: str) -> List[OutputOrder]:
    """
    Returns the output order from the configuration file.
    """
    algorithmConfig = getAlgorithmConfig(configFilePath)
    if algorithmConfig is None:
        return algorithmConfigDefaults.outputOrder
    outputOrderStrings: List[str] = algorithmConfig.get("outputOrder", [])
    return [
        OutputOrder(order) for order in outputOrderStrings
        if order in OutputOrder.__members__
    ] or algorithmConfigDefaults.outputOrder

def runAlgorithm(configFilePath: str) -> None:
    configJsonString: Optional[str] = readJsonFile(configFilePath)
    if configJsonString is None:
        logger.error(f"Config file {configFilePath} not found")
        return
    
    configJson = json.loads(configJsonString)

    inputFilePath: str = configJson.get("inputFilePath", "sentences.txt")
    outputFilePath: str = configJson.get("outputFilePath", "clozeFlashcards.json")
    clozeChoosingAlgorithmString: Optional[str] = configJson.get("clozeChoosingAlgorithm")
    clozeChoosingAlgorithm: ClozeChoosingAlgorithm = (
        ClozeChoosingAlgorithm(clozeChoosingAlgorithmString)
        if clozeChoosingAlgorithmString else ClozeChoosingAlgorithm.MOST_DIFFERENT
    )
    numFlashcardsPerWord: int = configJson.get("numFlashcardsPerWord", 3)
    benefitShorterSentences: bool = configJson.get("benefitShorterSentences", False)
    outputOrderStrings: List[str] = configJson.get("outputOrder", [])
    outputOrder: List[OutputOrder] = [ # TODO : handle invalid outputOrder strings
        OutputOrder(order) for order in outputOrderStrings
    ] or []
    wordsToBury: List[str] = configJson.get("wordsToBury", [])

    main(
        inputFilePath,
        outputFilePath,
        clozeChoosingAlgorithm,
        numFlashcardsPerWord,
        benefitShorterSentences,
        outputOrder,
        wordsToBury
    )