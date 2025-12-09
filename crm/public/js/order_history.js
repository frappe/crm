/**
 * CRM Order History - Client Scripts for CRM Lead and Deal
 * Adds "Fetch Order History" button and status badge styling
 */

frappe.ui.form.on('CRM Lead', {
    refresh: function(frm) {
        color_order_status_cells(frm);
        
        // Add button to fetch order history
        if (!frm.is_new()) {
            frm.add_custom_button(__('Fetch Order History'), function() {
                fetch_order_history(frm, 'CRM Lead');
            }, __('Actions'));
        }
    },
    
    custom_order_history: function(frm) {
        setTimeout(() => color_order_status_cells(frm), 500);
    }
});

frappe.ui.form.on('CRM Deal', {
    refresh: function(frm) {
        color_order_status_cells(frm);
        
        // Add button to fetch order history
        if (!frm.is_new()) {
            frm.add_custom_button(__('Fetch Order History'), function() {
                fetch_order_history(frm, 'CRM Deal');
            }, __('Actions'));
        }
    },
    
    custom_order_history: function(frm) {
        setTimeout(() => color_order_status_cells(frm), 500);
    }
});

function fetch_order_history(frm, doctype) {
    // Show loading indicator
    frappe.show_alert({
        message: __('Fetching order history...'),
        indicator: 'blue'
    }, 3);
    
    let args = {};
    let method = '';
    
    if (doctype === 'CRM Lead') {
        args = {
            lead_name: frm.doc.name,
            customer_name: frm.doc.lead_name || frm.doc.organization || ''
        };
        method = 'crm.api.order_history.fetch_lead_order_history';
    } else if (doctype === 'CRM Deal') {
        // Get customer name from linked Lead
        if (frm.doc.lead) {
            frappe.db.get_doc('CRM Lead', frm.doc.lead).then(lead_doc => {
                args = {
                    deal_name: frm.doc.name,
                    customer_name: lead_doc.lead_name || lead_doc.organization || ''
                };
                call_fetch_api('crm.api.order_history.fetch_deal_order_history', args, frm);
            });
            return;
        } else {
            frappe.show_alert({
                message: __('Please link a Lead to this Deal first'),
                indicator: 'orange'
            }, 5);
            return;
        }
    }
    
    call_fetch_api(method, args, frm);
}

function call_fetch_api(method, args, frm) {
    frappe.call({
        method: method,
        args: args,
        freeze: true,
        freeze_message: __('Fetching orders from Sales Orders...'),
        callback: function(r) {
            if (r.message) {
                if (r.message.success) {
                    frappe.show_alert({
                        message: __(r.message.message),
                        indicator: 'green'
                    }, 5);
                    
                    // Reload the form to show new data
                    frm.reload_doc();
                } else {
                    frappe.show_alert({
                        message: __(r.message.message),
                        indicator: 'orange'
                    }, 5);
                }
            }
        },
        error: function(r) {
            frappe.show_alert({
                message: __('Error fetching order history. Check Error Log.'),
                indicator: 'red'
            }, 5);
        }
    });
}

function color_order_status_cells(frm) {
    if (!frm.fields_dict.custom_order_history) return;
    
    const grid = frm.fields_dict.custom_order_history.grid;
    if (!grid) return;
    
    // Add CSS styles matching Work Order dashboard
    add_status_styles();
    
    setTimeout(() => {
        grid.grid_rows.forEach((row) => {
            if (!row.doc) return;
            
            const row_elem = $(row.wrapper);
            
            // Apply status badges to each status column
            apply_status_badge(row_elem, 'ops_status', row.doc.ops_status);
            apply_status_badge(row_elem, 'mat_status', row.doc.mat_status);
            apply_status_badge(row_elem, 'pro_status', row.doc.pro_status);
            apply_status_badge(row_elem, 'qa_status', row.doc.qa_status);
        });
    }, 300);
}

function apply_status_badge(row_elem, fieldname, status) {
    if (!status) return;
    
    const color = get_status_color_class(status);
    const cell = row_elem.find(`[data-fieldname="${fieldname}"]`);
    
    if (cell.length) {
        // Remove any existing badge
        cell.find('.status-badge-crm').remove();
        
        // Create badge element
        const badge = $(`
            <span class="status-badge-crm status-badge-${color}">
                ${get_status_icon(status)} ${status}
            </span>
        `);
        
        // Clear cell and add badge
        cell.empty().append(badge);
    }
}

function get_status_color_class(status) {
    const status_upper = (status || '').toUpperCase();
    
    // Green - Complete/Approved
    if (['APPROVED', 'IN_STOCK', 'DONE', 'PASS', 'READY'].includes(status_upper)) {
        return 'green';
    }
    
    // Blue - Active/In Progress
    if (['WIP', 'IN PROGRESS', 'CONFIRMATION PENDING'].includes(status_upper)) {
        return 'blue';
    }
    
    // Yellow - Warning/Review/Pending
    if (['NEW', 'AWAITING', 'REVIEW_REQUIRED', 'IN_STOCK_TENTATIVE', 
         'OPS REVIEW', 'EXPECTED', 'QA REWORK', 'ALTERNATE FABRIC', 
         'BLOCK REVIEW', 'NO RECIPE', 'NOT STARTED', 'NO_RECIPE'].includes(status_upper)) {
        return 'yellow';
    }
    
    // Red - Error/Blocked/Not Available
    if (['NOT_AVAILABLE', 'NOT AVAILABLE', 'BLOCKED_FACTORY', 'BLOCKED_OPS', 
         'FAIL', 'CANCEL REQUEST', 'POST APPROVAL HOLD OR CHANGE REQUEST', 
         'PRE_APPROVAL_CUSTOMER HOLD'].includes(status_upper)) {
        return 'red';
    }
    
    // Gray - Default
    return 'gray';
}

function get_status_icon(status) {
    const status_upper = (status || '').toUpperCase();
    
    const icon_map = {
        'APPROVED': '✅',
        'IN_STOCK': '✅',
        'DONE': '✅',
        'PASS': '✅',
        'READY': '✅',
        'WIP': '⚙️',
        'IN PROGRESS': '🔍',
        'NEW': '🆕',
        'AWAITING': '⏳',
        'REVIEW_REQUIRED': '⚠️',
        'OPS REVIEW': '👀',
        'NOT_AVAILABLE': '🔴',
        'NOT AVAILABLE': '🔴',
        'BLOCKED_FACTORY': '🚧',
        'BLOCKED_OPS': '⚠️',
        'FAIL': '❌',
        'EXPECTED': '📦',
        'NO RECIPE': '📝',
        'NO_RECIPE': '📝',
        'NOT STARTED': '🔵',
        'QA REWORK': '🔄'
    };
    
    return icon_map[status_upper] || '📋';
}

function add_status_styles() {
    // Check if styles already added
    if ($('#crm-status-badge-styles').length) return;
    
    const styles = `
        <style id="crm-status-badge-styles">
            .status-badge-crm {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.3px;
                white-space: nowrap;
                border: 1px solid;
            }
            
            /* Green - Complete/Approved */
            .status-badge-green {
                background: #ecfdf5;
                color: #059669;
                border-color: #a7f3d0;
            }
            
            /* Blue - Active/In Progress */
            .status-badge-blue {
                background: #eff6ff;
                color: #2563eb;
                border-color: #bfdbfe;
            }
            
            /* Yellow - Warning/Review */
            .status-badge-yellow {
                background: #fffbeb;
                color: #d97706;
                border-color: #fde68a;
            }
            
            /* Red - Error/Blocked */
            .status-badge-red {
                background: #fef2f2;
                color: #dc2626;
                border-color: #fecaca;
            }
            
            /* Gray - Default */
            .status-badge-gray {
                background: #f9fafb;
                color: #6b7280;
                border-color: #e5e7eb;
            }
            
            /* Make sure badges fit in grid cells */
            .grid-row [data-fieldname="ops_status"],
            .grid-row [data-fieldname="mat_status"],
            .grid-row [data-fieldname="pro_status"],
            .grid-row [data-fieldname="qa_status"] {
                padding: 8px !important;
            }
        </style>
    `;
    
    $('head').append(styles);
}

