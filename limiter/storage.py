#FIXED WINDOW COUNTER
import redis


# Create one Redis client for this Django process.
# Memurai uses the Redis-compatible protocol.
redis_client = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,
)


def check_redis_connection():
    """
    Check whether Django can communicate with Memurai.
    Returns True when the connection works.
    """
    return redis_client.ping()


def get_counter(key):
    """
    Read a counter from Redis.
    Return 0 when the key does not exist.
    """
    value = redis_client.get(key)

    if value is None:
        return 0

    return int(value)


def set_counter(key, value, expiry_seconds):
    """
    Store a counter with an expiration time.
    The key will expire after expiry_seconds.
    """
    redis_client.set(
        key,
        value,
        ex=expiry_seconds,
    )


def delete_counter(key):
    """
    Delete a counter from Redis.
    Useful when testing or resetting a specific key.
    """
    redis_client.delete(key)
    

# One Redis Lua script performs the check and update atomically.
FIXED_WINDOW_SCRIPT = redis_client.register_script("""
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local limit = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])

-- Repair a counter that exists without an expiration.
local existing_ttl = redis.call('TTL', KEYS[1])
if current > 0 and existing_ttl < 0 then
    redis.call('EXPIRE', KEYS[1], ttl)
end

-- If the limit has already been reached, reject the request.
if current >= limit then
    local remaining = redis.call('TTL', KEYS[1])
    if remaining < 1 then
        remaining = ttl
    end
    return {0, current, remaining}
end

-- Otherwise, increase the counter.
local new_count = redis.call('INCR', KEYS[1])

-- Give a newly created counter an expiration.
if new_count == 1 then
    redis.call('EXPIRE', KEYS[1], ttl)
end

-- Return: allowed, new count, retry-after.
return {1, new_count, 0}
""")


def check_and_increment_fixed_window(key, limit, ttl):
    """Check the limit and update its Redis counter atomically."""
    result = FIXED_WINDOW_SCRIPT(
        keys=[key],
        args=[limit, ttl],
    )

    return {
        "allowed": bool(int(result[0])),
        "count": int(result[1]),
        "retry_after": int(result[2]),
    }

#TOKEN BUCKET ALGORITHM 

# --------------------------------------------------
# TOKEN BUCKET: Redis Lua Script
# --------------------------------------------------

TOKEN_BUCKET_SCRIPT = redis_client.register_script("""
-- Get the current time from Redis in milliseconds.
local time = redis.call('TIME')
local now_ms = tonumber(time[1]) * 1000
    + math.floor(tonumber(time[2]) / 1000)

-- Read configuration supplied by Python.
local capacity = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local expiry_seconds = tonumber(ARGV[3])

-- Read the bucket's saved state from Redis.
local tokens = tonumber(redis.call('HGET', KEYS[1], 'tokens'))
local last_refill_ms = tonumber(
    redis.call('HGET', KEYS[1], 'last_refill_ms')
)

-- If this is a new bucket, start with full capacity.
if tokens == nil or last_refill_ms == nil then
    tokens = capacity
    last_refill_ms = now_ms
end

-- Calculate how much time has passed.
local elapsed_ms = math.max(0, now_ms - last_refill_ms)

-- Calculate the tokens earned during that time.
local new_tokens = (elapsed_ms / 1000) * refill_rate

-- Refill the bucket, but never exceed its capacity.
tokens = math.min(capacity, tokens + new_tokens)

-- Try to consume one token for this request.
local allowed = 0
local retry_after = 0

if tokens >= 1 then
    -- A token is available, so accept the request.
    tokens = tokens - 1
    allowed = 1
else
    -- No whole token is available: reject the request.
    retry_after = math.ceil((1 - tokens) / refill_rate)
end

-- Save the updated bucket state in Redis.
redis.call(
    'HSET',
    KEYS[1],
    'tokens', tokens,
    'last_refill_ms', now_ms
)

-- Remove inactive bucket data after the specified period.
redis.call('EXPIRE', KEYS[1], expiry_seconds)

-- Return: allowed, remaining tokens, retry-after seconds.
return {allowed, tokens, retry_after}
""")


def check_and_consume_token(key, capacity, refill_rate, expiry_seconds):
    """Ask Redis to refill, check, and consume a token atomically."""

    result = TOKEN_BUCKET_SCRIPT(
        keys=[key],
        args=[capacity, refill_rate, expiry_seconds],
    )

    return {
        "allowed": bool(int(result[0])),
        "tokens_remaining": float(result[1]),
        "retry_after": int(result[2]),
    }

#SLIDING WINDOW COUNTER 

# --------------------------------------------------
# Sliding Window Counter: Redis Lua Script
# --------------------------------------------------

SLIDING_WINDOW_SCRIPT = redis_client.register_script("""
-- Get the current time from Redis.
local time = redis.call('TIME')
local now_seconds = tonumber(time[1])
    + (tonumber(time[2]) / 1000000)

-- Read configuration supplied by Python.
local limit = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])

-- Identify the current and previous fixed windows.
local current_window = math.floor(now_seconds / window_seconds)
local previous_window = current_window - 1

-- Calculate how much of the previous window remains
-- relevant to the current rolling period.
local elapsed = now_seconds - (current_window * window_seconds)
local previous_weight = 1 - (elapsed / window_seconds)

-- Build separate Redis keys for both windows.
local current_key = KEYS[1] .. ':' .. current_window
local previous_key = KEYS[1] .. ':' .. previous_window

-- Read the request counts.
local current_count = tonumber(
    redis.call('GET', current_key)
) or 0

local previous_count = tonumber(
    redis.call('GET', previous_key)
) or 0

-- Estimate the requests in the sliding window.
local estimated_count =
    (previous_count * previous_weight) + current_count

-- Decide whether this request is allowed.
local allowed = 0

if estimated_count < limit then
    -- Accept the request and increment the current counter.
    current_count = redis.call('INCR', current_key)

    -- Expire the counter after its window plus a small buffer.
    redis.call('EXPIRE', current_key, window_seconds * 2)

    allowed = 1
end

-- Return the decision and useful counter information.
return {
    allowed,
    current_count,
    previous_count,
    estimated_count,
    previous_weight
}
""")


def check_and_increment_sliding_window(
    client_id,
    limit,
    window_seconds,
):
    # The base key is unique to this client.
    # The Lua script adds the window number to create
    # separate keys for the previous and current windows.
    base_key = f"rate_limit:sliding:{client_id}"

    result = SLIDING_WINDOW_SCRIPT(
        keys=[base_key],
        args=[limit, window_seconds],
    )

    # Convert the Redis response into a Python dictionary.
    return {
        "allowed": bool(int(result[0])),
        "current_count": int(result[1]),
        "previous_count": int(result[2]),
        "estimated_count": float(result[3]),
        "previous_weight": float(result[4]),
    }

#SLIDING WINDOW LOG 

# ==================================================
# SLIDING WINDOW LOG - REDIS STORAGE
# ==================================================

# Redis Lua script:
# Cleanup, count, decision, and insertion happen atomically.
SLIDING_WINDOW_LOG_SCRIPT = redis_client.register_script("""
-- Get the current time from Redis.
-- All Django workers use the same Redis time source.
local time = redis.call('TIME')

local now_ms = tonumber(time[1]) * 1000
    + math.floor(tonumber(time[2]) / 1000)

-- Read the rate-limit configuration from Python.
local limit = tonumber(ARGV[1])
local window_seconds = tonumber(ARGV[2])
local window_ms = window_seconds * 1000

-- Calculate the beginning of the rolling time window.
local cutoff_ms = now_ms - window_ms

-- Remove timestamps at or before the cutoff.
-- Only requests newer than the cutoff remain active.
redis.call(
    'ZREMRANGEBYSCORE',
    KEYS[1],
    '-inf',
    cutoff_ms
)

-- Count requests still inside the rolling window.
local current_count = redis.call('ZCARD', KEYS[1])

local allowed = 0
local retry_after = 0

-- Allow the request only if the current count
-- is below the configured limit.
if current_count < limit then

    -- Generate a unique request ID.
    -- The sequence prevents two requests with the
    -- same millisecond timestamp from overwriting each other.
    local sequence = redis.call('INCR', KEYS[2])
    local member = tostring(now_ms) .. ':' .. tostring(sequence)

    -- Store the request timestamp as the Sorted Set score.
    redis.call('ZADD', KEYS[1], now_ms, member)

    -- Count now includes the newly accepted request.
    current_count = current_count + 1
    allowed = 1

else
    -- Find the oldest active request.
    local oldest = redis.call(
        'ZRANGE',
        KEYS[1],
        0,
        0,
        'WITHSCORES'
    )

    -- Calculate approximately how long until that
    -- request leaves the rolling window.
    if #oldest >= 2 then
        local oldest_ms = tonumber(oldest[2])

        retry_after = math.max(
            1,
            math.ceil(
                (oldest_ms + window_ms - now_ms) / 1000
            )
        )
    end
end

-- Automatically remove inactive client data.
-- The extra window duration is a cleanup buffer.
redis.call('EXPIRE', KEYS[1], window_seconds * 2)
redis.call('EXPIRE', KEYS[2], window_seconds * 2)

-- Return the decision, active request count,
-- and suggested retry delay.
return {allowed, current_count, retry_after}
""")


def check_and_process_sliding_window_log(
    client_id,
    limit,
    window_seconds,
):
    # Each client gets a separate Sorted Set.
    base_key = f"rate_limit:sliding_log:{client_id}"

    # This key generates unique request IDs.
    sequence_key = f"{base_key}:sequence"

    # Execute the complete rate-limit operation in Redis.
    result = SLIDING_WINDOW_LOG_SCRIPT(
        keys=[base_key, sequence_key],
        args=[limit, window_seconds],
    )

    # Convert Redis results into a Python dictionary.
    return {
        "allowed": bool(int(result[0])),
        "current_count": int(result[1]),
        "retry_after": int(result[2]),
    }

#LEAKY BUCKET 

# ==================================================
# LEAKY BUCKET - REDIS STORAGE
# ==================================================

# Redis Lua script:
# Calculate leakage, check capacity, and update the
# bucket atomically.
LEAKY_BUCKET_SCRIPT = redis_client.register_script("""
-- Get the current time from Redis.
local time = redis.call('TIME')

local now_ms = tonumber(time[1]) * 1000
    + math.floor(tonumber(time[2]) / 1000)

-- Read the configuration supplied by Python.
local capacity = tonumber(ARGV[1])
local leak_rate = tonumber(ARGV[2])
local expiry_seconds = tonumber(ARGV[3])

-- Read the existing bucket state.
local level = tonumber(
    redis.call('HGET', KEYS[1], 'level')
)

local last_leak_ms = tonumber(
    redis.call('HGET', KEYS[1], 'last_leak_ms')
)

-- A new client's bucket starts empty.
if level == nil or last_leak_ms == nil then
    level = 0
    last_leak_ms = now_ms
end

-- Calculate how much time has passed.
local elapsed_ms = math.max(0, now_ms - last_leak_ms)
local elapsed_seconds = elapsed_ms / 1000

-- The bucket leaks gradually as time passes.
local leaked = elapsed_seconds * leak_rate

-- Bucket occupancy cannot fall below zero.
level = math.max(0, level - leaked)

-- Assume each incoming request adds one unit.
local allowed = 0
local retry_after = 0

-- Allow the request only if one more unit fits.
if level + 1 <= capacity then
    level = level + 1
    allowed = 1
else
    -- Calculate approximately how long until
    -- one request-unit of capacity becomes available.
    retry_after = math.ceil(
        (level + 1 - capacity) / leak_rate
    )
end

-- Save the latest bucket state and timestamp.
redis.call(
    'HSET',
    KEYS[1],
    'level', level,
    'last_leak_ms', now_ms
)

-- Delete inactive bucket data automatically.
redis.call('EXPIRE', KEYS[1], expiry_seconds)

-- Return the decision, bucket level, and wait time.
return {allowed, level, retry_after}
""")


def check_and_consume_leaky_bucket(
    key,
    capacity,
    leak_rate,
    expiry_seconds,
):
    # Execute the atomic Lua script in Redis.
    result = LEAKY_BUCKET_SCRIPT(
        keys=[key],
        args=[capacity, leak_rate, expiry_seconds],
    )

    # Convert the Redis result into a Python dictionary.
    return {
        "allowed": bool(int(result[0])),
        "level": float(result[1]),
        "retry_after": int(result[2]),
    }
