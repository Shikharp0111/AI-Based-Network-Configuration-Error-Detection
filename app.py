import pandas as pd
import streamlit as st
from network_sim import demo_network
from diagnostics import diagnose, feature_vector
from ml_model import train_demo_model, predict_risk

st.set_page_config(page_title="NetConfig AI Simulator", page_icon="🛡️", layout="wide")
st.title("🛡️ NetConfig AI Simulator")
st.caption("AI-Based Network Configuration Error Detection • Python simulation + web dashboard")

@st.cache_resource
def get_model():
    return train_demo_model()

if "network" not in st.session_state:
    st.session_state.network = demo_network()
if "last_issues" not in st.session_state:
    st.session_state.last_issues = None

net = st.session_state.network
with st.sidebar:
    st.header("Fault injection lab")
    st.write("Select a fault and inject it into the simulated network.")
    fault = st.selectbox("Fault type", [
        "None / reset demo", "Duplicate IP", "Invalid subnet mask",
        "Wrong gateway", "Link down", "ACL deny"
    ])
    if st.button("Apply selected fault", use_container_width=True):
        if fault == "None / reset demo":
            st.session_state.network = demo_network()
        elif fault == "Duplicate IP":
            net.hosts["PC-B"].ip = net.hosts["PC-A"].ip
        elif fault == "Invalid subnet mask":
            net.hosts["PC-A"].mask = "255.0.255.0"
        elif fault == "Wrong gateway":
            net.hosts["PC-A"].gateway = "10.10.10.1"
        elif fault == "Link down":
            net.set_link("PC-A", "R1", False)
        elif fault == "ACL deny":
            net.acls = []
            net.add_acl("PC-A", "PC-B", "deny")
        st.session_state.last_issues = None
        st.rerun()
    if st.button("Reset network", use_container_width=True):
        st.session_state.network = demo_network()
        st.session_state.last_issues = None
        st.rerun()

st.subheader("Simulated topology")
st.markdown("`PC-A` ── `R1` ── `R2` ── `PC-C`  |  `PC-B` ── `R1`")
host_rows = []
for h in net.hosts.values():
    host_rows.append({"Device":h.name,"IPv4":h.ip,"Mask":h.mask,
                      "Gateway":h.gateway or "—","Enabled":h.enabled})
st.dataframe(pd.DataFrame(host_rows), use_container_width=True, hide_index=True)

st.subheader("Connectivity test")
left, right = st.columns(2)
with left:
    source = st.selectbox("Source", list(net.hosts.keys()), index=0)
with right:
    dest = st.selectbox("Destination", list(net.hosts.keys()), index=1)
if st.button("Run simulated ping", type="primary"):
    result = net.ping(source, dest)
    if result["success"]:
        st.success(f"PING {source} → {dest}: SUCCESS — {result['reason']}")
    else:
        st.error(f"PING {source} → {dest}: FAILED — {result['reason']}")

if st.button("Run AI-assisted diagnostics", use_container_width=True):
    issues = diagnose(net)
    st.session_state.last_issues = issues
    features = feature_vector(issues)
    label, prob = predict_risk(get_model(), features)
    a,b,c = st.columns(3)
    a.metric("Devices", len(net.hosts))
    b.metric("Findings", len(issues))
    c.metric("ML risk category", label, f"{prob:.0%} demo score")
    st.progress(prob, text=f"Illustrative ML risk score: {prob:.0%}")
    st.info("The classifier uses synthetic training data for demonstration. Rule findings are the evidence; the risk score is not validated production accuracy.")

issues = st.session_state.last_issues
if issues is not None:
    st.subheader("Diagnostic findings")
    if issues:
        df = pd.DataFrame(issues)
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Download findings as CSV", df.to_csv(index=False).encode("utf-8"),
                           "netconfig_findings.csv", "text/csv")
    else:
        st.success("No issues detected by the configured rules.")
    st.subheader("Network state")
    st.json(net.export_state())

with st.expander("How the AI component works"):
    st.markdown("""
    1. The simulator stores devices, addresses, links and ACL rules.
    2. The diagnostic engine validates IPs, masks, gateways, duplicate addresses, link status and ACL deny rules.
    3. Findings are converted to a numeric feature vector.
    4. A Random Forest classifies the vector into an illustrative risk category.
    5. The dashboard displays findings and exports a CSV report.
    """)

with st.expander("Limitations"):
    st.markdown("""
    This is a simplified educational simulator, not a full TCP/IP emulator. Its gateway model is intentionally basic and does not implement routing tables, ARP, VLAN switching, spanning tree, packet timing or real packet transmission. The ML training data is synthetic; do not claim real-world accuracy. Production-grade evaluation requires labelled data and held-out testing.
    """)
