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
    """
    Efficiently sync attendance data from TabEmployeeAttendance to Employee Checkin.
    Processes records in batches with proper transaction handling.
    """
    conn = None
    cursor = None

    try:
        # Get database settings
        settings = frappe.get_doc("Excel Attendance Settings")
        server = settings.server
        database = settings.database
        username = settings.username
        password = settings.password

        # Connect to external database
        conn = pymssql.connect(server, username, password, database)
        cursor = conn.cursor()

        # Query to fetch unsynced records with deduplication
        query = """
            WITH RankedAttendance AS (
                SELECT
                    *,
                    ROW_NUMBER() OVER (
                        PARTITION BY EmployeeID, AuthenticationDateAndTime
                        ORDER BY AuthenticationDateAndTime ASC
                    ) AS rn
                FROM TabEmployeeAttendance
                WHERE sync = 0
            )
            SELECT TOP 200
                EmployeeID,
                PersonName,
                AuthenticationDate,
                AuthenticationTime,
                AuthenticationDateAndTime,
                DeviceName,
                sync
            FROM RankedAttendance
            WHERE rn = 1
            ORDER BY AuthenticationDateAndTime ASC
        """

        cursor.execute(query)
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()

        if not rows:
            frappe.logger().info("No unsynced attendance records found")
            return

        frappe.logger().info(f"Processing {len(rows)} attendance records")

        # Track statistics
        stats = {
            "processed": 0,
            "success": 0,
            "failed": 0,
            "unmatched_employee": 0,
            "duplicate_skipped": 0
        }

        # Track records to sync (batch update at the end)
        records_to_sync = []

        # Cache for employee lookups (reduce DB queries)
        employee_cache = {}

        # Cache for existing checkins to avoid duplicate DB queries
        existing_checkins_cache = {}

        # Cache for employee daily checkin status
        employee_daily_checkin_cache = {}

        # Process each record
        for row in rows:
            row_dict = dict(zip(columns, row))
            employee_id = str(row_dict["EmployeeID"]).strip()
            person_name = row_dict.get("PersonName", "").strip()
            auth_date = row_dict.get("AuthenticationDate")
            auth_time = row_dict.get("AuthenticationTime")
            auth_datetime = row_dict.get("AuthenticationDateAndTime")
            device_name = row_dict.get("DeviceName", "").strip()

            # Create full timestamp
            timestamp = f"{auth_date} {auth_time}"

            try:
                # Check employee cache first to reduce DB queries
                if employee_id not in employee_cache:
                    employee = frappe.db.get_value(
                        "Employee",
                        {"attandance_device_id": employee_id},
                        ["name", "employee_name"],
                        as_dict=True
                    )
                    employee_cache[employee_id] = employee
                else:
                    employee = employee_cache[employee_id]

                if not employee:
                    # Log unmatched employee
                    _create_checkin_log(
                        device_id=employee_id,
                        person_name=person_name,
                        timestamp=timestamp,
                        date=auth_date,
                        time=auth_time,
                        log_message=f"Device ID '{employee_id}' not matched with any employee"
                    )
                    stats["unmatched_employee"] += 1

                    # Add to batch sync list
                    records_to_sync.append((employee_id, auth_datetime))
                    continue

                # Check duplicate using cache
                checkin_key = f"{employee.name}|{timestamp}"
                if checkin_key not in existing_checkins_cache:
                    existing_checkin = frappe.db.exists(
                        "Employee Checkin",
                        {
                            "employee": employee.name,
                            "time": timestamp
                        }
                    )
                    existing_checkins_cache[checkin_key] = existing_checkin
                else:
                    existing_checkin = existing_checkins_cache[checkin_key]

                if existing_checkin:
                    frappe.logger().debug(
                        f"Duplicate checkin skipped for {employee.name} at {timestamp}"
                    )
                    stats["duplicate_skipped"] += 1

                    # Add to batch sync list
                    records_to_sync.append((employee_id, auth_datetime))
                    continue

                # Determine log type using cache
                daily_key = f"{employee.name}|{auth_date}"
                if daily_key not in employee_daily_checkin_cache:
                    log_type = _determine_log_type(employee.name, auth_date)
                    employee_daily_checkin_cache[daily_key] = True  # Mark as has checkin
                else:
                    # Already has a checkin today (from earlier in this batch), so this is OUT
                    log_type = "OUT"

                # Create Employee Checkin
                checkin_doc = frappe.get_doc({
                    "doctype": "Employee Checkin",
                    "employee": employee.name,
                    "employee_name": employee.employee_name,
                    "log_type": log_type,
                    "time": timestamp,
                    "date": auth_date,
                    "device_id": device_name,
                    "skip_auto_attendance": 0
                })
                checkin_doc.insert(ignore_permissions=True)

                # Update cache to mark this exact timestamp as processed
                existing_checkins_cache[checkin_key] = True

                frappe.logger().debug(
                    f"Created {log_type} checkin for {employee.name} at {timestamp}"
                )
                stats["success"] += 1

                # Add to batch sync list instead of immediate update
                records_to_sync.append((employee_id, auth_datetime))

            except Exception as e:
                stats["failed"] += 1
                error_msg = frappe.get_traceback()
                frappe.logger().error(
                    f"Error processing attendance for {employee_id}: {str(e)}\n{error_msg}"
                )

                # Log the error
                try:
                    _create_checkin_log(
                        device_id=employee_id,
                        person_name=person_name,
                        timestamp=timestamp,
                        date=auth_date,
                        time=auth_time,
                        log_message=f"Processing error: {str(e)}"
                    )
                except Exception as log_error:
                    frappe.logger().error(f"Failed to create error log: {str(log_error)}")

                # Still add to batch sync to avoid infinite retry
                records_to_sync.append((employee_id, auth_datetime))

            finally:
                stats["processed"] += 1

        # Batch update sync status - single transaction for all records
        if records_to_sync:
            _batch_update_sync_status(cursor, records_to_sync)

        # Commit all changes
        frappe.db.commit()
        conn.commit()

        # Log summary
        frappe.logger().info(
            f"Attendance sync completed: {stats['processed']} processed, "
            f"{stats['success']} success, {stats['failed']} failed, "
            f"{stats['unmatched_employee']} unmatched, {stats['duplicate_skipped']} duplicates"
        )

    except Exception as e:
        # Rollback on error
        if conn:
            conn.rollback()
        frappe.db.rollback()

        error_msg = frappe.get_traceback()
        frappe.logger().error(f"Fatal error in attendance sync: {str(e)}\n{error_msg}")
        frappe.log_error(title="Attendance Sync Failed", message=error_msg)

    finally:
        # Clean up database connections
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _determine_log_type(employee, date):
    """
    Determine if the checkin should be IN or OUT based on existing checkins for the day.
    Uses the last checkin's type to alternate properly.
    """
    has_checkins_today = frappe.db.get_value(
        "Employee Checkin",
        {
            "employee": employee,
            "date": date
        }
    )

    # If there's a previous checkin, alternate the type
    if  not has_checkins_today:
        return "IN"
    else:
        return "OUT"


def _create_checkin_log(device_id, person_name, timestamp, date, time, log_message):
    """
    Create an Employee Checkin Log entry for unmatched or error records.
    """
    try:
        frappe.get_doc({
            "doctype": "Employee Checkin Log",
            "device_id": device_id,
            "person_name": person_name,
            "authentication_time": timestamp,
            "date": date,
            "time": time,
            "log": log_message
        }).insert(ignore_permissions=True)
    except Exception as e:
        frappe.logger().error(f"Failed to create checkin log: {str(e)}")


def _batch_update_sync_status(cursor, records_to_sync):
    """
    Batch update sync status in the external database for multiple records.
    This is much more efficient than individual updates.

    Args:
        cursor: Database cursor
        records_to_sync: List of tuples [(employee_id, auth_datetime), ...]
    """
    if not records_to_sync:
        return

    try:
        # Build a batch update using CASE statement for better performance
        # For SQL Server, we can use a table-valued parameter approach or batch individual updates

        # Method 1: Execute batch updates (most compatible with pymssql)
        batch_size = 50
        total_updated = 0

        for i in range(0, len(records_to_sync), batch_size):
            batch = records_to_sync[i:i + batch_size]

            # Build WHERE clause with OR conditions for this batch
            conditions = []
            params = []

            for employee_id, auth_datetime in batch:
                conditions.append("(EmployeeID = %s AND AuthenticationDateAndTime = %s)")
                params.extend([employee_id, auth_datetime])

            where_clause = " OR ".join(conditions)
            query = f"UPDATE TabEmployeeAttendance SET sync = 1 WHERE {where_clause}"

            cursor.execute(query, tuple(params))
            total_updated += len(batch)

        frappe.logger().debug(f"Batch updated sync status for {total_updated} records")

    except Exception as e:
        frappe.logger().error(f"Failed to batch update sync status: {str(e)}")




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
        settings.attendance_sync_time if settings.attendance_sync_time else "23:50:00"
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
        # Execute the delete query
        frappe.db.sql(
            """
            DELETE FROM `tabEmployee Checkin`
            WHERE date < DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)
            """
        )
        frappe.db.commit()  # Commit the changes to the database
        print("Old Employee Checkin records deleted successfully.")
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

import re

def extract_number_from_id(identifier):
    if identifier.startswith("ETL") or identifier.startswith("EISL"):
        match = re.match(r"^(ETL|EISL)(\d+)(.*)", identifier)
        if match:
            number = match.group(2)
            suffix = match.group(3).strip()
            return f"{number} {suffix}".strip()
    return identifier
