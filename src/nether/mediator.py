class Dispatcher:
    """
    Publish/Subscribe
    """

    def __init__(self) -> None: ...
    def register_subscriber(self, message_type, subscriber): ...
    def publish() -> None: ...  # notify/deliver
