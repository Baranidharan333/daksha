import threading


class ThreadPauser:
    """
    Blocks a thread until another thread supplies a result.

    The `resumed` flag is what makes this safe: without it, a result that arrives
    before the waiter reaches wait() would be lost and the waiter would block
    forever. Condition.wait_for re-checks the flag, so an early result is seen
    immediately and the waiter never sleeps at all.
    """

    def __init__(self):
        self.condition = threading.Condition()
        self.result = None
        self.resumed = False

    def sleep_until_resumed(self, timeout=None):
        """
        Wait for a result. Returns True if one arrived, False if `timeout`
        seconds elapsed first.
        """
        with self.condition:
            return self.condition.wait_for(lambda: self.resumed, timeout=timeout)

    def resume_with_result(self, result):
        with self.condition:
            self.result = result
            self.resumed = True
            self.condition.notify_all()
