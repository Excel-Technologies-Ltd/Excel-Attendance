# Copyright (c) 2024, Shaid Azmin and contributors
# For license information, please see license.txt

import frappe
import pymssql
from frappe.model.document import Document

class ExcelEmployeeAttendance(Document):
	
	def db_insert(self, *args, **kwargs):
		pass

	def load_from_db(self):
		pass

	def db_update(self, *args, **kwargs):
		pass

	@staticmethod
	def get_list(args):
		settings=frappe.get_doc("Excel Attendance Settings")
		server=settings.server
		database=settings.database
		username=settings.username
		password=settings.password
		conn = pymssql.connect(server, username, password, database)

		cursor = conn.cursor()
		cursor.execute('SELECT * FROM TabEmployeeAttendance')
		columns = [column[0] for column in cursor.description]
		rows = cursor.fetchall()
		data=[]

		for row in rows:
			row_dict = dict(zip(columns, row))
			data.append({
				"employee_id": row_dict['EmployeeID'],
    			"authentication_date_and_time": row_dict['AuthenticationDateAndTime'],
				"authentication_date": row_dict['AuthenticationDate'],
				"authentication_time": row_dict['AuthenticationTime'],
				"direction": row_dict['Direction'],
				"device_name": row_dict['DeviceName'],
				"device_serial_no": row_dict['DeviceSerialNo'],
				"person_name": row_dict['PersonName'],
				"Card No": row_dict['CardNo'],
				"name": str(row_dict['AuthenticationDateAndTime']),
				"is_sync": "Yes" if row_dict['sync'] else "No"
    
    
			})
		return data

	

	@staticmethod
	def get_count(args):
		pass

	@staticmethod
	def get_stats(args):
		pass
	
		
		