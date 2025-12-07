from . import __version__ as app_version

app_name = "excel_attendance"
app_title = "Excel Attendance"
app_publisher = "Shaid Azmin"
app_description = (
    "A ERPNext Based Hikvision Device Integrated Attendane Management Apps"
)
app_email = "azmin@excelbd.com"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/excel_attendance/css/excel_attendance.css"
# app_include_js = "/assets/excel_attendance/js/excel_attendance.js"

# include js, css files in header of web template
# web_include_css = "/assets/excel_attendance/css/excel_attendance.css"
# web_include_js = "/assets/excel_attendance/js/excel_attendance.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "excel_attendance/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
doctype_list_js = {"Employee": "public/js/employee_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# "Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# "methods": "excel_attendance.utils.jinja_methods",
# "filters": "excel_attendance.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "excel_attendance.install.before_install"
# after_install = "excel_attendance.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "excel_attendance.uninstall.before_uninstall"
# after_uninstall = "excel_attendance.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "excel_attendance.utils.before_app_install"
# after_app_install = "excel_attendance.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "excel_attendance.utils.before_app_uninstall"
# after_app_uninstall = "excel_attendance.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "excel_attendance.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# "Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# "Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {"Shift Type": "excel_attendance.override.CustomShiftType"}

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# "*": {
# "on_update": "method",
# "on_cancel": "method",
# "on_trash": "method"
# }
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
    "all": ["excel_attendance.checkin.set_check_in"],
    "monthly": ["excel_attendance.checkin.delete_oldest_non_sync_records"],
    "cron": {
        "0 23 * * *": ["excel_attendance.checkin.attendance_sync"],
        "0 6 * * *": ["excel_attendance.checkin.delete_employee_checkin"],
        "0 0 */2 * *": ["excel_attendance.checkin.delete_synced_records"]
        },
}

# Testing
# -------

# before_tests = "excel_attendance.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# "frappe.desk.doctype.event.event.get_events": "excel_attendance.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# "Task": "excel_attendance.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["excel_attendance.utils.before_request"]
# after_request = ["excel_attendance.utils.after_request"]

# Job Events
# ----------
# before_job = ["excel_attendance.utils.before_job"]
# after_job = ["excel_attendance.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# {
# "doctype": "{doctype_1}",
# "filter_by": "{filter_by}",
# "redact_fields": ["{field_1}", "{field_2}"],
# "partial": 1,
# },
# {
# "doctype": "{doctype_2}",
# "filter_by": "{filter_by}",
# "partial": 1,
# },
# {
# "doctype": "{doctype_3}",
# "strict": False,
# },
# {
# "doctype": "{doctype_4}"
# }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# "excel_attendance.auth.validate"
# ]
fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name",
                "in",
                [
                    "Employee Checkin-longitude",
                    "Employee Checkin-latitude",
                    "Employee Checkin-address",
                    "Employee Checkin-project",
                    "Employee Checkin-location",
                    "Employee Checkin-date",
                    "Employee Checkin-attach_image",
                    "Employee Checkin-section_break_c4p01",
                    "Employee Checkin-column_break_rlf7h",
                    "Employee Checkin-section_break_gwzsw",
                    "Employee-attandance_device_id",
                ],
            ]
        ],
    }
]
