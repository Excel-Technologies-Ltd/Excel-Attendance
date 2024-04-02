import frappe
import pymssql
import datetime


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
    cursor.execute("SELECT * FROM TabEmployeeAttendance")
    columns = [column[0] for column in cursor.description]
    rows = cursor.fetchall()
    for row in rows:
        row_dict = dict(zip(columns, row))
        test = frappe.db.exists(
            "Employee", {"attandance_device_id": row_dict["employeeID"]}
        )
        if not test:
            cursor.execute(
                "DELETE TabEmployeeAttendance  WHERE employeeID = %s AND datetime = %s",
                (row_dict["employeeID"], row_dict["datetime"]),
            )
        else:
            employee_name, employee_number = frappe.db.get_value(
                "Employee",
                {"attandance_device_id": row_dict["employeeID"]},
                ["employee_name", "employee_number"],
            )
            date = row_dict.get("date")
            test_check_in = frappe.db.exists(
                "Employee Checkin", {"date": date, "employee": employee_number}
            )
            print(test_check_in)
            if test_check_in:
                log_type = "OUT"
            else:
                log_type = "IN"
            print(log_type)
            print(employee_name, employee_number)
            print(f"{date} {row_dict.get('time')}")
            try:
                doc = frappe.get_doc(
                    {
                        "doctype": "Employee Checkin",
                        "employee": employee_number,
                        "employee_name": employee_name,
                        "log_type": log_type,
                        "time": f"{date} {row_dict.get('time')}",
                        "date": row_dict.get("date"),
                        "device_id": row_dict.get("devicename"),
                    }
                ).insert()
                print(doc)
                if doc:
                    cursor.execute(
                        "DELETE TabEmployeeAttendance  WHERE employeeID = %s AND datetime = %s",
                        (row_dict["employeeID"], row_dict["datetime"]),
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
    shift_lists = frappe.db.get_list("Shift Type")
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
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
