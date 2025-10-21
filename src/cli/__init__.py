import argparse

from src.cli.commands import assets, gains, household, metrics, optimize, property_, rules


def main():
    parser = argparse.ArgumentParser(
        description="Tax optimization and management tool",
        prog="tax",
    )
    subparsers = parser.add_subparsers(dest="command")

    optimize.register(subparsers)
    property_.register(subparsers)
    gains.register(subparsers)
    assets.register(subparsers)
    metrics.register(subparsers)
    household.register(subparsers)
    rules.register(subparsers)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
