# Dagster Bench

Performance benchmarking tool for Dagster, designed to measure and analyze materialization lag across different asset configurations.

## Features

- **Measure lag** for single asset configurations
- **Analyze and compare** lag across multiple configurations
- **Two-component lag tracking**:
  - Queue time (RUN_ENQUEUED → RUN_START)
  - Init time (RUN_START → STEP_START)
- **Support for partitioned assets** (daily/hourly partitions)
- **Basic auth support** 
- **Stacked bar charts** for visualization

## Installation

Install using `uv` (recommended):

```bash
cd cli
uv pip install -e .
```

Or using pip:

```bash
cd cli
pip install -e .
```

## Usage

### Measure Command

Measure materialization lag for a single asset configuration:

```bash
# Basic usage (uses localhost:80 with admin:admin)
bench measure 2k --runs 3

# 1 asset with 2000 partitions
bench measure a1p2k --runs 3

# Custom URL and auth
bench measure 10k \
  --url https://dagster.example.com \
  --username user \
  --password pass \
  --runs 5

# Verbose output
bench measure 2k --runs 3 --verbose
```

### Analyze Command

Analyze and compare lag across multiple configurations:

```bash
# Compare assets vs partitions
bench analyze --prefixes a1p2k 2k --runs 3

# Compare multiple configurations
bench analyze --prefixes 250 500 2k 5k 10k --runs 5

# Custom output file
bench analyze --prefixes 2k 10k --output comparison.png

# Custom URL and auth
bench analyze --prefixes 2k 10k \
  --url https://dagster.example.com \
  --username user \
  --password pass
```

## Configuration

### Default Settings

- **URL**: `http://localhost:80`
- **Username**: `admin`
- **Password**: `admin`
- **Runs**: 3

### Asset Prefix Format

The tool supports several prefix formats:

- **Simple count**: `500`, `1000` → That many assets
- **K notation**: `2k`, `10k` → 2000, 10000 assets
- **Partition notation**: `a1p2k` → 1 asset with 2000 partitions

### Repository Locations

Repository locations are auto-constructed as `simple-asset-{prefix}`. For example:
- `2k` → `simple-asset-2k`
- `a1p2k` → `simple-asset-a1p2k`

You can override this with `--repo-location`.

## Output

### Measure Command

Outputs lag measurements with breakdown:

```
Measuring lag: 2k @ http://localhost:80
Runs: 3 | Location: simple-asset-2k

  1. Asset_548 | Queue: 11.028s | Init: 1.902s | Total: 12.930s
  2. Asset_1966 | Queue: 10.630s | Init: 2.219s | Total: 12.849s
  3. Asset_123 | Queue: 10.500s | Init: 2.100s | Total: 12.600s

Successful runs: 3/3

Queue time (Enqueued→Start):  10.719s (10719ms)
Init time (Start→Step):       2.074s (2074ms)
Total lag:                    12.793s (12793ms)
```

Also outputs JSON for programmatic use:
```json
{"enqueue_to_start": 10.719, "start_to_step": 2.074}
```

### Analyze Command

Outputs:
1. **PNG chart**: Stacked bar chart showing queue and init time for each configuration
2. **JSON file**: Raw measurement data for further analysis
3. **Console summary**: Tabular results

## Examples

### Compare Assets vs Partitions

```bash
# Deploy 2 configurations:
# - a1p2k: 1 asset with 2000 partitions
# - 2k: 2000 assets

# Run comparison
bench analyze --prefixes a1p2k 2k --runs 5 --output assets_vs_partitions.png
```

### Find Optimal Asset Count

```bash
bench analyze --prefixes 250 500 2k 5k 10k --runs 5 --output scaling_analysis.png
```

## Requirements

- Python 3.11+
- Access to a Dagster instance (locally or via ingress)
- Basic auth credentials (if using ingress)

## Development

```bash
# Install in development mode with dev dependencies
cd cli
uv pip install -e ".[dev]"

# Format code
ruff format .

# Lint
ruff check .
```