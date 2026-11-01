"""Small deterministic IPv4 network simulator for a classroom project."""
from dataclasses import dataclass, asdict
import ipaddress

@dataclass
class Host:
    name: str
    ip: str
    mask: str
    gateway: str = ""
    enabled: bool = True

@dataclass
class Link:
    source: str
    target: str
    up: bool = True

@dataclass
class ACLRule:
    source: str = "any"
    destination: str = "any"
    action: str = "permit"

class Network:
    def __init__(self):
        self.hosts = {}
        self.links = []
        self.acls = []

    def add_host(self, name, ip, mask, gateway="", enabled=True):
        self.hosts[name] = Host(name, ip, mask, gateway, enabled)

    def add_link(self, source, target, up=True):
        self.links.append(Link(source, target, up))

    def add_acl(self, source="any", destination="any", action="permit"):
        self.acls.append(ACLRule(source, destination, action))

    def set_link(self, source, target, up):
        found = False
        for link in self.links:
            if {link.source, link.target} == {source, target}:
                link.up = up
                found = True
        if not found:
            self.add_link(source, target, up)

    def link_up(self, source, target):
        return any({x.source, x.target} == {source, target} and x.up for x in self.links)

    def path_exists(self, source, target):
        if source not in self.hosts or target not in self.hosts:
            return False, "Source or destination host does not exist."
        if not self.hosts[source].enabled or not self.hosts[target].enabled:
            return False, "Source or destination host is disabled."
        graph = {name: [] for name in self.hosts}
        for link in self.links:
            if link.up and link.source in graph and link.target in graph:
                graph[link.source].append(link.target)
                graph[link.target].append(link.source)
        todo, seen = [source], {source}
        while todo:
            node = todo.pop(0)
            if node == target:
                return True, "Physical/logical path exists in the simulator."
            for nxt in graph[node]:
                if nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        return False, "No active link path connects source and destination."

    def ping(self, source, target):
        if source not in self.hosts or target not in self.hosts:
            return {"success": False, "reason": "Unknown source or destination."}
        a, b = self.hosts[source], self.hosts[target]
        if not a.enabled or not b.enabled:
            return {"success": False, "reason": "Source or destination is disabled."}
        try:
            ip_a = ipaddress.IPv4Address(a.ip)
            ip_b = ipaddress.IPv4Address(b.ip)
            net_a = ipaddress.IPv4Network(f"{a.ip}/{a.mask}", strict=False)
            net_b = ipaddress.IPv4Network(f"{b.ip}/{b.mask}", strict=False)
        except (ValueError, ipaddress.NetmaskValueError):
            return {"success": False, "reason": "Invalid IP address or subnet mask."}

        for acl in self.acls:
            src_match = acl.source == "any" or acl.source == a.ip
            dst_match = acl.destination == "any" or acl.destination == b.ip
            if src_match and dst_match and acl.action.lower() == "deny":
                return {"success": False, "reason": "Traffic denied by simulated ACL."}

        if ip_a == ip_b and source != target:
            return {"success": False, "reason": "Duplicate IP address detected."}

        if net_a.network_address == ip_a and net_a.prefixlen < 31:
            return {"success": False, "reason": f"{a.ip} is the source subnet's network address."}
        if net_b.network_address == ip_b and net_b.prefixlen < 31:
            return {"success": False, "reason": f"{b.ip} is the destination subnet's network address."}
        if net_a.broadcast_address == ip_a and net_a.prefixlen < 31:
            return {"success": False, "reason": f"{a.ip} is the source subnet's broadcast address."}
        if net_b.broadcast_address == ip_b and net_b.prefixlen < 31:
            return {"success": False, "reason": f"{b.ip} is the destination subnet's broadcast address."}

        connected, why = self.path_exists(source, target)
        if not connected:
            return {"success": False, "reason": why}

        if net_a == net_b:
            return {"success": True, "reason": "Hosts share a subnet and an active path exists."}

        # This simplified simulator treats a node's configured gateway as reachable
        # if it is a valid address inside the host's own subnet.
        try:
            gw_a = ipaddress.IPv4Address(a.gateway)
            gw_b = ipaddress.IPv4Address(b.gateway)
        except ValueError:
            return {"success": False, "reason": "Different subnets require valid configured gateways in this simulator."}
        if gw_a not in net_a or gw_b not in net_b:
            return {"success": False, "reason": "Configured gateway is outside the host's own subnet."}
        return {"success": True, "reason": "Different-subnet path accepted by simplified gateway model."}

    def export_state(self):
        return {
            "hosts": [asdict(h) for h in self.hosts.values()],
            "links": [asdict(l) for l in self.links],
            "acls": [asdict(a) for a in self.acls]
        }

def demo_network():
    n = Network()
    n.add_host("PC-A", "192.168.10.10", "255.255.255.0", "192.168.10.1")
    n.add_host("PC-B", "192.168.10.11", "255.255.255.0", "192.168.10.1")
    n.add_host("R1", "192.168.10.1", "255.255.255.0", "")
    n.add_host("PC-C", "192.168.20.10", "255.255.255.0", "192.168.20.1")
    n.add_host("R2", "192.168.20.1", "255.255.255.0", "")
    n.add_link("PC-A", "R1")
    n.add_link("PC-B", "R1")
    n.add_link("R1", "R2")
    n.add_link("R2", "PC-C")
    return n
