
# limiter/algorithms/sliding_window_log.py

# Import the Redis function we added in storage.py.
from ..storage import check_and_process_sliding_window_log


class SlidingWindowLogLimiter:
    def __init__(self, limit=5, window_seconds=60):
        # Maximum accepted requests inside the rolling window.
        self.limit = limit

        # Rolling window duration in seconds.
        self.window_seconds = window_seconds

        # Prevent invalid rate-limit configuration.
        if limit <= 0 or window_seconds <= 0:
            raise ValueError(
                "Limit and window_seconds must be positive."
            )

    def allow_request(self, client_id):
        # Ask Redis to remove expired timestamps, count
        # active requests, and make the decision atomically.
        result = check_and_process_sliding_window_log(
            client_id=client_id,
            limit=self.limit,
            window_seconds=self.window_seconds,
        )

        # Return the decision to the caller.
        return result


# Allow us to test the algorithm directly from the terminal.
if __name__ == "__main__":
    import time

    # Use a small window to make experimentation easier.
    limiter = SlidingWindowLogLimiter(
        limit=3,
        window_seconds=10,
    )

    # Use a unique client ID so old tests don't affect this run.
    client_id = f"log_test_{time.time_ns()}"

    # Send five requests rapidly.
    for number in range(1, 6):
        result = limiter.allow_request(client_id)

        # Display whether the request was allowed.
        status = (
            "ALLOWED" if result["allowed"] else "REJECTED"
        )

        print(
            f"Request {number}: {status} "
            f"| Active requests: {result['current_count']} "
            f"| Retry after: {result['retry_after']}s"
        )
