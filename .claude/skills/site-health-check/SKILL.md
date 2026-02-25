---
name: site-health-check
description: Full health check for an SD-WAN site — checks tunnels, BGP, and link quality
---

Perform a complete health check for the specified device. If no device name is provided, ask the user.

## Steps

1. **Find the device**: Use `find_device` with the device name to get its ADOM and connection status. If the device is not found, stop and report the error.

2. **Check IPsec tunnels**: Use `get_ipsec_tunnels` with the ADOM and device name. Flag any tunnels not in "up" state. Note the remote gateway and phase2 selector details for any down/partial tunnels.

3. **Check SD-WAN health probes**: Use `get_sdwan_health_checks` with the ADOM and device name. Flag any interfaces with:
   - Latency > 100 ms
   - Packet loss > 1%
   - Jitter > 30 ms
   - Link status not "up"

4. **Check BGP sessions**: Use `get_bgp_neighbors` with the ADOM and device name. Flag any neighbors not in "Established" state. Note the remote AS and neighbor IP for any down sessions.

5. **Summarize**: Present the results in a structured format:
   - Device info (name, serial, platform, connection status, ADOM)
   - Tunnel summary table: name, status, remote gateway
   - Link quality table: interface, health check, latency, jitter, packet loss, link status
   - BGP summary table: neighbor IP, remote AS, state
   - Overall assessment: list any issues found and recommended actions
   - If everything is healthy, state that clearly
