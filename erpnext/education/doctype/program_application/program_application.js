// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Program Application', {
	refresh: function(frm)
		{frm.fields_dict['company'].get_query = function(doc, cdt, cdn) {
          	return {
				filters: [
					['Company', 'is_group', '=', 0]
			    ]
			}
		}}
	})


frappe.ui.form.on("Follow Up" ,"commission_rule",function(frm,cdt, cdn){
        var doc = frappe.model.get_doc(cdt, cdn);
          frappe.call({
            method: "frappe.client.get_value",
            args: {
              doctype: "User",
             fieldname: ["sales_person"],
              filters: {
              "name":frappe.session.user
              }
            },
            callback: function (data) {
              if (data.exc || !data.message) return;
               doc.sales_person = data.message.sales_person
               doc.date = frappe.datetime.nowdate()
            }
          });
       });

frappe.ui.form.on("Follow Up" ,"before_follow_up_remove",function(frm){
              if (frappe.session.user != "Administrator") {
			frappe.throw(__("Cannot delete  Follow UP Row Please Contact Administrator"));
              }
          });


frappe.ui.form.on("STA Courses","date",function(frm,cdt,cdn){
	var d = locals[cdt][cdn];
    {frm.fields_dict["sta_courses"].grid.get_field("waiting_list").get_query = function(doc, cdt, cdn) {
			return {
				filters: [
					['Waiting List','available','>',0],
					['Waiting List','docstatus','=',1],
					['Waiting List','course_start_date','>=',d.date],
					['Waiting List', 'course', '=', d.course]

				]
			}
		}}
	})

frappe.ui.form.on('Program Application', {
	refresh: function(frm)
	    {frm.fields_dict['student_applicant'].get_query = function(doc, cdt, cdn) {
          	return {
				filters: [
					['Student Applicant', 'docstatus', '=', 1],
					['Student Applicant','application', '=', 'Program']
				]
			}
		}}
	})
frappe.ui.form.on("Program Application","down_payment",function(frm){
        if(frm.doc.down_payment==1) {
            frm.set_df_property("percent", "reqd", 1);
        };
        if(frm.doc.down_payment==1) {
            frm.set_df_property("amount", "reqd", 1);
        };
        if(frm.doc.down_payment==1) {
            frm.set_df_property("item", "reqd", 1);
        };
        if(frm.doc.down_payment==0) {
            frm.set_df_property("percent", "reqd", 0);
        };
        if(frm.doc.down_payment==0) {
            frm.set_df_property("amount", "reqd", 0);
        };
        if(frm.doc.down_payment==0) {
            frm.set_df_property("item", "reqd", 0);
        };
});
frappe.listview_settings['Program Application'] = {
	add_fields: [ "application_status", 'paid'],
	has_indicator_for_draft: 1,
	get_indicator: function(doc) {
         if (doc.application_status=="Applied") {
			return [__("Applied"), "orange", "application_status,=,Applied"];
		}
		else if (doc.application_status=="Approved") {
			return [__("Approved"), "green", "application_status,=,Approved"];
		}
		else if (doc.application_status=="Rejected") {
			return [__("Rejected"), "red", "application_status,=,Rejected"];
		}
	    else if (doc.application_status=="Admitted") {
			return [__("Admitted"), "blue", "application_status,=,Admitted"];
	    }
    }
};
frappe.ui.form.on(cur_frm.doctype, "application_status", function(frm){
frm.toggle_enable("follow_up", frm.doc.application_status != "Admitted");
  }
);

/**
frappe.ui.form.on("Program Application", "down_payment", function(frm) {
	frm.set_df_property("down_payment", "read_only", frm.doc.__islocal ? 0 : 1);
});
frappe.ui.form.on("Program Application", "amount", function(frm) {
	frm.set_df_property("amount", "read_only", frm.doc.__islocal ? 0 : 1);
});
frappe.ui.form.on("Program Application", "percent", function(frm) {
	frm.set_df_property("percent", "read_only", frm.doc.__islocal ? 0 : 1);
});
frappe.ui.form.on("Program Application", "item", function(frm) {
	frm.set_df_property("item", "read_only", frm.doc.__islocal ? 0 : 1);
});
**/
/***
frappe.ui.form.on("Program Application", {
	refresh: function(frm) {
		if(frm.doc.application_status== "Applied" && frm.doc.docstatus== 1 ) {
			frm.add_custom_button(__("Approve"), function() {
				frm.set_value("application_status", "Approved");
				frm.save_or_update();

			}, 'Actions');

			frm.add_custom_button(__("Reject"), function() {
				frm.set_value("application_status", "Rejected");
				frm.save_or_update();
			}, 'Actions')};
		if(frm.doc.application_status== "Admitted" && frm.doc.docstatus== 1 ){
					frm.add_custom_button(__("Finished"), function() {
				frm.set_value("application_status", "Approved");
				frm.save_or_update();

			}, 'Actions');
		}


		if(frm.doc.application_status== "Approved" && frm.doc.docstatus== 1 ) {
			frm.add_custom_button(__("Enroll"), function() {
				frm.events.enroll(frm)
			}).addClass("btn-primary");
			frm.add_custom_button(__("Reject"), function() {
				frm.set_value("application_status", "Rejected");
				frm.save_or_update();
			}, 'Actions');
		}
	},
	enroll: function(frm) {
            frm.set_value("application_status", "Admitted");
            frm.save_or_update();
	},
	validate: function(frm) {
                frm.set_value("application_status", "Draft");
                frm.save;
	}
});

// To Make Table read only by condition

frappe.ui.form.on(cur_frm.doctype, "application_status", function(frm){
frm.toggle_enable("sta_courses", frm.doc.application_status != "Finished");
  }
);

frappe.ui.form.on("Program Application","has_placement_test",function(frm){
        if(frm.doc.has_placement_test==1) {
            frm.set_df_property("placement_test", "reqd", 1);
        };
        if(frm.doc.has_placement_test==1) {
            frm.set_df_property("placement_test_amount", "reqd", 1);
        };
        if(frm.doc.has_placement_test==0) {
            frm.set_df_property("placement_test", "reqd", 0);
        };
        if(frm.doc.has_placement_test==0) {
            frm.set_df_property("placement_test_amount", "reqd", 0);
        };
});
***/