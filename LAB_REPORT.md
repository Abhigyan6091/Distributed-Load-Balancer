# Distributed Systems Lab Report: HTTP Load Balancer with Multiple Backends

**Course / Lab:** Distributed Systems Laboratory  
**Project:** Implementation & Performance Evaluation of a Multi-Backend Load Balancer  
**Author:** Abhigyan Sharma  
**Date:** August 21, 2026  

---

## 1. Executive Summary

This report presents the design, implementation, and empirical performance evaluation of an HTTP reverse-proxy **Load Balancer (Sys1)** distributing workloads across three **Messaging Project backend servers (Sys2, Sys3, Sys4)**.

Using a custom multi-threaded **Load Generator Client**, two controlled benchmarking experiments were conducted under identical workloads (300 requests, 15 concurrent clients):
1. **Experiment 1 (Baseline / Single Backend):** Traffic was routed strictly to a single backend node (`Sys2`).
2. **Experiment 2 (Three-Backend Cluster):** Traffic was distributed across three backend nodes (`Sys2`, `Sys3`, `Sys4`) using the **Round Robin** algorithm.

### Key Empirical Findings
- **Horizontal Scalability:** Adding two backend nodes increased overall throughput from **`199.00 RPS` to `224.68 RPS`**.
- **Tail Latency Mitigation:** The **95th percentile latency (P95)** dropped by **`74.2%`** (from `524.70 ms` down to `135.53 ms`), successfully preventing head-of-line blocking under concurrency bursts.
- **Uniform Load Distribution:** Round Robin achieved a **`33.3% / 33.3% / 33.3%` exact uniform distribution** (100 requests per node) with zero error rate across both runs.

---

## 2. System Architecture & Component Design

```text
                 +-----------------------------+
                 |       Load Generator        |
                 |  (High-Concurrency Client)  |
                 +--------------+--------------+
                                | HTTP REST API Calls
                                v
                 +-----------------------------+
                 |    Sys1: Load Balancer      |
                 |  - Round Robin Dispatcher   |
                 |  - Active/Passive Health    |
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
```

### 2.1 Sys1: Load Balancer
- **Reverse Proxy Architecture:** Receives incoming client HTTP requests, selects a healthy backend using the Round Robin policy, forwards headers/payloads, and returns the response to the client.
- **Active & Passive Fault Tolerance:** A background daemon probes `/health` every 3 seconds. In case of sudden backend timeouts, the proxy automatically fails over to the next healthy node.
- **Request Metadata Tracking:** Injects `X-Load-Balancer: Sys1`, `X-Selected-Backend: <node_id>`, and `X-Proxy-Total-Latency-Ms: <ms>` into downstream HTTP headers.

### 2.2 Sys2, Sys3, Sys4: Messaging Project Backends
- Multi-threaded REST service exposing:
  - `GET /health` / `GET /api/status`: Health and telemetry check.
  - `GET /api/messages` & `POST /api/messages`: Thread-safe messaging storage.
  - `GET /api/channels`: Channel metadata.
  - `GET/POST /api/workload`: Controlled computation simulation.

### 2.3 Load Generator
- Multi-threaded benchmarking client designed to measure system throughput (RPS), total duration, error rates, and full latency distribution (Min, Avg, P50, P90, P95, P99, Max).

---

## 3. Network Configuration & Deployment Map

### Single-Machine Simulation (Localhost)
| Role | System ID | Host Address | Port | Endpoint URL |
| :--- | :--- | :--- | :--- | :--- |
| **Load Balancer** | **Sys1** | `127.0.0.1` | `8000` | `http://127.0.0.1:8000` |
| **Backend 1** | **Sys2** | `127.0.0.1` | `8001` | `http://127.0.0.1:8001` |
| **Backend 2** | **Sys3** | `127.0.0.1` | `8002` | `http://127.0.0.1:8002` |
| **Backend 3** | **Sys4** | `127.0.0.1` | `8003` | `http://127.0.0.1:8003` |

### Multi-Machine Lab Deployment (4 Distributed VM Systems on `10.1.75.79`)
| System | Role | SSH Port | Internal Container IP | Service Port | Start Command |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Sys1** | Load Balancer (Server) | `2237` | `172.17.0.38` | `8000` | `python3 src/load_balancer/balancer.py --config config/distributed_lab.json` |
| **Sys2** | Backend Server 1 | `2238` | `172.17.0.39` | `8000` | `python3 src/backend/server.py --id Sys2 --port 8000` |
| **Sys3** | Backend Server 2 | `2239` | `172.17.0.40` | `8000` | `python3 src/backend/server.py --id Sys3 --port 8000` |
| **Sys4** | Backend Server 3 | `2240` | `172.17.0.41` | `8000` | `python3 src/backend/server.py --id Sys4 --port 8000` |

---

## 4. Experimental Results & Performance Comparison

Both experiments were subjected to an identical workload of **300 requests**, concurrency level of **15 concurrent worker threads**, with a mixed read/write/compute scenario.

### 4.1 Comparative Metrics Table

| Metric | Experiment 1: Single Backend (Sys2) | Experiment 2: Three Backends (Sys2, Sys3, Sys4) | Relative Delta / Improvement |
| :--- | :--- | :--- | :--- |
| **Active Backends** | 1 (Sys2) | 3 (Sys2, Sys3, Sys4) | **+2 Nodes (+200%)** |
| **Total Requests** | 300 | 300 | Identical Workload |
| **Successful Requests** | 300 (100.0%) | 300 (100.0%) | 0 errors |
| **Failed Requests** | 0 | 0 | 0 errors |
| **Error Rate (%)** | 0.0% | 0.0% | 0.0% |
| **Total Execution Duration** | 1.508 s | 1.335 s | **+11.5% faster** |
| **Throughput (RPS)** | 199.00 req/s | 224.68 req/s | **🚀 +12.9% RPS Increase** |
| **Average Latency** | 58.34 ms | 54.83 ms | **📉 +6.0% latency reduction** |
| **Median Latency (P50)** | 21.80 ms | 25.15 ms | Comparable |
| **90th Percentile Latency (P90)** | 48.07 ms | 51.51 ms | Comparable |
| **95th Percentile Latency (P95)** | 524.70 ms | 135.53 ms | **📉 +74.2% latency reduction** |
| **99th Percentile Latency (P99)** | 713.88 ms | 569.37 ms | **📉 +20.2% latency reduction** |
| **Maximum Latency** | 797.78 ms | 1058.22 ms | (Tail outlier) |
| **Minimum Latency** | 2.75 ms | 3.15 ms | (Base network RTT) |

### 4.2 Traffic Distribution Breakdown (Experiment 2)

| Backend Node | Port | Requests Handled | Traffic Share (%) | Distribution Histogram |
| :--- | :--- | :--- | :--- | :--- |
| **Sys2** | 8001 | 100 | 33.33% | `████████████████████` |
| **Sys3** | 8002 | 100 | 33.33% | `████████████████████` |
| **Sys4** | 8003 | 100 | 33.33% | `████████████████████` |

---

## 5. Technical Analysis & Discussion

### 5.1 Queueing Theory & Head-of-Line Blocking
In Experiment 1, all 15 concurrent worker threads competed for the single backend process on Sys2. According to **M/M/m Queueing Theory**, as the arrival rate $\lambda$ approaches the service capacity $\mu$, the average waiting time in the queue $W_q$ escalates exponentially:
$$W_q = \frac{\lambda}{\mu(\mu - \lambda)}$$
This explains why the single-backend configuration suffered high **P95 latency (524.70 ms)**.

In Experiment 2, requests are partitioned across 3 separate server processes ($\mu_1, \mu_2, \mu_3$), reducing the effective arrival rate per queue to $\lambda / 3$. Consequently, queued waiting time dropped sharply, lowering P95 latency to **135.53 ms** (**74.2% latency reduction**).

### 5.2 Round Robin Fairness & Determinism
The empirical distribution shows exact mathematical uniformity (100 requests per node across 300 total requests). Because requests were generated sequentially by concurrent workers, Round Robin distributed CPU and I/O loads with zero bias.

### 5.3 Reliability and High Availability
The load balancer was tested with active health probing and passive failover. If any backend node encounters network failure or becomes unavailable, the load balancer automatically reroutes traffic to remaining healthy nodes, ensuring high availability (zero dropped requests).

---

## 6. Conclusion

The distributed load balancer successfully demonstrates the fundamental principles of **horizontal scaling**, **fault tolerance**, and **load distribution** in distributed systems. By deploying multiple backend instances behind a Round Robin reverse proxy, the system achieves higher aggregate throughput, substantially reduced tail latencies, and resilience against individual node failures.
