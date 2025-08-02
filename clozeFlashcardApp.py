import logging
import click
import cProfile
import pstats
import io
import os
from typing import List, Tuple

from terminalUtils import runAlgorithm
from configUtils import (
    getConfigList,
    getCurrentConfigName,
    setConfigBenefitShorter,
    setConfigFlashcardsPerWord,
    setConfigOutputOrder,
    setCurrentConfig,
    getCurrentConfigFilePath,
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
    pass

@cli.command()
def help():
    """Show help info."""
    logger.info("Use --help with any command to see details.")

# Config command group
# TODO : when delete config is implemented, add a cascade delete option
# to delete all files associated with the config
@cli.group()
def config():
    """Commands for managing configs."""
    pass

@config.command()
def list():
    """List all available configs."""
    # Read the generatorConfigs/default.json file
    getTerminalConfigList: List[str] = getConfigList()
    click.echo("Available configs:")
    for config in getTerminalConfigList:
        click.echo(f"- {config}")

@config.command()
def current():
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
    ordersList = [order for order in orders]
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

@config.group(name='current')
def current_settings():
    """Commands for getting current config settings."""
    pass

@current_settings.command(name='input-file')
def getCurrentInputFile():
    """Get the input file path for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    # TODO : error handling
    inputFile = getInputFilePath(configFilePath)
    click.echo(f"Input file: {inputFile}")

@current_settings.command(name='output-file')
def getCurrentOutputFile():
    """Get the output file path for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    # TODO : error handling
    outputFile = getOutputFilePath(configFilePath)
    click.echo(f"Output file: {outputFile}")

@current_settings.command(name='algorithm')
def getCurrentAlgorithm():
    """Get the cloze choosing algorithm for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    # TODO : error handling
    algorithm = getClozeChoosingAlgorithm(configFilePath)
    click.echo(f"Algorithm: {algorithm.value}")

@current_settings.command(name='flashcards-per-word')
def getCurrentFlashcardsPerWord():
    """Get the number of flashcards per word for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    # TODO : error handling
    count = getNumFlashcardsPerWord(configFilePath)
    click.echo(f"Flashcards per word: {count}")

@current_settings.command(name='benefit-shorter')
def getCurrentBenefitShorter():
    """Get whether shorter sentences are benefited for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    # TODO : error handling
    enabled = getBenefitShorterSentences(configFilePath)
    click.echo(f"Benefit shorter sentences: {enabled}")

@current_settings.command(name='output-order')
def getCurrentOutputOrder():
    """Get the output order for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    # TODO : error handling
    orders = getOutputOrder(configFilePath)
    orderValues = [order.value for order in orders]
    click.echo(f"Output order: {', '.join(orderValues)}")

@current_settings.command(name='bury-words')
def getCurrentBuryWords():
    """Get the list of words to bury for the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    # TODO : error handling
    words = getWordsToBury(configFilePath)
    if words:
        click.echo(f"Bury words: {', '.join(words)}")
    else:
        click.echo("Bury words: None")

# Run command group
@cli.group()
def run():
    """Commands for running the app."""
    pass

@run.command()
def all() -> None:
    """Run the full app with the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    if configFilePath.startswith("error:"):
        logger.error(configFilePath)
        return
    # Proceed with running the app using the config file
    logger.info(f"Running app with config: {configFilePath}")

    runAlgorithm(configFilePath)

# TODO : come up with and stick to naming convention
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG, # Options are DEBUG, INFO, WARNING, ERROR, CRITICAL
        format='%(levelname)s: %(message)s'
    )
    
    isDev = os.getenv("DEV_MODE", "false").lower() == "true"
    
    profiler = None

    if isDev:
        # Create profiler
        profiler = cProfile.Profile()

        # Start profiling
        profiler.enable()
    
    if isDev:
        all()
    else:
        cli()

    if profiler is not None:
        # Stop profiling
        profiler.disable()

        # Create a string buffer to capture output
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s)

        # Sort by cumulative time and print top 20 functions
        ps.sort_stats('cumulative')
        ps.print_stats(20)

        # Print the results
        print(s.getvalue())

        # You can also save to file
        ps.dump_stats('profile_results.prof')