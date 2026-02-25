---
name: tunnel-troubleshoot
description: Diagnose IPsec tunnel issues for an SD-WAN device
---

Troubleshoot IPsec tunnel connectivity for the specified device. If a specific tunnel name is provided, focus on that tunnel. Otherwise, diagnose all tunnels.

## Steps

1. **Find the device**: Use `find_device` with the device name to get its ADOM. If the device is not found, stop and report the error.

2. **Get tunnel status**: Use `get_ipsec_tunnels` with the ADOM and device name. List all tunnels with their status.

3. **Focus on problem tunnels**: Identify any tunnels that are "down" or "partial". If a specific tunnel name was given, focus on that one. For each problem tunnel, note:
   - Remote gateway IP
   - Which phase2 selectors are down vs up
   - Creation time (if available — a recent creation time suggests a flapping tunnel)

4. **Cross-reference with SD-WAN health checks**: Use `get_sdwan_health_checks` with the ADOM and device name. For each problem tunnel, check if the corresponding SD-WAN interface shows:
   - Link down
   - High latency, jitter, or packet loss

5. **Check BGP over the tunnel**: Use `get_bgp_neighbors` with the ADOM and device name. Identify if any BGP sessions use the tunnel's remote gateway or are in a non-Established state that correlates with the tunnel issue.

6. **Compare with healthy tunnels**: Compare the problem tunnel(s) against healthy ones on the same device to determine if the issue is:
   - Isolated to one tunnel (likely remote end or path issue)
   - Affecting multiple tunnels (likely local device or uplink issue)
   - Affecting all tunnels (likely device-wide connectivity problem)

7. **Diagnosis and recommendations**: Present:
   - A summary table of all tunnels (name, status, remote gateway)
   - For each problem tunnel: correlated health check and BGP data
   - Assessment: isolated vs widespread issue
   - Recommended next steps (e.g., check remote end, check underlay connectivity, check ISP link)
