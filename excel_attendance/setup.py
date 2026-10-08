import frappe

# The hourly HRMS job `process_auto_attendance_for_all_shifts` marks attendance
# as soon as a shift's checkins become eligible, i.e. throughout the day. This app
# instead marks attendance once per day from `excel_attendance.checkin.attendance_sync`
# (the 23:59 cron). So the hourly job must stay stopped, otherwise it marks
# attendance mid-day. This runs on every `bench migrate` so the setting ships in the
# image and survives updates that would otherwise re-enable the job.
HOURLY_AUTO_ATTENDANCE_JOB = "shift_type.process_auto_attendance_for_all_shifts"


def stop_hourly_auto_attendance():
    if frappe.db.exists("Scheduled Job Type", HOURLY_AUTO_ATTENDANCE_JOB):
        frappe.db.set_value(
            "Scheduled Job Type", HOURLY_AUTO_ATTENDANCE_JOB, "stopped", 1
        )
        frappe.db.commit()
