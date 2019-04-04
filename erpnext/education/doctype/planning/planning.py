# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Planning(Document):
	def on_submit(self):
		self.make_new_waiting_list_and_student_group_and_trp()
	"""
	def on_cancel(self):
		if frappe.db.exists("Waiting List", {"planning": self.name}):
			wl = frappe.get_doc("Waiting List", {"planning": self.name})
			wl.cancel()
	"""
	def on_update_after_submit(self):
		self.update_waiting_list_and_student_group()

	def make_new_waiting_list_and_student_group_and_trp(self):

		sg = frappe.new_doc("Student Group")
		sg.update({
			"student_group_name": self.course + " "+self.academic_term,
			"company": self.company,
			"course": self.course,
			"planning": self.name,
			"parent": self.parent,
			"group_based_on": "Course",
			"max_strength": self.size,
			"academic_year": self.academic_year,
			"academic_term": self.academic_term,
			"type": self.type,
			"from_time": None,
			"to_time": None

		})
		sg.save()
		"""
		wl = frappe.new_doc("Waiting List")
		student_group = frappe.get_doc("Student Group", {"planning": self.name})
		wl.update({
			"company": self.company,
			"course": self.course,
			"room": self.room,
			"instructor": self.instructor,
			"student_group": student_group.name,
			"size": self.size,
			"course_start_date": self.course_start_date,
			"course_end_date": self.course_end_date,
			"parent": self.parent,
			"planning": self.name,
			"academic_year": self.academic_year,
			"academic_term": self.academic_term,
			"type": self.type
		})
		wl.save()
		wl.submit()
		trp = frappe.new_doc("TRP")
		cost = frappe.db.sql(select min(total_cost) from `tabRoom`)[0][0]
		roomDoc = frappe.get_doc("Room", {"total_cost": cost}, {"size_capacity": [">=", self.size]})
		#part_time = frappe.get_list("Employee", filters={"employment_type": "Part-time"}, fields=["employee_name"])[0]
		#rate = frappe.get_list("Salary Structure", filters={"name": part_time}, fields=["hour_rate"])
		#min_rate = min(rate)
		#ss = frappe.get_list("Salary Structure", filters={"hour_rate": min_rate}, fields=["name"])[0]
		min_rate = frappe.db.sql(select min(s.hour_rate)from `tabEmployee` e inner join `tabSalary Structure` s on s.name = e.employee_name
										where s.salary_slip_based_on_timesheet = 1)[0][0]
		instructor = frappe.get_value("Salary Structure", {"hour_rate": min_rate}, "name")

		trp.update({
			"company": self.company,
			"course": self.course,
			"room": self.room,
			"instructor": self.instructor,
			"room_size": self.size,
			"parent": self.parent,
			"planning": self.name,
			"academic_year": self.academic_year,
			"academic_term": self.academic_term,
			"system_suggests_room": roomDoc.name,
			"system_suggests_instructor": instructor,
			"system_suggests_room_size": roomDoc.size_capacity
		})
		trp.save()
		trp.submit()
		"""
	def update_waiting_list_and_student_group(self):
		sg = frappe.get_doc("Student Group", {"planning": self.name})
		sg.update({
			"max_strength": self.size,
			"academic_term": self.academic_term,
			"from_time": None,
			"to_time": None

		})
		sg.save()
		"""
		wl = frappe.get_doc("Waiting List", {"planning": self.name})
		wl.update({
			"room": self.room,
			"instructor": self.instructor,
			"size": self.size,
			"course_start_date": self.course_start_date,
			"course_end_date": self.course_end_date,
			"academic_term": self.academic_term
		})
		wl.submit()
		"""
