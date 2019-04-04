# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import _

class Course(Document):

	def validate(self):
		self.validate_assessment_criteria()
		self.course_code=self.course_name
		if self.hpt:
			self.placement_test = self.course_name + " Placement Test"

	def validate_assessment_criteria(self):
		if self.assessment_criteria:
			total_weightage = 0
			for criteria in self.assessment_criteria:
				total_weightage += criteria.weightage or 0
			if total_weightage != 100:
				frappe.throw(_("Total Weightage of all Assessment Criteria must be 100%"))

	def on_update(self):
		self.make_item_group()
		self.make_item()
		self.make_item_price()
		self.make_item_placement_test()
		self.make_item_price_placement_test()
		#self.make_item_down_payment()
		#self.make_item_price_down_payment()

	def make_item_group(self):
		if self.group and not frappe.db.exists("Item Group", {"name": self.course_name}):
			item_group_doc = frappe.new_doc("Item Group")
			item_group_doc.update({
				"item_group_name": self.course_name,
				"parent_item_group": self.parent,
				"course": self.course_name
			})
			item_group_doc.save()

	def make_item(self):
		if not self.group and not frappe.db.exists("Item", {"name": self.course_name}):
			item_doc = frappe.new_doc("Item")
			item_doc.update({
				"item_code": self.course_name,
				"item_name": self.course_name,
				"item_group": self.parent,
				"stock_uom": "Nos",
				"course_level": self.course_name
			})
			item_doc.save()

	def make_item_placement_test(self):
		if self.hpt and not frappe.db.exists("Item", {"name": self.course_name + " Placement Test"}):
			item_doc = frappe.new_doc("Item")
			item_doc.update({

				"item_code": self.course_name + " Placement Test",
				"item_name": self.course_name + " Placement Test",
				"item_group": self.course_name,
				"stock_uom": "Nos",
				"course_level": self.course_name
			})
			item_doc.save()

	def make_item_price_placement_test(self):
		if self.test_amount > 0 and not frappe.db.exists("Item Price", {"item_code": self.course_name + " Placement Test"}):
			item_price = frappe.new_doc("Item Price")
			item_price.update({
				"item_code": self.course_name + " Placement Test",
				"item_name": self.course_name + " Placement Test",
				"description": self.course_name + " Placement Test",
				"uom": "Nos",
				"min_qty": 1,
				"packing_unit": 1,
				"price_list_rate": self.test_amount,
				"currency": "EGP",
				"price_list": "Standard Selling",
				"selling": 1
			})
			item_price.save()
		if self.test_amount > 0 and frappe.db.exists("Item Price", {"item_code": self.course_name+ " Placement Test"}):
			item_price = frappe.get_doc("Item Price", {"item_code": self.course_name+ " Placement Test"})
			item_price.price_list_rate = self.test_amount
			item_price.save()

	def make_item_price(self):
		for d in self.price_list_courses1:
			if d.rate > 0 and not frappe.db.exists("Item Price", {"item_code": self.course_name,"valid_from": d.from_date,"price_list": d.price_list}):
				item_price = frappe.new_doc("Item Price")
				item_price.update({
					"item_code": self.course_name,
					"item_name": self.course_name,
					"description": self.course_name,
					"uom": "Nos",
					"min_qty": 1,
					"packing_unit": 1,
					"valid_from": d.from_date,
					"price_list_rate": d.rate,
					"currency": frappe.get_value("Price List", {"name":d.price_list},"currency"),
					"price_list": d.price_list,
					"selling": 1
				})
				item_price.save()
			if d.rate > 0 and frappe.db.exists("Item Price", {"item_code": self.course_name,"valid_from": d.from_date,"price_list": d.price_list}):
				item_price = frappe.get_doc("Item Price", {"item_code": self.course_name,"valid_from": d.from_date,"price_list": d.price_list})
				item_price.price_list_rate = d.rate
				item_price.valid_from = d.from_date
				item_price.save()

	"""
	def make_item_price_down_payment(self):
		if self.item_down_payment > 0 and not frappe.db.exists("Item Price", {"item_code": self.course_name + " Down Payment"},{"valid_from": self.from_date}):
			item_price = frappe.new_doc("Item Price")
			item_price.update({
				"item_code": self.course_name + " Down Payment",
				"item_name": self.course_name + " Down Payment",
				"description": self.course_name + " Down Payment",
				"uom": "Nos",
				"min_qty": 1,
				"packing_unit": 1,
				"valid_from": self.from_date,
				"price_list_rate": self.down_payment_amount,
				"currency": "EGP",
				"price_list": "Standard Selling",
				"selling": 1
			})
			item_price.save()
		if self.item_down_payment > 0 and frappe.db.exists("Item Price", {"item_code": self.course_name + " Down Payment"},{"valid_from": self.from_date}):
			item_price = frappe.get_doc("Item Price", {"item_code": self.course_name + " Down Payment"},{"valid_from": self.from_date})
			item_price.price_list_rate = self.down_payment_amount
			item_price.valid_from = self.from_date
			item_price.save()

	
	def make_item_down_payment(self):
		if self.down_payment and not frappe.db.exists("Item", {"name": self.course_name + " Down Payment"}):
			item_doc = frappe.new_doc("Item")
			item_doc.update({

				"item_code": self.course_name + " Down Payment",
				"item_name": self.course_name + " Down Payment",
				"item_group": self.course_name,
				"stock_uom": "Nos"
				#"course_level": self.course_name
			})
			item_doc.save()
	"""

