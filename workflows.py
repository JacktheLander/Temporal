import asyncio
import traceback
from datetime import timedelta
from dataclasses import dataclass
from typing import List
from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError
from temporalio.client import WorkflowFailureError

with workflow.unsafe.imports_passed_through():
    import activities

@dataclass
class Item:
    sku: str
    qty: int
@dataclass
class OrderDetails:
    order_id: str
    items: List[Item]
@dataclass
class PaymentDetails:
    payment_id: str
    status: str
    amount: float


# ReceiveOrder → ValidateOrder → (Timer: ManualReview) → ChargePayment → ShippingWorkflow
@workflow.defn
class OrderWorkflow:
    @workflow.run
    async def run(self, data) -> str:
        order_details: OrderDetails = data["order"]
        payment_details: PaymentDetails = data["payment"]

        retry_policy = RetryPolicy(
            maximum_attempts=10,
            initial_interval=timedelta(seconds=0),
            backoff_coefficient=1.0,
        )
        order_id = order_details["order_id"]

        # ReceiveOrder
        try:
            order_details = await workflow.execute_activity_method(
                activities.order_received,
                order_id,
                start_to_close_timeout=timedelta(seconds=0.1),
                retry_policy=retry_policy,
            )
        except asyncio.CancelledError:
            workflow.logger.warn("Activity cancelled due to timeout")
            return "Activity cancelled due to timeout"

        # ValidateOrder
        try:
            validate_output = await workflow.execute_activity_method(
                activities.order_validated,
                order_details,
                start_to_close_timeout=timedelta(seconds=0.1),
                retry_policy=retry_policy,
            )

        except asyncio.CancelledError:
            workflow.logger.warn("Activity cancelled due to timeout")
            return "Activity cancelled due to timeout"

        if validate_output:

            # Timer for manual review
            #time.sleep(300)

            # ChargePayment
            try:
                await workflow.execute_activity_method(
                    activities.payment_charged,
                    args=[order_details, payment_details["payment_id"]],
                    start_to_close_timeout = timedelta(seconds=0.1),
                    retry_policy = retry_policy,
                )
            except asyncio.CancelledError:
                workflow.logger.warn("Activity cancelled due to timeout")
                return "Activity cancelled due to timeout"

            # ShippingWorkflow
            try:
                await workflow.execute_child_workflow(
                    ShippingWorkflow.run,
                    order_details,
                    id=f"Shipping-{order_id}-Workflow",
                    task_queue="SHIPPING_QUEUE",
                )
            except WorkflowFailureError:
                print("Got expected exception: ", traceback.format_exc())


            # Shipped
            try:
                await workflow.execute_activity_method(
                    activities.order_shipped,
                    order_details,
                    start_to_close_timeout=timedelta(seconds=0.1),
                    retry_policy=retry_policy,
                )
            except asyncio.CancelledError:
                workflow.logger.warn("Activity cancelled due to timeout")
                return "Activity cancelled due to timeout"

            result = f"Order Workflow Complete for {order_id}!"
            return result

        else:
            workflow.logger.info("Rejecting order: no items")
            raise ValueError("No items to validate")


# PreparePackage → DispatchCarrier
@workflow.defn
class ShippingWorkflow:
    @workflow.run
    async def run(self, order_details) -> str:
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=0),
            backoff_coefficient=1.0,
        )

        print("Shipping workflow running")
        # PreparePackage
        try:
            await workflow.execute_activity_method(
                activities.package_prepared,
                order_details,
                start_to_close_timeout=timedelta(seconds=0.1),
                retry_policy=retry_policy,
                task_queue="SHIPPING_QUEUE",
            )
        except asyncio.CancelledError:
            workflow.logger.warn("Activity cancelled due to timeout")
            return "Activity cancelled due to timeout"

        # DispatchCarrier
        try:
            await workflow.execute_activity_method(
                activities.carrier_dispatched,
                order_details,
                start_to_close_timeout=timedelta(seconds=0.1),
                retry_policy=retry_policy,
                task_queue="SHIPPING_QUEUE",
            )
        except asyncio.CancelledError:
            workflow.logger.warn("Activity cancelled due to timeout")
            return "Activity cancelled due to timeout"

        result = f"Shipping Workflow Complete"
        return result
