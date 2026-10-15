
from django.http import JsonResponse

#FIXED WINDOW ALGORITHM

# Import the algorithm we already created.
from .algorithms.fixed_window import FixedWindowLimiter


# Create ONE limiter instance for this Django process.
# It allows 5 requests per 60-second fixed window.
limiter = FixedWindowLimiter(
    limit=5,
    window_seconds=60
)


def test_rate_limit(request):
    # Identify the client for testing.
    # Postman will send this value in the X-Client-ID header.
    # If the header is missing, use the client's IP address.
    client_id = request.headers.get(
        "X-Client-ID",
        request.META.get("REMOTE_ADDR", "unknown")
    )

    # Ask the algorithm whether this request is allowed.
    result = limiter.allow_request(client_id)

    # If the limit is exceeded, return HTTP 429.
    if not result["allowed"]:
        response = JsonResponse({
            "message": "Rate limit exceeded",
            "client_id": client_id,
            "count": result["count"],
            "retry_after": result["retry_after"],
        }, status=429)

        # Tell the client approximately how long to wait.
        response["Retry-After"] = str(result["retry_after"])

        return response

    # If allowed, return HTTP 200.
    return JsonResponse({
        "message": "Request allowed",
        "client_id": client_id,
        "count": result["count"],
    }, status=200)

#TOKEN BUCKET ALGORITHM 

from .algorithms.token_bucket import TokenBucketLimiter

# Create a separate Token Bucket limiter.
# Its bucket capacity is 5 tokens, refilling at 1 token/second.
token_bucket_limiter = TokenBucketLimiter(
    capacity=5,
    refill_rate=1,
)


def test_token_bucket(request):
    # Identify the client, using the same approach as Fixed Window.
    client_id = request.headers.get(
        "X-Client-ID",
        request.META.get("REMOTE_ADDR", "unknown"),
    )

    # Ask the Token Bucket algorithm whether to allow this request.
    result = token_bucket_limiter.allow_request(client_id)

    # If there is no complete token, reject the request.
    if not result["allowed"]:
        response = JsonResponse({
            "message": "Rate limit exceeded",
            "client_id": client_id,
            "tokens_remaining": result["tokens_remaining"],
            "retry_after": result["retry_after"],
        }, status=429)

        # Tell the client approximately how many seconds to wait.
        response["Retry-After"] = str(result["retry_after"])
        return response

    # Return success when a token was available and consumed.
    return JsonResponse({
        "message": "Request allowed",
        "client_id": client_id,
        "tokens_remaining": result["tokens_remaining"],
    }, status=200)

#SLIDING WINDOW COUNTER 

from .algorithms.sliding_window import SlidingWindowCounterLimiter
# --------------------------------------------------
# Sliding Window Counter Django View
# --------------------------------------------------

# Create a separate Sliding Window Counter limiter.
sliding_window_limiter = SlidingWindowCounterLimiter(
    limit=5,
    window_seconds=60,
)


def test_sliding_window(request):
    # Identify the client from the request header.
    # Fall back to the client's IP address if the header
    # is not provided.
    client_id = request.headers.get(
        "X-Client-ID",
        request.META.get("REMOTE_ADDR", "unknown"),
    )

    # Ask the Sliding Window Counter algorithm to
    # calculate the estimated count and decide.
    result = sliding_window_limiter.allow_request(client_id)

    # If the request is rejected, return HTTP 429.
    if not result["allowed"]:
        return JsonResponse({
            "message": "Rate limit exceeded",
            "algorithm": "Sliding Window Counter",
            "client_id": client_id,
            "current_count": result["current_count"],
            "previous_count": result["previous_count"],
            "estimated_count": round(
                result["estimated_count"], 2
            ),
        }, status=429)

    # If allowed, return HTTP 200.
    return JsonResponse({
        "message": "Request allowed",
        "algorithm": "Sliding Window Counter",
        "client_id": client_id,
        "current_count": result["current_count"],
        "previous_count": result["previous_count"],
        "estimated_count": round(
            result["estimated_count"], 2
        ),
    }, status=200)

#SLIDING_WINDOW_LOG 
from .algorithms.sliding_window_log import SlidingWindowLogLimiter

# ==================================================
# SLIDING WINDOW LOG - DJANGO VIEW
# ==================================================

# Create a separate limiter for Sliding Window Log.
# Allow 5 requests in any rolling 60-second period.
sliding_window_log_limiter = SlidingWindowLogLimiter(
    limit=5,
    window_seconds=60,
)


def test_sliding_window_log(request):
    # Identify the client using the request header.
    # Fall back to the client's IP address if no header
    # is supplied.
    client_id = request.headers.get(
        "X-Client-ID",
        request.META.get("REMOTE_ADDR", "unknown"),
    )

    # Ask the algorithm to check and record the request.
    result = sliding_window_log_limiter.allow_request(
        client_id
    )

    # Reject the request when the limit is reached.
    if not result["allowed"]:
        response = JsonResponse({
            "message": "Rate limit exceeded",
            "algorithm": "Sliding Window Log",
            "client_id": client_id,
            "active_requests": result["current_count"],
            "retry_after": result["retry_after"],
        }, status=429)

        # Tell the client when it may retry.
        response["Retry-After"] = str(result["retry_after"])
        return response

    # Return success when the request is allowed.
    return JsonResponse({
        "message": "Request allowed",
        "algorithm": "Sliding Window Log",
        "client_id": client_id,
        "active_requests": result["current_count"],
    }, status=200)

#LEAKY BUCKET 
from .algorithms.leaky_bucket import LeakyBucketLimiter

# ==================================================
# LEAKY BUCKET - DJANGO VIEW
# ==================================================

# Create a separate Leaky Bucket limiter.
# Allow a capacity of 5 request-units.
# Capacity becomes available at 1 unit per second.
leaky_bucket_limiter = LeakyBucketLimiter(
    capacity=5,
    leak_rate=1,
)


def test_leaky_bucket(request):
    # Identify the client using the request header.
    # Fall back to the client's IP address if no header
    # is provided.
    client_id = request.headers.get(
        "X-Client-ID",
        request.META.get("REMOTE_ADDR", "unknown"),
    )

    # Ask the Leaky Bucket algorithm to check the request.
    result = leaky_bucket_limiter.allow_request(client_id)

    # Reject the request if the bucket is full.
    if not result["allowed"]:
        response = JsonResponse({
            "message": "Rate limit exceeded",
            "algorithm": "Leaky Bucket",
            "client_id": client_id,
            "bucket_level": round(result["level"], 2),
            "retry_after": result["retry_after"],
        }, status=429)

        # Tell the client approximately how long to wait.
        response["Retry-After"] = str(result["retry_after"])
        return response

    # Return success when the request fits in the bucket.
    return JsonResponse({
        "message": "Request allowed",
        "algorithm": "Leaky Bucket",
        "client_id": client_id,
        "bucket_level": round(result["level"], 2),
    }, status=200)
