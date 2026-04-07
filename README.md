Remote System Health Monitoring Service

## Overview
This project implements a socket-based distributed monitoring system that collects system health metrics from multiple remote nodes (agents) and aggregates them at a central server.

The server analyzes incoming data and generates alerts when predefined thresholds are exceeded. The system uses UDP for fast metric transmission and TLS for secure communication.

Metrics Assessed - CPU Usage, Disk Usage, Memory Usage

## Objectives
- Periodic collection of system metrics  
- Multi-client monitoring  
- Centralized data aggregation  
- Threshold-based alert generation  
- Secure communication using TLS  
- Performance evaluation under load  

---

##  Architecture
- Agent (Client) 
  Collects system metrics and sends them to the server using UDP. Also receives alerts via TLS.

- Server  
  Receives metrics, analyzes data, detects threshold violations, and sends alerts back to agents.

---

##  Technologies Used
- Python  
- Socket Programming (UDP & TCP)  
- SSL/TLS Encryption  
- Multithreading  
- JSON  

---

## Project Structure
project/
│
├── server.py
├── agent.py
├── generate_certs.py
├── perf_test.py
├── certs/
└── requirements.txt