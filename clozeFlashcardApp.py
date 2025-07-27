import logging
import click
import cProfile
import pstats
import io
import os
from typing import List

from terminalUtils import runAlgorithm
from configUtils import (
    getConfigList,
    getCurrentConfigName,
    setCurrentConfig,
    getCurrentConfigFilePath
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
    # Read the algorithmConfigs/default.json file
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