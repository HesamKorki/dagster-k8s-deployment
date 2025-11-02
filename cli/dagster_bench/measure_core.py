"""Measure Dagster materialization lag."""

import argparse
import json
import random
import sys
import time
from datetime import datetime

from dagster_bench.client import DagsterGraphQLClient
from dagster_bench.utils import get_latest_partition
from dagster_bench.utils import parse_asset_count as parse_num_assets


def measure_lag(client, asset_prefix, num_assets, repo_location, num_runs=3, verbose=False):
    """Measure lag for asset materialization.

    For each run, randomly selects an asset from 0 to num_assets-1.

    Returns a dict with two lag components:
    - enqueue_to_start: Time from RUN_ENQUEUED to RUN_START (queueing)
    - start_to_step: Time from RUN_START to STEP_START (initialization)
    """
    enqueue_to_start_lags = []
    start_to_step_lags = []

    for run_num in range(1, num_runs + 1):
        # Randomly select an asset for this run
        asset_num = random.randint(0, num_assets - 1)
        asset_key = f"{asset_prefix}_dummy_asset_{asset_num}"

        if verbose:
            print(f"\n  Run {run_num}/{num_runs}:")
            print(f"    Asset: {asset_key}")

        # Check if asset is partitioned and get latest partition
        latest_partition = get_latest_partition(client, asset_key, repo_location, verbose)

        if verbose:
            print(f"    Request: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

        # Submit run with partition if available
        if latest_partition:
            query = """
            mutation LaunchAssetRun(
                $repoLocation: String!,
                $assetKeys: [AssetKeyInput!]!,
                $partition: String!
            ) {
              launchPipelineExecution(
                executionParams: {
                  selector: {
                    repositoryLocationName: $repoLocation
                    repositoryName: "__repository__"
                    pipelineName: "__ASSET_JOB"
                    assetSelection: $assetKeys
                  }
                  mode: "default"
                  executionMetadata: {
                    tags: [
                      { key: "dagster/partition", value: $partition }
                    ]
                  }
                }
              ) {
                __typename
                ... on LaunchRunSuccess {
                  run { id status }
                }
                ... on PipelineNotFoundError { message }
                ... on InvalidSubsetError { message }
                ... on PythonError { message }
              }
            }
            """

            variables = {
                "repoLocation": repo_location,
                "assetKeys": [{"path": [asset_key]}],
                "partition": latest_partition
            }
        else:
            query = """
            mutation LaunchAssetRun($repoLocation: String!, $assetKeys: [AssetKeyInput!]!) {
              launchPipelineExecution(
                executionParams: {
                  selector: {
                    repositoryLocationName: $repoLocation
                    repositoryName: "__repository__"
                    pipelineName: "__ASSET_JOB"
                    assetSelection: $assetKeys
                  }
                }
              ) {
                __typename
                ... on LaunchRunSuccess {
                  run { id status }
                }
                ... on PipelineNotFoundError { message }
                ... on InvalidSubsetError { message }
                ... on PythonError { message }
              }
            }
            """

            variables = {
                "repoLocation": repo_location,
                "assetKeys": [{"path": [asset_key]}]
            }

        try:
            result = client._execute(query, variables)
            launch_result = result.get("launchPipelineExecution", {})

            if launch_result.get("__typename") != "LaunchRunSuccess":
                error_msg = launch_result.get(
                    'message',
                    launch_result.get('__typename', 'Unknown error'),
                )
                if verbose:
                    print(f"    Failed: {error_msg}")
                continue

            run_id = launch_result["run"]["id"]

            # Poll for events to measure both lag components
            max_wait = 300
            poll_interval = 0.1  # 100ms polling
            elapsed = 0

            enqueue_time = None
            start_time = None
            step_time = None

            while elapsed < max_wait:
                events_query = """
                query GetEvents($runId: ID!) {
                  logsForRun(runId: $runId) {
                    ... on EventConnection {
                      events {
                        ... on MessageEvent {
                          eventType
                          timestamp
                        }
                      }
                    }
                  }
                }
                """

                events_result = client._execute(events_query, {"runId": run_id})
                logs = events_result.get("logsForRun", {})
                events = logs.get("events", [])

                # Find timestamps for each event type
                for event in events:
                    event_type = event.get("eventType")
                    timestamp = event.get("timestamp")

                    if event_type == "RUN_ENQUEUED" and not enqueue_time:
                        enqueue_time = float(timestamp) / 1000.0  # Convert ms to seconds
                    elif event_type == "RUN_START" and not start_time:
                        start_time = float(timestamp) / 1000.0
                    elif event_type == "STEP_START" and not step_time:
                        step_time = float(timestamp) / 1000.0

                # Break when we have all three events
                if enqueue_time and start_time and step_time:
                    enqueue_to_start = start_time - enqueue_time
                    start_to_step = step_time - start_time

                    enqueue_to_start_lags.append(enqueue_to_start)
                    start_to_step_lags.append(start_to_step)

                    total = enqueue_to_start + start_to_step

                    if verbose:
                        print(f"    Enqueued→Start: {enqueue_to_start:.3f}s")
                        print(f"    Start→Step:     {start_to_step:.3f}s")
                        print(f"    Total:          {total:.3f}s")
                    else:
                        msg = (
                            f"  {run_num}. Asset_{asset_num} | "
                            f"Queue: {enqueue_to_start:.3f}s | "
                            f"Init: {start_to_step:.3f}s | "
                            f"Total: {total:.3f}s"
                        )
                        print(msg)
                    break

                time.sleep(poll_interval)
                elapsed += poll_interval

            if elapsed >= max_wait:
                if verbose:
                    print(f"    Timeout after {max_wait}s")
                    got_enq = enqueue_time is not None
                    got_start = start_time is not None
                    got_step = step_time is not None
                    print(f"    Got: ENQUEUED={got_enq}, START={got_start}, STEP={got_step}")

        except Exception as e:
            if verbose:
                print(f"    Error: {e}")
            continue

        time.sleep(1)

    return {
        'enqueue_to_start': enqueue_to_start_lags,
        'start_to_step': start_to_step_lags
    }


def main():
    parser = argparse.ArgumentParser(
        description='Measure Dagster materialization lag',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bench measure 10k
  bench measure 2k --runs 5
  bench measure a1p2k --runs 3  # 1 asset with 2000 partitions
  bench measure prod --url https://dagster.example.com --username user --password pass
        """
    )

    parser.add_argument('asset_prefix', help='Asset prefix (e.g., 10k, a1p2k, test, prod)')
    parser.add_argument('--url', default='http://localhost:80',
                        help='Dagster URL (default: http://localhost:80)')
    parser.add_argument('--username', default='admin',
                        help='Basic auth username (default: admin)')
    parser.add_argument('--password', default='admin',
                        help='Basic auth password (default: admin)')
    parser.add_argument('--runs', type=int, default=3,
                        help='Number of test runs (default: 3)')
    parser.add_argument('--repo-location', dest='repo_location',
                        help='Repository location name (default: simple-asset-{prefix})')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Verbose output')

    args = parser.parse_args()

    # Parse number of assets from prefix
    num_assets = parse_num_assets(args.asset_prefix)

    # Infer repo location if not provided
    if not args.repo_location:
        args.repo_location = f"simple-asset-{args.asset_prefix}"

    # Normalize URL
    url = args.url.rstrip('/').replace('/graphql', '')

    # Connect with basic auth
    try:
        client = DagsterGraphQLClient(url, args.username, args.password)
        # Test connection
        client._execute("query { __typename }")
    except Exception as e:
        print(f"Error: Failed to connect to {url}")
        print(f"Details: {e}")
        sys.exit(1)

    # Print header
    if not args.verbose:
        print(f"\nMeasuring lag: {args.asset_prefix} @ {url}")
        print(f"Runs: {args.runs} | Location: {args.repo_location}\n")
    else:
        print(f"\n{'='*70}")
        print("Dagster Materialization Lag Measurement")
        print(f"{'='*70}")
        print(f"Asset prefix:        {args.asset_prefix}")
        print(f"Repository location: {args.repo_location}")
        print(f"Dagster URL:         {url}")
        print(f"Test runs:           {args.runs}")
        print(f"{'='*70}")

    # Measure
    if args.verbose:
        print(f"Number of assets:    {num_assets}")
        print(f"{'='*70}")

    result = measure_lag(
        client,
        args.asset_prefix,
        num_assets,
        args.repo_location,
        args.runs,
        args.verbose,
    )

    # Results
    enqueue_lags = result['enqueue_to_start']
    step_lags = result['start_to_step']

    if not enqueue_lags or not step_lags:
        print("\nNo successful measurements")
        sys.exit(1)

    avg_enqueue = sum(enqueue_lags) / len(enqueue_lags)
    avg_step = sum(step_lags) / len(step_lags)
    avg_total = avg_enqueue + avg_step

    if args.verbose:
        print(f"\n{'='*70}")
        print("RESULTS")
        print(f"{'='*70}")
    else:
        print()

    print(f"Successful runs: {len(enqueue_lags)}/{args.runs}")
    print()
    print(f"Queue time (Enqueued→Start):  {avg_enqueue:.3f}s ({avg_enqueue*1000:.0f}ms)")
    print(f"Init time (Start→Step):       {avg_step:.3f}s ({avg_step*1000:.0f}ms)")
    print(f"Total lag:                    {avg_total:.3f}s ({avg_total*1000:.0f}ms)")

    if avg_total > 5:
        print(f"\n⚠️  Significant lag detected ({avg_total:.1f}s average)")

    # Return averages for use by other scripts
    print(f"\n{json.dumps({'enqueue_to_start': avg_enqueue, 'start_to_step': avg_step})}")


if __name__ == "__main__":
    main()
