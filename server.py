import os
import urllib3
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from pyFMG.fortimgr import FortiManager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

FMG_HOST = os.getenv("FMG_HOST")
FMG_API_KEY = os.getenv("FMG_API_KEY")

mcp = FastMCP("Fortinet FortiManager", host="0.0.0.0", port=8000)


def _fmg_get(endpoint: str) -> list:
    """Connect to FortiManager, execute a GET request, return data."""
    with FortiManager(FMG_HOST, apikey=FMG_API_KEY, verify_ssl=False) as fmg:
        status, data = fmg.get(endpoint)
        if status != 0:
            raise RuntimeError(f"FortiManager API error (status {status}): {data}")
        return data


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


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
