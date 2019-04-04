
from __future__ import unicode_literals
import frappe
from frappe import msgprint, _
from frappe.model.document import Document
from frappe.utils import comma_and

class ProgramApplication(Document):

    def validate(self):
        program = frappe.get_doc("Program", {"name": self.program})
        price_list = frappe.get_value("Customer Group", {"name": self.kind}, "default_price_list")
        if frappe.db.exists("Item Price", {"item_code": self.program, "price_list": price_list}):
            item_price = frappe.get_doc("Item Price", {"item_code": self.program, "price_list": price_list})
            self.program_price = item_price.price_list_rate
            self.currency = item_price.currency
        else:
            frappe.throw("Program {0} doesn't has item price".format(self.program))

        if self.application_status == "Draft":
            self.placement_test = program.placement_test
            self.has_placement_test = program.has_placement_test
            self.placement_test_amount = program.test_amount
            self.percent = program.percent
            self.amount = self.percent * self.program_price / 100
            self.down_payment = program.down_payment

        if frappe.session.user != "Administrator":
            if frappe.db.exists("Employee", {"user_id": frappe.session.user}):
                employee = frappe.get_doc("Employee", {"user_id": frappe.session.user})
                self.company = employee.company
            else:
                frappe.throw(_("User {0} Must To Link With Employee").format(frappe.session.user))
        if not self.sta_courses:
            for d in program.courses:
                if d.required:
                    self.append("sta_courses", {"course": d.course})

    def on_change(self):
        if self.application_status =="Admitted" and self.docstatus == 0 and not frappe.db.exists("Program Enrollment", {"program_application":self.name}) \
                and not frappe.db.exists("Student", {"title": self.student_applicant}):
            self.make_student()
            self.make_program_enrollment()
            # TO Add Student TO Student Group
        if self.application_status == "Admitted":
            for d in self.sta_courses:
                if d.waiting_list:
                    actual = frappe.db.sql("""
                                            select count(sc.waiting_list) 
                                            from `tabSTA Courses` as sc 
                                            left join `tabProgram Application` as pa
                                            on pa.name = sc.parent    
                                            where
                                            pa.docstatus = 0 and pa.application_status = 'Admitted' and sc.waiting_list = %s 
                                            """
                                            ,d.waiting_list)[0][0]
                    frappe.db.set_value("Waiting List", d.waiting_list, "actual", actual)
                    wl = frappe.get_doc("Waiting List", {"name": d.waiting_list})
                    wl.available = wl.size - wl.actual
                    wl.save()
                    sg = frappe.get_doc("Student Group", {"name": d.student_group})
                    if not frappe.db.exists("Student Group Student", {"parent":sg.name, "student":self.student}):
                        sg.append("students", {
                            "student": self.student,
                            "student_name": self.student_name,
                            "active": 1,
                            "application": "Program"
                        })
                        sg.save()

        self.total_commission_sp = 0
        for d in self.follow_up:
            self.total_commission_sp += d.commission_rate

        for c in self.sta_courses:
            if c.student_group:
                c.start_date = frappe.db.sql("""select min(schedule_date) from `tabCourse Schedule` where docstatus = 1 and student_group = %s""",c.student_group)[0][0]
                c.end_date = frappe.db.sql(
                    """select max(schedule_date) from `tabCourse Schedule` where docstatus = 1 and student_group = %s""",
                    c.student_group)[0][0]
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
                "company": self.company,
                "program_application": self.name,
                "price": self.program_price,
                "application": "Program"
        	})
            for d in self.sta_courses:
                program_enrollment.append("courses", {"course": d.course})
            program_enrollment.save()
            program_enrollment_msg = frappe.get_doc("Program Enrollment", {"program_application": self.name})
            link = ["""<a href=desk#Form/Program%20Enrollment/{0}>{0}</a>""".format(program_enrollment_msg.name)]
            frappe.msgprint(_("Program Enrollment Created - {0} As a Draft").format(comma_and(link)))
        else:
            for d in self.follow_up:
                if not d.sales_person:
                    frappe.throw("Please Enter Sales Person In Follow UP")
                else:
                    user = frappe.get_doc("User", {"name": frappe.session.user})
                    if not user.sales_person and frappe.session.user != "Administrator" :
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
            program_enrollment.company = self.company
            program_enrollment.program_application = self.name
            program_enrollment.price = self.program_price
            program_enrollment.application = "Program"
            for d in self.sta_courses:
                program_enrollment.append("courses", {"course": d.course})

            program_enrollment.save()
            program_enrollment_msg = frappe.get_doc("Program Enrollment",
                                                    {"program_application": self.name})
            link = ["""<a href=desk#Form/Program%20Enrollment/{0}>{0}</a>""".format(
                program_enrollment_msg.name)]
            frappe.msgprint(_("Program Enrollment Created - {0} As Draft").format(comma_and(link)))

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
        if self.has_placement_test and not frappe.db.exists("Sales Order", {"program_application": self.name}):
            si = frappe.new_doc("Sales Order")
            si.update({
                "customer": self.student_name,
                "transaction_date": frappe.utils.nowdate(),
                "company": self.company,
                "program_application": self.name,
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


