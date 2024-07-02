import os
import requests
import time

from dagster import asset, AssetExecutionContext, MaterializeResult


def download_file(url, directory, filename=None):
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    local_filename = filename if filename else url.split('/')[-1]
    local_path = os.path.join(directory, local_filename)

    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    
    return local_path

@asset
def gldas_noah025_3h(context: AssetExecutionContext) -> MaterializeResult:

    # Dummy file to download (to check ephermeral volume storage)
    url = "https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml"

    # Data Provider Configs
    api_key = os.getenv("GLDAS_DATA_APIKEY")

    # AWS S3
    s3_bucket = os.getenv("GLDAS_S3_BUCKET")
    s3_region = os.getenv("GLDAS_S3_REGION")
    s3_key = os.getenv("GLDAS_S3_ACCESS_KEY")
    s3_secret = os.getenv("GLDAS_S3_SECRET_KEY")

    scratch_space = "/tmp/gldas"
    context.log.info(f"Starting downloading GLDAS file from {url} to {scratch_space}")
    local_path = download_file(url, scratch_space)
    context.log.info(f"Finished downloading GLDAS file to {local_path}")
    time.sleep(60)
    return MaterializeResult(
        metadata={
            "local_path": local_path,
            "api_key": api_key,
            "s3_bucket": s3_bucket,
            "s3_region": s3_region,
            "s3_key": s3_key,
            "s3_secret": s3_secret,
        })
