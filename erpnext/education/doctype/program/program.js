// Copyright (c) 2015, Frappe Technologies and contributors
// For license information, please see license.txt

cur_frm.add_fetch('fee_structure', 'total_amount', 'amount');

frappe.ui.form.on("Program", "refresh", function(frm) {
	if(!frm.doc.__islocal) {
		frm.add_custom_button(__("Student Applicant"), function() {
			frappe.route_options = {
				program: frm.doc.name
			}
			frappe.set_route("List", "Student Applicant");
		});
		
		frm.add_custom_button(__("Program Enrollment"), function() {
			frappe.route_options = {
				program: frm.doc.name
			}
			frappe.set_route("List", "Program Enrollment");
		});
		
		frm.add_custom_button(__("Student Group"), function() {
			frappe.route_options = {
				program: frm.doc.name
			}
			frappe.set_route("List", "Student Group");
		});
		
		frm.add_custom_button(__("Fee Structure"), function() {
			frappe.route_options = {
				program: frm.doc.name
			}
			frappe.set_route("List", "Fee Structure");
		});
		
		frm.add_custom_button(__("Fees"), function() {
			frappe.route_options = {
				program: frm.doc.name
			}
			frappe.set_route("List", "Fees");
		});
	}
});
frappe.ui.form.on("Program","has_placement_test",function(frm){
        if(frm.doc.has_placement_test==1) {
            frm.set_df_property("test_amount", "reqd", 1);
            frm.set_df_property("from_date", "reqd", 1);

        };

        if(frm.doc.has_placement_test==0) {
            frm.set_df_property("test_amount", "reqd", 0);
            frm.set_df_property("from_date", "reqd", 0);

        };

});

frappe.ui.form.on("Program","down_payment",function(frm){
        if(frm.doc.down_payment==1) {
            frm.set_df_property("percent", "reqd", 1);
        };
        if(frm.doc.down_payment==0) {
            frm.set_df_property("percent", "reqd", 0);
        };
});
