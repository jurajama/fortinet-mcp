#!/usr/bin/env python3
"""Test FortiManager /sys/proxy/json IPsec tunnel status.
Run: source venv/bin/activate && python fortitest.py
"""
import os, json, urllib3
from dotenv import load_dotenv
from pyFMG.fortimgr import FortiManager

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()

FMG_HOST = os.getenv("FMG_HOST")
FMG_API_KEY = os.getenv("FMG_API_KEY")
ADOM = "fin-3001126209"
DEVICE = "trv-sdwan-tre-lte"

with FortiManager(FMG_HOST, apikey=FMG_API_KEY, verify_ssl=False) as fmg:
    status, data = fmg.execute("/sys/proxy/json", data={
        "action": "get",
        "resource": "/api/v2/monitor/vpn/ipsec",
        "target": [f"adom/{ADOM}/device/{DEVICE}"],
    })

print(f"FMG status: {status}")
print(json.dumps(data, indent=2))
