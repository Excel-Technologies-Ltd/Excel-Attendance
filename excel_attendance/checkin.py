import frappe
import pymssql
import datetime
from frappe.utils import get_datetime


def get_name():
    doc = frappe.get_doc(
        {
            "doctype": "Employee Checkin",
            "employee": "ETL20050261",
            "employee_name": "sohan",
            "log_type": "IN",
            "time": "2024-03-28 08:30:00",
            "device_id": "device1",
        }
    ).insert()


def set_check_in():
    settings = frappe.get_doc("Excel Attendance Settings")
    server = settings.server
    database = settings.database
    username = settings.username
    password = settings.password
    conn = pymssql.connect(server, username, password, database)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM TabEmployeeAttendance WHERE sync=0")
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    for row in rows:
        row_dict = dict(zip(columns, row))
        test = frappe.db.exists(
            "Employee", {"attandance_device_id": row_dict["EmployeeID"]}
        )
        if not test:
            try:
                frappe.get_doc({
                    "doctype": "Employee Checkin Log",
                    "device_id": row_dict.get("EmployeeID"),
                    "person_name": row_dict.get("PersonName"),
                    "authentication_time": f"{row_dict.get('AuthenticationDate')} {row_dict.get('AuthenticationTime')}",
                    "log": "Device id not match with employee id",
                    "date":row_dict.get("AuthenticationDate"),
                    "time":row_dict.get("AuthenticationTime")
                }).insert()
            except Exception as ex:
                print("Error inserting Employee Checkin Log document:", )
                cursor.execute(
                            "UPDATE TabEmployeeAttendance SET sync = 1 WHERE EmployeeID = %s AND AuthenticationDateAndTime = %s",
                            (row_dict["EmployeeID"], row_dict["AuthenticationDateAndTime"]),
                )

        else:
            employee_name, employee_number = frappe.db.get_value(
                "Employee",
                {"attandance_device_id": row_dict["EmployeeID"]},
                ["employee_name", "employee_number"],
            )
            date = row_dict.get("AuthenticationDate")
            test_check_in = frappe.db.exists(
                "Employee Checkin", {"date": date, "employee": employee_number}
            )
            print(test_check_in)
            if test_check_in:
                log_type = "OUT"
            else:
                log_type = "IN"
            try:
                doc = frappe.get_doc(
                    {
                        "doctype": "Employee Checkin",
                        "employee": employee_number,
                        "employee_name": employee_name,
                        "log_type": log_type,
                        "skip_auto_attendance":0,
                        "time": f"{date} {row_dict.get('AuthenticationTime')}",
                        "date": row_dict.get("AuthenticationDate"),
                        "device_id": row_dict.get("DeviceName"),
                    }
                ).insert()
                print(doc)
                if doc:
                    try:
                        cursor.execute(
                            "UPDATE TabEmployeeAttendance SET sync = 1 WHERE EmployeeID = %s AND AuthenticationDateAndTime = %s",
                            (row_dict["EmployeeID"], row_dict["AuthenticationDateAndTime"]),
                        )
                        frappe.db.commit()
                        conn.commit()
                    except Exception as update_error:
                        frappe.db.rollback()
                        conn.rollback()
                        print("Error updating TabEmployeeAttendance:", update_error)
                        try:
                            frappe.get_doc({
                                "doctype": "Employee Checkin Log",
                                "device_id": row_dict.get("EmployeeID"),
                                "person_name": row_dict.get("PersonName"),
                                "authentication_time": f"{row_dict.get('AuthenticationDate')} {row_dict.get('AuthenticationTime')}",
                                "log": f"Rollback",
                                "date":row_dict.get("AuthenticationDate"),
                                "time":row_dict.get("AuthenticationTime")
                            }).insert()
                        except Exception as ex:
                            print("Error inserting Employee Checkin Log document:", ex)
            except Exception as e:
                try:
                    frappe.get_doc({
                        "doctype": "Employee Checkin Log",
                        "device_id": row_dict.get("EmployeeID"),
                        "person_name": row_dict.get("PersonName"),
                        "authentication_time": f"{row_dict.get('AuthenticationDate')} {row_dict.get('AuthenticationTime')}",
                        "log": f"Error inserting Employee Checkin document: {frappe.as_json(e)}",
                        "date":row_dict.get("AuthenticationDate"),
                        "time":row_dict.get("AuthenticationTime")
                    }).insert()
                except Exception as ex:
                    print("Error inserting Employee Checkin Log document:", ex)

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

import datetime

def delete_oldest_non_sync_records():
    settings = frappe.get_doc("Excel Attendance Settings")
    server = settings.server
    database = settings.database
    username = settings.username
    password = settings.password
    conn = pymssql.connect(server, username, password, database)
    cursor = conn.cursor()

    # Calculate the date three months ago
    two_months_ago = datetime.datetime.now() - datetime.timedelta(days=60)

    # Construct the SQL query to delete records older than three months and have sync = 1
    delete_query = """
    DELETE FROM TabEmployeeAttendance
    WHERE sync=0 AND AuthenticationDateAndTime <= %s
    """
    
    # Execute the delete query
    cursor.execute(delete_query, (two_months_ago,))
    conn.commit()


def attendance_sync():
    settings = frappe.get_doc("Excel Attendance Settings")
    shift_lists = frappe.db.get_list("Shift Type")
    current_datetime = get_datetime()
    current_date = current_datetime.strftime("%Y-%m-%d")
    target_time = (
        settings.attendance_sync_time if settings.attendance_sync_time else "23:30:00"
    )

    # Combine date and time to form the target datetime
    target_datetime_str = f"{current_date} {target_time}"
    target_datetime = datetime.datetime.strptime(
        target_datetime_str, "%Y-%m-%d %H:%M:%S"
    )

    for shift in shift_lists:
        frappe.db.set_value(
            "Shift Type", shift.name, "last_sync_of_checkin", target_datetime
        )

def delete_employee_checkin():
    try:
        results = frappe.db.sql(
            """
            SELECT e.attendance, e.date, e.name
            FROM `tabEmployee Checkin` AS e
            WHERE e.date < DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY) AND e.attendance IS NOT NULL
            """,
            as_dict=True)
        
        for data in results:
            try:
                frappe.delete_doc('Employee Checkin', data.name)
                print(f"Deleted document: {data.name}")
            except Exception as e:
                print(f"An error occurred while deleting {data.name}: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    
@frappe.whitelist()
def set_device_id():
    employees = frappe.db.get_list(
        "Employee", filters={"status": "Active"}, fields=["name"]
    )
    for employee in employees:
        id = extract_number_from_id(employee.name)
        frappe.db.set_value("Employee", employee.name, "attandance_device_id", id)


def extract_number_from_id(identifier):
    if identifier.startswith("ETL") or identifier.startswith("EISL"):
        number = "".join(filter(str.isdigit, identifier))
        return number
    else:
        return identifier
