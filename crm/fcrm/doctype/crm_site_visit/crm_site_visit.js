// Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('CRM Site Visit', {
    refresh: function(frm) {
        // Add custom buttons based on status
        add_geolocation_buttons(frm);
        
        // Update title display
        if (frm.doc.reference_title) {
            frm.set_df_property('reference_title', 'description', 
                `Visit for: ${frm.doc.reference_title}`);
        }
        
        // Show map button if coordinates exist
        if (frm.doc.check_in_latitude && frm.doc.check_in_longitude) {
            frm.add_custom_button(__('View on Map'), function() {
                show_location_on_map(frm);
            }, __('Location'));
        }
        
        // Add follow-up creation button
        if (frm.doc.follow_up_required && frm.doc.follow_up_date && !frm.is_new()) {
            frm.add_custom_button(__('Create Follow-up Task'), function() {
                create_follow_up_task(frm);
            }, __('Actions'));
        }
        
        // Add calendar-related buttons
        if (!frm.is_new()) {
            // View calendar event button
            if (frm.doc.calendar_event) {
                frm.add_custom_button(__('View Calendar Event'), function() {
                    frappe.set_route('Form', 'Event', frm.doc.calendar_event);
                }, __('Calendar'));
            }
            
            // Sync with calendar button
            frm.add_custom_button(__('Sync with Calendar'), function() {
                sync_with_calendar(frm);
            }, __('Calendar'));
            
            // Create calendar event manually
            if (!frm.doc.calendar_event) {
                frm.add_custom_button(__('Create Calendar Event'), function() {
                    create_calendar_event_manually(frm);
                }, __('Calendar'));
            }
        }

        // Set up mobile interface if on mobile
        if (frappe.utils.is_mobile()) {
            setup_mobile_interface(frm);
        }
    },
    
    reference_type: function(frm) {
        // Clear reference when type changes
        frm.set_value('reference_name', '');
        frm.set_value('reference_title', '');
    },
    
    reference_name: function(frm) {
        if (frm.doc.reference_name && frm.doc.reference_type) {
            // Auto-populate reference details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: frm.doc.reference_type,
                    name: frm.doc.reference_name
                },
                callback: function(r) {
                    if (r.message) {
                        update_reference_details(frm, r.message);
                    }
                }
            });
        }
    },
    
    organization: function(frm) {
        if (frm.doc.reference_name && frm.doc.reference_type) {
            // Auto-populate reference details
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: frm.doc.reference_type,
                    name: frm.doc.reference_name
                },
                callback: function(r) {
                    if (r.message) {
                        update_reference_details(frm, r.message);
                    }
                }
            });
        }
    },
    
    customer_address: function(frm) {
        if (frm.doc.customer_address) {
            // Auto-populate address fields
            frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Address',
                    name: frm.doc.customer_address
                },
                callback: function(r) {
                    if (r.message) {
                        const addr = r.message;
                        frm.set_value('visit_address', addr.address_line1 + 
                            (addr.address_line2 ? '\n' + addr.address_line2 : ''));
                        frm.set_value('city', addr.city);
                        frm.set_value('state', addr.state);
                        frm.set_value('country', addr.country);
                        frm.set_value('pincode', addr.pincode);
                    }
                }
            });
        }
    },
    
    follow_up_required: function(frm) {
        if (frm.doc.follow_up_required && !frm.doc.follow_up_date) {
            // Auto-set follow-up date to next week
            let nextWeek = frappe.datetime.add_days(frm.doc.visit_date, 7);
            frm.set_value('follow_up_date', nextWeek);
        }
    }
});

// Geolocation Functions
function add_geolocation_buttons(frm) {
    // Check-in button
    if (frm.doc.status === 'Planned' && !frm.doc.check_in_time) {
        frm.add_custom_button(__('Check In'), function() {
            check_in(frm);
        }, __('Location')).addClass('btn-primary');
    }
    
    // Check-out button
    if (frm.doc.check_in_time && !frm.doc.check_out_time && frm.doc.status === 'In Progress') {
        frm.add_custom_button(__('Check Out'), function() {
            check_out(frm);
        }, __('Location')).addClass('btn-success');
    }
    
    // Manual location button
    if (!frm.doc.check_in_time) {
        frm.add_custom_button(__('Set Manual Location'), function() {
            set_manual_location(frm);
        }, __('Location'));
    }
}

function check_in(frm) {
    if (!navigator.geolocation) {
        frappe.msgprint(__('Geolocation is not supported by this browser.'));
        return;
    }
    
    frappe.show_alert({
        message: __('Getting your location...'),
        indicator: 'blue'
    });
    
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            const accuracy = position.coords.accuracy;
            
            // Validate location accuracy
            if (accuracy > 100) {
                frappe.confirm(
                    __('Location accuracy is low ({0}m). Continue anyway?', [Math.round(accuracy)]),
                    function() {
                        process_checkin(frm, latitude, longitude, accuracy);
                    }
                );
            } else {
                process_checkin(frm, latitude, longitude, accuracy);
            }
        },
        function(error) {
            handle_geolocation_error(error);
        },
        {
            enableHighAccuracy: true,
            timeout: 15000,
            maximumAge: 0
        }
    );
}

function process_checkin(frm, latitude, longitude, accuracy) {
    // Get address from coordinates
    get_address_from_coords(latitude, longitude, function(address) {
        frm.set_value('check_in_time', frappe.datetime.now_datetime());
        frm.set_value('check_in_latitude', latitude);
        frm.set_value('check_in_longitude', longitude);
        frm.set_value('check_in_location', address);
        frm.set_value('location_accuracy', Math.round(accuracy) + ' meters');
        frm.set_value('status', 'In Progress');
        
        frm.save().then(() => {
            frappe.show_alert({
                message: __('Check-in successful! Location: {0}', [address]),
                indicator: 'green'
            });
            frm.refresh();
        });
    });
}

function check_out(frm) {
    if (!navigator.geolocation) {
        frappe.msgprint(__('Geolocation is not supported by this browser.'));
        return;
    }
    
    navigator.geolocation.getCurrentPosition(
        function(position) {
            const latitude = position.coords.latitude;
            const longitude = position.coords.longitude;
            
            get_address_from_coords(latitude, longitude, function(address) {
                // Calculate duration
                const check_in_time = moment(frm.doc.check_in_time);
                const check_out_time = moment();
                const duration = check_out_time.diff(check_in_time, 'seconds');
                
                frm.set_value('check_out_time', frappe.datetime.now_datetime());
                frm.set_value('check_out_latitude', latitude);
                frm.set_value('check_out_longitude', longitude);
                frm.set_value('check_out_location', address);
                frm.set_value('total_duration', duration);
                frm.set_value('status', 'Completed');
                
                frm.save().then(() => {
                    frappe.show_alert({
                        message: __('Check-out successful! Duration: {0}', 
                            [format_duration(duration)]),
                        indicator: 'green'
                    });
                    frm.refresh();
                });
            });
        },
        function(error) {
            handle_geolocation_error(error);
        }
    );
}

function set_manual_location(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Set Manual Location'),
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
                label: __('Latitude'),
                precision: 6
            },
            {
                fieldtype: 'Float',
                fieldname: 'longitude',
                label: __('Longitude'),
                precision: 6
            },
            {
                fieldtype: 'Small Text',
                fieldname: 'reason',
                label: __('Reason for Manual Entry'),
                reqd: 1
            }
        ],
        primary_action: function() {
            let values = d.get_values();
            frm.set_value('check_in_time', frappe.datetime.now_datetime());
            frm.set_value('check_in_location', values.location_name);
            frm.set_value('check_in_latitude', values.latitude || 0);
            frm.set_value('check_in_longitude', values.longitude || 0);
            frm.set_value('location_accuracy', 'Manual Entry: ' + values.reason);
            frm.set_value('status', 'In Progress');
            
            frm.save();
            d.hide();
            frappe.show_alert({
                message: __('Manual location set successfully'),
                indicator: 'green'
            });
        },
        primary_action_label: __('Set Location')
    });
    d.show();
}

// Utility Functions
function get_address_from_coords(lat, lng, callback) {
    // Using Nominatim (OpenStreetMap) reverse geocoding - free alternative
    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}&zoom=18&addressdetails=1`)
        .then(response => response.json())
        .then(data => {
            if (data && data.display_name) {
                callback(data.display_name);
            } else {
                callback(`${lat.toFixed(6)}, ${lng.toFixed(6)}`);
            }
        })
        .catch(error => {
            console.log('Geocoding error:', error);
            callback(`${lat.toFixed(6)}, ${lng.toFixed(6)}`);
        });
}

function update_reference_details(frm, doc) {
    if (frm.doc.reference_type === 'CRM Lead') {
        frm.set_value('reference_title', (doc.lead_name || doc.organization || 'Unknown'));
        if (doc.mobile_no) frm.set_value('contact_phone', doc.mobile_no);
        if (doc.phone && !frm.doc.contact_phone) frm.set_value('contact_phone', doc.phone);
        if (doc.email) frm.set_value('contact_email', doc.email);
        
        // Set address if available
        if (doc.city) frm.set_value('city', doc.city);
        if (doc.state) frm.set_value('state', doc.state);
        if (doc.country) frm.set_value('country', doc.country);
        
    } else if (frm.doc.reference_type === 'CRM Deal') {
        frm.set_value('reference_title', (doc.organization || doc.name || 'Unknown'));
        // Add deal-specific field mapping here
        
    } else if (frm.doc.reference_type === 'Customer') {
        frm.set_value('reference_title', doc.customer_name || 'Unknown');
    }
}

function show_location_on_map(frm) {
    const lat = frm.doc.check_in_latitude;
    const lng = frm.doc.check_in_longitude;
    
    if (!lat || !lng) {
        frappe.msgprint(__('No location coordinates available'));
        return;
    }
    
    // Open in different map applications based on user preference
    frappe.confirm(
        __('Open location in which map application?'),
        function() {
            // Google Maps
            window.open(`https://www.google.com/maps?q=${lat},${lng}`, '_blank');
        },
        function() {
            // OpenStreetMap
            window.open(`https://www.openstreetmap.org/?mlat=${lat}&mlon=${lng}&zoom=16`, '_blank');
        },
        __('Google Maps'),
        __('OpenStreetMap')
    );
}

function create_follow_up_task(frm) {
    frappe.call({
        method: 'frappe.client.insert',
        args: {
            doc: {
                doctype: 'ToDo',
                description: `Follow-up for Site Visit: ${frm.doc.name}\nCustomer: ${frm.doc.reference_title}`,
                date: frm.doc.follow_up_date,
                assigned_by: frappe.session.user,
                owner: frm.doc.sales_person,
                reference_type: 'CRM Site Visit',
                reference_name: frm.doc.name,
                priority: 'Medium',
                status: 'Open'
            }
        },
        callback: function(r) {
            if (r.message) {
                frappe.show_alert({
                    message: __('Follow-up task created: {0}', [r.message.name]),
                    indicator: 'green'
                });
            }
        }
    });
}

function handle_geolocation_error(error) {
    let message = __('Location access denied');
    
    switch(error.code) {
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
        title: __('Geolocation Error'),
        message: message + '<br><br>' + __('You can use Manual Location option instead.'),
        indicator: 'red'
    });
}

function format_duration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
        return `${minutes}m ${secs}s`;
    } else {
        return `${secs}s`;
    }
}

function sync_with_calendar(frm) {
    frappe.call({
        method: 'crm.api.site_visit_calendar.sync_visit_with_calendar_event',
        args: {
            visit_name: frm.doc.name
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: r.message.message,
                    indicator: 'green'
                });
                frm.reload_doc();
            } else {
                frappe.msgprint({
                    title: __('Sync Failed'),
                    message: r.message ? r.message.message : 'Unknown error occurred',
                    indicator: 'red'
                });
            }
        }
    });
}

function create_calendar_event_manually(frm) {
    frappe.confirm(
        __('This will create a calendar event for this site visit. Continue?'),
        function() {
            // Temporarily enable sync to create event
            frm.set_value('sync_with_calendar', 1);
            frm.save().then(() => {
                frappe.show_alert({
                    message: __('Calendar event will be created on save'),
                    indicator: 'blue'
                });
            });
        }
    );
}

function create_recurring_visits(frm) {
    let d = new frappe.ui.Dialog({
        title: __('Create Recurring Visits'),
        fields: [
            {
                fieldtype: 'Select',
                fieldname: 'frequency',
                label: __('Frequency'),
                options: 'Weekly\nBi-weekly\nMonthly\nQuarterly',
                reqd: 1,
                default: 'Weekly'
            },
            {
                fieldtype: 'Date',
                fieldname: 'end_date',
                label: __('End Date'),
                reqd: 1,
                default: frappe.datetime.add_months(frm.doc.visit_date, 3)
            },
            {
                fieldtype: 'Int',
                fieldname: 'max_count',
                label: __('Maximum Visits'),
                default: 12,
                description: 'Maximum number of visits to create (safety limit)'
            },
            {
                fieldtype: 'HTML',
                fieldname: 'preview',
                label: __('Preview')
            }
        ],
        primary_action: function() {
            let values = d.get_values();
            
            frappe.call({
                method: 'crm.api.calendar_integration.create_recurring_visit_series',
                args: {
                    visit_name: frm.doc.name,
                    frequency: values.frequency,
                    end_date: values.end_date,
                    count: values.max_count
                },
                callback: function(r) {
                    if (r.message && r.message.success) {
                        frappe.show_alert({
                            message: r.message.message,
                            indicator: 'green'
                        });
                        d.hide();
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            message: r.message ? r.message.message : 'Failed to create recurring visits',
                            indicator: 'red'
                        });
                    }
                }
            });
        },
        primary_action_label: __('Create Visits')
    });
    
    // Update preview when frequency or end date changes
    d.fields_dict.frequency.$input.on('change', update_preview);
    d.fields_dict.end_date.$input.on('change', update_preview);
    
    function update_preview() {
        let frequency = d.get_value('frequency');
        let end_date = d.get_value('end_date');
        
        if (frequency && end_date) {
            let preview_html = `<p>This will create visits every <strong>${frequency.toLowerCase()}</strong> until <strong>${frappe.datetime.str_to_user(end_date)}</strong></p>`;
            d.fields_dict.preview.$wrapper.html(preview_html);
        }
    }
    
    d.show();
    update_preview();
}

function view_calendar_events(frm) {
    frappe.route_options = {
        'reference_type': 'CRM Site Visit',
        'reference_name': frm.doc.name
    };
    frappe.set_route('List', 'Event');
}

function setup_mobile_interface(frm) {
    // Hide non-essential fields on mobile
    const mobile_hide_fields = [
        'planned_start_time', 'planned_end_time', 'location_accuracy',
        'check_in_latitude', 'check_in_longitude', 
        'check_out_latitude', 'check_out_longitude'
    ];
    
    mobile_hide_fields.forEach(field => {
        frm.set_df_property(field, 'hidden', 1);
    });
    
    // Make essential fields more prominent
    frm.set_df_property('visit_type', 'reqd', 1);
    frm.set_df_property('visit_purpose', 'reqd', 1);
    
    // Add quick check-in button at top
    if (frm.doc.status === 'Planned') {
        $('<button class="btn btn-primary btn-lg btn-block" style="margin: 10px 0;">🔍 Quick Check-In</button>')
            .insertAfter(frm.fields_dict.visit_date.$wrapper)
            .click(function() {
                check_in(frm);
            });
    }
}
