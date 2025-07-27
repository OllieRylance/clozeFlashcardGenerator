import click
from typing import List

from terminalUtils import (
    getConfigList,
    getCurrentConfigFilePath,
    getCurrentConfigName,
    runAlgorithm
)

@click.group()
def cli():
    """Flashcard App CLI."""
    pass

@cli.command()
def help():
    """Show help info."""
    click.echo("Use --help with any command to see details.")

# Config command group
@cli.group()
def config():
    """Commands for managing configs."""
    pass

# @config.command()
# @click.argument('name')
# def create(name: str):
#     """Create a new config."""
#     click.echo(f"Creating config '{name}'")

# @config.command()
# @click.argument('name')
# def delete(name: str):
#     """Delete a config."""
#     click.echo(f"Deleting config '{name}'")

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

# Run command group
@cli.group()
def run():
    """Commands for running the app."""
    pass

@run.command()
def all():
    """Run the full app with the current config."""
    configFilePath: str = getCurrentConfigFilePath()
    if configFilePath.startswith("error:"):
        click.echo(configFilePath)
        return
    # Proceed with running the app using the config file
    click.echo(f"Running app with config: {configFilePath}")

    runAlgorithm(configFilePath)

if __name__ == "__main__":
    #cli()
    all()