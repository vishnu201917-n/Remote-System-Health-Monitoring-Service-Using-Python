# Remote System Health Monitoring Service

## Overview
The **Remote System Health Monitoring Service** is a distributed client-server application that monitors the health of multiple remote systems. Monitoring agents periodically collect system resource metrics and transmit them to a centralized server for analysis.

The server evaluates the received metrics against predefined thresholds and sends secure alerts to clients whenever abnormal resource usage is detected. The project uses **UDP** for lightweight metric transmission and **TLS-secured TCP** for encrypted alert communication.

---

## Features

- Real-time monitoring of remote systems
- Periodic collection of CPU, Memory, and Disk usage
- Multi-client support
- Centralized metric aggregation
- Threshold-based alert generation
- Secure TLS-based alert communication
- Performance testing under varying client loads

---

## System Architecture

### Agent (Client)

- Collects system health metrics periodically
- Sends monitoring data to the server using UDP
- Receives secure alerts over a TLS connection

### Server

- Accepts monitoring data from multiple clients
- Analyzes incoming metrics
- Detects threshold violations
- Sends encrypted alerts back to clients using TLS

---

## Metrics Monitored

- CPU Usage
- Memory Usage
- Disk Usage

---

## Technologies Used

- Python
- Socket Programming (UDP & TCP)
- SSL/TLS
- Multithreading
- JSON
- psutil

---

## Project Structure

```
project/
│
├── server.py              # Central monitoring server
├── agent.py               # Monitoring client/agent
├── generate_certs.py      # Generates SSL/TLS certificates
├── perf_test.py           # Performance testing script
│
├── certs/
│   ├── server.crt
│   ├── server.key
│   ├── client.crt
│   ├── client.key
│   └── ca.crt
│
└── README.md
```

---

## Prerequisites

- Python 3.10 or later

Install the required dependency:

```bash
pip install psutil
```

---

## Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd project
```

---

### 2. Generate SSL Certificates

Run the certificate generation script:

```bash
python generate_certs.py
```

This creates the certificates required for secure TLS communication.

---

## Running the Project

### Step 1 — Start the Server

```bash
python server.py
```

The server begins listening for incoming monitoring data from agents.

---

### Step 2 — Start One or More Agents

Open another terminal for each client and run:

```bash
python agent.py
```

Each agent periodically collects system metrics and sends them to the server.

---

### Step 3 — Observe Alerts

If CPU, memory, or disk usage exceeds the configured threshold, the server sends an encrypted TLS alert to the corresponding client.

---

## Performance Testing

To evaluate the system under multiple concurrent clients:

```bash
python perf_test.py
```

This simulates multiple monitoring agents and helps analyze the server's performance under load.

---

## Communication Flow

```
                       UDP Metrics
+-----------+      │
| Agent 1   |──────┐
+-----------+      │
                   │
+-----------+      │
| Agent 2   |──────┼──────────────+
+-----------+      │              │
                   │              │
+-----------+      │              ▼
| Agent N   |──────┘      +----------------------+
                           | Monitoring Server    |
                           |                      |
                           +----------------------+
                                     │
                                     │ TLS Alerts
                                     ▼
                    Alerts sent back to the respective agents
```

## Future Improvements

- Interactive monitoring dashboard
- Historical metric storage
- Email/SMS alert notifications
- Configurable monitoring intervals
- Docker deployment
- Web-based administration interface

---
