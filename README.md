# NetConfig AI Simulator — Advanced college project

## Features
- Python-based simulated network with PCs and router-like nodes.
- Fault injection for duplicate IP, invalid mask, wrong gateway, link down and ACL deny.
- Simulated ping tests.
- Diagnostic rules with severity, evidence and recommendations.
- Random Forest risk-category demo.
- Streamlit web dashboard and CSV export.
- Unit tests.

## Requirements
Python 3.10+ and internet for first-time dependency installation.

## Windows setup
Extract the ZIP, open the folder in VS Code, then run:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed in the terminal, usually `http://localhost:8501`.

## Run tests
```powershell
python -m unittest discover -s tests -v
```

## Demonstration
1. Start the app; select PC-A -> PC-B and run simulated ping.
2. Run diagnostics on the baseline.
3. Use the sidebar to inject Duplicate IP, then rerun ping and diagnostics.
4. Repeat for Invalid subnet mask, Wrong gateway, Link down and ACL deny.
5. Download the CSV report.
6. Reset the network between experiments.

## Architecture
Network state -> simulated ping -> deterministic diagnostics -> feature extraction -> Random Forest risk category -> dashboard/report.

## Honest ML note
The Random Forest is trained on synthetic feature vectors so it runs immediately. Its score is illustrative, not validated real-world accuracy. For a research-quality model, build a labelled dataset from many simulated configurations and report precision, recall, F1-score, confusion matrix and false-positive rate on held-out scenarios.

## Scope
This is a simplified educational simulator, not a full TCP/IP emulator. It does not implement actual packet transmission, ARP, VLAN forwarding, routing protocols, packet timing or production device management.
