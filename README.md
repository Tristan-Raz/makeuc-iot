# Aegis: A Zero Trust IoT Gateway
**MakeUC 2025 Project**

This project is a software-only simulation of a Zero Trust framework for IoT networks, built for the "Bettering Society" theme. We demonstrate how to protect critical hospital infrastructure (like patient heart monitors) from being attacked by low-trust devices (like a hacked Patient TV) on the same network.

## 🏥 The "Hospital Network" Scenario
* **Heart Monitor (High Trust):** Needs to send data to the `/vitals-db`. **Access Should Be GRANTED.**
* **Patient TV (Low Trust):** Tries to access the `/vitals-db`. **Access Should Be DENIED (Policy).**
* **Hacker (No Trust):** Tries to spoof a token to access `/vitals-db`. **Access Should Be DENIED (Spoofing).**

## 🗺️ Project Architecture

This diagram shows how all the pieces of our simulation fit together.

```mermaid
graph TD
    subgraph "Host PC"
        
        subgraph IoT_Network ["IoT-Network (Internal vSwitch)"]
            
            subgraph VM_Gateway ["VM-Gateway"]
                Gateway["gateway.py 🧠\n192.168.100.10"]
                Log["log.txt 📄"]
                Gateway --> |Writes to| Log
            end

            subgraph VM_Devices ["VM-Devices"]
                Simulator["device_simulator.py 🎭\n192.168.100.20"]
            end

        end

        subgraph Host_OS ["Host OS"]
            Dashboard["dashboard.py 📊"]
        end

        Simulator --> |HTTP Request| Gateway
        Log -.-> |Reads| Dashboard
    end
