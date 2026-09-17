from typing import Any
import ipaddress


def nested_get(data: dict, *keys: str, default=None) -> Any:
    """Safely access nested dictionary values."""
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


def normalize_ip(value):
    """
    Return a valid IPv4/IPv6 address or None.
    """

    if not value:
        return None

    value = str(value).strip()

    try:
        return str(ipaddress.ip_address(value))
    except ValueError:
        return None


def normalize_log(log: dict) -> dict:
    """Convert heterogeneous OSSEC events into a common structure."""

    data = log.get("data")

    if not isinstance(data, dict):
        data = {}

    return {
        # -------------------------
        # Core event information
        # -------------------------

        "timestamp": log.get("timestamp"),
        "event_id": log.get("id"),

        "agent_id": nested_get(log, "agent", "id"),
        "agent_name": nested_get(log, "agent", "name"),
        "agent_ip": normalize_ip(
            nested_get(log, "agent", "ip")
        ),

        "manager_name": nested_get(
            log,
            "manager",
            "name"
        ),

        "decoder": nested_get(
            log,
            "decoder",
            "name"
        ),

        "location": log.get("location"),

        # -------------------------
        # Rule / security metadata
        # -------------------------

        "rule_id": nested_get(
            log,
            "rule",
            "id"
        ),

        "rule_level": nested_get(
            log,
            "rule",
            "level"
        ),

        "rule_description": nested_get(
            log,
            "rule",
            "description"
        ),

        # -------------------------
        # Network
        # -------------------------

        "source_ip": normalize_ip(
            data.get("srcip")
            or data.get("src_ip")
        ),

        "source_port": (
            data.get("srcport")
            or data.get("src_port")
        ),

        "destination_ip": normalize_ip(
            data.get("dstip")
            or data.get("dst_ip")
        ),

        "destination_port": (
            data.get("dstport")
            or data.get("dst_port")
        ),

        # -------------------------
        # Users / authentication
        # -------------------------

        "source_user": data.get("srcuser"),

        "destination_user": data.get("dstuser"),

        "uid": data.get("uid"),

        # -------------------------
        # HTTP / Web
        # -------------------------

        "http_method": data.get("method"),

        "http_status": data.get("status"),

        "http_host": data.get("host"),

        "http_uri": data.get("uri"),

        "http_user_agent": data.get(
            "user_agent"
        ),

        "http_referrer": data.get(
            "referrer"
        ),

        "http_upstream_status": data.get(
            "upstream_status"
        ),

        "http_sent_to": data.get(
            "sent_to"
        ),

        "http_response_length": data.get(
            "length"
        ),

        # -------------------------
        # Original message
        # -------------------------

        "message": log.get("full_log"),

        # Keep raw structured data for now
        "data": data,
    }