# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe

from frappe.utils import getdate, nowdate
from frappe import _
from frappe.model.document import Document
from erpnext.hr.utils import set_employee_name
from frappe.utils import cstr
import datetime

class Attendance(Document):

	def on_change(self):
		if frappe.db.exists("Employee", {"fingerprint": self.fingerprint}):
			employee = frappe.get_doc("Employee", {"fingerprint": self.fingerprint})
			self.employee = employee.name
			self.employee_name = employee.employee_name
			self.company = employee.company

	def validate_duplicate_record(self):
		res = frappe.db.sql("""select name from `tabAttendance` where employee = %s and attendance_date = %s
			and name != %s and docstatus != 2""",
			(self.employee, self.attendance_date, self.name))
		if res:
			frappe.throw(_("Attendance for employee {0} is already marked").format(self.employee))

		set_employee_name(self)

	def check_leave_record(self):
		leave_record = frappe.db.sql("""select leave_type, half_day, half_day_date from `tabLeave Application`
			where employee = %s and %s between from_date and to_date and status = 'Approved'
			and docstatus = 1""", (self.employee, self.attendance_date), as_dict=True)
		if leave_record:
			for d in leave_record:
				if d.half_day_date == getdate(self.attendance_date):
					self.status = 'Half Day'
					frappe.msgprint(_("Employee {0} on Half day on {1}").format(self.employee, self.attendance_date))
				else:
					self.status = 'On Leave'
					self.leave_type = d.leave_type
					frappe.msgprint(_("Employee {0} is on Leave on {1}").format(self.employee, self.attendance_date))

		if self.status == "On Leave" and not leave_record:
			frappe.throw(_("No leave record found for employee {0} for {1}").format(self.employee, self.attendance_date))

	def validate_attendance_date(self):
		date_of_joining = frappe.db.get_value("Employee", self.employee, "date_of_joining")

		if getdate(self.attendance_date) > getdate(nowdate()):
			frappe.throw(_("Attendance can not be marked for future dates"))
		elif date_of_joining and getdate(self.attendance_date) < getdate(date_of_joining):
			frappe.throw(_("Attendance date can not be less than employee's joining date"))

	def validate_employee(self):
		emp = frappe.db.sql("select name from `tabEmployee` where name = %s and status = 'Active'",
		 	self.employee)
		if not emp:
			frappe.throw(_("Employee {0} is not active or does not exist").format(self.employee))

	def validate(self):
		from erpnext.controllers.status_updater import validate_status
		validate_status(self.status, ["Present", "Absent", "On Leave", "Half Day"])
		self.validate_attendance_date()
		self.validate_duplicate_record()
		self.check_leave_record()
		self.attendance_times()

	def on_update(self):
		self.attendance_times()

	def on_submit(self):
		self.make_attendance_deduction()
		self.attendance_times()


	def attendance_times(self):
		from frappe.utils import to_timedelta
		d = datetime.datetime.strptime(self.attendance_date, '%Y-%m-%d')
		shift = frappe.db.get_value("Employee", self.employee, "shift_type")
		if frappe.db.exists("Shift Type", {"name": shift}) and self.status == "Present":
			self.total_hours = to_timedelta(self.end_time) - to_timedelta(self.start_time)
			shift_type = frappe.get_doc("Shift Type", {"name": shift})
			remaining_minutes = (to_timedelta(frappe.db.sql("""select (sum(TIME_TO_SEC(late))) as lates from `tabAttendance`  where   employee = %s
													and month(attendance_date) = %s and over1 = "-120"  and docstatus != 2  """
														   , [self.employee, d.month])[0][0]) )
			if not remaining_minutes:
				remaining_minutes = 0.0
				self.over1 = "N"
			else:
				remaining_minutes = remaining_minutes /60
			self.remaining_minutes = 0.0
			if to_timedelta(self.start_time) > to_timedelta(shift_type.start_time) and \
					(to_timedelta(self.start_time) - to_timedelta(shift_type.start_time)) > to_timedelta(shift_type.late_attendance):
				self.late = to_timedelta(self.start_time) - to_timedelta(shift_type.start_time)
				self.over1 = "+15"
			elif to_timedelta(self.start_time) > to_timedelta(shift_type.start_time) and \
						(to_timedelta(self.start_time) - to_timedelta(shift_type.start_time)) <= to_timedelta(shift_type.late_attendance) \
						and remaining_minutes == to_timedelta(shift_type.total_allowance_minutes_on_month):
				self.late = to_timedelta(self.start_time) - to_timedelta(shift_type.start_time)
				self.over1 = "N"
				self.remaining_minutes = remaining_minutes
			elif to_timedelta(self.start_time) > to_timedelta(shift_type.start_time) and \
						(to_timedelta(self.start_time) - to_timedelta(shift_type.start_time)) <= to_timedelta(shift_type.late_attendance) \
						and remaining_minutes < to_timedelta(shift_type.total_allowance_minutes_on_month):
				self.late = to_timedelta(self.start_time) - to_timedelta(shift_type.start_time)
				self.over1 = "-120"
				self.remaining_minutes = remaining_minutes
			elif to_timedelta(self.start_time) > to_timedelta(shift_type.start_time) and \
						(to_timedelta(self.start_time) - to_timedelta(shift_type.start_time)) <= to_timedelta(shift_type.late_attendance) \
						and remaining_minutes > to_timedelta(shift_type.total_allowance_minutes_on_month):
				self.late = to_timedelta(self.start_time) - to_timedelta(shift_type.start_time)
				self.over1 = "+120"
			else:
				self.late = None
				self.over1 = "N"

			if to_timedelta(shift_type.end_time) > to_timedelta(self.end_time):
				self.early = to_timedelta(shift_type.end_time) - to_timedelta(self.end_time)
			else:
				self.early = None
			if to_timedelta(self.end_time) > to_timedelta(shift_type.end_time):
				self.extra_hours = to_timedelta(self.end_time) - to_timedelta(shift_type.end_time)
			else:
				self.extra_hours = None
		else:
			self.late = None
			self.early = None
			self.extra_hours = None

		if not self.status == "Present":
			self.start_time = None
			self.end_time = None
			self.total_hours = None

		if not frappe.db.exists("Shift Type", {"name": shift}) and self.status == "Present":
			self.total_hours = to_timedelta(self.end_time) - to_timedelta(self.start_time)

	def make_attendance_deduction(self):
		from frappe.utils import to_timedelta
		shift = frappe.db.get_value("Employee", self.employee, "shift_type")
		if frappe.db.exists("Shift Type", {"name": shift}) and self.status == "Absent":
			shift_type = frappe.get_doc("Shift Type", {"name": shift})
			if shift_type.apply_absent_rules:
				ad = frappe.new_doc("Attendance Deduction")
				ad.update({
					"employee": self.employee,
					"posting_date": self.attendance_date,
					"shifts": shift_type.name,
					"attendance": self.name,
					"absent": 1,
					"rate": self.absent_count
					})
				ad.save()
				ad.submit()
		if frappe.db.exists("Shift Type", {"name": shift}) and self.late and (self.over1 == "+120" or self.over1 == "+15") and self.status == "Present":
			late = frappe.db.sql("""select TIME_TO_SEC(late) from `tabAttendance` where name = %s""", self.name)[0][0]
			if late:
				shift = frappe.db.get_value("Employee", self.employee, "shift_type")
				shift_type = frappe.get_doc("Shift Type", {"name": shift})
				ad = frappe.new_doc("Attendance Deduction")
				ad.update({
					"employee": self.employee,
					"posting_date": self.attendance_date,
					"shifts": shift_type.name,
					"attendance": self.name,
					"deduction_type": "Minutes",
					"rate_minutes": 4 * late / 60
				})
				ad.save()
				ad.submit()

	def on_cancel(self):
		if frappe.db.exists("Attendance Deduction" , {"attendance":self.name}):
			ad = frappe.get_doc("Attendance Deduction" , {"attendance":self.name})
			ad.cancel()

@frappe.whitelist()
def get_events(start, end, filters=None):
	events = []

	employee = frappe.db.get_value("Employee", {"user_id": frappe.session.user})

	if not employee:
		return events

	from frappe.desk.reportview import get_filters_cond
	conditions = get_filters_cond("Attendance", filters, [])
	add_attendance(events, start, end, conditions=conditions)
	return events

def add_attendance(events, start, end, conditions=None):
	query = """select name, attendance_date, status
		from `tabAttendance` where
		attendance_date between %(from_date)s and %(to_date)s
		and docstatus < 2"""
	if conditions:
		query += conditions

	for d in frappe.db.sql(query, {"from_date":start, "to_date":end}, as_dict=True):
		e = {
			"name": d.name,
			"doctype": "Attendance",
			"date": d.attendance_date,
			"title": cstr(d.status),
			"docstatus": d.docstatus
		}
		if e not in events:
			events.append(e)
