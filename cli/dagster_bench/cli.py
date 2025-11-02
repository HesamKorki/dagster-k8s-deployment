"""Main CLI entry point for Dagster Bench."""

import sys


def main() -> None:
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        _print_help()
        sys.exit(1)

    command = sys.argv[1]

    if command == "measure":
        from dagster_bench.measure_core import main as measure_main
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        measure_main()
    elif command == "analyze":
        from dagster_bench.analyze_core import main as analyze_main
        sys.argv = [sys.argv[0]] + sys.argv[2:]
        analyze_main()
    elif command in {"-h", "--help", "help"}:
        _print_help()
    elif command in {"-v", "--version", "version"}:
        from dagster_bench import __version__
        print(f"Dagster Bench v{__version__}")
    else:
        print(f"Error: Unknown command '{command}'")
        print()
        _print_help()
        sys.exit(1)


def _print_help() -> None:
    """Print CLI help message."""
    print("""Dagster Bench - Performance benchmarking tool for Dagster

Usage:
  bench <command> [options]

Commands:
  measure    Measure materialization lag for a single asset configuration
  analyze    Analyze and compare lag across multiple configurations

Options:
  -h, --help     Show this help message
  -v, --version  Show version

Examples:
  # Measure lag for 2000 assets
  bench measure 2k --runs 3

  # Compare 1 asset with 2000 partitions vs 2000 assets
  bench analyze --prefixes a1p2k 2k --runs 3

  # Use custom Dagster URL
  bench measure 10k --url https://dagster.example.com --username user --password pass

For more help on a specific command:
  bench measure --help
  bench analyze --help
""")


if __name__ == "__main__":
    main()

