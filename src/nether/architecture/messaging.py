"""
Messaging contains concrete implementations of outbound messaging ports.
These handle communication with message brokers, event buses, or other messaging systems.

- Classes for publishing events/messages (e.g., to RabbitMQ, Kafka, Azure Service Bus).
- Classes for subscribing/consuming messages.
- Serialization/deserialization logic for messages.
- Integration code for external messaging infrastructure.

"""


class EventPublisher:
  def __init__(self, broker):
    self.broker = broker

  def publish(self, event):
    """Serialize and send event to broker."""
    pass


class EventSubscriber:
  def __init__(self, broker):
    self.broker = broker

  def subscribe(self, topic, handler):
    """Listen for messages and call handler."""
    pass
