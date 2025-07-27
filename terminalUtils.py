import logging
import json
import os
from typing import Any, List, Optional

from readWrite import readJsonFile
from resources import ClozeChoosingAlgorithm, OutputOrder
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
    appConfigJsonString: Optional[str] = readJsonFile("appConfig.json")
    if appConfigJsonString is None:
        #TODO : create an appConfig.json file with a default config
        return ["error: appConfig.json not found"]

    appConfigJson = json.loads(appConfigJsonString)
    return [
        config.get("name")
        for config in appConfigJson.get("configs", [])
        if validateConfigObject(config)
    ]

def getCurrentConfigName() -> str:
    """
    Returns the name of the currently active configuration.
    """
    appConfigJsonString: Optional[str] = readJsonFile("appConfig.json")
    if appConfigJsonString is None:
        return "error: appConfig.json not found"
    
    appConfigJson = json.loads(appConfigJsonString)
    currentConfigIndex = appConfigJson.get("currentConfigIndex", 0)
    configs = appConfigJson.get("configs", [])
    if 0 <= currentConfigIndex < len(configs):
        return configs[currentConfigIndex].get("name", "unknown")
    # TODO : make the currentConfigIndex the first config if there is a
    # first config. else, create a default config amd set it as current
    return "error: invalid currentConfigIndex"

def getCurrentConfigFilePath() -> str:
    """
    Returns the file path of the currently active configuration.
    """
    appConfigJsonString: Optional[str] = readJsonFile("appConfig.json")
    if appConfigJsonString is None:
        return "error: appConfig.json not found"
    
    appConfigJson = json.loads(appConfigJsonString)
    currentConfigName: str = getCurrentConfigName()
    configs = appConfigJson.get("configs", [])
    if not configs:
        return "error: no configs available"
    for config in configs:
        if config.get("name") == currentConfigName:
            configFileName: Optional[str] = config.get("file")
            if not configFileName:
                return "error: config file name not found"
            return os.path.join("algorithmConfigs", configFileName)
    return "error: current config file not found"

def runAlgorithm(configFilePath: str) -> None:
    configJsonString: Optional[str] = readJsonFile(configFilePath)
    if configJsonString is None:
        logger.error(f"Config file {configFilePath} not found")
        return
    
    configJson = json.loads(configJsonString)

    inputFilePath: str = configJson.get("inputFilePath", "")
    outputFilePath: str = configJson.get("outputFilePath", "")
    clozeChoosingAlgorithmString: Optional[str] = configJson.get("clozeChoosingAlgorithm")
    clozeChoosingAlgorithm: ClozeChoosingAlgorithm = (
        ClozeChoosingAlgorithm(clozeChoosingAlgorithmString)
        if clozeChoosingAlgorithmString else ClozeChoosingAlgorithm.MOST_DIFFERENT
    )
    numFlashcardsPerWord: int = configJson.get("numFlashcardsPerWord", 0)
    benefitShorterSentences: bool = configJson.get("benefitShorterSentences", False)
    outputOrderStrings: List[str] = configJson.get("outputOrder", [])
    outputOrder: List[OutputOrder] = [ # TODO : handle invalid outputOrder strings
        OutputOrder(order) for order in outputOrderStrings
    ] or [OutputOrder.ALPHABETICAL]
    existingOutputFilePath: Optional[str] = configJson.get("existingOutputFilePath", "Same")
    wordsToBury: Optional[List[str]] = configJson.get("wordsToBury", None)

    main(
        inputFilePath,
        outputFilePath,
        clozeChoosingAlgorithm,
        numFlashcardsPerWord,
        benefitShorterSentences,
        outputOrder,
        existingOutputFilePath,
        wordsToBury
    )