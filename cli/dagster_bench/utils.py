"""Utility functions for Dagster benchmarking."""


def parse_asset_count(prefix: str) -> int:
    """Parse asset count from prefix.

    Examples:
        '10k' -> 10000, '2k' -> 2000, 'a1p2k' -> 1, '500' -> 500
    """
    prefix = prefix.lower()

    # Handle partition format: a{assets}p{partitions}k
    if prefix.startswith('a') and 'p' in prefix:
        asset_part = prefix[1:prefix.index('p')]
        try:
            return int(asset_part)
        except ValueError:
            return 1

    # Handle k suffix: 10k -> 10000
    if prefix.endswith('k'):
        return int(prefix[:-1]) * 1000

    # Plain number: 500 -> 500
    try:
        return int(prefix)
    except ValueError:
        return 1


def get_latest_partition(
    client,
    asset_key: str,
    repo_location: str,
    verbose: bool = False,
) -> str | None:
    """Get the latest partition key for a partitioned asset."""
    query = """
    query GetAssetPartitions($assetKey: AssetKeyInput!) {
      assetNodeOrError(assetKey: $assetKey) {
        ... on AssetNode {
          partitionKeys
        }
      }
    }
    """

    try:
        result = client._execute(query, {"assetKey": {"path": [asset_key]}})
        asset_node = result.get("assetNodeOrError", {})
        partition_keys = asset_node.get("partitionKeys", [])

        if partition_keys:
            latest = partition_keys[-1]
            if verbose:
                print(f"    Found {len(partition_keys)} partitions, using latest: {latest}")
            return latest
        return None
    except Exception as e:
        if verbose:
            print(f"    Could not get partitions: {e}")
        return None

