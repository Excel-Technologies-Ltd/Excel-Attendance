import frappe
import pymssql
import datetime

def get_name():
    print("Hello World")

def set_check_in():
    settings = frappe.get_doc("Excel Attendance Settings")
    server = settings.server
    database = settings.database
    username = settings.username
    password = settings.password
    print(settings)
    conn = pymssql.connect(server, username, password, database)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM TabEmployeeAttendance')
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    print(cursor)

    for row in rows:
        print(row)
        row_dict = dict(zip(columns, row))
        employee_name,employee_number = frappe.db.get_value('Employee', {"attandance_device_id":row_dict['EmployeeID']}, ['employee_name','employee_number'])
        # employee_name,employee_number = frappe.db.get_value('Employee', {"employee_number":row_dict['EmployeeID']}, ['employee_name','employee_number'])
        doc = frappe.get_doc({
            'doctype': "Employee Checkin",
            'employee': employee_number,
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


def attendance_sync():
    settings = frappe.get_doc("Excel Attendance Settings")
    shift_lists = frappe.db.get_list('Shift Type')
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    target_time = settings.attendance_sync_time if settings.attendance_sync_time else "23:30:00"

    # Combine date and time to form the target datetime
    target_datetime_str = f"{current_date} {target_time}"
    target_datetime = datetime.datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")

    for shift in shift_lists:
        frappe.db.set_value('Shift Type', shift.name, 'last_sync_of_checkin', target_datetime)

        
   
   
def set_device_id():
    employees = frappe.db.get_list('Employee', filters={'status': 'Active'}, fields=['name'])
    for employee in employees:
       id=extract_number_from_id(employee.name)
       frappe.db.set_value('Employee', employee.name, 'attandance_device_id', id)

   
def extract_number_from_id(identifier):
    if identifier.startswith('ETL') or identifier.startswith('EISL'):
        number = ''.join(filter(str.isdigit, identifier))
        return number
    else:
        return identifier    