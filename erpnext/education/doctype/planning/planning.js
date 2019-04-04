// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Planning', {
	refresh: function(frm)
	    {frm.fields_dict['course'].get_query = function(doc, cdt, cdn) {
          	return {
				filters: [
					['Course', 'group', '=', 0]
			    ]
			}
		}}
	})
frappe.ui.form.on('Planning', {
	refresh: function(frm)
		{frm.fields_dict['company'].get_query = function(doc, cdt, cdn) {
          	return {
				filters: [
					['Company', 'is_group', '=', 0]
			    ]
			}
		}}
	})
frappe.ui.form.on('Planning', {
	refresh: function(frm)
	    {frm.fields_dict['academic_term'].get_query = function(doc, cdt, cdn) {
          	return {
				filters: [
					['Academic Term','academic_year','=',doc.academic_year]
				]
			}
		}}
	})