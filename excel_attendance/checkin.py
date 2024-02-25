import frappe
import pymssql

def get_name():
    print("Hello World")

def set_check_in():
    settings = frappe.get_doc("Excel Attendance Settings")
    server = settings.server
    database = settings.database
    username = settings.username
    password = settings.password
    conn = pymssql.connect(server, username, password, database)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM TabEmployeeAttendance WHERE sync = 0')
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()

    for row in rows:
        row_dict = dict(zip(columns, row))
        employee_name = frappe.db.get_value('Employee', row_dict['EmployeeID'], 'employee_name')
        print(employee_name)
        
        doc = frappe.get_doc({
            'doctype': "Employee Checkin",
            'employee': row_dict['EmployeeID'],
            'employee_name': employee_name,
            'log_type': row_dict['Direction'],
            'time': row_dict['AuthenticationDateAndTime'],
            'device_id': row_dict['DeviceName'],
        }).insert()
       

        cursor.execute(
            "DELETE TabEmployeeAttendance  WHERE EmployeeID = %s AND AuthenticationDateAndTime = %s",
            (row_dict['EmployeeID'], row_dict['AuthenticationDateAndTime'])
        )
        conn.commit()

    
    
    
def delete_synced_records():
	settings = frappe.get_doc("Excel Attendance Settings")
	server = settings.server
	database = settings.database
	username = settings.username
	password = settings.password
	conn = pymssql.connect(server, username, password, database)
	cursor = conn.cursor()

	cursor.execute("DELETE FROM TabEmployeeAttendance WHERE sync = 1")
	conn.commit()
