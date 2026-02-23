import os
import time
import urllib3
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pyFMG.fortimgr import FortiManager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

FMG_HOST = os.getenv("FMG_HOST")
FMG_API_KEY = os.getenv("FMG_API_KEY")

mcp = FastMCP("Fortinet FortiManager", host="0.0.0.0", port=8000)


def _fmg_get(endpoint: str, retries: int = 3, retry_delay: float = 5.0, **params) -> list:
    """Connect to FortiManager, execute a GET request, return data.

    Any additional keyword arguments (e.g. filter, fields, loadsub) are
    forwarded to pyFMG's fmg.get() and merged into the JSON-RPC params.

    Retries up to `retries` times with `retry_delay` second intervals on
    status -11 ('No permission for the resource'), a known FortiManager bug.
    """
    for attempt in range(retries + 1):
        with FortiManager(FMG_HOST, apikey=FMG_API_KEY, verify_ssl=False) as fmg:
            status, data = fmg.get(endpoint, **params)
        if status == 0:
            return data
        if status == -11 and attempt < retries:
            time.sleep(retry_delay)
            continue
        raise RuntimeError(f"FortiManager API error (status {status}): {data}")


def _fmg_execute(endpoint: str, data: dict, retries: int = 3, retry_delay: float = 5.0) -> list | dict:
    """Connect to FortiManager, execute an exec-method request, return data.

    Used for proxy calls and other exec-type operations that require a payload.
    Retries on status -11 with the same logic as _fmg_get().
    """
    for attempt in range(retries + 1):
        with FortiManager(FMG_HOST, apikey=FMG_API_KEY, verify_ssl=False) as fmg:
            status, result = fmg.execute(endpoint, data=data)
        if status == 0:
            return result
        if status == -11 and attempt < retries:
            time.sleep(retry_delay)
            continue
        raise RuntimeError(f"FortiManager API error (status {status}): {result}")


@mcp.tool()
def list_adoms() -> list[dict]:
    """List all ADOMs (Administrative Domains) on FortiManager."""
    data = _fmg_get("/dvmdb/adom")
    return [{"name": adom["name"]} for adom in data]


@mcp.tool()
def list_devices(adom: str) -> list[dict]:
    """List all devices in a FortiManager ADOM.

    Args:
        adom: The ADOM name (e.g. 'fin-3001126209').
    """
    data = _fmg_get(f"/dvmdb/adom/{adom}/device")
    return [
        {
            "name": device["name"],
            "serial": device.get("sn", ""),
            "platform": device.get("platform_str", ""),
            "conn_status": device.get("conn_status", ""),
        }
        for device in data
    ]


@mcp.tool()
def find_device(device_name: str) -> dict:
    """Find a device across all ADOMs and return its details including ADOM membership.

    Queries the global device table instead of iterating ADOM by ADOM,
    making it much faster when there are many ADOMs.

    Args:
        device_name: The device name as it appears in FortiManager (e.g. 'FGT-BRANCH-01').

    Returns a dict with:
        name, serial, platform, conn_status, adom (the ADOM the device belongs to).
        Returns an error dict if the device is not found.
    """
    data = _fmg_get(
        "/dvmdb/device",
        filter=[["name", "==", device_name]],
        option=["extra info"],
    )
    if not data:
        return {"error": f"Device '{device_name}' not found in any ADOM"}
    device = data[0]
    # ADOM is in "extra info" dict (confirmed on FMG 7.4, stable across 7.x)
    extra = device.get("extra info") or {}
    adom = extra.get("adom", "")
    return {
        "name": device.get("name", ""),
        "serial": device.get("sn", ""),
        "platform": device.get("platform_str", ""),
        "conn_status": device.get("conn_status", ""),
        "adom": adom,
    }


@mcp.tool()
def get_device_interfaces(adom: str, device: str) -> list[dict]:
    """Get network interfaces for a FortiGate device managed by FortiManager.

    Reads interface configuration from FortiManager's stored config database.

    Args:
        adom: The ADOM name the device belongs to (e.g. 'fin-3001126209').
        device: The device name as it appears in FortiManager (e.g. 'FGT-BRANCH-01').

    Returns a list of interfaces, each with:
        name, ip, netmask, type, status, alias, description,
        vlanid (int or None), parent_interface (str, for VLAN interfaces).
    """
    data = _fmg_get(f"/pm/config/device/{device}/global/system/interface")
    if isinstance(data, dict):
        data = [data]
    result = []
    for iface in data:
        ip_raw = iface.get("ip", "")
        if isinstance(ip_raw, list):
            parts = ip_raw
        elif isinstance(ip_raw, str):
            parts = ip_raw.split() if ip_raw else []
        else:
            parts = []
        result.append({
            "name": iface["name"],
            "ip": parts[0] if len(parts) > 0 else "",
            "netmask": parts[1] if len(parts) > 1 else "",
            "type": iface.get("type", ""),
            "status": iface.get("status", ""),
            "alias": iface.get("alias", ""),
            "description": iface.get("description", ""),
            "vlanid": iface.get("vlanid", None),
            "parent_interface": iface.get("interface", ""),
        })
    return result


@mcp.tool()
def get_ipsec_tunnels(adom: str, device: str) -> list[dict]:
    """Get live IPsec VPN tunnel status for a FortiGate device via FortiManager proxy.

    Queries the FortiGate in real-time through FortiManager's /sys/proxy/json
    endpoint, which proxies to FortiOS REST API /api/v2/monitor/vpn/ipsec.
    The device must be online and reachable from FortiManager.

    Args:
        adom: The ADOM name the device belongs to (e.g. 'fin-3001126209').
        device: The device name as it appears in FortiManager (e.g. 'trv-sdwan-tre-lte').

    Returns a list of IPsec tunnels, each with:
        name, status (up/down/partial/unknown), remote_gateway,
        incoming_bytes, outgoing_bytes, creation_time (Unix epoch),
        phase2_selectors (list with name, src, dst, status per selector).
    """
    raw = _fmg_execute("/sys/proxy/json", data={
        "action": "get",
        "resource": "/api/v2/monitor/vpn/ipsec",
        "target": [f"adom/{adom}/device/{device}"],
    })

    if not raw or not isinstance(raw, list):
        return []

    target_response = raw[0]
    fgt_status = target_response.get("status", {}).get("code", -1)
    if fgt_status != 0:
        raise RuntimeError(
            f"FortiGate proxy error (code {fgt_status}) for {device}: "
            f"{target_response.get('status', {})}"
        )

    tunnels = (target_response.get("response") or {}).get("results") or []
    result = []
    for t in tunnels:
        phase2 = []
        for p2 in (t.get("proxyid") or []):
            src_list = p2.get("proxy_src") or []
            dst_list = p2.get("proxy_dst") or []
            phase2.append({
                "name": p2.get("p2name", ""),
                "src": src_list[0]["subnet"] if src_list else "",
                "dst": dst_list[0]["subnet"] if dst_list else "",
                "status": p2.get("status", ""),
            })
        p2_statuses = {p["status"] for p in phase2}
        if not p2_statuses:
            tunnel_status = "unknown"
        elif p2_statuses == {"up"}:
            tunnel_status = "up"
        elif p2_statuses == {"down"}:
            tunnel_status = "down"
        else:
            tunnel_status = "partial"
        result.append({
            "name": t.get("name", ""),
            "status": tunnel_status,
            "remote_gateway": t.get("rgwy", ""),
            "incoming_bytes": t.get("incoming_bytes", 0),
            "outgoing_bytes": t.get("outgoing_bytes", 0),
            "creation_time": t.get("creation_time", None),
            "phase2_selectors": phase2,
        })
    return result


@mcp.tool()
def get_sdwan_health_checks(adom: str, device: str) -> list[dict]:
    """Get live SD-WAN health check (SLA monitor) status for a FortiGate device.

    Queries the FortiGate in real-time through FortiManager's proxy endpoint.
    Returns the most recent latency, jitter, and packet loss measurement per
    SD-WAN interface per health check — the primary way to assess overlay link
    quality beyond simple tunnel up/down status.

    Args:
        adom: The ADOM name the device belongs to (e.g. 'fin-3001126209').
        device: The device name as it appears in FortiManager (e.g. 'trv-sdwan-tre-lte').

    Returns a list of health check entries, each with:
        health_check (name), interface, link (up/down),
        latency (ms), jitter (ms), packet_loss (%),
        timestamp (Unix epoch of the measurement).
        If no recent measurement is available, metrics are None.
    """
    raw = _fmg_execute("/sys/proxy/json", data={
        "action": "get",
        "resource": "/api/v2/monitor/virtual-wan/sla-log",
        "target": [f"adom/{adom}/device/{device}"],
    })

    if not raw or not isinstance(raw, list):
        return []

    target_response = raw[0]
    response = target_response.get("response") or {}
    if response.get("status") == "error":
        raise RuntimeError(
            f"FortiGate proxy error for {device}: {response}"
        )

    results = response.get("results") or []
    output = []
    for entry in results:
        logs = entry.get("logs") or []
        latest = logs[-1] if logs else {}
        output.append({
            "health_check": entry.get("name", ""),
            "interface": entry.get("interface", ""),
            "link": latest.get("link", "no data"),
            "latency": latest.get("latency"),
            "jitter": latest.get("jitter"),
            "packet_loss": latest.get("packetloss"),
            "timestamp": latest.get("timestamp"),
        })
    return output


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
