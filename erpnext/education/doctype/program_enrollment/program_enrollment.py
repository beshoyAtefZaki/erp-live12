# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.model.document import Document
from frappe.desk.reportview import get_match_cond, get_filters_cond
from frappe.utils import comma_and


class ProgramEnrollment(Document):

    def validate(self):
        # self.validate_duplication()
        if not self.student_name:
            self.student_name = frappe.db.get_value("Student", self.student, "title")
        # if not self.courses:
        #   self.extend("courses", self.get_courses())
        self.warehouse = frappe.get_value("Company", {"name": self.company}, "warehouse")

    def on_update(self):
        if self.application == "Program":
            self.commission_rate = frappe.get_value("Item", {"name": self.program}, "commission_rate")
            #self.price = frappe.get_value("Program Application", {"name",self.program_application},"program_price")
        else:
            self.commission_rate = frappe.get_value("Item", {"name": self.course_level}, "commission_rate")
            #self.price = frappe.get_value("Course Application", {"name", self.course_application}, "course_level_price")
        self.total_commission_sp = 0
        total_commission_amount = 0
        self.total_amount = 0
        self.premiums_amount = 0
        if self.commission_rate and self.price:
            self.commission_amount = (self.commission_rate * self.price) / 100
        else:
            self.commission_rate = 0
        for f in self.follow_up:
            self.total_commission_sp += f.commission_rate

        for d in self.program_sales_invoice:
            if not d.price:
                d.price = 0
            else:
                d.commission_amount = (d.commission_rate * d.price) / 100
                total_commission_amount += d.commission_amount
                self.total_commission_amount = total_commission_amount + self.commission_amount
                self.total_amount += d.price

        for p in self.premiums1:
            self.premiums_amount += p.amount

    def on_submit(self):
        self.update_student_joining_date()
        # self.make_fee_records()
        self.make_sales_order_and_change_in_group()

    def make_sales_order_and_change_in_group(self):
        # To Remove Active From Other Student Group that don't belong to parent course in courses
        if self.application == "Course":
            for i in self.courses:
                frappe.db.sql(
                    """update `tabStudent Group Student` set active = 0 where parent_course = %s and student = %s""",
                    [i.course, self.student])

            # TO Add Student TO Student Group

            sg = frappe.get_doc("Student Group", {"name": self.student_group})
            if not frappe.db.exists("Student Group Student", {"parent":sg.name, "student": self.student}):
                sg.append("students", {
                    "student": self.student,
                    "student_name": self.student_name,
                    "active": 1,
                    "application": "Course"
                })
                sg.save()
        if self.premiums_amount != self.total_amount + self.price:
            frappe.throw(_("Premiums Amount Must Equal Total Amount + Price"))
        else:
            # make sales order
            si = frappe.new_doc("Sales Order")
            si.update({
                "customer": self.student_name,
                "transaction_date": self.enrollment_date,
                "total_commission_sp": self.total_commission_sp,
                "program_enrollment": self.name,
                "company": self.company,
                "currency": frappe.get_value("Course Application", {"name": self.course_application}, "currency")
            })
            if self.application == "Course":
                si.append("items", {
                    "item_code": self.course_level,
                    "qty": 1,
                    "rate": self.price,
                    "uom": "nos",
                    "conversion_factor": 1,
                    "item_name": self.course_level,
                    "description": self.course_level,
                    "delivery_date": self.enrollment_date,
                    "commission_amount": self.commission_amount
                })
            else:
                itemProgram = frappe.get_value("Item", {"name": self.program}, "name")
                si.append("items", {
                    "item_code":itemProgram,
                    "qty": 1,
                    "rate": self.price,
                    "uom": "nos",
                    "conversion_factor": 1,
                    "item_name": itemProgram,
                    "description": itemProgram,
                    "delivery_date": self.enrollment_date,
                    "commission_amount": self.commission_amount
                })

            for d in self.program_sales_invoice:
                si.append("items", {
                    "item_code": d.item,
                    "qty": 1,
                    "rate": d.price,
                    "uom": "nos",
                    "conversion_factor": 1,
                    "item_name": d.item,
                    "description": d.item,
                    "delivery_date": self.enrollment_date,
                    "commission_amount": d.commission_amount,
                    "warehouse": self.warehouse
                })
            for p in self.premiums1:
                si.append("payment_schedule", {
                    "due_date": p.due_date,
                    "invoice_portion": (p.amount/self.premiums_amount)*100,
                    "payment_amount": p.amount
                })
            if self.total_commission_sp:
                for t in self.follow_up:
                    si.append("sales_team", {
                        "commission_rate": t.commission_rate,
                        "sales_person": t.sales_person,
                        "allocated_percentage": (t.commission_rate / self.total_commission_sp) * 100,
                        "incentives": (t.commission_rate / self.total_commission_sp) * self.total_commission_amount
                    })
            si.save()
            si.submit()
            sales_order = frappe.get_last_doc("Sales Order")
            link = ["""<a href=desk#Form/Sales%20Order/{0}>{0}</a>""".format(sales_order.name)]
            frappe.msgprint(_("Sales Order Created - {0}").format(comma_and(link)))

    def update_student_joining_date(self):
        date = frappe.db.sql("select min(enrollment_date) from `tabProgram Enrollment` where student= %s", self.student)
        frappe.db.set_value("Student", self.student, "joining_date", date)

    """
    def validate_duplication(self):
        enrollment = frappe.get_all("Program Enrollment", filters={
            "student": self.student,
            "program": self.program,
            "academic_year": self.academic_year,
            "docstatus": ("<", 2),
            "name": ("!=", self.name)
        })
        if enrollment:
            frappe.throw(_("Student is already enrolled."))


    """

    def make_fee_records(self):
        from erpnext.education.api import get_fee_components
        fee_list = []
        for d in self.fees:
            fee_components = get_fee_components(d.fee_structure)
            if fee_components:
                fees = frappe.new_doc("Fees")
                fees.update({
                    "student": self.student,
                    "academic_year": self.academic_year,
                    "academic_term": d.academic_term,
                    "fee_structure": d.fee_structure,
                    "program": self.program,
                    "due_date": d.due_date,
                    "student_name": self.student_name,
                    "program_enrollment": self.name,
                    "components": fee_components
                })

                fees.save()
                fees.submit()
                fee_list.append(fees.name)
        if fee_list:
            fee_list = ["""<a href="#Form/Fees/%s" target="_blank">%s</a>""" % \
                        (fee, fee) for fee in fee_list]
            msgprint(_("Fee Records Created - {0}").format(comma_and(fee_list)))

    def get_courses(self):
        return frappe.db.sql(
            '''select course, course_name from `tabProgram Course` where parent = %s and required = 1''',
            (self.program), as_dict=1)


@frappe.whitelist()
def get_program_courses(doctype, txt, searchfield, start, page_len, filters):
    if filters.get('program'):
        return frappe.db.sql("""select course, course_name from `tabProgram Course`
			where  parent = %(program)s and course like %(txt)s {match_cond}
			order by
				if(locate(%(_txt)s, course), locate(%(_txt)s, course), 99999),
				idx desc,
				`tabProgram Course`.course asc
			limit {start}, {page_len}""".format(
            match_cond=get_match_cond(doctype),
            start=start,
            page_len=page_len), {
            "txt": "%{0}%".format(txt),
            "_txt": txt.replace('%', ''),
            "program": filters['program']
        })


@frappe.whitelist()
def get_students(doctype, txt, searchfield, start, page_len, filters):
    if not filters.get("academic_term"):
        filters["academic_term"] = frappe.defaults.get_defaults().academic_term

    if not filters.get("academic_year"):
        filters["academic_year"] = frappe.defaults.get_defaults().academic_year

    enrolled_students = frappe.get_list("Program Enrollment", filters={
        "academic_term": filters.get('academic_term'),
        "academic_year": filters.get('academic_year')
    }, fields=["student"])

    students = [d.student for d in enrolled_students] if enrolled_students else [""]

    return frappe.db.sql("""select
			name, title from tabStudent
		where 
			name not in (%s)
		and 
			`%s` LIKE %s
		order by 
			idx desc, name
		limit %s, %s""" % (
        ", ".join(['%s'] * len(students)), searchfield, "%s", "%s", "%s"),
                         tuple(students + ["%%%s%%" % txt, start, page_len]
                               )
                         )