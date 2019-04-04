# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Program(Document):
	def on_update(self):
		for d in self.courses:
			course = frappe.get_doc("Course", {"name": d.course})
			course.program = self.name
			course.save()
		if self.has_placement_test:
			self.placement_test = self.name + " Placement Test"
		self.make_item()
		self.make_item_price()
		self.make_item_placement_test()
		self.make_item_price_placement_test()
	def make_item(self):
		if not frappe.db.exists("Item", {"name": self.name}):
			item_doc = frappe.new_doc("Item")
			item_doc.update({
				"item_code": self.name,
				"item_name": self.name,
				"item_group": "Programs",
				"stock_uom": "Nos",
			})
			item_doc.save()

	def make_item_placement_test(self):
		if self.has_placement_test and not frappe.db.exists("Item", {"name": self.name + " Placement Test"}):
			item_doc = frappe.new_doc("Item")
			item_doc.update({

				"item_code": self.name + " Placement Test",
				"item_name": self.name + " Placement Test",
				"item_group": "Programs",
				"stock_uom": "Nos",
			})
			item_doc.save()

	def make_item_price_placement_test(self):
		if self.test_amount > 0 and not frappe.db.exists("Item Price", {"item_code": self.name + " Placement Test"}):
			item_price = frappe.new_doc("Item Price")
			item_price.update({
				"item_code": self.name + " Placement Test",
				"item_name": self.name + " Placement Test",
				"description": self.name + " Placement Test",
				"uom": "Nos",
				"min_qty": 1,
				"packing_unit": 1,
				"price_list_rate": self.test_amount,
				"currency": "EGP",
				"price_list": "Standard Selling",
				"selling": 1
			})
			item_price.save()
		if self.test_amount > 0 and frappe.db.exists("Item Price", {"item_code": self.name+ " Placement Test"}):
			item_price = frappe.get_doc("Item Price", {"item_code": self.name+ " Placement Test"})
			item_price.price_list_rate = self.test_amount
			item_price.save()

	def make_item_price(self):
		for d in self.price_list_courses1:
			if d.rate > 0 and not frappe.db.exists("Item Price", {"item_code": self.name,"valid_from": d.from_date,"price_list": d.price_list}):
				item_price = frappe.new_doc("Item Price")
				item_price.update({
					"item_code": self.name,
					"item_name": self.name,
					"description": self.name,
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
			if d.rate > 0 and frappe.db.exists("Item Price", {"item_code": self.name,"valid_from": d.from_date,"price_list": d.price_list}):
				item_price = frappe.get_doc("Item Price", {"item_code": self.name,"valid_from": d.from_date,"price_list": d.price_list})
				item_price.price_list_rate = d.rate
				item_price.valid_from = d.from_date
				item_price.save()
