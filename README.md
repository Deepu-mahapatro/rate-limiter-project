# ⚡ Rate Limiter System

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Django-6.1-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django">
  <img src="https://img.shields.io/badge/Redis-Compatible_Memurai-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/Lua-Atomic_Scripts-000080?style=for-the-badge&logo=lua&logoColor=white" alt="Lua">
  <img src="https://img.shields.io/badge/Postman-API_Testing-FF6C37?style=for-the-badge&logo=postman&logoColor=white" alt="Postman">
  <img src="https://img.shields.io/badge/Git-GitHub-F05032?style=for-the-badge&logo=git&logoColor=white" alt="Git">
</p>

<p align="center">
  <b>A practical rate-limiting project implementing five algorithms using Django, Python, and Redis-compatible Memurai to control API request traffic and manage shared rate-limit state.</b>
</p>

---

## 📌 About the Project

This project demonstrates how **rate limiting** controls the number of requests a client can send to an API within a specified time period.

It implements five algorithms: Fixed Window, Sliding Window Counter, Sliding Window Log, Token Bucket, and Leaky Bucket.

Django handles API requests, while Redis-compatible Memurai stores the state required by each algorithm. Postman is used to test the endpoints and verify how the algorithms allow or reject requests.

The project focuses on understanding the complete rate-limiting lifecycle, from receiving an API request to checking shared state and returning an HTTP response.

---

## 🎯 Project Objectives

- Understand the fundamentals and purpose of rate limiting.
- Implement five rate-limiting algorithms in Python.
- Integrate Django with Redis-compatible Memurai.
- Maintain shared rate-limit state across Django workers.
- Use Redis operations and Lua scripts for atomic state updates.
- Understand counters, timestamps, tokens, bucket levels, and key expiration.
- Test API limits and responses using Postman.
- Compare algorithms based on accuracy, memory usage, complexity, and burst handling.

---

## 🏗️ Architecture

```text
                  CLIENT / POSTMAN
                         |
                         | API Request
                         | X-Client-ID
                         v
                    DJANGO API
                         |
                         v
                    URL ROUTING
                         |
                         v
                    DJANGO VIEW
                         |
                         v
                RATE LIMIT ALGORITHM
                         |
                         v
                REDIS / MEMURAI
                Shared Rate-Limit State
                         |
                         v
                 ALLOW OR REJECT
                         |
                 +-------+-------+
                 |               |
                 v               v
             HTTP 200         HTTP 429
             Allowed          Rejected
```

### Core Principle

> **Django handles requests, the algorithm defines the rate-limiting rules, and Redis stores and updates the shared state needed to enforce those rules.**

Lua scripts help execute related Redis operations atomically, reducing race conditions when multiple requests arrive simultaneously.

---

## 🔄 Rate-Limiting Workflow

```text
Client Sends API Request
          |
          v
Django Receives Request
          |
          v
URL Routes to the View
          |
          v
View Selects Algorithm
          |
          v
Algorithm Checks Client State
          |
          v
Redis Reads / Updates State
          |
          v
Algorithm Evaluates the Limit
          |
          v
    +-----+-----+
    |           |
    v           v
  Allowed    Rejected
    |           |
    v           v
 HTTP 200    HTTP 429
```

---

## 🚀 Algorithms Implemented

| Algorithm | Purpose | Main Trade-off |
|---|---|---|
| Fixed Window | Counts requests in a fixed time interval | Simple, but can allow boundary bursts |
| Sliding Window Counter | Estimates rolling-window traffic using weighted counters | Memory-efficient, but approximate |
| Sliding Window Log | Tracks individual request timestamps | Accurate rolling-window counting, but higher memory usage |
| Token Bucket | Uses replenishing tokens to control requests | Allows controlled bursts |
| Leaky Bucket | Tracks accumulated request load and rejects excess requests | Limits accumulated load; this implementation does not queue requests |

---

## 🌐 API Endpoints

All endpoints use the `GET` method in this project.

| Method | Endpoint | Algorithm |
|---|---|---|
| `GET` | `/api/test/` | Fixed Window |
| `GET` | `/api/sliding-window/` | Sliding Window Counter |
| `GET` | `/api/sliding-window-log/` | Sliding Window Log |
| `GET` | `/api/token-bucket/` | Token Bucket |
| `GET` | `/api/leaky-bucket/` | Leaky Bucket |

### Example Request

```http
GET /api/token-bucket/
X-Client-ID: client_01
```

For local testing, use:

```text
http://127.0.0.1:8000/api/token-bucket/
```

The `X-Client-ID` header identifies the client whose rate-limit state should be checked. Use the same client ID for repeated requests when testing a single client's limit.

### Expected Responses

| Status Code | Meaning |
|---|---|
| `200 OK` | The request was allowed |
| `429 Too Many Requests` | The configured limit was exceeded |

The exact response body depends on the corresponding Django view.

---

## 🛡️ Important Implementation Details

- **Shared State:** Redis-compatible Memurai allows Django workers to use common rate-limit state.
- **Atomic Updates:** Lua scripts help keep related checks and updates atomic.
- **Key Expiration:** Redis expiry operations can clean up state that is no longer needed.
- **Client Identification:** Client-specific keys separate rate-limit state.
- **No Automatic Retry:** Rejected requests are not automatically queued or retried.
- **Leaky Bucket Behavior:** The current implementation tracks accumulated load and rejects excess requests rather than queueing them.

---

## 🛠️ Tech Stack

### Backend
- Python
- Django

### Rate-Limiting Storage
- Redis-compatible Memurai
- Redis Python package
- Lua scripts

### API Testing
- Postman

### Development Tools
- VS Code
- Git
- GitHub

---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd rate-limiter-project
```

### 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Memurai

Make sure your Memurai service is running.

Verify the Redis-compatible connection:

```bash
memurai-cli ping
```

Expected output:

```text
PONG
```

### 5. Verify the Django Project

```bash
python manage.py check
```

### 6. Start the Development Server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

### 7. Test Using Postman

1. Select the `GET` method.
2. Enter one of the API endpoint URLs.
3. Add the header `X-Client-ID: client_01`.
4. Send requests repeatedly.
5. Observe when the response changes from `200 OK` to `429 Too Many Requests`, depending on the algorithm's configuration.

**Note:** Use the Python version and package versions specified by your actual project environment and `requirements.txt`. If your settings require environment variables, configure them before starting Django.

---

## 📚 Documentation

| Document | Description |
|---|---|
| `docs/01_Project_Overview.md` | Project introduction, architecture, technologies, and request flow |
| `docs/02_Window_Algorithms.md` | Fixed Window, Sliding Window Counter, and Sliding Window Log |
| `docs/03_Bucket_Algorithms.md` | Token Bucket and Leaky Bucket |
| `docs/04_Redis_Purpose.md` | Redis/Memurai role, state storage, commands, and atomic operations |
| `docs/05_Overall_Conclusion.md` | End-to-end flow, key learnings, and conclusion |

---

## 🧪 Testing

The endpoints can be tested using Postman to verify:

- Requests within the configured limit.
- Requests exceeding the limit.
- Client-specific rate-limit state.
- Behavior after time passes and state is replenished, reduced, or expires.
- Differences between the five algorithms.
- Redis state using Memurai CLI commands.

Testing should include boundary cases and concurrent requests before considering the implementation production-ready.

---

## 🎓 Learning Outcomes

- Rate-limiting fundamentals and real API use cases.
- Fixed Window and rolling-window approaches.
- Token Bucket and Leaky Bucket behavior.
- Django URL routing and view execution.
- Redis data structures and key expiration.
- Shared state across Django workers.
- Atomic Redis operations using Lua scripts.
- API testing