# Bucket Algorithms

## 1. Introduction
Bucket-based rate-limiting algorithms control API traffic using a bucket model. This project implements two algorithms: Token Bucket and Leaky Bucket. Both use time-based calculations, but they maintain different types of state.

## 2. Token Bucket

**Definition:** Token Bucket controls requests using tokens that are replenished over time up to a fixed capacity. Each allowed request consumes a token.

**Working:**
1. Identify the client and retrieve its bucket state from Redis.
2. Calculate how much time has passed since the last refill.
3. Refill tokens based on the configured rate, without exceeding capacity.
4. If a token is available, consume one and allow the request.
5. If no token is available, reject the request.
6. Save the updated token count and refill time.

**Project configuration:** Capacity of 5 tokens, refill rate of 1 token per second, and 1 token consumed per request.

**Advantages:**
- Allows controlled bursts when tokens are available.
- Controls sustained request rates.
- Uses relatively little storage.

**Disadvantages:**
- Allows bursts up to the available token capacity.
- Requires suitable capacity and refill-rate settings.

**Endpoint:** `/api/token-bucket/`

## 3. Leaky Bucket

**Definition:** Leaky Bucket tracks accumulated request load and reduces that load over time at a configured leak rate.

**Working:**
1. Identify the client and retrieve the bucket level from Redis.
2. Calculate the elapsed time since the last leak calculation.
3. Reduce the stored level according to the leak rate, without going below zero.
4. Check whether adding the new request would exceed capacity.
5. If capacity is available, accept the request and increase the level.
6. Otherwise, reject the request.
7. Save the updated level and time.

**Project configuration:** Capacity of 5 request-units and a leak rate of 1 unit per second.

**Important:** Our implementation rejects excess requests; it does not queue them for later processing.

**Advantages:**
- Tracks accumulated load.
- Reduces the stored load over time.
- Rejects requests when capacity is exceeded.

**Disadvantages:**
- Excess requests are rejected rather than queued.
- Rapid bursts can fill the bucket.
- Requires suitable capacity and leak-rate settings.

**Endpoint:** `/api/leaky-bucket/`

## 4. Comparison

| Feature | Token Bucket | Leaky Bucket |
|---|---|---|
| Stores | Available tokens | Accumulated load |
| Time behavior | Tokens refill | Load leaks away |
| Burst handling | Allows bursts within available capacity | Rapid requests can fill capacity |
| When capacity is exceeded | Rejects when no token remains | Rejects when the bucket is full |
| Queue in our project | No | No |

## 5. Role of Redis
Redis-compatible Memurai stores each client's bucket state. Token Bucket stores the available tokens and last-refill time, while Leaky Bucket stores the current level and last-leak time. Atomic operations help prevent incorrect state updates when requests arrive simultaneously.

## 6. Conclusion
Token Bucket is useful when an API needs to
