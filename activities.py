import asyncio, random
from typing import Dict, Any
import mysql.connector
from temporalio import activity
from datetime import datetime
import json

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="trellis"
)
cursor = conn.cursor()

async def flaky_call() -> None:
    """Either raise an error or sleep long enough to trigger an activity timeout."""
    rand_num = random.random()
    if rand_num < 0.33:
        raise RuntimeError("Forced failure for testing")

    if rand_num < 0.67:
        await asyncio.sleep(300)  # Expect the activity layer to time out before this completes

@activity.defn
async def order_received(order_id: str) -> Dict[str, Any]:
    await flaky_call()
    # TODO: Implement DB write: insert new order record

    # Write to orders
    cursor.execute("SELECT 1 FROM orders WHERE id = %s", (order_id,))
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO orders (id, state, address_json, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
            (order_id, "received", '{"street":"123 Main St"}', datetime.now(), datetime.now()))
        conn.commit()

    payload = {"order_id": order_id, "items": [{"sku": "ABC", "qty": 1}]}

    # Log event
    cursor.execute(
        "INSERT INTO events (order_id, type, payload_json, ts) VALUES (%s, %s, %s, %s)",
        (order_id, "received", json.dumps(payload), datetime.now()))
    conn.commit()
    print("Received Order:", order_id)

    return payload
@activity.defn
async def order_validated(order: Dict[str, Any]) -> bool:
    await flaky_call()
    # TODO: Implement DB read/write: fetch order, update validation status

    # Fetch order
    cursor.execute("SELECT id FROM orders WHERE id=%s", (order["order_id"],))
    row = cursor.fetchone()

    if row is None:
        print("Order already validated")
        return False

    else:
        cursor.execute(
            "UPDATE orders SET state=%s, updated_at=%s WHERE id=%s",
            ("validated", datetime.now(), order["order_id"]))
        conn.commit()
        # Log event
        cursor.execute(
            "INSERT INTO events (order_id, type, payload_json, ts) VALUES (%s, %s, %s, %s)",
            (order["order_id"], "validated", json.dumps(order), datetime.now()))
        conn.commit()
        print("Validated Order:", order)

        return True
@activity.defn
async def payment_charged(order: Dict[str, Any], payment_id: str) -> Dict[str, Any]:
    # Check if paid
    cursor.execute(
        "SELECT status FROM payments WHERE payment_id=%s",
        (payment_id,))
    row = cursor.fetchone()

    await flaky_call()
    # TODO: Implement DB read/write: check payment record, insert/update payment status

    amount = sum(i.get("qty", 1) for i in order.get("items", []))

    if row is None:
        # Charge
        cursor.execute(
            "INSERT INTO payments (payment_id, order_id, status, amount) VALUES (%s, %s, %s, %s)",
            (payment_id, order["order_id"], "charged", amount)
        )
        conn.commit()

        # Update status
        cursor.execute(
            "UPDATE orders SET state=%s, updated_at=%s WHERE id=%s",
            ("charged", datetime.now(), order["order_id"]))
        conn.commit()

        # Log event
        cursor.execute(
            "INSERT INTO events (order_id, type, payload_json, ts) VALUES (%s, %s, %s, %s)",
            (order["order_id"], "charged", json.dumps(order), datetime.now()))
        conn.commit()
    print("Charged Payment:", order, payment_id)
    return {"status": "charged", "amount": amount}

@activity.defn
async def order_shipped(order: Dict[str, Any]) -> str:
    await flaky_call()
    # TODO: Implement DB write: update order status to shipped

    cursor.execute(
        "UPDATE orders SET state=%s, updated_at=%s WHERE id=%s",
        ("shipped", datetime.now(), order["order_id"]))
    conn.commit()

    # Log event
    cursor.execute(
        "INSERT INTO events (order_id, type, payload_json, ts) VALUES (%s, %s, %s, %s)",
        (order["order_id"], "shipped", json.dumps(order), datetime.now()))
    conn.commit()

    print("Shipped Order:", order)
    return "Shipped"
@activity.defn
async def package_prepared(order: Dict[str, Any]) -> str:
    await flaky_call()
    # TODO: Implement DB write: mark package prepared in DB

    print("Preparing package")
    cursor.execute(
        "UPDATE orders SET state=%s, updated_at=%s WHERE id=%s",
        ("package prepared", datetime.now(), order["order_id"]))
    conn.commit()

    # Log event
    cursor.execute(
        "INSERT INTO events (order_id, type, payload_json, ts) VALUES (%s, %s, %s, %s)",
        (order["order_id"], "package prepared", json.dumps(order), datetime.now()))
    conn.commit()

    print("Prepared Package for Order:", order)
    return "Package ready"
@activity.defn
async def carrier_dispatched(order: Dict[str, Any]) -> str:
    await flaky_call()
    # TODO: Implement DB write: record carrier dispatch status

    cursor.execute(
        "UPDATE orders SET state=%s, updated_at=%s WHERE id=%s",
        ("Dispatched", datetime.now(), order["order_id"]))
    conn.commit()

    # Log event
    cursor.execute(
        "INSERT INTO events (order_id, type, payload_json, ts) VALUES (%s, %s, %s, %s)",
        (order["order_id"], "Dispatched", json.dumps(order), datetime.now()))
    conn.commit()

    print("Dispatched Order:", order)
    return "Dispatched"
