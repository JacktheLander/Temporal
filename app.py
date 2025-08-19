from flask import Flask, request, jsonify
import asyncio
import json
from run_workflow import main as workflow
from temporalio.client import Client
import mysql.connector
from datetime import datetime

app = Flask(__name__)
conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="trellis"
    )
cursor = conn.cursor()

@app.post("/orders/<order_id>/start")
async def start_order(order_id):
    try:
        result = await workflow(order_id)
        return "", 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.post("/orders/<order_id>/signals/cancel")
async def cancel_order(order_id):
    client: Client = await Client.connect("localhost:7233", namespace="default")
    try:
        result = await client.get_workflow_handle(f"Order-{order_id}-Workflow").terminate()
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

@app.get("/orders/<order_id>/status")
async def get_status(order_id):
    # Fetch order
    try:
        cursor.execute("SELECT state FROM orders WHERE id=%s", (order_id,))
        row = cursor.fetchone()
        return jsonify({"state": row[0]})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=8000)