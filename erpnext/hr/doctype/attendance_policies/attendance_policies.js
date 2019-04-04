// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Policies', {
	refresh: function(frm) {

	}
});
frappe.ui.form.on("Attendance Policies","all_shifts",function(frm){
        if(frm.doc.all_shifts==0) {
            frm.set_df_property("shifts", "reqd", 1);
        };
});