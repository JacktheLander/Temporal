import asyncio
import traceback
import secrets
from temporalio.client import Client, WorkflowFailureError

from workflows import OrderWorkflow, OrderDetails, PaymentDetails


async def main(order_id: str,) -> None:
    # Create client connected to server at the given address
    client: Client = await Client.connect("localhost:7233")

    OrderData = OrderDetails(
        order_id=f"{order_id}",
        items=[],
    )

    PaymentData = PaymentDetails(
        payment_id=f"{secrets.token_hex(3)}",
        status="New",
        amount=0.0,
    )
    data = {
        "order": OrderData,
        "payment": PaymentData,
    }

    try:
        result = await client.execute_workflow(
            OrderWorkflow.run,
            data,
            id=f"Order-{OrderData.order_id}-Workflow",
            task_queue="ORDER_QUEUE",
        )

        print(f"Result: {result}")

    except WorkflowFailureError:
        print("Got expected exception: ", traceback.format_exc())


if __name__ == "__main__":
    asyncio.run(main(f'{secrets.token_hex(3)}'))