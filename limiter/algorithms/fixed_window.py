
import math
import time

# Import the shared Redis operation from storage.py.
from ..storage import check_and_increment_fixed_window


class FixedWindowLimiter:
    def __init__(self, limit=5, window_seconds=60):
        # Maximum allowed requests in one window.
        self.limit = limit

        # Duration of each fixed window in seconds.
        self.window_seconds = window_seconds

    def allow_request(self, client_id):
        # Get the current Unix timestamp.
        current_time = time.time()

        # Identify which fixed window this request belongs to.
        window_id = int(current_time // self.window_seconds)

        # Calculate when the current window ends.
        window_end = (window_id + 1) * self.window_seconds

        # Seconds remaining until the window ends.
        ttl = max(1, math.ceil(window_end - current_time))

        # Each client gets a separate counter for each window.
        redis_key = f"rate_limit:fixed:{client_id}:{window_id}"

        # Redis checks the limit and updates the counter atomically.
        result = check_and_increment_fixed_window(
            key=redis_key,
            limit=self.limit,
            ttl=ttl,
        )

        # Return the result to the caller.
        return result


# Run this file directly to test the algorithm.
if __name__ == "__main__":
    limiter = FixedWindowLimiter(limit=5, window_seconds=60)

    for number in range(1, 7):
        result = limiter.allow_request("user_101")

        status = "ALLOWED" if result["allowed"] else "REJECTED"

        print(
            f"Request {number}: {status} "
            f"| Count: {result['count']} "
            f"| Retry after: {result['retry_after']}s"
        )
