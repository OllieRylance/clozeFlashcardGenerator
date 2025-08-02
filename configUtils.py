import logging
import json
import os
from typing import Any, List, Optional

from readWrite import readJsonFile, writeJsonFile
from resources import (
    ClozeChoosingAlgorithm,
    OutputOrder,
    generatorConfigDefaults,
    generatorConfigMapping
)

logger = logging.getLogger(__name__)

def validateConfigObject(config: Any) -> bool:
    """
    Validates the configuration object.
    """
    requiredKeys: List[str] = generatorConfigMapping.requiredKeys
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
    if configs:
        logger.error("Invalid currentConfigIndex, resetting to first config")
        appConfigJson["currentConfigIndex"] = 0
        writeJsonFile("appConfig.json", appConfigJson)
        return configs[0].get("name", "unknown")
    
    logger.error("No configs available, creating default config")
    defaultConfig = {
        "name": "default",
        "file": "default.json"
    }
    appConfigJson["configs"] = [defaultConfig]
    appConfigJson["currentConfigIndex"] = 0
    writeJsonFile("appConfig.json", appConfigJson)

    defaultConfigContent = {}
    defaultConfigFilePath = getConfigFilePath("default")
    writeJsonFile(defaultConfigFilePath, defaultConfigContent)

    return defaultConfig.get("name", "unknown")

def getAppConfigJson() -> Any:
    appConfigJsonString: Optional[str] = readJsonFile("appConfig.json")
    if appConfigJsonString is None:
        # TODO : when reaching this point automatically create an
        # appConfig.json file with a default config
        return "error: appConfig.json not found"
    
    return json.loads(appConfigJsonString)

def getConfigFilePath(configName: str) -> str:
    appConfigJson = getAppConfigJson()
    configs = appConfigJson.get("configs", [])
    
    if not configs:
        return os.path.join("generatorConfigs", configName + ".json")
    
    for config in configs:
        if config.get("name") == configName:
            configFileName: Optional[str] = config.get("file")
            if not configFileName:
                configFileName = configName + ".json"
            return os.path.join("generatorConfigs", configFileName)
    
    return os.path.join("generatorConfigs", configName + ".json")

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

def getConfigJson(configFilePath: str) -> Any:
    """
    Returns the algorithm configuration from the specified file.
    """
    configJsonString: Optional[str] = readJsonFile(configFilePath)
    if configJsonString is None:
        logger.error(f"Config file {configFilePath} not found")
        setCurrentConfig("default")
        return getConfigJson(getConfigFilePath("default"))
    
    try:
        configJson = json.loads(configJsonString)
        return configJson
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse config file {configFilePath}: {e}")
        return None

def createConfigMapping(configName: str, configFilePath: str) -> None:
    """
    Creates a mapping for the configuration in the appConfig.json.
    """
    appConfigJson = getAppConfigJson()
    configs = appConfigJson.get("configs", [])
    
    # Check if the config already exists
    for config in configs:
        if config.get("name") == configName:
            logger.info(f"Config '{configName}' already exists")
            return
    
    # Add new config mapping
    newConfig = {
        "name": configName,
        "file": configFilePath
    }
    configs.append(newConfig)
    writeJsonFile("appConfig.json", appConfigJson)
    logger.info(f"Created new config mapping for: {configName}")

def createNewConfigName() -> str:
    existingConfigNames: List[str] = getConfigList()

    newConfigNumber: int = 1
    newConfigName: str = f"new_config_{newConfigNumber}"
    while newConfigName in existingConfigNames:
        newConfigNumber += 1
        newConfigName = f"new_config_{newConfigNumber}"

    return newConfigName

def createAndUseNewConfig() -> str:
    defaultConfig = getConfigJson(getConfigFilePath("default"))
    if defaultConfig is None:
        logger.error("Failed to load default config")
        # Create a default and continue
        return ""

    newConfigName: str = createNewConfigName()
    
    newConfigFilePath = getConfigFilePath(newConfigName)
    writeJsonFile(newConfigFilePath, defaultConfig)

    newConfigFile: str = f"{newConfigName}.json"
    createConfigMapping(newConfigName, newConfigFile)

    setCurrentConfig(newConfigName)

    return newConfigName

def getInputFilePath(configFilePath: str) -> str:
    """
    Returns the input file path from the configuration file.
    """
    configJson = getConfigJson(configFilePath)
    if configJson is None:
        return generatorConfigDefaults.inputFilePath
    return configJson.get("inputFilePath", generatorConfigDefaults.inputFilePath)

def getOutputFilePath(configFilePath: str) -> str:
    """
    Returns the output file path from the configuration file.
    """
    configJson = getConfigJson(configFilePath)
    if configJson is None:
        return generatorConfigDefaults.outputFilePath
    return configJson.get("outputFilePath", generatorConfigDefaults.outputFilePath)

def getClozeChoosingAlgorithm(configFilePath: str) -> ClozeChoosingAlgorithm:
    """
    Returns the cloze choosing algorithm from the configuration file.
    """
    configJson = getConfigJson(configFilePath)
    if configJson is None:
        return generatorConfigDefaults.clozeChoosingAlgorithm
    clozeChoosingAlgorithmString: Optional[str] = configJson.get("clozeChoosingAlgorithm")
    return (
        ClozeChoosingAlgorithm(clozeChoosingAlgorithmString)
        if clozeChoosingAlgorithmString else generatorConfigDefaults.clozeChoosingAlgorithm
    )

def getNumFlashcardsPerWord(configFilePath: str) -> int:
    """
    Returns the number of flashcards per word from the configuration file.
    """
    configJson = getConfigJson(configFilePath)
    if configJson is None:
        return generatorConfigDefaults.numFlashcardsPerWord
    return configJson.get("numFlashcardsPerWord", generatorConfigDefaults.numFlashcardsPerWord)

def getBenefitShorterSentences(configFilePath: str) -> bool:
    """
    Returns whether to benefit shorter sentences from the configuration file.
    """
    configJson = getConfigJson(configFilePath)
    if configJson is None:
        return generatorConfigDefaults.benefitShorterSentences
    return configJson.get("benefitShorterSentences", generatorConfigDefaults.benefitShorterSentences)

def getOutputOrder(configFilePath: str) -> List[OutputOrder]:
    """
    Returns the output order from the configuration file.
    """
    configJson = getConfigJson(configFilePath)
    if configJson is None:
        return generatorConfigDefaults.outputOrder
    outputOrderStrings: List[str] = configJson.get("outputOrder", [])
    return [
        # TODO : handle invalid output order strings
        OutputOrder(order) for order in outputOrderStrings
    ] or generatorConfigDefaults.outputOrder

def getWordsToBury(configFilePath: str) -> List[str]:
    """
    Returns the list of words to bury from the configuration file.
    """
    configJson = getConfigJson(configFilePath)
    if configJson is None:
        return generatorConfigDefaults.wordsToBury
    return configJson.get("wordsToBury", generatorConfigDefaults.wordsToBury)

def updateConfigFile(configName: str, update: Any) -> None:
    """
    Updates the configuration file with the given update dictionary.
    """
    # TODO : add error handling
    configFilePath: str = getConfigFilePath(configName)
    configJson = getConfigJson(configFilePath)
    # TODO : error handling
    configJson.update(update)
    writeJsonFile(configFilePath, configJson)

def setConfigInputFile(configName: str, path: str) -> None:
    """
    Sets the input file path for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"inputFilePath": path})

def setConfigOutputFile(configName: str, path: str) -> None:
    """
    Sets the output file path for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"outputFilePath": path})

def setConfigAlgorithm(configName: str, algorithm: str) -> None:
    """
    Sets the cloze choosing algorithm for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"clozeChoosingAlgorithm": algorithm})

def setConfigFlashcardsPerWord(configName: str, count: int) -> None:
    """
    Sets the number of flashcards per word for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"numFlashcardsPerWord": count})

def setConfigBenefitShorter(configName: str, enabled: bool) -> None:
    """
    Enables or disables benefiting shorter sentences for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"benefitShorterSentences": enabled})

def setConfigOutputOrder(configName: str, orders: List[str]) -> None:
    """
    Sets the output order for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"outputOrder": list(orders)})

def addBuryWordToConfig(configName: str, word: str) -> None:
    """
    Adds a word to the bury list in the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        configName = createAndUseNewConfig()
    currentWordsToBury = getWordsToBury(getConfigFilePath(configName))
    if word not in currentWordsToBury:
        currentWordsToBury.append(word)
        updateConfigFile(configName, {"wordsToBury": currentWordsToBury})

def removeBuryWordFromConfig(configName: str, word: str) -> None:
    """
    Removes a word from the bury list in the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        configName = createAndUseNewConfig()
    currentWordsToBury = getWordsToBury(getConfigFilePath(configName))
    if word in currentWordsToBury:
        currentWordsToBury.remove(word)
        updateConfigFile(configName, {"wordsToBury": currentWordsToBury})