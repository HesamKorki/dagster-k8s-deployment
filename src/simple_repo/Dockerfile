FROM python:3.11-slim

WORKDIR /app

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml .

# Install dependencies using uv
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy the Dagster code
COPY dagster_code.py .

# IMPORTANT: ASSET_PREFIX must be set at deployment time
# It ensures stable asset IDs across all Dagster processes
# Without it, the code will fail with a clear error message
# Example: docker run -e ASSET_PREFIX=test ...

