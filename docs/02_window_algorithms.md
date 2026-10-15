# 02. Window Algorithms

## 1. Introduction
Window-based rate-limiting algorithms control the number of requests a client can make within a specified time period. This project implements three window algorithms: Fixed Window, Sliding Window Counter, and Sliding Window Log.

## 2. Fixed Window

**Definition:** Fixed Window counts requests within a fixed time interval.

**Working:**
1. Identify the client and current time window.
2. Check the request counter stored in Redis.
3. If the count is below the limit, allow the request and increment the counter.
4. If the limit is reached, reject the request.
5. Expire the counter when its window ends.

**Advantages:** Simple, fast, and uses less memory.

**Disadvantages:** Can allow a burst of requests around the boundary between two windows.

**Endpoint:** `/api/test/`

## 3. Sliding Window Counter

**Definition:** Sliding Window Counter estimates the number of requests in a rolling time period by combining the previous and current window counts.

**Working:**
1. Read the previous and current window counters.
2. Calculate the previous window's weight based on elapsed time.
3. Estimate the request count using both counters.
4. Compare the estimated count with the limit.
5. Allow or reject the request and update the stored state.

**Formula:**

`Estimated Count = (Previous Count × Previous Weight) + Current Count`

**Advantages:** Uses less memory than storing every request timestamp and reduces boundary bursts.

**Disadvantages:** The result is an estimate rather than an exact rolling-window count.

**Endpoint:** `/api/sliding-window/`

## 4. Sliding Window Log

**Definition:** Sliding Window Log records individual request timestamps and counts those that fall within the rolling time period.

**Working:**
1. Identify the client and current time.
2. Remove timestamps older than the rolling-window cutoff.
3. Count the remaining timestamps.
4. If the count is below the limit, record the new request and allow it.
5. Otherwise, reject the request.

**Advantages:** Provides accurate rolling-window counting and avoids fixed-window boundary bursts.

**Disadvantages:** Requires more memory and processing because individual request timestamps are stored.

**Endpoint:** `/api/sliding-window-log/`

## 5. Comparison

| Feature | Fixed Window | Sliding Window Counter | Sliding Window Log |
|---|---|---|---|
| Method | Fixed interval counter | Weighted counters | Individual timestamps |
| Accuracy | Fixed-window count | Estimated | Exact for recorded timestamps |
| Memory usage | Low | Low | High |
| Complexity | Simple | Moderate | Higher |
| Boundary bursts | Possible | Reduced | Avoided |

## 6. Role of Redis
Redis-compatible Memurai stores the counters or timestamps required by these algorithms. It allows the application to access shared state and uses atomic operations where implemented to keep concurrent updates safe.

## 7. Conclusion
Fixed Window is suitable for simple limits, Sliding Window Counter provides a balance between efficiency and smoother counting, and Sliding Window Log is suitable when accurate rolling-window counting is more important than memory usage.