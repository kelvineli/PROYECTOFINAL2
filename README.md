Nombre: Kélvin Elí Ramírez Ponciano
ID: 000131643
Curso: Programación IV
Proyecto Final - Fase II

Este proyecto implementa una arquitectura distribuida. Una API permite enviar notificaciones mediante RabbitMQ
Un worker procesa estas notificaciones y registra las trazas en MySQL
Un balanceador con NGINX permite escalar horizontalmente la API con varias réplicas.

Se usó Python 3.12 + Flask, MySQL 8.0, RabbitMQ 3-managment, Docker y Docker Compose, NGINX (como balanceador reverse proxy), Worker en Python

INSTRUCCIONES:
1. Clonar el repositorio:
  git clone https://github.com/kelvineli/PROYECTOFINAL2
  cd practica
2. Construir y levantar servicios:
   docker compose up -d --build --scale api=3
   Esto levanta:
     1. MySQL (mysql-students)
     2. 1 RabbitMQ (rabbitmq)
     3. 3 Instancias de API (practica-api-1, practica-api-2 y practica-api-3)
     4. 1 Worker (practica-worker-1)
     5. 1 NGINX (nginx-balancer)

PRUEBA: 
POST http://localhost:8080/api/v1/notifications/email (o bien) POST http://localhost:8080/api/v1/notifications/sms
Content-Type: application/json

{
  "to": "test@example.com",
  "subject": "Hola",
  "body": "Prueba"
}
RESPUESTA:
{
  "request_id": "uuid utilizada"
}

PARA APAGAR AMBIENTE:
docker compose down -v
