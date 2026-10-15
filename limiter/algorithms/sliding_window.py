
# limiter/algorithms/sliding_window.py

# Import the Redis storage function.
# We will implement this function in storage.py in Step 2.
from ..storage import check_and_increment_sliding_window


class SlidingWindowCounterLimiter:
    def __init__(self, limit=5, window_seconds=60):
        # Maximum estimated requests allowed in the window.
        self.limit = limit

        # Duration of one window, in seconds.
        self.window_seconds = window_seconds

        # Prevent invalid configurations.
        if limit <= 0 or window_seconds <= 0:
            raise ValueError(
                "Limit and window_seconds must be positive."
            )

    def allow_request(self, client_id):
        # Ask Redis to calculate the estimated request count
        # and make the allow/reject decision atomically.
        result = check_and_increment_sliding_window(
            client_id=client_id,
            limit=self.limit,
            window_seconds=self.window_seconds,
        )

        # Return the decision and counter information to Django.
        return result
