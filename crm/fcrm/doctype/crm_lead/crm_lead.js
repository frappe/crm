// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("CRM Lead", {
	refresh(frm) {
		frm.add_web_link(`/crm/leads/${frm.doc.name}`, __("Open in Portal"));
		
		// Add Transfer to HD Ticket button
		if (!frm.is_new()) {
			frm.add_custom_button(__('Transfer to HD Ticket'), function() {
				transfer_to_helpdesk_via_api(frm);
			}, __('Email Actions'));
		}
	},
	update_total: function (frm) {
		let total = 0;
		let total_qty = 0;
		let net_total = 0;
		frm.doc.products.forEach((d) => {
			total += d.amount;
			total_qty += d.qty;
			net_total += d.net_amount;
		});

		frappe.model.set_value(frm.doctype, frm.docname, "total", total);
		frappe.model.set_value(
			frm.doctype,
			frm.docname,
			"net_total",
			net_total || total
		);
	}
});

frappe.ui.form.on("CRM Products", {
	products_add: function (frm, cdt, cdn) {
		frm.trigger("update_total");
	},
	products_remove: function (frm, cdt, cdn) {
		frm.trigger("update_total");
	},
	product_code: function (frm, cdt, cdn) {
		let d = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "product_name", d.product_code);
	},
	rate: function (frm, cdt, cdn) {
		let d = frappe.get_doc(cdt, cdn);
		if (d.rate && d.qty) {
			frappe.model.set_value(cdt, cdn, "amount", d.rate * d.qty);
		}
		frm.trigger("update_total");
	},
	qty: function (frm, cdt, cdn) {
		let d = frappe.get_doc(cdt, cdn);
		if (d.rate && d.qty) {
			frappe.model.set_value(cdt, cdn, "amount", d.rate * d.qty);
		}
		frm.trigger("update_total");
	},
	discount_percentage: function (frm, cdt, cdn) {
		let d = frappe.get_doc(cdt, cdn);
		if (d.discount_percentage && d.amount) {
			discount_amount = (d.discount_percentage / 100) * d.amount;
			frappe.model.set_value(
				cdt,
				cdn,
				"discount_amount",
				discount_amount
			);
			frappe.model.set_value(
				cdt,
				cdn,
				"net_amount",
				d.amount - discount_amount
			);
		}
		frm.trigger("update_total");
	}
});

// Transfer to HD Ticket functionality
function transfer_to_helpdesk_via_api(frm) {
	try {
		frappe.show_alert({
			message: __('Loading emails...'),
			indicator: 'blue'
		});
		
		// Get communications using the backend API
		frappe.call({
			method: 'crm.api.email_transfer.get_communications_for_transfer',
			args: {
				doctype: 'CRM Lead',
				name: frm.doc.name
			},
			callback: function(r) {
				if (r.message && r.message.length > 0) {
					show_email_selection_dialog(frm, r.message);
				} else {
					frappe.msgprint(__('No emails found for this CRM lead.'));
				}
			},
			error: function(r) {
				console.error('Error getting communications:', r);
				frappe.msgprint(__('Error loading emails.'));
			}
		});
	} catch (error) {
		console.error('Error in transfer_to_helpdesk_via_api:', error);
	}
}

function show_email_selection_dialog(frm, emails) {
	try {
		let dialog = new frappe.ui.Dialog({
			title: __('Transfer to HD Ticket'),
			fields: [
				{
					fieldname: 'lead_info',
					fieldtype: 'HTML',
					options: generate_lead_info_preview(frm)
				},
				{
					fieldname: 'email_selection',
					fieldtype: 'HTML',
					options: generate_email_html(emails)
				}
			],
			primary_action_label: __('Create HD Ticket'),
			primary_action: function() {
				try {
					let selected = [];
					dialog.$wrapper.find('input[type="checkbox"]:checked').not('#select-all').each(function() {
						selected.push($(this).val());
					});
					
					if (selected.length === 0) {
						frappe.msgprint(__('Please select at least one email to transfer.'));
						return;
					}
					
					// Use backend API to transfer
					perform_transfer_via_api(frm, selected);
					dialog.hide();
				} catch (error) {
					console.error('Error in dialog action:', error);
					frappe.msgprint(__('Error processing selection.'));
				}
			}
		});
		
		dialog.show();
		
		// Add select all functionality
		setTimeout(function() {
			try {
				dialog.$wrapper.find('.modal-body').prepend(
					'<div style="margin-bottom: 10px;"><label style="cursor: pointer;"><input type="checkbox" id="select-all" style="margin-right: 8px;" checked> <strong>Select All Emails</strong></label></div>'
				);
				
				dialog.$wrapper.find('#select-all').change(function() {
					let checked = $(this).prop('checked');
					dialog.$wrapper.find('input[type="checkbox"][value]').prop('checked', checked);
				});
			} catch (error) {
				console.error('Error adding select all:', error);
			}
		}, 100);
		
	} catch (error) {
		console.error('Error creating dialog:', error);
		frappe.msgprint(__('Error creating dialog.'));
	}
}

function generate_lead_info_preview(frm) {
	let first_name = frm.doc.first_name || '';
	let last_name = frm.doc.last_name || '';
	let full_name = (first_name + ' ' + last_name).trim() || 'Not specified';
	let email = frm.doc.email || frm.doc.email_id || frm.doc.email_account || 'Not specified';
	let phone = frm.doc.mobile_no || frm.doc.phone || 'Not specified';
	
	return `
		<div style="margin-bottom: 15px; padding: 10px; background: #f0f4ff; border-left: 4px solid #2490ef;">
			<strong>Customer Information:</strong><br>
			<strong>Name:</strong> ${full_name}<br>
			<strong>Email:</strong> ${email}<br>
			<strong>Phone:</strong> ${phone}
		</div>
	`;
}

function generate_email_html(emails) {
	try {
		let html = '<div style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;">';
		
		emails.forEach(function(email) {
			let subject = email.subject || 'No Subject';
			let sender = email.sender || 'Unknown';
			let creation = email.creation || '';
			let content_preview = '';
			
			if (email.content) {
				content_preview = email.content.replace(/<[^>]*>/g, '').substring(0, 100) + '...';
			}
			
			// Escape HTML
			subject = $('<div>').text(subject).html();
			sender = $('<div>').text(sender).html();
			
			html += `
				<div style="border: 1px solid #e0e6ed; margin: 8px 0; padding: 10px; border-radius: 5px; background: #f9f9f9;">
					<label style="cursor: pointer; display: block;">
						<input type="checkbox" value="${email.name}" style="margin-right: 10px;" checked>
						<strong>${subject}</strong><br>
						<small>From: ${sender}</small><br>
						<small>Date: ${frappe.datetime.str_to_user(creation)}</small><br>
						${content_preview ? '<div style="margin-top: 5px; color: #666; font-style: italic;">' + content_preview + '</div>' : ''}
					</label>
				</div>
			`;
		});
		html += '</div>';
		return html;
	} catch (error) {
		console.error('Error generating email HTML:', error);
		return '<div>Error loading emails</div>';
	}
}

function perform_transfer_via_api(frm, selected_email_ids) {
	try {
		console.log('=== Transfer Debug ===');
		console.log('Lead:', frm.doc.name);
		console.log('Selected emails:', selected_email_ids);
		
		frappe.show_alert({
			message: __('Transferring to HD Ticket...'),
			indicator: 'orange'
		});
		
		// Use the backend API that properly copies all fields
		frappe.call({
			method: 'crm.api.email_transfer.transfer_to_helpdesk',
			args: {
				lead_name: frm.doc.name,
				communication_ids: selected_email_ids,
				delete_source: true
			},
			callback: function(r) {
				console.log('Transfer API Response:', r);
				if (r.message && r.message.success) {
					console.log('Transfer successful! Ticket:', r.message.ticket_name);
					console.log('Transferred count:', r.message.transferred_count);
					
					frappe.show_alert({
						message: r.message.message || __('Transfer completed successfully!'),
						indicator: 'green'
					});
					
					// Navigate to the created ticket
					setTimeout(function() {
						frappe.set_route('Form', 'HD Ticket', r.message.ticket_name);
					}, 1500);
				} else {
					console.error('Transfer completed but with warnings:', r.message);
					frappe.msgprint({
						title: __('Transfer Warning'),
						message: r.message || __('Transfer completed but with warnings.'),
						indicator: 'orange'
					});
				}
			},
			error: function(r) {
				console.error('=== Transfer API Error ===');
				console.error('Full error:', r);
				console.error('Error message:', r.message);
				console.error('Exception:', r.exc);
				
				let error_msg = r.message || r.exc || __('Error transferring to HD Ticket.');
				frappe.msgprint({
					title: __('Transfer Failed'),
					message: error_msg,
					indicator: 'red'
				});
			}
		});
		
	} catch (error) {
		console.error('Error in perform_transfer_via_api:', error);
		frappe.msgprint({
			title: __('Error'),
			message: __('Error during transfer process: ') + error.message,
			indicator: 'red'
		});
	}
}