"""GraphQL client for Dagster with authentication support."""

import base64
from typing import Any

import requests


class DagsterGraphQLClient:
    """GraphQL client for Dagster with basic auth support."""

    def __init__(
        self,
        url: str,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize client with URL and optional basic auth credentials."""
        self.url = url if url.endswith('/graphql') else f"{url}/graphql"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

        if username and password:
            credentials = f"{username}:{password}"
            encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
            self.session.headers.update({'Authorization': f'Basic {encoded}'})

    def _execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        """Execute a GraphQL query."""
        payload: dict[str, Any] = {'query': query}
        if variables:
            payload['variables'] = variables

        try:
            response = self.session.post(self.url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result.get('data', {})
        except requests.exceptions.RequestException as e:
            raise Exception(f"GraphQL request failed: {e}") from e

