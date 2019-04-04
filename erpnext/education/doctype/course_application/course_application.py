
from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.model.document import Document
from frappe.utils import comma_and

class CourseApplication(Document):

    def validate(self):
        course_level = frappe.get_value("Student Group", {"name": self.student_group}, "course")
        price_list = frappe.get_value("Customer Group", {"name": self.kind}, "default_price_list")
        self.currency = frappe.get_value("Item Price", {"item_code": course_level, "price_list": price_list},"currency")
        self.course_level = course_level
        course_level_price = frappe.get_value("Item Price", {"item_code": course_level, "price_list": price_list},
                                              "price_list_rate")
        self.course_level_price = course_level_price

        self.placement_test = frappe.get_value("Course", {"name": self.course}, "placement_test")
        if self.placement_test and not frappe.db.exists("Course Application", {"has_placement_test": 1, "student": self.student, "course": self.course}):
            self.has_placement_test = 1

        self.percent = frappe.get_value("Course", {"name": self.course}, "percent")

        if frappe.session.user != "Administrator":
            if frappe.db.exists("Employee", {"user_id": frappe.session.user}):
                employee = frappe.get_doc("Employee", {"user_id": frappe.session.user})
                self.company = employee.company
            else:
                frappe.throw(_("User {0} Must To Link With Employee").format(frappe.session.user))

    def on_change(self):
        self.amount = self.percent * self.course_level_price / 100
        if self.amount:
            self.down_payment = 1
        if self.application_status =="Admitted" and self.docstatus == 1 and not frappe.db.exists("Program Enrollment", {"course_application":self.name}) \
                and not frappe.db.exists("Student", {"title": self.student_applicant}):
            self.make_student()
            self.make_program_enrollment()
            actual = frappe.db.sql("select count(waiting_list) from `tabCourse Application` where "
                                   " docstatus = '1' and application_status = 'Admitted' and waiting_list= %s", self.waiting_list)
            frappe.db.set_value("Waiting List", self.waiting_list, "actual", actual)
            wl = frappe.get_doc("Waiting List", {"name": self.waiting_list})
            wl.available = wl.size - wl.actual
            wl.save()

        self.total_commission_sp = 0
        for d in self.follow_up:
            self.total_commission_sp += d.commission_rate

    def on_update_after_submit(self):
        if self.application_status == "Approved":
            self.make_customer()
            self.make_sales_order()

    def make_program_enrollment(self):
        if not self.follow_up:
            program_enrollment = frappe.new_doc("Program Enrollment")
            program_enrollment.update({
                "student": self.student,
                "student_name": self.student_name,
                "academic_year": self.academic_year,
                "academic_term": self.academic_term,
                "program": self.program,
                "percent": self.percent,
                "student_group": self.student_group,
                "company": self.company,
                "course_application": self.name,
                "course_level": self.course_level,
                "price": self.course_level_price,
                "application": "Course"
            })
            #Link Materials
            course = frappe.get_doc("Course", {"name": self.course_level})
            for m in course.materials:
                if frappe.get_value("Item Price", {"item_code": m.materials, "price_list": "Standard Selling"},"price_list_rate"):
                    price = frappe.get_value("Item Price", {"item_code": m.materials, "price_list": "Standard Selling"},"price_list_rate")
                else:
                    price = 0
                commission_rate = frappe.get_value("Item", {"name": m.materials}, "commission_rate")
                program_enrollment.append("program_sales_invoice", {
                    "item": m.materials,
                    "price": price,
                    "commission_rate": commission_rate,
                    "commission_amount":  price * commission_rate
                })
            program_enrollment.append("courses", {"course": self.course_level})
            program_enrollment.save()
            program_enrollment_msg = frappe.get_doc("Program Enrollment", {"course_application": self.name})
            link = ["""<a href=desk#Form/Program%20Enrollment/{0}>{0}</a>""".format(program_enrollment_msg.name)]
            frappe.msgprint(_("Program Enrollment Created - {0} As a Draft.").format(comma_and(link)))
        else:
            for d in self.follow_up:
                if not d.sales_person:
                    frappe.throw("Please Enter Sales Person In Follow UP")
                else:
                    user = frappe.get_doc("User", {"name": frappe.session.user})
                    if not user.sales_person:
                        frappe.throw(_("User {0} Missing Field Sales Person").format(user.name))
                    else:
                        self.mpe = 1
        if self.mpe:
            program_enrollment = frappe.new_doc("Program Enrollment")
            program_enrollment.student = self.student
            program_enrollment.student_name = self.student_name
            program_enrollment.academic_year = self.academic_year
            program_enrollment.academic_term = self.academic_term
            program_enrollment.follow_up = self.follow_up
            program_enrollment.program = self.program
            program_enrollment.percent = self.percent
            program_enrollment.student_group = self.student_group
            program_enrollment.company = self.company
            program_enrollment.course_application = self.name
            program_enrollment.course_level = self.course_level
            program_enrollment.price = self.course_level_price,
            program_enrollment.application = "Course"
            program_enrollment.append("courses", {"course": self.course_level})
            #Link Materials
            course = frappe.get_doc("Course", {"name": self.course_level})
            for m in course.materials:
                if frappe.get_value("Item Price", {"item_code": m.materials, "price_list": "Standard Selling"},"price_list_rate"):
                    price = frappe.get_value("Item Price", {"item_code": m.materials, "price_list": "Standard Selling"},"price_list_rate")
                else:
                    price = 0
                commission_rate = frappe.get_value("Item", {"name": m.materials}, "commission_rate")
                program_enrollment.append("program_sales_invoice", {
                    "item": m.materials,
                    "price": price,
                    "commission_rate": commission_rate,
                    "commission_amount":  price * commission_rate
                })
            program_enrollment.save()
            program_enrollment_msg = frappe.get_doc("Program Enrollment",
                                                    {"course_application": self.name})
            link = ["""<a href=desk#Form/Program%20Enrollment/{0}>{0}</a>""".format(
                program_enrollment_msg.name)]
            frappe.msgprint(_("Program Enrollment Created - {0} As a Draft").format(comma_and(link)))

    def make_customer(self):
        title = frappe.db.get_value("Student Applicant", {"name": self.student_applicant}, "title")
        kind = frappe.db.get_value("Student Applicant", {"name": self.student_applicant}, "kind")
        if not frappe.db.exists("Customer", {"customer_name": title}):
            if self.application_status == "Approved":
                customer = frappe.new_doc("Customer")
                customer.update({
                    "customer_name": title,
                    "customer_code": title,
                    "customer_group": kind,
                    "territory": "All Territories",
                    "customer_type": "Individual",
                    "student_applicant": self.student_applicant,
                    "currency": self.currency
                })
                customer.save()

    def make_sales_order(self):
        if self.has_placement_test and not frappe.db.exists("Sales Order", {"course_application": self.name}):
            si = frappe.new_doc("Sales Order")
            si.update({
                "customer": self.student_name,
                "transaction_date": frappe.utils.nowdate(),
                "company": self.company,
                "course_application": self.name,
                "currency": self.currency
            })
            si.append("items", {
                "item_code": self.placement_test,
                "qty": 1,
                "rate": self.placement_test_amount,
                "uom": "nos",
                "conversion_factor": 1,
                "item_name": self.placement_test,
                "description": self.placement_test,
                "delivery_date": frappe.utils.nowdate(),
            })
            si.append("payment_schedule", {
                "due_date": frappe.utils.nowdate(),
                "payment_amount": self.placement_test_amount,
                "description": self.placement_test,
            })
            si.save()
            si.submit()
            sales_order = frappe.get_last_doc("Sales Order")
            link = ["""<a href=desk#Form/Sales%20Order/{0}>{0}</a>""".format(sales_order.name)]
            frappe.msgprint(_("Sales Order Created - {0} For Placement Test").format(comma_and(link)))

    def make_payment_request(self):
        if self.down_payment and not frappe.db.exists("Payment Request", {"reference_name": self.name}):
            pr = frappe.new_doc("Payment Request")
            pr.update({
                "payment_request_type": "Outward",
                "transaction_date": frappe.utils.nowdate(),
                "mode_of_payment": "Cash",
                "party_type": "Customer",
                "party": self.student,
                "reference_doctype": "Course Application",
                "reference_name": self.name,
                "Amount": self.amount
            })
            pr.save()


    def make_student(self):
        if not frappe.db.exists("Student", {"name", self.student}):
            sp = frappe.get_doc("Student Applicant", {"name": self.student_applicant})
            student = frappe.new_doc("Student")
            student.update({
                "first_name": sp.first_name,
                "middle_name": sp.middle_name,
                "last_name": sp.last_name,
                "program": sp.program,
                "academic_year": sp.academic_year,
                "academic_term": sp.academic_term,
                "date_of_birth": sp.date_of_birth,
                "student_email_id": sp.student_email_id,
                "student_mobile_number": sp.student_mobile_number,
                "nationality": sp.nationality,
                "address_line_1": sp.address_line_1,
                "address_line_2": sp.address_line_2,
                "pincode": sp.pincode,
                "city": sp.city,
                "state": sp.state,
                "guardians": sp.guardians,
                "siblings": sp.siblings,
                "title": sp.title,
                "joining_date": frappe.utils.nowdate(),
                "company": self.company
            })
            student.save()
            self.student = student.name
        else:
            self.student = ("Student", {"name": self.student_applicant}, "name")
    #def make_sales_order_percent(self):
    #   si = frappe.new_doc("Sales Order")
    #   if self.down_payment:
    #        if not frappe.db.exists("Sales Order", {"course_application": self.name}):
    #            si.update({
    #                "customer": self.student_name,
    #                "transaction_date": frappe.utils.nowdate(),
    #                "course_application": self.name,
    #                "company": self.company
    #            })
    #            si.append("items", {
    #                "item_code": self.item,
    #                "qty": 1,
    #                "rate": self.amount,
    #                "uom": "nos",
    #                "conversion_factor": 1,
    #                "item_name": self.item,
    #                "description": self.item,
    #                "delivery_date": frappe.utils.nowdate(),
    #            })

    #           si.save()
    #            si.submit()
    #            sales_order = frappe.get_last_doc("Sales Order")
    #            link = ["""<a href=desk#Form/Sales%20Order/{0}>{0}</a>""".format(sales_order.name)]
    #            frappe.msgprint(_("Sales Order Created - {0} For Down Payment").format(comma_and(link)))




