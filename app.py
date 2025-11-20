from flask import Flask, request, jsonify
from typing import Dict
from dataclasses import asdict, dataclass
import os
import mysql.connector
from mysql.connector import Error

from uuid import uuid4
import json
import pika

def publish_queue(queue_name: str, message: dict):
    credentials = pika.PlainCredentials('guest', 'guest')
    params = pika.ConnectionParameters(host=os.getenv("RABBIT_HOST", "rabbitmq"), credentials=credentials, heartbeat=600, blocked_connection_timeout=300)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        )
    )
    connection.close()

app = Flask(__name__)

#---Configuración bd
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_USER = os.getenv("DB_USER", "students_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "student_pass")
DB_NAME = os.getenv("DB_NAME", "students_db")   

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

@app.get("/health")
def health_check():
    instance = os.getenv("HOSTNAME", "unknown")
    return jsonify({"status": "ok", "instance": instance}), 200

def bad_request(msg: str, status: int =400):
    return jsonify("Error: " + msg), status

"""
@dataclass
class Student:
    id: int
    name: str
    age: int | None = None
    email: str | None = None

students: Dict [int, Student] = {}
"""

@app.post("/student")
def create_student():
    """Create a new student record.
        {
            "name": "Kelvin",
            "age": 35,
            "email": "stkram@upana.edu.gt"
        }
    """

    if not request.is_json:
        return bad_request("Debe ser JSON")
    data = request.get_json(silent=True) or {}
    """
    missing = [k for k in ("name") if k not in data]
    if missing:
        return bad_request("Faltan campos")
    """
    try:
        name = str(data["name"]).strip()
    except Exception:
        return bad_request("Nombre debe estar vacio")
    
    age = None
    if "age" in data and data ["age"] is not None:
        try:
            age = int(data["age"])
        except Exception:
            return bad_request("Edad debe ser entero")

    email = None
    if "email" in data and data ["email"] is not None:
        email = str(data["email"]).strip()
        if not email:
            email = None
    

    try:
        conn = get_connection()
        cursor = conn.cursor()

        sql="INSERT INTO student (id, name, age, email) VALUES (NULL, %s, %s, %s)"

        cursor.execute(sql, (name, age, email))
        conn.commit()

        student_id = cursor.lastrowid
        cursor.close()
        conn.close()
        student = {
            "id": student_id,
            "name": name,
            "age": age,
            "email": email
        }

        print("Nuevo Estudiante:",student)
        return jsonify(student), 201
    except Error as e:
        print("[DB]Error al Insertar", e)
        return bad_request("Error base de datos", 500)

@app.get("/students")
def get_all_students():
    """Devuelve todos estudiantes"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, age, email FROM student")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        students = []
        for r in rows:
            students.append({
                "id": r[0],
                "name": r[1],
                "age": r[2],
                "email": r[3]
            })
        return jsonify(students), 200
            
    except Error as e:
        print("[DB]Error al Insertar", e)
        return bad_request("Error base de datos", 500) 

@app.post("/api/v1/notifications/email")
def notify_email():
    if not request.is_json:
        return jsonify({"error":"Debe ser JSON"}), 400
    data = request.get_json(silent=True) or {}
    # validar campos mínimos según tu criterio
    if not data.get("to"):
        return jsonify({"error":"Falta campo 'to'"}), 400

    request_id = str(uuid4())
    message = {
        "request_id": request_id,
        "type": "email",
        "payload": data,
        "balanceador": request.headers.get("Host", "unknown"),
        "api_instance": os.getenv("HOSTNAME", "unknown")
    }
    try:
        publish_queue("q.email", message)
        return jsonify({"request_id": request_id}), 202
    except Exception as e:
        print("[API] Error publicando q.email:", e)
        return jsonify({"error":"Error interno"}), 500

@app.post("/api/v1/notifications/sms")
def notify_sms():
    if not request.is_json:
        return jsonify({"error":"Debe ser JSON"}), 400
    data = request.get_json(silent=True) or {}
    if not data.get("to"):
        return jsonify({"error":"Falta campo 'to'"}), 400

    request_id = str(uuid4())
    message = {
        "request_id": request_id,
        "type": "sms",
        "payload": data,
        "balanceador": request.headers.get("Host", "unknown"),
        "api_instance": os.getenv("HOSTNAME", "unknown")
    }
    try:
        publish_queue("q.sms", message)
        return jsonify({"request_id": request_id}), 202
    except Exception as e:
        print("[API] Error publicando q.sms:", e)
        return jsonify({"error":"Error interno"}), 500

@app.get("/students/<int:student_id>")
def get_student_by_id(student_id: int):
    """Devuelve un estudiante por ID"""
    try:
        conn=get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, age, email FROM student WHERE id = %s", (student_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return bad_request("Estudiante no encontrado", 404)
        student = {
            "id": row[0],
            "name": row[1],
            "age": row[2],
            "email": row[3]
        }
        return jsonify(student), 200

    except Error as e:
        print("[DB]Error al Insertar", e)
        return bad_request("Error base de datos", 500)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)