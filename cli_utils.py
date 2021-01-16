from typing import Tuple
from pathlib import Path


def iface_type(v: str) -> str:
    if len(v) > 16:
        raise ValueError(f"Interface name ('{v}') is too long")

    if Path(f"/sys/class/net/{v}").exists():
        raise ValueError(f"Interface '{v}' already exist")

    return v


def endpoint_type(v: str) -> Tuple[str, int]:
    try:
        host, port = v.split(":")
    except ValueError:
        raise ValueError("Endpoint format: <HOST>:<PORT>")
    return host, int(port)
