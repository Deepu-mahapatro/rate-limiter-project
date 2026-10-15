
# limiter/algorithms/leaky_bucket.py

import math

# Import the Redis storage function.
from ..storage import check_and_consume_leaky_bucket


class LeakyBucketLimiter:
    def __init__(self, capacity=5, leak_rate=1):
        # Maximum request-units the bucket can hold.
        self.capacity = capacity

        # Number of request-units that leak per second.
        self.leak_rate = leak_rate

        # Prevent invalid configurations.
        if capacity <= 0 or leak_rate <= 0:
            raise ValueError(
                "Capacity and leak_rate must be positive."
            )

    def allow_request(self, client_id):
        # Use a separate Redis key for each client.
        redis_key = f"rate_limit:leaky:{client_id}"

        # Keep inactive buckets long enough for their
        # full capacity to leak away, plus a safety buffer.
        expiry_seconds = math.ceil(
            self.capacity / self.leak_rate
        ) + 60

        # Ask Redis to calculate leakage and decide
        # whether the new request fits.
        result = check_and_consume_leaky_bucket(
            key=redis_key,
            capacity=self.capacity,
            leak_rate=self.leak_rate,
            expiry_seconds=expiry_seconds,
        )

        # Return the decision to the caller.
        return result


# Allow direct testing without starting Django.
if __name__ == "__main__":
    import time

    # Use a small bucket for a quick experiment.
    limiter = LeakyBucketLimiter(
        capacity=3,
        leak_rate=1,
    )

    # Generate a unique client ID for this test.
    client_id = f"leaky_test_{time.time_ns()}"

    # Send five requests quickly.
    for number in range(1, 6):
        result = limiter.allow_request(client_id)

        status = (
            "ALLOWED" if result["allowed"] else "REJECTED"
        )

        print(
            f"Request {number}: {status} "
            f"| Bucket level: "
            f"{result['level']:.2f} "
            f"| Retry after: {result['retry_after']}s"
        )
