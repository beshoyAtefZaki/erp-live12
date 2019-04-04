	# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import time

class CourseSchedule(Document):
	def validate(self):
		self.instructor_name = frappe.db.get_value("Instructor", self.instructor, "instructor_name")
		self.set_title()
		self.validate_course()
		self.validate_date()
		self.validate_overlap()

	def on_submit(self):
		self.make_time_sheet()
	
	def set_title(self):
		"""Set document Title"""
		self.title = self.course + " by " + (self.instructor_name if self.instructor_name else self.instructor)
	
	def validate_course(self):
		group_based_on, course = frappe.db.get_value("Student Group", self.student_group, ["group_based_on", "course"])
		if group_based_on == "Course":
			self.course = course

	def validate_date(self):
		"""Validates if from_time is greater than to_time"""
		if self.from_time > self.to_time:
			frappe.throw(_("From Time cannot be greater than To Time."))
	
	def validate_overlap(self):
		"""Validates overlap for Student Group, Instructor, Room"""
		
		from erpnext.education.utils import validate_overlap_for

		#Validate overlapping course schedules.
		if self.student_group:
			validate_overlap_for(self, "Course Schedule", "student_group")
		
		validate_overlap_for(self, "Course Schedule", "instructor")
		validate_overlap_for(self, "Course Schedule", "room")

		#validate overlapping assessment schedules.
		if self.student_group:
			validate_overlap_for(self, "Assessment Plan", "student_group")
		
		validate_overlap_for(self, "Assessment Plan", "room")
		validate_overlap_for(self, "Assessment Plan", "supervisor", self.instructor)

	def make_time_sheet(self):
		if self.calculate_instructor_hour_rate and not frappe.db.exists("Timesheet", {"course_schedule": self.name}):
			from frappe.utils import time_diff
			from frappe.utils import get_datetime
			ts = frappe.new_doc("Timesheet")
			ts.update({
				"employee": frappe.get_value("Instructor", {"name": self.instructor}, "employee"),
				"company": self.company,
				"course_schedule": self.name
			})
			ts.append("time_logs", {
				"activity_type": "Teaching",
				"hours": round(float(time_diff(self.to_time, self.from_time).total_seconds()) / 3600, 6),

				"from_time": get_datetime(str(self.schedule_date) + " "+str(self.from_time)),
				"to_time":  get_datetime(str(self.schedule_date) + " "+str(self.to_time))
			})
			ts.save()
			ts.submit()


