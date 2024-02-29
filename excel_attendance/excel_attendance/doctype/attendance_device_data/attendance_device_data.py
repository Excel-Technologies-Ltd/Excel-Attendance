from frappe.model.document import Document
import pymssql
import pika


class AttendanceDeviceData(Document):
    
    pass
    # server = '192.168.30.200'
    # database = 'hikvisiondb'
    # username = 'sa'
    # password = 'Excel@Azmin2024'
    # conn = pymssql.connect(server, username, password, database )
    # cursor = conn.cursor()
    # print("\n\n\n")
    # print("\nConnected to the database successfully.\n")
    # print("\n\n\n")
    # cursor.execute('SELECT * FROM TabEmployeeAttendance')
    # for row in cursor:
    #     print("\n\n\n")
    #     print('ROW : %r' %(row,))
    #     print("\n\n\n")
    
    # # Connect to RabbitMQ
    # connection = pika.BlockingConnection(pika.ConnectionParameters('192.168.30.200'))
    # channel = connection.channel()

    # # Declare the queue to receive messages
    # channel.queue_declare(queue='employee_queue')

    # def onMQ_data_insert(ch, method, properties, body):
    #     print("New record inserted into TabEmployeeAttendance table:")
    #     print(body.decode())

    # # Start consuming messages from the queue
    # channel.basic_consume(queue='employee_queue', on_message_callback=onMQ_data_insert, auto_ack=True)
    # print("Waiting for new records...")
    # channel.start_consuming()    



