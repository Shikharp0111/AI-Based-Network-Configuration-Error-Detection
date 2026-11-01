import ipaddress
from collections import defaultdict

ORDER = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}

def add(out, severity, code, finding, device, evidence, recommendation):
    out.append({
        "Severity": severity, "Code": code, "Finding": finding,
        "Device": device, "Evidence": evidence, "Recommendation": recommendation
    })

def diagnose(network):
    out = []
    seen = defaultdict(list)
    parsed_nets = {}
    for name, host in network.hosts.items():
        if not host.enabled:
            add(out, "Medium", "HOST-001", "Host disabled", name,
                "Host is marked disabled in the simulation.",
                "Enable the host if it is intended to participate in the network.")
        try:
            ip = ipaddress.IPv4Address(host.ip)
        except ValueError:
            add(out, "High", "IP-001", "Invalid IPv4 address", name,
                f"Configured address {host.ip!r} is invalid.",
                "Enter a valid IPv4 address.")
            continue
        try:
            net = ipaddress.IPv4Network(f"{host.ip}/{host.mask}", strict=False)
            parsed_nets[name] = net
        except (ValueError, ipaddress.NetmaskValueError):
            add(out, "High", "IP-002", "Invalid subnet mask", name,
                f"Mask {host.mask!r} is invalid for {host.ip}.",
                "Use a valid contiguous IPv4 subnet mask.")
            continue
        seen[str(ip)].append(name)
        if net.prefixlen < 31 and ip == net.network_address:
            add(out, "High", "IP-003", "Network address assigned to host", name,
                f"{ip} is the network address of {net}.",
                "Choose a usable host address in the intended subnet.")
        if net.prefixlen < 31 and ip == net.broadcast_address:
            add(out, "High", "IP-004", "Broadcast address assigned to host", name,
                f"{ip} is the broadcast address of {net}.",
                "Choose a usable host address in the intended subnet.")
        if host.gateway:
            try:
                gw = ipaddress.IPv4Address(host.gateway)
                if gw not in net:
                    add(out, "High", "GW-001", "Gateway outside host subnet", name,
                        f"Gateway {gw} is not inside {net}.",
                        "Set the gateway to an address reachable in the host's local subnet.")
            except ValueError:
                add(out, "High", "GW-002", "Invalid gateway address", name,
                    f"Gateway {host.gateway!r} is invalid.",
                    "Enter a valid IPv4 gateway address.")
    for ip, names in seen.items():
        if len(names) > 1:
            add(out, "Critical", "IP-005", "Duplicate IP address", ", ".join(names),
                f"{ip} is assigned to multiple simulated devices.",
                "Assign unique addresses and rerun connectivity tests.")

    for link in network.links:
        if not link.up:
            add(out, "High", "LINK-001", "Link is down",
                f"{link.source} ↔ {link.target}",
                "The simulated connection is marked down.",
                "Restore the link and rerun the ping test.")

    for acl in network.acls:
        if acl.action.lower() == "deny":
            add(out, "Medium", "ACL-001", "Simulated ACL deny rule",
                f"{acl.source} → {acl.destination}",
                "A deny rule is present in the simulator.",
                "Confirm that the rule matches the intended traffic policy.")

    out.sort(key=lambda x: (ORDER.get(x["Severity"], 9), x["Code"]))
    return out

def feature_vector(issues):
    codes = {i["Code"] for i in issues}
    return {
        "ip_issue": int(bool(codes & {"IP-001", "IP-002", "IP-003", "IP-004"})),
        "duplicate_ip": int("IP-005" in codes),
        "gateway_issue": int(bool(codes & {"GW-001", "GW-002"})),
        "link_down": int("LINK-001" in codes),
        "acl_issue": int("ACL-001" in codes),
        "disabled_host": int("HOST-001" in codes),
        "issue_count": len(issues)
    }
