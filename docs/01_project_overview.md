# Project Overview

## 1. Project Title
**Rate Limiter Using Django and Redis**

## 2. Project Introduction
Rate Limiting is a technique used to control how many requests a client can send to an API within a specific period. It helps protect applications from excessive requests, reduces unnecessary resource usage, and maintains API stability.

This project implements five rate-limiting algorithms using Django and Redis-compatible Memurai. Each algorithm follows a different approach to controlling request traffic.

## 3. Project Objectives
- Understand and implement five rate-limiting algorithms.
- Control API request frequency for individual clients.
- Use Redis-compatible storage to maintain rate-limit state.
- Handle requests that exceed the configured limits.
- Test and compare algorithm behavior using Postman.

## 4. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Implements the application and algorithms |
| Django | Handles API requests and responses |
| Redis / Memurai | Stores shared rate-limit state |
| Lua Scripts | Execute related Redis operations atomically |
| Postman | Tests API endpoints |

## 5. Algorithms Implemented
1. **Fixed Window** — Counts requests within a fixed time interval.
2. **Sliding Window Counter** — Estimates request counts using adjacent time windows.
3. **Sliding Window Log** — Tracks individual request timestamps within a rolling window.
4. **Token Bucket** — Uses replenishing tokens to control requests and allow controlled bursts.
5. **Leaky Bucket** — Tracks accumulated request load and rejects requests when capacity is exceeded.

## 6. Project Architecture
The project separates request handling, rate-limiting rules, and state storage.

- **Django Views:** Receive requests and return HTTP responses.
- **Algorithm Modules:** Apply the selected rate-limiting rules.
- **Redis Storage:** Maintains the shared state required by each algorithm.
- **URL Configuration:** Connects API endpoints to the appropriate views.

## 7. End-to-End Request Flow
1. The client sends an API request with an `X-Client-ID` header.
2. Django receives the request and routes it to the correct view.
3. The view calls the selected rate-limiting algorithm.
4. The algorithm checks and updates its state through Redis.
5. The algorithm decides whether the request is allowed.
6. Django returns the response.

Requests within the configured limit generally receive **HTTP 200 OK**, while requests exceeding the limit receive **HTTP 429 Too Many Requests**.

## 8. API Endpoints

| Algorithm | Endpoint |
|---|---|
| Fixed Window | `/api/test/` |
| Sliding Window Counter | `/api/sliding-window/` |
| Sliding Window Log | `/api/sliding-window-log/` |
| Token Bucket | `/api/token-bucket/` |
| Leaky Bucket | `/api/leaky-bucket/` |

For local testing, the base URL is `http://127.0.0.1:8000`.

## 9. Expected Outcome
This project demonstrates how different rate-limiting algorithms work in a real Django API, how Redis maintains shared state, and how excessive requests can be controlled. It also helps compare the algorithms based on accuracy, memory usage, complexity, and burst handling.
