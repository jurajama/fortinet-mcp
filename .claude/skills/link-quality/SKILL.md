---
name: link-quality
description: Compare SD-WAN link quality across all interfaces on a device
---

Analyze and compare SD-WAN link quality for the specified device. If no device name is provided, ask the user.

## Steps

1. **Find the device**: Use `find_device` with the device name to get its ADOM. If the device is not found, stop and report the error.

2. **Get SD-WAN health checks**: Use `get_sdwan_health_checks` with the ADOM and device name to get current link quality measurements for all interfaces.

3. **Rank and compare**: Create a table ranking all interfaces by quality. Sort by link status (down links last), then by latency (lowest first). Include columns:
   - Interface name
   - Health check name
   - Link status (up/down)
   - Latency (ms)
   - Jitter (ms)
   - Packet loss (%)

4. **Flag SLA violations**: Highlight any interfaces exceeding these thresholds:
   - Latency > 100 ms
   - Jitter > 30 ms
   - Packet loss > 1%
   - Link down

5. **Summarize**: Present:
   - The ranked link quality table
   - Best performing link(s) and worst performing link(s)
   - Any links with SLA violations
   - If all links are healthy, state that clearly
