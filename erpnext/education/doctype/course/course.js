frappe.ui.form.on("Course", "refresh", function(frm) {
	if(!cur_frm.doc.__islocal) {
		frm.add_custom_button(__("Program"), function() {
			frappe.route_options = {
				"Program Course.course": frm.doc.name
			}
			frappe.set_route("List", "Program");
		});
		
		frm.add_custom_button(__("Student Group"), function() {
			frappe.route_options = {
				course: frm.doc.name
			}
			frappe.set_route("List", "Student Group");
		});

        if (frm.doc.group){
		frm.add_custom_button(__("Course Application"), function() {
			frappe.route_options = {
				course: frm.doc.name
			}
			frappe.set_route("List", "Course Application");
		})};
		
		frm.add_custom_button(__("Course Schedule"), function() {
			frappe.route_options = {
				course: frm.doc.name
			}
			frappe.set_route("List", "Course Schedule");
		});
		
		frm.add_custom_button(__("Assessment Plan"), function() {
			frappe.route_options = {
				course: frm.doc.name
			}
			frappe.set_route("List", "Assessment Plan");
		});
	}

	frm.set_query('default_grading_scale', function(){
		return {
			filters: {
				docstatus: 1
			}
		}
	});
});

frappe.ui.form.on("Course","hpt",function(frm){
        if(frm.doc.hpt==1) {
            frm.set_df_property("test_amount", "reqd", 1);
        };

        if(frm.doc.hpt==0) {
            frm.set_df_property("test_amount", "reqd", 0);
        };

});

frappe.ui.form.on("Course","down_payment",function(frm){
        if(frm.doc.down_payment==1) {
            frm.set_df_property("percent", "reqd", 1);
        };
        if(frm.doc.down_payment==0) {
            frm.set_df_property("percent", "reqd", 0);
        };
});


frappe.ui.form.on("Course","group",function(frm){
        if(frm.doc.group== 1) {
            frm.set_df_property("parent", "reqd", 0);

        };
});

frappe.ui.form.on('Course', {
	refresh: function(frm)
	    {frm.fields_dict['parent'].get_query = function(doc, cdt, cdn) {
          	return {
				filters: [
					['Course', 'group', '=', 1]
			    ]
			}
		}}
	})