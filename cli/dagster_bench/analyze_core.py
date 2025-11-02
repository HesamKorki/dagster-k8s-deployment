"""Analyze Dagster lag across different asset counts and generate charts."""

import argparse
import json
import subprocess
import sys

try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("Error: matplotlib and numpy required for charting")
    print("Install: uv pip install matplotlib numpy")
    sys.exit(1)

from dagster_bench.utils import parse_asset_count


def run_measurement(
    asset_prefix,
    url,
    runs=3,
    repo_location=None,
    username=None,
    password=None,
    verbose=False,
):
    """Run lag measurement for a given asset prefix.

    Returns dict with 'enqueue_to_start' and 'start_to_step' metrics, or None if failed.
    """
    cmd = [
        "bench",
        "measure",
        asset_prefix,
        "--url", url,
        "--runs", str(runs)
    ]

    if username:
        cmd.extend(["--username", username])
    if password:
        cmd.extend(["--password", password])
    if repo_location:
        cmd.extend(["--repo-location", repo_location])

    if verbose:
        print(f"  Measuring {asset_prefix}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )

        # Parse JSON output from last line
        lines = result.stdout.strip().split('\n')
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    data = json.loads(line)
                    if 'enqueue_to_start' in data and 'start_to_step' in data:
                        return data
                except json.JSONDecodeError:
                    continue

        return None

    except subprocess.CalledProcessError as e:
        if verbose:
            print(f"    Error: {e}")
        return None


def save_results(asset_counts, enqueue_lags, step_lags, prefixes, output_file):
    """Save measurement results to JSON."""
    data = {
        'measurements': [
            {
                'prefix': prefix,
                'asset_count': int(count),
                'enqueue_to_start_seconds': float(enqueue),
                'start_to_step_seconds': float(step),
                'total_lag_seconds': float(enqueue + step)
            }
            for prefix, count, enqueue, step in zip(prefixes, asset_counts, enqueue_lags, step_lags)
        ]
    }

    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    return data


def create_chart(asset_counts, enqueue_lags, step_lags, prefixes, output_file):
    """Create stacked bar chart showing both lag components."""
    fig, ax = plt.subplots(figsize=(14, 8))

    # Convert to numpy arrays
    enqueue_lags = np.array(enqueue_lags)
    step_lags = np.array(step_lags)
    total_lags = enqueue_lags + step_lags

    # Create bar positions
    x = np.arange(len(prefixes))
    width = 0.6

    # Create stacked bars
    ax.bar(
        x,
        enqueue_lags,
        width,
        label='Queue (Enqueued→Start)',
        color='#FF6B6B',
        alpha=0.8,
    )
    ax.bar(
        x,
        step_lags,
        width,
        bottom=enqueue_lags,
        label='Init (Start→Step)',
        color='#4ECDC4',
        alpha=0.8,
    )

    # Customize axes
    ax.set_xlabel('Asset Configuration', fontsize=12, fontweight='bold')
    ax.set_ylabel('Lag (seconds)', fontsize=12, fontweight='bold')
    ax.set_title('Dagster Materialization Lag Breakdown\n(Queue Time + Initialization Time)',
                 fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(prefixes, fontsize=11)
    ax.legend(fontsize=11, loc='upper left')
    ax.grid(True, alpha=0.3, linestyle='--', axis='y')

    # Add value labels on bars
    for i, (enqueue, step, total) in enumerate(zip(enqueue_lags, step_lags, total_lags)):
        # Queue time label (middle of first segment)
        if enqueue > 0.1:  # Only show if significant
            ax.text(i, enqueue/2, f'{enqueue:.2f}s',
                   ha='center', va='center', fontsize=9, fontweight='bold', color='white')

        # Init time label (middle of second segment)
        if step > 0.1:  # Only show if significant
            ax.text(i, enqueue + step/2, f'{step:.2f}s',
                   ha='center', va='center', fontsize=9, fontweight='bold', color='white')

        # Total label on top
        ax.text(i, total, f'{total:.2f}s',
               ha='center', va='bottom', fontsize=10, fontweight='bold',
               bbox=dict(boxstyle='round,pad=0.4', facecolor='yellow', alpha=0.8))

    plt.tight_layout()
    plt.savefig(output_file, dpi=150, bbox_inches='tight')
    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='Analyze Dagster lag across asset counts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bench analyze --prefixes a1p2k 2k
  bench analyze --prefixes 250 500 2k 5k 10k --runs 5
  bench analyze --prefixes 2k 10k --url https://dagster.example.com --username user --password pass

Note: Repository locations are auto-constructed as 'simple-asset-{prefix}'
      Default URL is http://localhost:80 with admin:admin auth
        """
    )

    parser.add_argument('--prefixes', nargs='+', required=True,
                        help='Asset prefixes to test (e.g., 500 2k 10k 25k 50k)')
    parser.add_argument('--url', default='http://localhost:80',
                        help='Dagster URL (default: http://localhost:80)')
    parser.add_argument('--username', default='admin',
                        help='Basic auth username (default: admin)')
    parser.add_argument('--password', default='admin',
                        help='Basic auth password (default: admin)')
    parser.add_argument('--runs', type=int, default=3,
                        help='Number of test runs per prefix (default: 3)')
    parser.add_argument('--output', default='lag_analysis.png',
                        help='Output chart filename (default: lag_analysis.png)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    print("=" * 70)
    print("Dagster Lag Analysis - Elbow Chart")
    print("=" * 70)
    print(f"Asset prefixes: {', '.join(args.prefixes)}")
    print(f"Dagster URL:    {args.url}")
    print(f"Runs per test:  {args.runs}")
    print("=" * 70)
    print()

    # Run measurements
    results = {}
    asset_counts = []
    enqueue_lags = []
    step_lags = []

    print("Running measurements...")
    for prefix in args.prefixes:
        # Auto-construct repo location name
        repo_location = f"simple-asset-{prefix}"

        if args.verbose:
            print(f"\nTesting {prefix}...")
            print(f"  Repo location: {repo_location}")
        else:
            print(f"  {prefix} ({repo_location})...", end='', flush=True)

        data = run_measurement(
            prefix,
            args.url,
            args.runs,
            repo_location,
            args.username,
            args.password,
            args.verbose,
        )

        if data is not None:
            asset_count = parse_asset_count(prefix)
            results[prefix] = {
                'count': asset_count,
                'enqueue': data['enqueue_to_start'],
                'step': data['start_to_step']
            }
            asset_counts.append(asset_count)
            enqueue_lags.append(data['enqueue_to_start'])
            step_lags.append(data['start_to_step'])

            if not args.verbose:
                total = data['enqueue_to_start'] + data['start_to_step']
                enq = data['enqueue_to_start']
                stp = data['start_to_step']
                print(f" {total:.2f}s (Q:{enq:.2f}s + I:{stp:.2f}s)")
        else:
            if not args.verbose:
                print(" FAILED")
            print(f"    Warning: Failed to measure {prefix}")

    if len(results) < 1:
        print("\nError: No successful measurements")
        sys.exit(1)

    # Sort by asset count
    sorted_indices = np.argsort(asset_counts)
    sorted_prefixes = [args.prefixes[i] for i in sorted_indices]
    asset_counts = np.array(asset_counts)[sorted_indices]
    enqueue_lags = np.array(enqueue_lags)[sorted_indices]
    step_lags = np.array(step_lags)[sorted_indices]

    # Save results to JSON first
    print("\nSaving results...")
    json_file = args.output.replace('.png', '.json')
    data = save_results(asset_counts, enqueue_lags, step_lags, sorted_prefixes, json_file)
    print(f"✅ Data saved: {json_file}")

    # Create chart from data
    print("Generating chart...")
    create_chart(asset_counts, enqueue_lags, step_lags, sorted_prefixes, args.output)
    print(f"✅ Chart saved: {args.output}")

    # Print summary
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    print(f"{'Config':<15} {'Queue (s)':<12} {'Init (s)':<12} {'Total (s)':<12} {'Total (ms)':<12}")
    print("-" * 70)

    total_lags = enqueue_lags + step_lags
    for prefix, enqueue, step, total in zip(sorted_prefixes, enqueue_lags, step_lags, total_lags):
        print(f"{prefix:<15} {enqueue:<12.3f} {step:<12.3f} {total:<12.3f} {int(total*1000):<12,}")

    print("=" * 70)
    print()


if __name__ == "__main__":
    main()

