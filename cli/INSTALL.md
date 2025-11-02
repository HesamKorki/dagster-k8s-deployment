# Installation Guide

## Quick Install

```bash
cd cli
uv pip install -e .
```

## Verify Installation

```bash
bench --version
bench --help
```

## Test Commands

```bash
# Test measure command
bench measure 2k --runs 2

# Test analyze command
bench analyze --prefixes a1p2k 2k --runs 2
```


## Troubleshooting

### Command not found: bench

Make sure the installation directory is in your PATH:

```bash
# Check where bench is installed
which bench

# If not found, try reinstalling
pip uninstall dagster-bench
uv pip install -e .
```

### Connection errors

Make sure your Dagster instance is accessible:

```bash
# Test connection
curl http://localhost:80/graphql

# Or with auth
curl -u admin:admin http://localhost:80/graphql
```

