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
    check_out_time = settings.check_out_time
    if not check_out_time:
        check_out_time = "15:00:00"
    conn = pymssql.connect(server, username, password, database)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM TabEmployeeAttendance')
   
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    check_out_time = datetime.datetime.strptime(check_out_time, "%H:%M:%S").time()
    for row in rows:
        row_dict = dict(zip(columns, row))
        test=frappe.db.exists("Employee", {"attandance_device_id": row_dict['EmployeeID']})
        if not test:
            print('come')
            cursor.execute(
                "DELETE TabEmployeeAttendance  WHERE EmployeeID = %s AND AuthenticationDateAndTime = %s",
                (row_dict['EmployeeID'], row_dict['AuthenticationDateAndTime'])
            )
        else:
            employee_name, employee_number = frappe.db.get_value('Employee', {"attandance_device_id":row_dict['EmployeeID']}, ['employee_name','employee_number'])
            authentication_time = row_dict['AuthenticationTime']
            if authentication_time >= check_out_time:
                log_type = 'OUT'
            else:
                log_type = 'IN'
            print(log_type)
            try:
                doc = frappe.get_doc({
                    'doctype': "Employee Checkin",
                    'employee': employee_number,
                    'employee_name': employee_name,
                    'log_type': log_type,
                    'time': row_dict['AuthenticationDateAndTime'],
                    'device_id': row_dict['DeviceName'],
                }).insert()
                print(doc)
                if doc:
                    cursor.execute(
                        "DELETE TabEmployeeAttendance  WHERE EmployeeID = %s AND AuthenticationDateAndTime = %s",
                        (row_dict['EmployeeID'], row_dict['AuthenticationDateAndTime'])
                    )
            except Exception as e:
                print("Error inserting Employee Checkin document:", e)
        conn.commit()

    
    
    
def delete_synced_records():
	settings = frappe.get_doc("Excel Attendance Settings")
	server = settings.server
	database = settings.database
	username = settings.username
	password = settings.password
	conn = pymssql.connect(server, username, password, database)
	cursor = conn.cursor()

	cursor.execute("DELETE FROM TabEmployeeAttendance")
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