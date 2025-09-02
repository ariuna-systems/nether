"""
Advanced Workflow Patterns - Practical Examples
===============================================

This file demonstrates real-world patterns using the Nether framework including:
- E-commerce order processing with compensation
- Data ingestion pipelines with error handling
- Real-time event streaming
- Circuit breaker patterns
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from nether import Application, execute
from nether.protocol import Command, Event, Message
from nether.component import Component

# =============================================================================
# BUSINESS DOMAIN MODELS
# =============================================================================


class OrderStatus(StrEnum):
    PENDING = "pending"
    VALIDATED = "validated"
    PAYMENT_PROCESSED = "payment_processed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    FAILED = "failed"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"


# =============================================================================
# COMMANDS
# =============================================================================


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessOrder(Command):
    order_id: str
    customer_id: str
    items: list[dict] = field(default_factory=list)
    total_amount: float = 0.0


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidateInventory(Command):
    order_id: str
    items: list[dict] = field(default_factory=list)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessPayment(Command):
    order_id: str
    customer_id: str
    amount: float
    payment_method: str = "credit_card"


@dataclass(frozen=True, slots=True, kw_only=True)
class ShipOrder(Command):
    order_id: str
    shipping_address: dict = field(default_factory=dict)


@dataclass(frozen=True, slots=True, kw_only=True)
class CancelOrder(Command):
    order_id: str
    reason: str = "customer_request"


@dataclass(frozen=True, slots=True, kw_only=True)
class CompensateTransaction(Command):
    """Command to compensate/rollback a failed transaction"""

    transaction_id: str
    compensation_type: str
    related_order_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderStatusChanged(Event):
    order_id: str
    old_status: str
    new_status: str
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True, kw_only=True)
class InventoryValidated(Event):
    order_id: str
    valid: bool
    unavailable_items: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True, kw_only=True)
class PaymentProcessed(Event):
    order_id: str
    payment_id: str
    status: PaymentStatus
    amount: float


@dataclass(frozen=True, slots=True, kw_only=True)
class PaymentFailed(Event):
    order_id: str
    reason: str
    amount: float


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderShipped(Event):
    order_id: str
    tracking_number: str
    estimated_delivery: str


@dataclass(frozen=True, slots=True, kw_only=True)
class OrderCancelled(Event):
    order_id: str
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CompensationRequired(Event):
    """Event indicating that compensation/rollback is needed"""

    order_id: str
    failed_step: str
    compensation_actions: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True, kw_only=True)
class SystemHealthCheck(Event):
    """Event for monitoring system health"""

    service_name: str
    status: str
    response_time_ms: float
    error_rate: float


# ============================================================================= #


class OrderProcessingSaga(Component[ProcessOrder | InventoryValidated | PaymentProcessed | PaymentFailed]):
    """
    Orchestrates the order processing workflow with compensation patterns
    """

    def __init__(self, application: Application):
        super().__init__(application)
        self.order_states: dict[str, dict] = {}

    async def handle(
        self,
        message: ProcessOrder | InventoryValidated | PaymentProcessed | PaymentFailed,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        match message:
            case ProcessOrder():
                await self._start_order_processing(message, handler)
            case InventoryValidated():
                await self._handle_inventory_validation(message, handler)
            case PaymentProcessed():
                await self._handle_payment_success(message, handler)
            case PaymentFailed():
                await self._handle_payment_failure(message, handler)

    async def _start_order_processing(
        self, command: ProcessOrder, handler: Callable[[Message], Awaitable[None]]
    ) -> None:
        """Initialize order processing"""
        self._logger.info(f"🛒 Starting order processing for {command.order_id}")

        # Initialize order state
        self.order_states[command.order_id] = {
            "status": OrderStatus.PENDING,
            "customer_id": command.customer_id,
            "items": command.items,
            "total_amount": command.total_amount,
            "completed_steps": set(),
            "compensation_stack": [],  # Track actions for potential rollback
        }

        # Emit status change event
        await handler(
            OrderStatusChanged(order_id=command.order_id, old_status="", new_status=OrderStatus.PENDING.value)
        )

        # Start inventory validation
        await handler(ValidateInventory(order_id=command.order_id, items=command.items))

    async def _handle_inventory_validation(
        self, event: InventoryValidated, handler: Callable[[Message], Awaitable[None]]
    ) -> None:
        """Handle inventory validation results"""
        order_id = event.order_id
        order_state = self.order_states.get(order_id)

        if not order_state:
            self._logger.error(f"Order {order_id} not found in saga state")
            return

        if event.valid:
            self._logger.info(f"✅ Inventory validated for order {order_id}")
            order_state["completed_steps"].add("inventory_validated")
            order_state["compensation_stack"].append("release_inventory")

            # Update status and proceed to payment
            await handler(
                OrderStatusChanged(
                    order_id=order_id, old_status=order_state["status"].value, new_status=OrderStatus.VALIDATED.value
                )
            )

            order_state["status"] = OrderStatus.VALIDATED

            # Process payment
            await handler(
                ProcessPayment(
                    order_id=order_id, customer_id=order_state["customer_id"], amount=order_state["total_amount"]
                )
            )
        else:
            self._logger.warning(f"❌ Inventory validation failed for order {order_id}")
            await handler(
                CompensationRequired(order_id=order_id, failed_step="inventory_validation", compensation_actions=[])
            )

    async def _handle_payment_success(
        self, event: PaymentProcessed, handler: Callable[[Message], Awaitable[None]]
    ) -> None:
        """Handle successful payment"""
        order_id = event.order_id
        order_state = self.order_states.get(order_id)

        if not order_state:
            return

        self._logger.info(f"💳 Payment processed for order {order_id}: {event.payment_id}")
        order_state["completed_steps"].add("payment_processed")
        order_state["compensation_stack"].append(f"refund_payment:{event.payment_id}")
        order_state["payment_id"] = event.payment_id

        # Update status
        await handler(
            OrderStatusChanged(
                order_id=order_id,
                old_status=order_state["status"].value,
                new_status=OrderStatus.PAYMENT_PROCESSED.value,
            )
        )

        order_state["status"] = OrderStatus.PAYMENT_PROCESSED

        # Proceed to shipping
        await handler(
            ShipOrder(
                order_id=order_id,
                shipping_address={"street": "123 Main St", "city": "Anytown"},  # Mock address
            )
        )

    async def _handle_payment_failure(
        self, event: PaymentFailed, handler: Callable[[Message], Awaitable[None]]
    ) -> None:
        """Handle payment failure - trigger compensation"""
        order_id = event.order_id
        order_state = self.order_states.get(order_id)

        if not order_state:
            return

        self._logger.error(f"💳❌ Payment failed for order {order_id}: {event.reason}")

        # Trigger compensation for all completed steps
        await handler(
            CompensationRequired(
                order_id=order_id,
                failed_step="payment_processing",
                compensation_actions=order_state["compensation_stack"].copy(),
            )
        )


# ============================================================================= #


class InventoryService(Component[ValidateInventory]):
    """Handles inventory validation with simulated failures"""

    def __init__(self, application: Application):
        super().__init__(application)
        self.failure_rate = 0.2  # 20% failure rate for demonstration

    async def handle(
        self,
        message: ValidateInventory,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        self._logger.info(f"📦 Validating inventory for order {message.order_id}")

        # Simulate processing time
        await asyncio.sleep(0.3)

        # Simulate occasional failures
        import random

        is_valid = random.random() > self.failure_rate

        unavailable_items = []
        if not is_valid:
            # Simulate some items being unavailable
            unavailable_items = [item["id"] for item in message.items[:1]]  # First item unavailable

        await handler(
            InventoryValidated(order_id=message.order_id, valid=is_valid, unavailable_items=unavailable_items)
        )


class PaymentService(Component[ProcessPayment]):
    """Handles payment processing with circuit breaker pattern."""

    def __init__(self, application: Application):
        super().__init__(application)
        self.failure_count = 0
        self.last_failure_time = 0
        self.circuit_open = False
        self.failure_threshold = 3
        self.recovery_time = 5.0  # seconds

    def _should_allow_request(self) -> bool:
        """Circuit breaker logic"""
        if not self.circuit_open:
            return True

        # Check if recovery time has passed
        if time.time() - self.last_failure_time > self.recovery_time:
            self.circuit_open = False
            self.failure_count = 0
            self._logger.info("🔄 Circuit breaker reset - allowing requests")
            return True

        return False

    def _record_success(self):
        """Record successful operation"""
        self.failure_count = 0
        if self.circuit_open:
            self._logger.info("✅ Circuit breaker closed - service recovered")
            self.circuit_open = False

    def _record_failure(self):
        """Record failed operation"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.circuit_open = True
            self._logger.warning("⚠️ Circuit breaker opened - service degraded")

    async def handle(
        self,
        message: ProcessPayment,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        if not self._should_allow_request():
            self._logger.warning("🚫 Payment request rejected - circuit breaker open")
            await handler(PaymentFailed(order_id=message.order_id, reason="service_unavailable", amount=message.amount))
            return

        self._logger.info(f"💳 Processing payment for order {message.order_id}: ${message.amount}")

        try:
            # Simulate payment processing
            await asyncio.sleep(0.5)

            # Simulate occasional failures (30% failure rate)
            import random

            if random.random() < 0.3:
                raise Exception("Payment gateway timeout")

            # Success case
            payment_id = f"pay_{message.order_id}_{int(time.time())}"
            self._record_success()

            await handler(
                PaymentProcessed(
                    order_id=message.order_id,
                    payment_id=payment_id,
                    status=PaymentStatus.CAPTURED,
                    amount=message.amount,
                )
            )

        except Exception as e:
            self._record_failure()
            self._logger.error(f"💳❌ Payment failed for order {message.order_id}: {str(e)}")

            await handler(PaymentFailed(order_id=message.order_id, reason=str(e), amount=message.amount))


class ShippingService(Component[ShipOrder]):
    """Handles order shipping"""

    async def handle(
        self,
        message: ShipOrder,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        self._logger.info(f"📮 Shipping order {message.order_id}")

        # Simulate shipping process
        await asyncio.sleep(0.4)

        tracking_number = f"TRK{message.order_id}{int(time.time())}"

        await handler(
            OrderShipped(order_id=message.order_id, tracking_number=tracking_number, estimated_delivery="2024-01-15")
        )


# ============================================================================= #


class CompensationHandler(Component[CompensationRequired]):
    """Handles compensation/rollback actions"""

    async def handle(
        self,
        message: CompensationRequired,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        self._logger.warning(f"⚠️ Compensation required for order {message.order_id}")
        self._logger.info(f"Failed step: {message.failed_step}")

        # Execute compensation actions in reverse order (LIFO)
        for action in reversed(message.compensation_actions):
            await self._execute_compensation_action(action, message.order_id, handler)

        # Cancel the order
        await handler(CancelOrder(order_id=message.order_id, reason=f"compensation_after_{message.failed_step}"))

    async def _execute_compensation_action(
        self, action: str, order_id: str, handler: Callable[[Message], Awaitable[None]]
    ) -> None:
        """Execute individual compensation action"""
        self._logger.info(f"🔄 Executing compensation: {action}")

        if action == "release_inventory":
            # Simulate releasing reserved inventory
            await asyncio.sleep(0.1)
            self._logger.info(f"📦🔄 Released inventory for order {order_id}")

        elif action.startswith("refund_payment:"):
            payment_id = action.split(":")[1]
            # Simulate payment refund
            await asyncio.sleep(0.2)
            self._logger.info(f"💳🔄 Refunded payment {payment_id} for order {order_id}")


# ============================================================================= #


class SystemMonitor(Component[OrderStatusChanged | PaymentFailed | OrderShipped]):
    """Monitors system health and performance"""

    def __init__(self, application: Application):
        super().__init__(application)
        self.metrics = {"orders_processed": 0, "orders_failed": 0, "payments_failed": 0, "orders_shipped": 0}

    async def handle(
        self,
        message: OrderStatusChanged | PaymentFailed | OrderShipped,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        match message:
            case OrderStatusChanged():
                if message.new_status == OrderStatus.PENDING.value:
                    self.metrics["orders_processed"] += 1
                elif message.new_status == OrderStatus.CANCELLED.value:
                    self.metrics["orders_failed"] += 1

            case PaymentFailed():
                self.metrics["payments_failed"] += 1

            case OrderShipped():
                self.metrics["orders_shipped"] += 1

        # Log metrics periodically
        if self.metrics["orders_processed"] % 5 == 0 and self.metrics["orders_processed"] > 0:
            await self._emit_health_metrics(handler)

    async def _emit_health_metrics(self, handler: Callable[[Message], Awaitable[None]]) -> None:
        """Emit system health metrics"""
        total_orders = self.metrics["orders_processed"]
        if total_orders > 0:
            success_rate = 1.0 - (self.metrics["orders_failed"] / total_orders)
            payment_failure_rate = self.metrics["payments_failed"] / total_orders

            await handler(
                SystemHealthCheck(
                    service_name="order_processing",
                    status="healthy" if success_rate > 0.8 else "degraded",
                    response_time_ms=150.0,  # Mock response time
                    error_rate=1.0 - success_rate,
                )
            )

            self._logger.info(
                f"📊 System Metrics: Success Rate: {success_rate:.2%}, Payment Failure Rate: {payment_failure_rate:.2%}"
            )


class EventLogger(Component[OrderStatusChanged | OrderShipped | OrderCancelled | SystemHealthCheck]):
    """Logs all important events for audit trail"""

    async def handle(
        self,
        message: OrderStatusChanged | OrderShipped | OrderCancelled | SystemHealthCheck,
        *,
        handler: Callable[[Message], Awaitable[None]],
        channel: Callable[[], tuple[asyncio.Queue[Any], asyncio.Event]],
    ) -> None:
        match message:
            case OrderStatusChanged():
                self._logger.info(f"📋 Order {message.order_id}: {message.old_status} → {message.new_status}")

            case OrderShipped():
                self._logger.info(f"📦✅ Order {message.order_id} shipped with tracking: {message.tracking_number}")

            case OrderCancelled():
                self._logger.warning(f"❌ Order {message.order_id} cancelled: {message.reason}")

            case SystemHealthCheck():
                status_emoji = "✅" if message.status == "healthy" else "⚠️"
                self._logger.info(
                    f"{status_emoji} System Health: {message.service_name} - "
                    f"Status: {message.status}, Error Rate: {message.error_rate:.2%}"
                )


# ============================================================================= #


class ECommerceApplication(Application):
    async def main(self) -> None:
        self.logger.info("🛍️ Starting E-Commerce Order Processing Demo")

        # Process multiple orders to demonstrate different scenarios
        orders = [
            {
                "order_id": "ORD-001",
                "customer_id": "CUST-123",
                "items": [{"id": "item1", "name": "Laptop"}],
                "total_amount": 999.99,
            },
            {
                "order_id": "ORD-002",
                "customer_id": "CUST-456",
                "items": [{"id": "item2", "name": "Mouse"}],
                "total_amount": 29.99,
            },
            {
                "order_id": "ORD-003",
                "customer_id": "CUST-789",
                "items": [{"id": "item3", "name": "Keyboard"}],
                "total_amount": 89.99,
            },
            {
                "order_id": "ORD-004",
                "customer_id": "CUST-101",
                "items": [{"id": "item4", "name": "Monitor"}],
                "total_amount": 299.99,
            },
            {
                "order_id": "ORD-005",
                "customer_id": "CUST-202",
                "items": [{"id": "item5", "name": "Webcam"}],
                "total_amount": 79.99,
            },
        ]

        async with self.mediator.context() as ctx:
            # Process orders with small delays
            for order_data in orders:
                await ctx.process(ProcessOrder(**order_data))
                await asyncio.sleep(0.1)  # Small delay between orders

            # Wait for processing to complete
            self.logger.info("⏳ Waiting for order processing to complete...")
            await asyncio.sleep(8)

            self.logger.info("✅ Demo completed!")


async def main():
    import argparse

    configuration = argparse.Namespace()
    configuration.host = "localhost"
    configuration.port = 8083

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    application = ECommerceApplication(configuration=configuration)

    # Register all modules
    application.register_module(OrderProcessingSaga(application))
    application.register_module(InventoryService(application))
    application.register_module(PaymentService(application))
    application.register_module(ShippingService(application))
    application.register_module(CompensationHandler(application))
    application.register_module(SystemMonitor(application))
    application.register_module(EventLogger(application))

    await application.start()


if __name__ == "__main__":
    execute(main())
