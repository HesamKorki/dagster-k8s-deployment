import os
import time
from datetime import datetime
from dagster import asset, Definitions, DailyPartitionsDefinition, HourlyPartitionsDefinition


# Get configuration from environment variables
NUM_ASSETS = int(os.getenv("NUM_ASSETS", "100"))
NUM_PARTITIONS = int(os.getenv("NUM_PARTITIONS", "0"))  # 0 means no partitions
PARTITION_TYPE = os.getenv("PARTITION_TYPE", "daily").lower()  # daily or hourly

# Get asset prefix - REQUIRED to ensure stable asset IDs across process restarts
ASSET_PREFIX = os.getenv("ASSET_PREFIX")

if not ASSET_PREFIX:
    raise ValueError(
        "ASSET_PREFIX environment variable must be set! "
        "This ensures stable asset IDs across Dagster process restarts. "
        "Set it to a unique identifier for this deployment, e.g., 'dev1', 'test', 'prod'. "
        "Example: export ASSET_PREFIX=dev1"
    )


# Create partition definition if needed
partitions_def = None
if NUM_PARTITIONS > 0:
    from datetime import timedelta
    
    # Use a FIXED end date to ensure stable partition definitions across restarts
    # This prevents partition definitions from changing when code is reloaded
    end_date = datetime(2025, 11, 1)  # Fixed: November 1, 2025
    
    if PARTITION_TYPE == "hourly":
        # For hourly partitions, go back NUM_PARTITIONS hours from fixed end date
        start_datetime = end_date - timedelta(hours=NUM_PARTITIONS)
        start_date = start_datetime.strftime("%Y-%m-%d-%H:00")
        partitions_def = HourlyPartitionsDefinition(start_date=start_date)
    else:  # daily (default)
        # For daily partitions, go back NUM_PARTITIONS days from fixed end date
        start_datetime = end_date - timedelta(days=NUM_PARTITIONS)
        start_date = start_datetime.strftime("%Y-%m-%d")
        partitions_def = DailyPartitionsDefinition(start_date=start_date)


# Dynamically create assets
def create_dummy_asset(i):
    if partitions_def:
        @asset(
            name=f"{ASSET_PREFIX}_dummy_asset_{i}",
            partitions_def=partitions_def
        )
        def dummy_asset():
            """A partitioned dummy asset that sleeps for 100ms."""
            time.sleep(0.1)  # Sleep for 100ms
            return f"Asset {ASSET_PREFIX}_{i} completed"
    else:
        @asset(name=f"{ASSET_PREFIX}_dummy_asset_{i}")
        def dummy_asset():
            """A dummy asset that sleeps for 100ms."""
            time.sleep(0.1)  # Sleep for 100ms
            return f"Asset {ASSET_PREFIX}_{i} completed"
    
    return dummy_asset


# Generate all assets
assets = [create_dummy_asset(i) for i in range(NUM_ASSETS)]


# Define the code location
defs = Definitions(
    assets=assets,
)
