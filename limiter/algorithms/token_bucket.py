
import math
import time

# Import the atomic Redis operation.
from ..storage import check_and_consume_token


class TokenBucketLimiter:
    def __init__(self, capacity=5, refill_rate=1):
        # Maximum number of tokens the bucket can hold.
        self.capacity = capacity

        # Number of tokens added per second.
        self.refill_rate = refill_rate

        # Reject invalid configuration.
        if capacity <= 0 or refill_rate <= 0:
            raise ValueError(
                "Capacity and refill_rate must be positive."
            )

    def allow_request(self, client_id):
        # Each client gets a separate bucket.
        # The token bucket uses a different key from Fixed Window.
        redis_key = f"rate_limit:token:{client_id}"

        # Keep inactive buckets long enough to refill fully,
        # plus an additional 60 seconds before deleting them.
        expiry_seconds = math.ceil(
            self.capacity / self.refill_rate
        ) + 60

        # Redis calculates refill, checks the balance,
        # consumes a token if available, and saves the state.
        result = check_and_consume_token(
            key=redis_key,
            capacity=self.capacity,
            refill_rate=self.refill_rate,
            expiry_seconds=expiry_seconds,
        )

        # Return the decision to Django.
        return result


# Run this file directly to test Token Bucket.
if __name__ == "__main__":
    limiter = TokenBucketLimiter(
        capacity=5,
        refill_rate=1,
    )

    # Use a fresh client ID for this demonstration.
    client_id = f"token_test_{time.time_ns()}"

    for number in range(1, 7):
        result = limiter.allow_request(client_id)

        status = (
            "ALLOWED" if result["allowed"] else "REJECTED"
        )

        print(
            f"Request {number}: {status} "
            f"| Tokens remaining: "
            f"{result['tokens_remaining']:.2f} "
            f"| Retry after: {result['retry_after']}s"
        )
