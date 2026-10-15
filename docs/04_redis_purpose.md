# Redis Purpose and Usage

## 1. Introduction

Redis is an in-memory data store used in our Rate Limiter project to store and update the information needed to control API requests.

Our project uses **Memurai**, a Redis-compatible server running locally on Windows.

The rate-limiting algorithm defines the rules, while Redis stores the shared state needed to apply those rules.

## 2. Why Do We Use Redis?

Redis is used for four main reasons:

- **Fast access:** Reads and updates data quickly.
- **Shared state:** Multiple Django workers can access the same rate-limit information.
- **Automatic expiry:** Keys can expire using `EXPIRE` or other expiry settings.
- **Atomic operations:** Lua scripts help perform related checks and updates safely when requests arrive simultaneously.

## 3. Redis Usage in Each Algorithm

### A. Fixed Window

**Purpose:** Store the number of requests made by a client during a fixed time window.

```redis
# Increase the client's request counter by 1
INCR rate_limit:fixed:client_01:window_123

# Set the key to expire after 60 seconds
EXPIRE rate_limit:fixed:client_01:window_123 60
```

**Explanation:**
- `INCR` increases the request counter.
- `EXPIRE` sets the key's lifetime.
- The algorithm checks whether the configured request limit has been reached.

*Note: These commands illustrate the operations; our implementation uses an atomic Lua script for its counter decision.*

### B. Sliding Window Counter

**Purpose:** Store request counts for the previous and current time windows.

```redis
# Increase the current window's request count
INCR rate_limit:sliding:client_01:current

# Set an expiry for the counter
EXPIRE rate_limit:sliding:client_01:current 120
```

**Explanation:**
- Redis stores window counters.
- The algorithm reads the previous and current counts.
- It estimates the rolling-window request count using a weighted formula.
- The algorithm decides whether to allow or reject the request.

*Note: The actual project implementation may use window-specific keys and atomic Lua logic; these commands are illustrative.*

### C. Sliding Window Log

**Purpose:** Store the timestamps of individual accepted requests.

```redis
# Add a request identifier with its timestamp as the score
ZADD rate_limit:sliding_log:client_01 1760000000 request_001

# Count the stored request entries
ZCARD rate_limit:sliding_log:client_01

# Remove entries older than the rolling-window cutoff
ZREMRANGEBYSCORE rate_limit:sliding_log:client_01 -inf 1759999940
```

**Explanation:**
- `ZADD` stores a request entry with its timestamp.
- `ZCARD` counts the entries currently stored.
- `ZREMRANGEBYSCORE` removes timestamps outside the rolling window.
- The algorithm checks the remaining count against the limit.

Our implementation uses Redis time and an atomic Lua script to perform the rolling-window decision.

### D. Token Bucket

**Purpose:** Store the available tokens and the time of the last refill.

```redis
# Store the current number of available tokens
HSET rate_limit:token:client_01 tokens 5

# Store the last refill time in milliseconds
HSET rate_limit:token:client_01 last_refill_ms 1760000000000

# Read the current token count
HGET rate_limit:token:client_01 tokens
```

**Explanation:**
- `HSET` stores token-bucket fields in a Redis hash.
- `HGET` reads a field.
- The algorithm calculates how many tokens have refilled based on elapsed time.
- If a token is available, the request consumes one; otherwise, it is rejected.

Our actual implementation uses a Lua script to calculate and update the bucket atomically.

### E. Leaky Bucket

**Purpose:** Store the current accumulated load and the time of the last leak calculation.

```redis
# Store the current accumulated load
HSET rate_limit:leaky:client_01 level 3

# Store the last leak calculation time
HSET rate_limit:leaky:client_01 last_leak_ms 1760000000000

# Read the current bucket level
HGET rate_limit:leaky:client_01 level
```

**Explanation:**
- `HSET` stores the bucket's state.
- `HGET` reads the stored level.
- The algorithm calculates how much load has leaked away over time.
- If adding the new request exceeds capacity, the request is rejected.

Our implementation calculates leakage when a request arrives. It does not run a background timer or queue rejected requests.

## 4. Redis Commands Summary

| Algorithm | Main Redis data structure | Main operations |
|---|---|---|
| Fixed Window | String counter | `INCR`, `EXPIRE` |
| Sliding Window Counter | Window counters | Counter reads/updates, expiry |
| Sliding Window Log | Sorted Set | `ZADD`, `ZCARD`, `ZREMRANGEBYSCORE` |
| Token Bucket | Hash | `HGET`, `HSET`, `EXPIRE`, `TIME` |
| Leaky Bucket | Hash | `HGET`, `HSET`, `EXPIRE`, `TIME` |

The exact operations are determined by each algorithm's implementation. The examples above explain the concepts; they are not a replacement for the project's existing Lua scripts.

## 5. End-to-End Redis Flow

1. Postman sends an API request with an `X-Client-ID`.
2. Django routes the request to the correct view.
3. The view calls the selected algorithm.
4. The algorithm communicates with Redis through the Python Redis package.
5. Redis reads or updates the client's stored state.
6. The algorithm decides whether the request is allowed.
7. Django returns HTTP `200 OK` or `429 Too Many Requests`.

## 6. Conclusion

Redis provides fast, shared storage for the state used by all five rate-limiting algorithms. It supports counters, hashes, sorted sets, expiry, and atomic Lua scripts. Django handles the request, the algorithm defines the rate-limiting rules, and Redis stores and updates the information required to enforce those rules.