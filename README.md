# 🛡️ Zero Trust for IoT - makeUC Hackathon

**Our submission for the makeUC Hackathon. This is a 3-VM simulation of a Zero Trust IoT network for a hospital, designed to show how identity-first security can protect critical systems.**

This project demonstrates how a central gateway can enforce "least-privilege" access by validating identity tokens (JWTs) for every single network request, effectively stopping impersonation and spoofing attacks.

## 💡 How It Works

This project simulates a secure hospital network using three distinct roles, which can be run on three separate Virtual Machines:

* **VM 1: The Gateway (`auth0_server.py`)**
    This is the "brain" of the network. It's a **FastAPI** server that intercepts all traffic. It validates Auth0 JWTs, checks for specific permissions (like `write:vitals`), and logs every success, policy denial, or attack attempt.

* **VM 2: The Dashboard (`dashboard.py`)**
    This is the "Security Operations Center." It's a **Streamlit** application that reads the Gateway's logs in real-time to provide a live view of all network activity, clearly showing granted, denied, and spoofing events.

* **VM 3: The Simulator (`attack_simulator.py`)**
    This script simulates all "devices" on the network. It sends requests from valid devices (like a Heart Monitor) and malicious devices (like an Attacker) to test the Gateway's defenses.

## 💻 Tech Stack

* **Backend:** FastAPI
* **Frontend:** Streamlit
* **Security:** Auth0 for identity & RS256 JWT Validation
* **Language:** Python
* **Core Libraries:** `python-jose`, `pyjwt`, `requests`, `pandas`

## 🚀 How to Run

1.  **Clone Repo:** `git clone https://github.com/Tristan-Raz/makeuc-iot.git` onto three separate VMs.
2.  **Install Dependencies:** On all VMs, create a virtual environment and install the requirements:
    ```bash
    # Create and activate the venv
    python3 -m venv venv
    source venv/bin/activate
    
    # Install packages
    pip install fastapi "uvicorn[standard]" streamlit requests pandas "python-jose[cryptography]" pyjwt
    ```
3.  **Find Gateway IP:** On **VM 1**, find its private IP address (e.g., `192.168.56.101`) using `ip addr show`.
4.  **Update Code:** On **VM 2** and **VM 3**, edit `attack_simulator.py` and `dashboard.py` to point the `API_URL_BASE` variable to the Gateway's IP.
5.  **Run the Project:**
    * **On VM 1 (Gateway):** `uvicorn auth0_server:app --host 0.0.0.0 --port 8000`
    * **On VM 2 (Dashboard):** `streamlit run dashboard.py`
    * **On VM 3 (Attacker):** `python attack_simulator.py`

## 👥 The Team

* **Tobore Takpor**
* **Michael Vargas**
* **Antonio K.**
* **Tristan Razote**