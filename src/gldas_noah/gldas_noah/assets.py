from dagster import asset

@asset
def gldas_noah025_3h():
    return "gldas_noah025_3h"
