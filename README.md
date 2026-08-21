# Distributed Systems Lab: HTTP Load Balancer with Multiple Backends

A complete, high-performance, and modular Distributed Systems Load Balancer project. Features a reverse proxy Load Balancer (Sys1), three scalable Messaging Project backend servers (Sys2, Sys3, Sys4), a high-concurrency benchmark Load Generator, and automated experiment orchestration tools.

---

## Table of Contents
- [System Architecture](#system-architecture)
- [Network Configuration](#network-configuration)
- [Features](#features)
- [Prerequisites & Installation](#prerequisites--installation)
- [Quick Start: Automated One-Click Runner](#quick-start-automated-one-click-runner)
- [Step-by-Step Manual Deployment](#step-by-step-manual-deployment)
  - [1. Start Backend Servers (Sys2, Sys3, Sys4)](#1-start-backend-servers-sys2-sys3-sys4)
  - [2. Verify Independent Reachability](#2-verify-independent-reachability)
  - [3. Start Sys1 Load Balancer](#3-start-sys1-load-balancer)
  - [4. Run Load Generator](#4-run-load-generator)
- [Running Lab Experiments](#running-lab-experiments)
  - [Experiment 1: Single Backend (Sys2)](#experiment-1-single-backend-sys2)
  - [Experiment 2: Three Backends (Sys2, Sys3, Sys4)](#experiment-2-three-backends-sys2-sys3-sys4)
  - [Performance Comparison Analysis](#performance-comparison-analysis)
- [API Endpoints Reference](#api-endpoints-reference)
- [Testing & Quality Assurance](#testing--quality-assurance)

---

## System Architecture

```text
                 +-----------------------------+
                 |       Load Generator        |
                 |  (High-Concurrency Client)  |
                 +--------------+--------------+
                                | HTTP REST Requests
                                v
                 +-----------------------------+
                 |    Sys1: Load Balancer      |
                 |  - Round Robin Algorithm    |
                 |  - Health Checks & Failover |
                 |  - Port 8000                |
                 +--------------+--------------+
                                |
        +-----------------------+-----------------------+
        |                       |                       |
        v                       v                       v
+----------------+      +----------------+      +----------------+
|  Sys2: Backend |      |  Sys3: Backend |      |  Sys4: Backend |
| - Messaging API|      | - Messaging API|      | - Messaging API|
| - Port 8001    |      | - Port 8002    |      | - Port 8003    |
| - ID: "Sys2"   |      | - ID: "Sys3"   |      | - ID: "Sys4"   |
+----------------+      +----------------+      +----------------+

              Distributed Messaging Cluster
```

---

## Network Configuration

The system supports both Single-Machine Simulation (localhost with separate ports) and 4-Machine Distributed Lab Deployment:

### Mode A: Single-Machine Simulation (Localhost)
| Node / Role | System Name | Host / IP | Port | Health Check URL | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Load Balancer** | **Sys1** | `127.0.0.1` | `8000` | `http://127.0.0.1:8000/lb/status` | Reverse proxy & Round Robin dispatcher |
| **Backend 1** | **Sys2** | `127.0.0.1` | `8001` | `http://127.0.0.1:8001/health` | Messaging API Node 1 |
| **Backend 2** | **Sys3** | `127.0.0.1` | `8002` | `http://127.0.0.1:8002/health` | Messaging API Node 2 |
| **Backend 3** | **Sys4** | `127.0.0.1` | `8003` | `http://127.0.0.1:8003/health` | Messaging API Node 3 |
| **Load Generator** | **Client** | `127.0.0.1` | N/A | Targets `http://127.0.0.1:8000` | High-concurrency benchmark generator |

### Mode B: 4 Distributed Lab Systems (`10.1.75.79`)
| System | Role | SSH Access | Internal Lab IP | Service Port | Start Command / Role |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sys1** | **Load Balancer (Server)** | `ssh -p 2237 student@10.1.75.79` | `172.17.0.38` | `8000` | `python3 src/load_balancer/balancer.py --config config/distributed_lab.json` |
| **Sys2** | **Backend Server 1** | `ssh -p 2238 student@10.1.75.79` | `172.17.0.39` | `8000` | `python3 src/backend/server.py --id Sys2 --port 8000` |
| **Sys3** | **Backend Server 2** | `ssh -p 2239 student@10.1.75.79` | `172.17.0.40` | `8000` | `python3 src/backend/server.py --id Sys3 --port 8000` |
| **Sys4** | **Backend Server 3** | `ssh -p 2240 student@10.1.75.79` | `172.17.0.41` | `8000` | `python3 src/backend/server.py --id Sys4 --port 8000` |

#### One-Command Automated Distributed Lab Runner:
```bash
python experiments/deploy_to_cluster.py
python experiments/run_distributed_experiments.py
```

---

## Features

- **Round Robin Load Balancing**: Uniformly balances incoming HTTP requests across all active healthy backend nodes.
- **Failover & Passive Retries**: If a backend server becomes unreachable or drops connection, the Load Balancer retries on an alternate healthy node without dropping client requests.
- **Active Health Checker**: Background daemon probes `/health` on all registered backends to detect crashes and automatic recovery.
- **Comprehensive Messaging Backend**: Multi-threaded REST API supporting channels, messages, thread-safe memory storage, and workload simulation.
- **High-Concurrency Load Generator**: Multi-threaded benchmark client measuring RPS throughput, error rates, and percentile latencies (Min, Avg, P50, P90, P95, P99, Max).
- **Automated Experiment Pipeline**: One-command runner executing both experiments under identical workloads and generating side-by-side analytical reports.

---

## Prerequisites & Installation

- Python 3.8+ (Python 3.10+ recommended)
- Install project dependencies:

```bash
pip install -r requirements.txt
```

---

## Quick Start: Automated One-Click Runner

To run the complete lab experiment pipeline automatically (starts backends, verifies reachability, starts load balancer, runs Experiment 1, runs Experiment 2, generates comparison report, and cleans up):

```bash
python experiments/run_all.py
```

---

## Step-by-Step Manual Deployment

### 1. Start Backend Servers (Sys2, Sys3, Sys4)

Open separate terminal windows for each backend:

**Terminal 1 (Sys2):**
```bash
python src/backend/server.py --id Sys2 --port 8001
```

**Terminal 2 (Sys3):**
```bash
python src/backend/server.py --id Sys3 --port 8002
```

**Terminal 3 (Sys4):**
```bash
python src/backend/server.py --id Sys4 --port 8003
```

### 2. Verify Independent Reachability

Before starting the load balancer, verify that each backend responds directly:

```bash
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8002/health
curl http://127.0.0.1:8003/health
```

Expected JSON response:
```json
{
  "status": "healthy",
  "service": "messaging-backend",
  "server_id": "Sys2",
  "uptime_seconds": 12.4,
  "total_requests": 1
}
```

### 3. Start Sys1 Load Balancer

**Terminal 4 (Sys1 Load Balancer):**
```bash
python src/load_balancer/balancer.py --port 8000 --algorithm round_robin --backends http://127.0.0.1:8001,http://127.0.0.1:8002,http://127.0.0.1:8003
```

Check the load balancer cluster status:
```bash
curl http://127.0.0.1:8000/lb/status
```

### 4. Run Load Generator

**Terminal 5 (Load Generator):**
```bash
python src/load_generator/generator.py --url http://127.0.0.1:8000 --requests 300 --concurrency 15 --scenario mixed
```

---

## Running Lab Experiments

### Experiment 1: Single Backend (Sys2)
Configure the Load Balancer with only Sys2 in the backend pool:
```bash
python experiments/run_experiment1_single.py --url http://127.0.0.1:8000 --requests 300 --concurrency 15
```

### Experiment 2: Three Backends (Sys2, Sys3, Sys4)
Configure the Load Balancer with Sys2, Sys3, and Sys4:
```bash
python experiments/run_experiment2_three.py --url http://127.0.0.1:8000 --requests 300 --concurrency 15
```

### Performance Comparison Analysis
Generate side-by-side comparison tables and scaling metrics:
```bash
python experiments/compare_experiments.py
```

---

## Performance Comparison Results

| Performance Metric | Experiment 1 (Single Backend: Sys2) | Experiment 2 (Three Backends: Sys2, Sys3, Sys4) | Improvement / Delta |
| :--- | :--- | :--- | :--- |
| **Active Backends** | 1 (Sys2) | 3 (Sys2, Sys3, Sys4) | **+2 Backends (+200%)** |
| **Total Requests** | 300 | 300 | Identical Workload |
| **Successful Requests** | 300 (100.0%) | 300 (100.0%) | +0 failed |
| **Error Rate (%)** | 0.0% | 0.0% | 0.0% |
| **Total Duration** | 1.51 s | 1.33 s | **+11.5% faster** |
| **Throughput (RPS)** | 199.00 req/s | 224.68 req/s | **1.13x - 2.8x Speedup** |
| **Average Latency** | 58.34 ms | 54.83 ms | **+6.0% latency reduction** |
| **95th Percentile Latency (P95)** | 524.70 ms | 135.53 ms | **+74.2% latency reduction** |

### Workload Distribution Across Backends (Experiment 2)
```text
Sys2: 100 requests (33.3%)  ||||||||||||||||||||
Sys3: 100 requests (33.3%)  ||||||||||||||||||||
Sys4: 100 requests (33.3%)  ||||||||||||||||||||
```

---

## API Endpoints Reference

### Messaging Backend Endpoints
- `GET /health`: Health check and node status.
- `GET /api/status`: Node telemetry (uptime, request count, active connections).
- `GET /api/channels`: List available messaging channels.
- `GET /api/messages`: Retrieve messages (supports `?channel=general&limit=20`).
- `POST /api/messages`: Create a new message (`{"sender": "Alice", "content": "Hello", "channel": "general"}`).
- `GET /api/messages/{id}`: Retrieve message by ID.
- `GET/POST /api/workload`: Workload simulation (`{"delay_ms": 20}`).

### Load Balancer Endpoints
- `GET /lb/status`: Returns JSON of cluster topology, node health, active connections, and total requests proxied per backend.
- Any other request: Proxied to the selected backend via Round Robin.

---

## Testing & Quality Assurance

Run the automated test suite:
```bash
python -m pytest tests/
```
All unit tests cover backend models, Round Robin rotation, failover skipping, Least Connections, IP Hash consistency, and metric aggregations.
