import click
from watcher.main import main as watcher_main

@click.command()
def main():
    """Main entry point for the Watcher OS application."""
    watcher_main()

if __name__ == "__main__":
    main()