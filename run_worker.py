import asyncio
import uuid
from temporalio.client import Client
from temporalio.worker import Worker

import activities
from workflows import OrderWorkflow, ShippingWorkflow

async def main() -> None:
    client: Client = await Client.connect("localhost:7233", namespace="default")
    # Run the worker
    worker = Worker(
        client,
        task_queue="ORDER_QUEUE",
        workflows=[OrderWorkflow],
        activities=[activities.order_received,
                    activities.order_validated,
                    activities.payment_charged,
                    activities.order_shipped],
        identity=f"order-w1-{uuid.uuid4()}",
    )
    # Worker for the child workflow
    worker_child = Worker(
        client,
        task_queue="SHIPPING_QUEUE",
        workflows=[ShippingWorkflow],
        activities=[activities.package_prepared,
                    activities.carrier_dispatched],
        identity = f"ship-w1-{uuid.uuid4()}",
    )

    await asyncio.gather(worker.run(), worker_child.run())


if __name__ == "__main__":
    asyncio.run(main())