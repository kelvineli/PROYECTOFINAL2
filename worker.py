import os
import json
import time
import pika
import mysql.connector
from mysql.connector import Error

RABBIT_HOST = os.getenv("RABBIT_HOST", "rabbitmq")
WORKER_NAME = os.getenv("WORKER_NAME", "worker1")
DB_HOST = os.getenv("DB_HOST", "db")
DB_USER = os.getenv("DB_USER", "students_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "student_pass")
DB_NAME = os.getenv("DB_NAME", "students_db")

def get_db_conn():
    return mysql.connector.connect(
        host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME
    )

def insert_trace(request_id, balanceador, api_instance, queue_name, worker_name, notification_type, payload, status):
    conn = None
    cursor = None
    try:
        conn = get_db_conn()
        cursor = conn.cursor()
        sql = """INSERT INTO notification_trace
                 (request_id, balanceador, api_instance, queue_name, worker_name, notification_type, payload, status)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
        cursor.execute(sql, (
            request_id, balanceador, api_instance, queue_name, worker_name, notification_type, json.dumps(payload), status
        ))
        conn.commit()
    except Exception as e:
        print("[WORKER] DB insert error:", e)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def process_message(ch, method, properties, body):
    try:
        msg = json.loads(body)
        request_id = msg.get("request_id")
        qname = method.routing_key
        ntype = msg.get("type")
        api_instance = msg.get("api_instance")
        balanceador = msg.get("balanceador")
        payload = msg.get("payload")

        # Simula procesamiento
        print(f"[{WORKER_NAME}] Procesando {request_id} tipo={ntype} desde {qname}")
        time.sleep(1)  # simular trabajo

        # insertar traza en BD
        insert_trace(request_id, balanceador, api_instance, qname, WORKER_NAME, ntype, payload, "processed")

        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"[{WORKER_NAME}] Procesado {request_id}")
    except Exception as e:
        print("[WORKER] Error procesando:", e)
        try:
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception:
            pass

def main():
    credentials = pika.PlainCredentials('guest','guest')
    params = pika.ConnectionParameters(host=RABBIT_HOST, credentials=credentials, heartbeat=600, blocked_connection_timeout=300)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='q.email', durable=True)
    channel.queue_declare(queue='q.sms', durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume('q.email', process_message)
    channel.basic_consume('q.sms', process_message)
    print(f"[*] Worker {WORKER_NAME} esperando mensajes (RabbitMQ={RABBIT_HOST})")
    channel.start_consuming()

if __name__ == "__main__":
    main()
