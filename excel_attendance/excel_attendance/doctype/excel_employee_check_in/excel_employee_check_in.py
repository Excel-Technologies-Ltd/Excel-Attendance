# Copyright (c) 2024, Shaid Azmin and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import pymssql
import pika
import time

def send_to_queue(channel, data):
    channel.basic_publish(exchange='',
                          routing_key='employee_queue',
                          body=data)

def real_time_consumer(ch, method, properties, body):
    # Modify this function to perform actions when a new record is received
    print("New record received:")
    print(body.decode())

def start_consumer():
    # Set up RabbitMQ connection
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare the same queue named 'employee_queue'
    channel.queue_declare(queue='employee_queue')

    # Set up the consumer to use the real_time_consumer function
    channel.basic_consume(queue='employee_queue',
                          on_message_callback=real_time_consumer,
                          auto_ack=True)

    print("Consumer waiting for messages. To exit press CTRL+C")
    try:
        # Start consuming messages
        channel.start_consuming()
    except KeyboardInterrupt:
        pass
    finally:
        connection.close()

class ExcelEmployeeCheckIN(Document):
    server = '192.168.30.175'
    database = 'hickvisondb'
    username = 'sa'
    password = 'Excel@Azmin2023'
    conn = pymssql.connect(server, username, password, database)

    cursor = conn.cursor()
    # Set up RabbitMQ connection
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    # Declare a queue named 'employee_queue'
    channel.queue_declare(queue='employee_queue')

    try:
        while True:
            # Check for new events by querying the TabEmployeeAttendance table
            cursor.execute('SELECT * FROM TabEmployeeAttendance')

            for row in cursor:
                # Send each new row to the RabbitMQ queue
                send_to_queue(channel, str(row))

            # Sleep for a short duration to avoid continuous polling
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        conn.close()
        connection.close()
