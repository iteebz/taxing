import argparse

from src.cli.commands import (
    assets,
    coverage,
    gains,
    household,
    lookalike,
    metrics,
    mining,
    optimize,
    property,
    rules,
    run,
    sample,
)


def main():
    parser = argparse.ArgumentParser(
        description="Tax optimization and management tool",
        prog="tax",
    )
    subparsers = parser.add_subparsers(dest="command")

    run.register(subparsers)
    optimize.register(subparsers)
    property.register(subparsers)
    gains.register(subparsers)
    assets.register(subparsers)
    metrics.register(subparsers)
    coverage.register(subparsers)
    mining.register(subparsers)
    sample.register(subparsers)
    lookalike.register(subparsers)
    household.register(subparsers)
    rules.register(subparsers)
    rules.register_add_rule_command(subparsers)  # Register the new top-level 'rule' command

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
