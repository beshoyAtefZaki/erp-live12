// Copyright (c) 2016, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on('Program Enrollment', {
	refresh: function(frm)
		{frm.fields_dict['company'].get_query = function(doc, cdt, cdn) {
          	return {
				filters: [
					['Company', 'is_group', '=', 0]
			    ]
			}
		}}
	})

frappe.ui.form.on("Program Sales Invoice", "item", function(frm, cdt, cdn) {
  var doc = frappe.model.get_doc(cdt, cdn);

  frappe.call({
    method: "frappe.client.get_value",
    args: {
      doctype: "Item Price",
      fieldname: ["price_list_rate"],
      filters: {
      "item_code": doc.item,
      "price_list": "Standard Selling"
      }
    },
    callback: function (data) {
      if (data.exc || !data.message) return;
      frappe.model.set_value(cdt, cdn, "price", data.message.price_list_rate);
    }
  });
});

frappe.ui.form.on("Program Enrollment", {
	setup: function(frm) {
		frm.add_fetch('fee_structure', 'total_amount', 'amount');
	},

	onload: function(frm, cdt, cdn){
		frm.set_query("academic_term", "fees", function(){
			return{
				"filters":{
					"academic_year": (frm.doc.academic_year)
				}
			};
		});

		frm.fields_dict['fees'].grid.get_field('fee_structure').get_query = function(doc, cdt, cdn) {
			var d = locals[cdt][cdn];
			return {
				filters: {'academic_term': d.academic_term}
			}
		};

		if (frm.doc.program) {
			frm.set_query("course", "courses", function(doc, cdt, cdn) {
				return{
					query: "erpnext.education.doctype.program_enrollment.program_enrollment.get_program_courses",
					filters: {
						'program': frm.doc.program
					}
				}
			});
		}

		frm.set_query("student", function() {
			return{
				query: "erpnext.education.doctype.program_enrollment.program_enrollment.get_students",
				filters: {
					'academic_year': frm.doc.academic_year,
					'academic_term': frm.doc.academic_term
				}
			}
		});
	},

	program: function(frm) {
		frm.events.get_courses(frm);
		if (frm.doc.program) {
			frappe.call({
				method: "erpnext.education.api.get_fee_schedule",
				args: {
					"program": frm.doc.program,
					"student_category": frm.doc.student_category
				},
				callback: function(r) {
					if(r.message) {
						frm.set_value("fees" ,r.message);
						frm.events.get_courses(frm);
					}
				}
			});
		}
	},

	student_category: function() {
		frappe.ui.form.trigger("Program Enrollment", "program");
	},

	get_courses: function(frm) {
		frm.set_value("courses",[]);
		frappe.call({
			method: "get_courses",
			doc:frm.doc,
			callback: function(r) {
				if(r.message) {
					frm.set_value("courses", r.message);
				}
			}
		})
	}
});