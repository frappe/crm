// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

/**
 * Simplified CRM Site Visit Client-Side Script
 * Delegates most functionality to server-side APIs for better performance and security
 */

frappe.ui.form.on('CRM Site Visit', {
    refresh: function(frm) {
        // Get server-side metadata and render form accordingly
        load_form_metadata(frm);
    },

    onload: function (frm) {
        // Setup form based on device and user context
        setup_form_context(frm);
    },
    
    reference_type: function(frm) {
        // Handle server-side field change
        handle_server_field_change(frm, 'reference_type', frm.doc.reference_type);
    },
    
    reference_name: function(frm) {
        // Handle server-side field change
        handle_server_field_change(frm, 'reference_name', frm.doc.reference_name);
    },

    customer_address: function (frm) {
        // Handle server-side field change
        handle_server_field_change(frm, 'customer_address', frm.doc.customer_address);
    },
    
    organization: function(frm) {
        // Handle server-side field change
        handle_server_field_change(frm, 'organization', frm.doc.organization);
    },

    follow_up_required: function (frm) {
        // Handle server-side field change
        handle_server_field_change(frm, 'follow_up_required', frm.doc.follow_up_required);
    },

    visit_type: function (frm) {
        // Handle server-side field change
        handle_server_field_change(frm, 'visit_type', frm.doc.visit_type);
    },

    visit_date: function (frm) {
        // Handle server-side field change
        handle_server_field_change(frm, 'visit_date', frm.doc.visit_date);
    }
});

/**
 * Load form metadata from server and setup UI accordingly
 */
function load_form_metadata(frm) {
    frappe.call({
        method: 'crm.api.site_visit_workflow.get_form_metadata',
        args: {
            docname: frm.doc.name,
            reference_type: frm.doc.reference_type,
            reference_name: frm.doc.reference_name
        },
        callback: function (r) {
            if (r.message && r.message.success) {
                render_form_ui(frm, r.message.metadata);
            }
        }
    });
}

/**
 * Setup form context based on device and user agent
 */
function setup_form_context(frm) {
    const user_agent = navigator.userAgent;

    frappe.call({
        method: 'crm.api.form_controller.get_field_properties',
        args: {
            docname: frm.doc.name,
            user_agent: user_agent,
            form_data: frm.doc
        },
        callback: function (r) {
            if (r.message && r.message.success) {
                apply_field_properties(frm, r.message.field_properties);

                // Setup mobile interface if detected
                if (r.message.is_mobile) {
                    setup_mobile_interface(frm);
                }
            }
        }
    });
}

/**
 * Render form UI based on server metadata
 */
function render_form_ui(frm, metadata) {
    // Clear existing custom buttons
    frm.clear_custom_buttons();

    // Add workflow buttons based on server response
    if (metadata.available_actions && metadata.available_actions.length > 0) {
        metadata.available_actions.forEach(action => {
            const button = frm.add_custom_button(action.label, function () {
                perform_workflow_action(frm, action);
            });

            // Apply button styling
            if (action.primary) {
                button.addClass('btn-primary');
            }
            if (action.button_class) {
                button.addClass(action.button_class);
            }

            // Add to appropriate group
            if (action.action.includes('checkin') || action.action.includes('checkout')) {
                button.parent().appendTo(frm.page.add_menu_item(__('Location'), null, true));
            } else if (action.action.includes('submit')) {
                button.parent().appendTo(frm.page.add_menu_item(__('Workflow'), null, true));
            }
        });
    }

    // Show workflow guidance
    if (metadata.form_guidance && metadata.form_guidance.message) {
        const guidance_type = metadata.form_guidance.type || 'info';
        frm.dashboard.set_headline(metadata.form_guidance.message);

        // Add workflow progress indicator
        if (metadata.workflow_state && metadata.workflow_state.progress_percentage !== undefined) {
            show_workflow_progress(frm, metadata.workflow_state.progress_percentage);
        }
    }

    // Apply reference auto-population if available
    if (metadata.reference_data && metadata.reference_data.auto_populate_data) {
        apply_auto_populate_data(frm, metadata.reference_data.auto_populate_data);
    }

    // Apply field properties
    if (metadata.field_properties) {
        apply_field_properties(frm, metadata.field_properties);
    }
}

/**
 * Perform workflow action via server API
 */
function perform_workflow_action(frm, action) {
    if ((action.action === 'checkin' || action.action === 'checkout') && action.requires_location) {
        // Handle location-based actions
        handle_location_action(frm, action);
    } else if (action.action === 'submit' && action.requires_confirmation) {
        // Handle submission with confirmation
        handle_submission_action(frm, action);
    } else if (action.action === 'quick_submit') {
        // Handle quick submission with dialog
        handle_quick_submission(frm, action);
    } else {
        // Standard server-side action
        call_workflow_action(frm, action.action, {});
    }
}

/**
 * Handle location-based actions (check-in/check-out)
 */
function handle_location_action(frm, action) {
    if (navigator.geolocation) {
        frappe.show_alert({
            message: __('Getting your location...'),
            indicator: 'blue'
        });

        navigator.geolocation.getCurrentPosition(
            function (position) {
                const args = {
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                };

                // Validate location accuracy
                if (position.coords.accuracy > 100) {
                    frappe.confirm(
                        __('Location accuracy is low ({0}m). Continue anyway?', [Math.round(position.coords.accuracy)]),
                        function () {
                            call_workflow_action(frm, action.action, args);
                        }
                    );
                } else {
                    call_workflow_action(frm, action.action, args);
                }
            },
            function (error) {
                handle_location_error(frm, action, error);
            },
            {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 0
            }
        );
    } else {
        frappe.msgprint(__('Geolocation is not supported by this browser.'));
        offer_manual_location(frm, action);
    }
}

/**
 * Handle location errors and offer alternatives
 */
function handle_location_error(frm, action, error) {
    let message = __('Location access failed');

    switch (error.code) {
        case error.PERMISSION_DENIED:
            message = __('Location access denied by user');
            break;
        case error.POSITION_UNAVAILABLE:
            message = __('Location information unavailable');
            break;
        case error.TIMEOUT:
            message = __('Location request timeout');
            break;
    }

    frappe.msgprint({
        title: __('Location Error'),
        message: message + '<br><br>' + __('Would you like to enter location manually?'),
        primary_action: {
            label: __('Manual Location'),
            action: function () {
                offer_manual_location(frm, action);
            }
        }
    });
}

/**
 * Offer manual location entry
 */
function offer_manual_location(frm, action) {
    const dialog = new frappe.ui.Dialog({
        title: __('Manual Location Entry'),
        fields: [
            {
                fieldtype: 'Data',
                fieldname: 'location_name',
                label: __('Location Name'),
                reqd: 1
            },
            {
                fieldtype: 'Float',
                fieldname: 'latitude',
                label: __('Latitude (Optional)'),
                precision: 6
            },
            {
                fieldtype: 'Float',
                fieldname: 'longitude',
                label: __('Longitude (Optional)'),
                precision: 6
            },
            {
                fieldtype: 'Small Text',
                fieldname: 'reason',
                label: __('Reason for Manual Entry'),
                reqd: 1,
                default: 'GPS not available'
            }
        ],
        primary_action: function() {
            const values = dialog.get_values();
            const args = {
                manual_location: values
            };

            call_workflow_action(frm, 'manual_' + action.action, args);
            dialog.hide();
        },
        primary_action_label: __('Continue')
    });

    dialog.show();
}

/**
 * Handle submission actions with validation
 */
function handle_submission_action(frm, action) {
    // Check if visit summary exists
    if (!frm.doc.visit_summary) {
        frappe.confirm(
            __('No visit summary added. Submit anyway?'),
            function () {
                call_workflow_action(frm, action.action, {});
            },
            function () {
                frappe.msgprint(__('Please add a visit summary before submitting.'));
                frm.scroll_to_field('visit_summary');
            }
        );
    } else {
        call_workflow_action(frm, action.action, {});
    }
}

/**
 * Handle quick submission with summary dialog
 */
function handle_quick_submission(frm, action) {
    const dialog = new frappe.ui.Dialog({
        title: __('Complete & Submit Visit'),
        fields: [
            {
                fieldtype: 'Text Editor',
                fieldname: 'visit_summary',
                label: __('Visit Summary'),
                default: frm.doc.visit_summary || '',
                reqd: 1
            },
            {
                fieldtype: 'Select',
                fieldname: 'lead_quality',
                label: __('Lead Quality'),
                options: 'Hot\nWarm\nCold\nNot Qualified',
                default: frm.doc.lead_quality
            },
            {
                fieldtype: 'Text',
                fieldname: 'next_steps',
                label: __('Next Steps'),
                default: frm.doc.next_steps || ''
            },
            {
                fieldtype: 'Check',
                fieldname: 'follow_up_required',
                label: __('Follow-up Required'),
                default: frm.doc.follow_up_required
            },
            {
                fieldtype: 'Date',
                fieldname: 'follow_up_date',
                label: __('Follow-up Date'),
                depends_on: 'follow_up_required',
                default: frm.doc.follow_up_date
            }
        ],
        primary_action: function () {
            const values = dialog.get_values();
            call_workflow_action(frm, 'quick_submit', values);
            dialog.hide();
        },
        primary_action_label: __('Submit Visit')
    });

    dialog.show();
}

/**
 * Call server-side workflow action
 */
function call_workflow_action(frm, action, args) {
    frappe.call({
        method: 'crm.api.site_visit_workflow.perform_workflow_action',
        args: {
            docname: frm.doc.name,
            action: action,
            ...args
        },
        callback: function(r) {
            if (r.message) {
                if (r.message.success) {
                    // Show success message
                    frappe.show_alert({
                        message: r.message.message,
                        indicator: 'green'
                    });

                    // Reload form to reflect changes
                    frm.reload_doc();

                    // Handle special cases
                    if (action === 'checkout' && r.message.prompt_submission) {
                        setTimeout(() => {
                            show_post_checkout_options(frm);
                        }, 2000);
                    }
                } else {
                    // Show error message
                    frappe.msgprint({
                        title: __('Action Failed'),
                        message: r.message.message || 'Unknown error occurred',
                        indicator: 'red'
                    });
                }

                // Show warnings if any
                if (r.message.warning) {
                    frappe.msgprint({
                        title: __('Warning'),
                        message: r.message.warning,
                        indicator: 'orange'
                    });
                }
            }
        }
    });
}

/**
 * Handle server-side field changes
 */
function handle_server_field_change(frm, fieldname, value) {
    frappe.call({
        method: 'crm.api.form_controller.handle_field_change',
        args: {
            docname: frm.doc.name,
            fieldname: fieldname,
            value: value,
            form_data: frm.doc
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                // Apply server-side field updates
                if (r.message.field_updates) {
                    Object.keys(r.message.field_updates).forEach(field => {
                        frm.set_value(field, r.message.field_updates[field]);
                    });
                }

                // Apply field property changes
                if (r.message.field_properties) {
                    apply_field_properties(frm, r.message.field_properties);
                }

                // Show messages
                if (r.message.messages && r.message.messages.length > 0) {
                    r.message.messages.forEach(msg => {
                        frappe.show_alert({
                            message: msg,
                            indicator: 'blue'
                        });
                    });
                }

                // Show validation errors
                if (r.message.validations && r.message.validations.length > 0) {
                    r.message.validations.forEach(error => {
                        frappe.msgprint({
                            title: __('Validation Error'),
                            message: error,
                            indicator: 'red'
                        });
                    });
                }
            }
        }
    });
}

/**
 * Apply field properties from server
 */
function apply_field_properties(frm, properties) {
    Object.keys(properties).forEach(fieldname => {
        const props = properties[fieldname];

        if (props.hidden !== undefined) {
            frm.set_df_property(fieldname, 'hidden', props.hidden);
        }
        if (props.required !== undefined) {
            frm.set_df_property(fieldname, 'reqd', props.required);
        }
        if (props.readonly !== undefined) {
            frm.set_df_property(fieldname, 'read_only', props.readonly);
        }
        if (props.description) {
            frm.set_df_property(fieldname, 'description', props.description);
        }
        if (props.highlight) {
            frm.get_field(fieldname).$wrapper.addClass('highlight-field');
        }
        if (props.bold) {
            frm.get_field(fieldname).$wrapper.addClass('bold-field');
        }
    });
}

/**
 * Apply auto-populate data from server
 */
function apply_auto_populate_data(frm, data) {
    Object.keys(data).forEach(fieldname => {
        if (!frm.doc[fieldname] && data[fieldname]) {
            frm.set_value(fieldname, data[fieldname]);
        }
    });
}

/**
 * Setup mobile-specific interface
 */
function setup_mobile_interface(frm) {
    // Add mobile CSS class
    frm.page.wrapper.addClass('mobile-site-visit-form');

    // Add quick action button at top for mobile
    if (frm.doc.status === 'Planned' && !frm.doc.check_in_time) {
        add_mobile_quick_button(frm, 'Check In', 'checkin', 'btn-primary');
    } else if (frm.doc.status === 'In Progress' && !frm.doc.check_out_time) {
        add_mobile_quick_button(frm, 'Check Out', 'checkout', 'btn-success');
    }
}

/**
 * Add mobile quick action button
 */
function add_mobile_quick_button(frm, label, action, btn_class) {
    const button = $(`<button class="btn ${btn_class} btn-lg btn-block mobile-quick-action" style="margin: 10px 0;">${label}</button>`);
    button.insertAfter(frm.fields_dict.visit_date.$wrapper);

    button.click(function () {
        const action_config = {
            action: action,
            label: label,
            requires_location: true,
            primary: true
        };
        perform_workflow_action(frm, action_config);
    });
}

/**
 * Show workflow progress indicator
 */
function show_workflow_progress(frm, percentage) {
    const progress_html = `
        <div class="progress" style="margin: 10px 0;">
            <div class="progress-bar" role="progressbar" style="width: ${percentage}%;" 
                 aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100">
                ${percentage}%
            </div>
        </div>
    `;

    frm.dashboard.add_section(progress_html, __('Workflow Progress'));
}

/**
 * Show post-checkout options
 */
function show_post_checkout_options(frm) {
    frappe.confirm(
        __('Visit completed successfully! Would you like to submit this visit now to finalize the record?'),
        function () {
            // Quick submit
            handle_quick_submission(frm, {action: 'quick_submit'});
        },
        function() {
            // Submit later
            frappe.show_alert({
                message: __('You can submit this visit later using the Submit button.'),
                indicator: 'blue'
            });
        },
        __('Submit Now'),
        __('Submit Later')
    );
}

// Add custom CSS for mobile interface
frappe.ready(function () {
    $('head').append(`
        <style>
            .mobile-site-visit-form .form-section {
                margin-bottom: 15px;
            }
            .mobile-site-visit-form .frappe-control {
                margin-bottom: 10px;
            }
            .mobile-quick-action {
                font-size: 16px !important;
                padding: 12px !important;
            }
            .highlight-field {
                background-color: #fff3cd !important;
                border-left: 4px solid #ffc107;
                padding-left: 10px;
            }
            .bold-field .control-label {
                font-weight: bold !important;
            }
        </style>
    `);
});
