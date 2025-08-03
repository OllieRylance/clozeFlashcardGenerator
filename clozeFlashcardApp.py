import cProfile
import io
import logging
import os
import pstats
from typing import List, Tuple

import click

from terminalUtils import runAlgorithm
from configUtils import (
    getConfigList,
    getCurrentConfigName,
    setConfigBenefitShorter,
    setConfigFlashcardsPerWord,
    setConfigOutputOrder,
    setCurrentConfig,
    getCurrentConfigFilePath,
    addConfigByName,
    deleteConfigByName,
    setConfigInputFile,
    setConfigOutputFile,
    setConfigAlgorithm,
    addBuryWordToConfig,
    removeBuryWordFromConfig,
    getInputFilePath,
    getOutputFilePath,
    getClozeChoosingAlgorithm,
    getNumFlashcardsPerWord,
    getBenefitShorterSentences,
    getOutputOrder,
    getWordsToBury
)
from resources import (
    ClozeChoosingAlgorithm,
    OutputOrder
)

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Flashcard App CLI."""

@cli.command(name='help')
def showHelp():
    """Show help info."""
    logger.info("Use --help with any command to see details.")

# Config command group
@cli.group()
def config():
    """Commands for managing configs."""

@config.command(name='list')
def listConfigs():
    """List all available configs."""
    # Read the generatorConfigs/default.json file
    getTerminalConfigList: List[str] = getConfigList()
    click.echo("Available configs:")
    for cfg in getTerminalConfigList:
        click.echo(f"- {cfg}")

@config.command(name='view')
def viewCurrent():
    """Show the currently active config's name."""
    click.echo(getCurrentConfigName())

@config.command(name='set-current')
@click.argument('name')
def setCurrent(name: str):
    """Set the currently active config by name."""
    setCurrentConfig(name)

@config.command(name='set-input-file')
@click.argument('path')
def setInputFile(path: str):
    """Set the input file path for the current config."""
    currentConfigName: str = getCurrentConfigName()
    setConfigInputFile(currentConfigName, path)

@config.command(name='set-output-file')
@click.argument('path')
def setOutputFile(path: str):
    """Set the output file path for the current config."""
    currentConfigName: str = getCurrentConfigName()
    setConfigOutputFile(currentConfigName, path)

@config.command(name='set-algorithm')
@click.argument('algorithm', type=click.Choice(ClozeChoosingAlgorithm.getTerminalOptions()))
def setAlgorithm(algorithm: str):
    """Set the cloze choosing algorithm for the current config."""
    currentConfigName: str = getCurrentConfigName()
    setConfigAlgorithm(currentConfigName, algorithm)

@config.command(name='set-flashcards-per-word')
@click.argument('count', type=int)
def setFlashcardsPerWord(count: int):
    """Set the number of flashcards per word for the current config."""
    currentConfigName: str = getCurrentConfigName()
    setConfigFlashcardsPerWord(currentConfigName, count)

@config.command(name='set-benefit-shorter')
@click.argument('enabled', type=bool)
def setBenefitShorter(enabled: bool):
    """Enable or disable benefiting shorter sentences for the current config."""
    currentConfigName: str = getCurrentConfigName()
    setConfigBenefitShorter(currentConfigName, enabled)

@config.command(name='set-output-order')
@click.argument('orders', nargs=-1, type=click.Choice(OutputOrder.getTerminalOptions()))
def setOutputOrder(orders: Tuple[str, ...]):
    """Set the output order for the current config."""
    currentConfigName: str = getCurrentConfigName()
    ordersList = list(orders)
    setConfigOutputOrder(currentConfigName, ordersList)

@config.command(name='add-bury-word')
@click.argument('word')
def addBuryWord(word: str):
    """Add a word to bury in the current config."""
    currentConfigName: str = getCurrentConfigName()
    addBuryWordToConfig(currentConfigName, word)

@config.command(name='remove-bury-word')
@click.argument('word')
def removeBuryWord(word: str):
    """Remove a word from bury list in the current config."""
    currentConfigName: str = getCurrentConfigName()
    removeBuryWordFromConfig(currentConfigName, word)

@config.command(name='add')
@click.argument('name')
def addConfig(name: str):
    """Add a new config by name."""
    addConfigByName(name)

# config delete command
@config.command(name='delete')
@click.argument('name')
@click.option(
    '--cascade',
    is_flag=True,
    help="Delete all files associated with the config."
)
def deleteConfig(name: str, cascade: bool = False):
    """Delete a config by name."""
    deleteConfigByName(name, cascade)

@config.group(name='current')
def currentSettings():
    """Commands for getting current config settings."""

@currentSettings.command(name='input-file')
def getCurrentInputFile():
    """Get the input file path for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    inputFile = getInputFilePath(configFilePath)
    click.echo(f"Input file: {inputFile}")

@currentSettings.command(name='output-file')
def getCurrentOutputFile():
    """Get the output file path for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    outputFile = getOutputFilePath(configFilePath)
    click.echo(f"Output file: {outputFile}")

@currentSettings.command(name='algorithm')
def getCurrentAlgorithm():
    """Get the cloze choosing algorithm for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    algorithm = getClozeChoosingAlgorithm(configFilePath)
    click.echo(f"Algorithm: {algorithm.value}")

@currentSettings.command(name='flashcards-per-word')
def getCurrentFlashcardsPerWord():
    """Get the number of flashcards per word for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    count = getNumFlashcardsPerWord(configFilePath)
    click.echo(f"Flashcards per word: {count}")

@currentSettings.command(name='benefit-shorter')
def getCurrentBenefitShorter():
    """Get whether shorter sentences are benefited for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    enabled = getBenefitShorterSentences(configFilePath)
    click.echo(f"Benefit shorter sentences: {enabled}")

@currentSettings.command(name='output-order')
def getCurrentOutputOrder():
    """Get the output order for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    orders = getOutputOrder(configFilePath)
    orderValues = [order.value for order in orders]
    click.echo(f"Output order: {', '.join(orderValues)}")

@currentSettings.command(name='bury-words')
def getCurrentBuryWords():
    """Get the list of words to bury for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    words = getWordsToBury(configFilePath)
    if words:
        click.echo(f"Bury words: {', '.join(words)}")
    else:
        click.echo("Bury words: None")

# Run command group
@cli.group()
def run():
    """Commands for running the app."""

@run.command(name='all')
def runAll() -> None:
    """Run the full app with the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    if configFilePath.startswith("error:"):
        logger.error(configFilePath)
        return
    # Proceed with running the app using the config file
    logger.info("Running app with config: %s", configFilePath)

    runAlgorithm(configFilePath)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING, # Options are DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(levelname)s: %(message)s'
    )

    isDev = os.getenv("DEV_MODE", "false").lower() == "true"

    code_profiler = None

    if isDev:
        # Create profiler
        code_profiler = cProfile.Profile()

        # Start profiling
        code_profiler.enable()

    if isDev:
        runAll()
    else:
        cli()

    if code_profiler is not None:
        # Stop profiling
        code_profiler.disable()

        # Create a string buffer to capture output
        s = io.StringIO()
        ps = pstats.Stats(code_profiler, stream=s)

        # Sort by cumulative time and print top 20 functions
        ps.sort_stats('cumulative')
        ps.print_stats(20)

        # Print the results
        print(s.getvalue())

        # You can also save to file
        ps.dump_stats('profile_results.prof')
