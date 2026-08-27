"""Command-line entry point."""

from argparse import ArgumentParser


def main() -> None:
    """Show the available CLI surface while orchestration is built in later chunks."""
    parser = ArgumentParser(description="AI-augmented investment pipeline")
    parser.parse_args()
    parser.print_help()
