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

def writeAppConfigJsonFile(appConfigJson: Any) -> None:
    """
    Writes the appConfig.json file with the provided JSON object.
    """
    writeJsonFile("appConfig.json", appConfigJson)

def resetConfigsList() -> None:
    appConfigJson = getAppConfigJson()
    appConfigJson["configs"] = [
        {
            "name": "default",
            "file": "default.json"
        }
    ]
    writeAppConfigJsonFile(appConfigJson)

def resetCurrentConfigIndex() -> None:
    appConfigJson = getAppConfigJson()
    appConfigJson["currentConfigIndex"] = 0
    writeAppConfigJsonFile(appConfigJson)

def resetAppConfigJson() -> None:
    appConfigJson: Any = {
        "configs": [
            {
                "name": "default",
                "file": "default.json"
            }
        ],
        "currentConfigIndex": 0
    }
    writeAppConfigJsonFile(appConfigJson)

def getConfigs() -> List[Any]:
    """
    Returns the list of configurations from appConfig.json.
    """
    appConfigJson = getAppConfigJson()
    configs = appConfigJson.get("configs")
    if not configs:
        logger.error("No configs available, resetting configs in appConfig.json")
        resetConfigsList()
        appConfigJson = getAppConfigJson()
        configs = appConfigJson.get("configs")
    
    if not configs:
        logger.critical("Failed to retrieve configs after reset")
        return [
            {
                "name": "default",
                "file": "default.json"
            }
        ]

    return configs

def getCurrentConfigIndex() -> int:
    """
    Returns the index of the currently active configuration.
    """
    appConfigJson = getAppConfigJson()
    currentConfigIndex = appConfigJson.get("currentConfigIndex")

    if not isinstance(currentConfigIndex, int):
        logger.error("Invalid currentConfigIndex, resetting to 0")
        resetCurrentConfigIndex()
        appConfigJson = getAppConfigJson()
        currentConfigIndex = appConfigJson.get("currentConfigIndex")

    if not isinstance(currentConfigIndex, int):
        logger.critical("currentConfigIndex is not an integer after reset")
        return 0
    
    return currentConfigIndex

def getCurrentConfigName() -> str:
    """
    Returns the name of the currently active configuration.
    """
    currentConfigIndex = getCurrentConfigIndex()
    configs = getConfigs()

    if 0 > currentConfigIndex or currentConfigIndex >= len(configs):
        logger.error("Invalid currentConfigIndex, resetting to default config")
        resetCurrentConfigIndex()
        

    configName = configs[currentConfigIndex].get("name")
    if configName:
        return configName

    logger.error("Current config name is not set, resetting to default config")
    resetAppConfigJson()

    return "default"

    if configs:
        logger.error("Invalid currentConfigIndex, resetting to default config")
        appConfigJson["currentConfigIndex"] = 0
        writeAppConfigJsonFile(appConfigJson)
        return configs[0].get("name", "unknown")
    
    logger.error("No configs available, creating default config")
    defaultConfig = {
        "name": "default",
        "file": "default.json"
    }
    appConfigJson["configs"] = [defaultConfig]
    appConfigJson["currentConfigIndex"] = 0
    writeAppConfigJsonFile(appConfigJson)

    defaultConfigContent = {}
    defaultConfigFilePath = getConfigFilePath("default")
    writeJsonFile(defaultConfigFilePath, defaultConfigContent)

    return defaultConfig.get("name", "unknown")

def readAppConfigJsonFile() -> Optional[str]:
    """
    Reads the appConfig.json file and returns its content as a string.
    """
    return readJsonFile("appConfig.json")

def getAppConfigJson() -> Any:
    appConfigJsonString: Optional[str] = readAppConfigJsonFile()
    if not appConfigJsonString:
        logger.warning("appConfig.json not found, resetting to default")
        resetAppConfigJson()
        appConfigJsonString = readAppConfigJsonFile()
    
    if not appConfigJsonString:
        logger.critical("Failed to read appConfig.json after reset")
        return {
            "configs": [
                {
                    "name": "default",
                    "file": "default.json"
                }
            ],
            "currentConfigIndex": 0
        }

    return json.loads(appConfigJsonString)

def getConfigFilePath(configName: str) -> str:
    configs = getConfigs()

    for config in configs:
        if config.get("name") == configName:
            optionalConfigFileName: Optional[str] = config.get("file")
            if optionalConfigFileName:
                return os.path.join("generatorConfigs", optionalConfigFileName)
            logger.error(f"Config '{configName}' found but has no file name, making a new one")

    configFileName: str = f"{configName}.json"
    configs.append({
        "name": configName,
        "file": configFileName
    })

    return os.path.join("generatorConfigs", configFileName)

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
            writeAppConfigJsonFile(appConfigJson)
            logger.info(f"Current config set to: {name}")
            return
    logger.error(f"Config '{name}' not found")

def getConfigJson(configFilePath: str) -> Any:
    """
    Returns the algorithm configuration from the specified file.
    """
    configJsonString: Optional[str] = readJsonFile(configFilePath)
    if configJsonString is None:
        logger.error(f"Config file {configFilePath} not found, resetting to default")
        resetConfigFile(configFilePath)
        return {}
    
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
    writeAppConfigJsonFile(appConfigJson)
    logger.info(f"Created new config mapping for: {configName}")

def createNewConfigName() -> str:
    existingConfigNames: List[str] = getConfigList()

    newConfigNumber: int = 1
    newConfigName: str = f"new_config_{newConfigNumber}"
    while newConfigName in existingConfigNames:
        newConfigNumber += 1
        newConfigName = f"new_config_{newConfigNumber}"

    return newConfigName

def resetConfigFile(filePath: str) -> None:
    """
    Resets the configuration file to the default state.
    """
    defaultConfig = getConfigJson(getConfigFilePath("default"))
    if defaultConfig is None:
        logger.error("Failed to load default config")
        resetConfigFile("default.json")
        defaultConfig = {}

    writeJsonFile(filePath, defaultConfig)
    logger.info(f"Reset config file {filePath} to default state")

def createAndUseNewConfig() -> str:
    newConfigName: str = createNewConfigName()
    
    newConfigFilePath = getConfigFilePath(newConfigName)
    resetConfigFile(newConfigFilePath)

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
    return configJson.get("benefitShorterSentences", generatorConfigDefaults.benefitShorterSentences)

def getOutputOrder(configFilePath: str) -> List[OutputOrder]:
    """
    Returns the output order from the configuration file.
    """
    configJson = getConfigJson(configFilePath)
    if configJson is None:
        return generatorConfigDefaults.outputOrder
    outputOrderStrings: List[str] = configJson.get("outputOrder", [])

    outputOrderEnums: List[OutputOrder] = []
    for order in outputOrderStrings:
        try:
            outputOrderEnums.append(OutputOrder(order))
        except ValueError:
            logger.warning(f"Invalid output order string: {order}, skipping")

    return outputOrderEnums

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
    if configName == "default":
        # Create a new config based on the default
        logger.warning("Cannot update 'default' config, creating a new one")
        configName = createAndUseNewConfig()
    configFilePath: str = getConfigFilePath(configName)
    configJson = getConfigJson(configFilePath)
    configJson.update(update)
    writeJsonFile(configFilePath, configJson)

def setConfigInputFile(configName: str, path: str) -> None:
    """
    Sets the input file path for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        logger.warning("Cannot update 'default' config, creating a new one")
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"inputFilePath": path})

def setConfigOutputFile(configName: str, path: str) -> None:
    """
    Sets the output file path for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        logger.warning("Cannot update 'default' config, creating a new one")
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"outputFilePath": path})

def setConfigAlgorithm(configName: str, algorithm: str) -> None:
    """
    Sets the cloze choosing algorithm for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        logger.warning("Cannot update 'default' config, creating a new one")
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"clozeChoosingAlgorithm": algorithm})

def setConfigFlashcardsPerWord(configName: str, count: int) -> None:
    """
    Sets the number of flashcards per word for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        logger.warning("Cannot update 'default' config, creating a new one")
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"numFlashcardsPerWord": count})

def setConfigBenefitShorter(configName: str, enabled: bool) -> None:
    """
    Enables or disables benefiting shorter sentences for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        logger.warning("Cannot update 'default' config, creating a new one")
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"benefitShorterSentences": enabled})

def setConfigOutputOrder(configName: str, orders: List[str]) -> None:
    """
    Sets the output order for the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        logger.warning("Cannot update 'default' config, creating a new one")
        configName = createAndUseNewConfig()
    updateConfigFile(configName, {"outputOrder": list(orders)})

def addBuryWordToConfig(configName: str, word: str) -> None:
    """
    Adds a word to the bury list in the specified configuration.
    """
    if configName == "default":
        # Create a new config based on the default
        logger.warning("Cannot update 'default' config, creating a new one")
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
        logger.warning("Cannot update 'default' config, creating a new one")
        configName = createAndUseNewConfig()
    currentWordsToBury = getWordsToBury(getConfigFilePath(configName))
    if word in currentWordsToBury:
        currentWordsToBury.remove(word)
        updateConfigFile(configName, {"wordsToBury": currentWordsToBury})