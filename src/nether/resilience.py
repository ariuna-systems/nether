import random
import time


class CircuitBreaker:
  def __init__(self, failure_threshold=3, recovery_timeout=5):
    self.failure_threshold = failure_threshold
    self.recovery_timeout = recovery_timeout
    self.failure_count = 0
    self.state = "CLOSED"
    self.last_failure_time = None

  def __enter__(self):
    if self.state == "OPEN":
      if time.time() - self.last_failure_time > self.recovery_timeout:
        self.state = "HALF-OPEN"
        print("Circuit is HALF-OPEN. Trying test call...")
      else:
        raise Exception("Circuit is OPEN. Try again later.")
    return self

  def __exit__(self, exc_type, exc_val, exc_tb):
    if exc_type is None:
      self._reset()
    else:
      self._record_failure()
    # Don't suppress exceptions
    return False

  def _record_failure(self):
    self.failure_count += 1
    self.last_failure_time = time.time()
    if self.failure_count >= self.failure_threshold:
      self.state = "OPEN"
      print("Circuit opened due to repeated failures!")

  def _reset(self):
    if self.state in ("OPEN", "HALF-OPEN"):
      print("Circuit closed. Service recovered.")
    self.failure_count = 0
    self.state = "CLOSED"


class Retry:
  def __ini__(self, max_attempts):
    self.max_attemps = max_attempts
    self.num_retries = 0

  def __call__(self, *args, **kwargs) -> None: ...


if __name__ == "__main__":

  def unstable_service():
    # Simulated unreliable function
    if random.random() < 0.5:
      raise Exception("Service failed!")
    return "Success!"

  breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=5)

  for i in range(20):
    try:
      with breaker:
        result = unstable_service()
        print(f"[{i}] Call success: {result}")
    except Exception as e:
      print(f"[{i}] Call failed: {e}")
    time.sleep(1)
