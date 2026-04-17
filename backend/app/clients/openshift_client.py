from __future__ import annotations

import base64
import logging

import httpx

from app.config import OpenShiftClusterConfig

logger = logging.getLogger(__name__)

_CREDENTIAL_PLACEHOLDERS = {"{username}", "{password}", "{host}", "{port}"}


def needs_secret(template: str) -> bool:
    """Return True if the template contains any credential placeholders."""
    return any(p in template for p in _CREDENTIAL_PLACEHOLDERS)


def apply_template(template: str, vars: dict[str, str]) -> str:
    for key, value in vars.items():
        template = template.replace(f"{{{key}}}", value)
    return template


async def fetch_secret_fields(
    cluster: OpenShiftClusterConfig,
    namespace: str,
    secret_name: str,
    fields: list[str],
    http_client: httpx.AsyncClient,
) -> dict[str, str]:
    """
    Fetch a Kubernetes/OpenShift secret and return the requested field values.
    Secret data values are base64-encoded; stringData values are plain text.
    """
    url = f"{cluster.api_url.rstrip('/')}/api/v1/namespaces/{namespace}/secrets/{secret_name}"
    headers = {"Authorization": f"Bearer {cluster.token}"}

    try:
        resp = await http_client.get(url, headers=headers)
        resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise RuntimeError(
            f"Failed to fetch secret '{secret_name}' in namespace '{namespace}' "
            f"from cluster '{cluster.cluster_name}': HTTP {exc.response.status_code}"
        ) from exc
    except httpx.HTTPError as exc:
        raise RuntimeError(
            f"Network error fetching secret from cluster '{cluster.cluster_name}': {exc}"
        ) from exc

    body = resp.json()
    # Secrets have `data` (base64) and optionally `stringData` (plain)
    raw_data: dict[str, str] = body.get("data") or {}
    string_data: dict[str, str] = body.get("stringData") or {}

    result: dict[str, str] = {}
    for field in fields:
        if field in string_data:
            result[field] = string_data[field]
        elif field in raw_data:
            result[field] = base64.b64decode(raw_data[field]).decode()
        else:
            logger.warning(
                "Field '%s' not found in secret '%s' (cluster: %s)",
                field,
                secret_name,
                cluster.cluster_name,
            )
            result[field] = ""

    return result
