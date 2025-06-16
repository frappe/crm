# 📍 CRM Site Visit - Complete Implementation Guide

## Overview
The CRM Site Visit module provides comprehensive field sales management with real-time geolocation tracking, mobile optimization, and advanced analytics.

## 🚀 Features Implemented

### ✅ Core Functionality
- **Site Visit DocType** with comprehensive field structure
- **Real-time Geolocation** tracking for check-in/check-out
- **Mobile-optimized interface** for field sales teams
- **Integration** with CRM Leads, Deals, and Customers
- **Automated follow-up** task creation
- **Advanced analytics** and reporting
- **Visit reminders** via email

### 📅 Calendar Integration
- **Automatic Calendar Events** creation for each site visit
- **Real-time sync** between visits and calendar events
- **Calendar view** with visual visit scheduling
- **Recurring visits** creation with customizable frequency
- **Event timing updates** on check-in/check-out
- **Google Calendar sync** (optional integration)

### 📱 Mobile Features
- **Quick Check-in/Check-out** with GPS coordinates
- **Offline location capture** with manual entry option
- **Mobile dashboard** for field sales teams
- **Real-time location accuracy** validation
- **Address reverse geocoding** using OpenStreetMap

### 📊 Analytics & Reporting
- **Site Visit Summary Report** with charts and filters
- **Performance analytics** by sales person and territory
- **Visit type analysis** and conversion tracking
- **Location-based heatmaps** and trends
- **Weekly/monthly trends** and KPI tracking

## 📁 Files Created

### DocType Files
```
crm/fcrm/doctype/crm_site_visit/
├── crm_site_visit.json          # DocType definition
├── crm_site_visit.py            # Python controller
├── crm_site_visit.js            # Client-side scripts
├── test_crm_site_visit.py       # Unit tests
└── __init__.py
```

### Reports
```
crm/fcrm/report/site_visit_summary/
├── site_visit_summary.json     # Report definition
├── site_visit_summary.py       # Report logic
├── site_visit_summary.js       # Report frontend
└── __init__.py
```

### API Files
```
crm/api/
├── site_visit.py               # Main API endpoints
├── site_visit_analytics.py     # Advanced analytics
├── site_visit_calendar.py      # Calendar integration
└── calendar_integration.py     # Event management
```

### Mobile Interface
```
crm/www/mobile_visit/
└── index.html                  # Mobile dashboard

crm/www/site_visit_calendar/
└── index.html                  # Calendar view page
```

### Integration Files
```
crm/patches/v15_0/
└── add_site_visit_fields.py    # Custom field patches
```

## 🛠️ Installation & Setup

### 1. Install the Module
The Site Visit module is now part of your CRM app. After adding these files:

```bash
# Navigate to your bench directory
cd /path/to/your/bench

# Run migrate to create the DocType
bench --site your-site migrate

# Clear cache
bench --site your-site clear-cache
```

### 2. Set Permissions
The module comes with pre-configured permissions:
- **Sales User**: Full access to create, read, update, delete
- **Sales Manager**: Full access + import/export rights
- **System Manager**: Full administrative access

### 3. Configure Scheduler (Optional)
The daily reminder system is automatically configured via hooks.py. To customize:

```python
# In hooks.py - already configured
scheduler_events = {
    "daily": [
        "crm.fcrm.doctype.crm_site_visit.crm_site_visit.send_visit_reminders"
    ],
}
```

## 🎯 How to Use

### Creating a Site Visit

#### From CRM Interface
1. Go to **CRM Workspace** → **Site Visits**
2. Click **New**
3. Fill in the details:
   - **Visit Date**: When the visit is planned
   - **Visit Type**: Purpose (Initial Meeting, Demo, etc.)
   - **Reference**: Link to CRM Lead, Deal, or Customer
   - **Sales Person**: Assigned sales representative
   - **Location**: Customer address and visit location

#### From Mobile Interface
1. Visit `/mobile_visit` on your site
2. Click the **+** button
3. Fill in quick details and save

### Mobile Check-in/Check-out Process

#### Check-in
1. Open the Site Visit record on mobile
2. Click **Check In** button
3. Allow location access when prompted
4. System captures:
   - Current timestamp
   - GPS coordinates (latitude/longitude)
   - Location accuracy
   - Reverse geocoded address
   - Updates status to "In Progress"

#### Check-out
1. Click **Check Out** button when visit is complete
2. Allow location access
3. Optionally add:
   - Visit summary
   - Lead quality assessment
   - Key discussion points
4. System calculates total duration automatically

### Calendar Integration

#### Automatic Event Creation
By default, every site visit automatically creates a calendar event:
- **Event Subject**: "📍 Site Visit: [Customer Name]"
- **Timing**: Uses planned start/end times or defaults to 9 AM - 10 AM
- **Description**: Includes visit details, contact info, and direct link
- **Color Coding**: Different colors for visit types and status
- **Participants**: Sales person and sales manager (if specified)

#### Calendar View Dashboard
Access the calendar view at `/site_visit_calendar`:
- **Monthly Calendar**: Visual grid showing all visits
- **Color-coded dots**: Quick status identification
- **List View**: Detailed daily breakdown
- **Filtering**: By sales person, status, and date range
- **Statistics**: Monthly performance metrics

#### Calendar Synchronization
```javascript
// Sync individual visit with calendar
frappe.call({
    method: 'crm.api.site_visit_calendar.sync_visit_with_calendar_event',
    args: { visit_name: 'SV-2025-00001' }
});

// Bulk sync all visits
frappe.call({
    method: 'crm.api.site_visit_calendar.create_event_for_existing_visits'
});
```

#### Creating Recurring Visits
Create series of recurring visits:
1. Open any existing site visit
2. Click **Actions** → **Create Recurring Visits**
3. Choose frequency: Weekly, Bi-weekly, Monthly, or Quarterly
4. Set end date and maximum count
5. System creates visits with calendar events automatically

### Advanced Features

#### Follow-up Management
- **Automatic Task Creation**: When follow-up is required
- **Email Reminders**: Sent to assigned sales person
- **Integration**: Links with Frappe's ToDo system

#### Analytics Dashboard
Access comprehensive analytics via:
- **Site Visit Summary Report**: Standard report with filters
- **API Endpoints**: For custom dashboards
- **Mobile Dashboard**: Real-time KPIs

## 📊 API Reference

### Core Endpoints

#### Get Upcoming Visits
```javascript
frappe.call({
    method: 'crm.api.site_visit.get_upcoming_visits',
    args: { limit: 10 },
    callback: function(r) {
        console.log(r.message);
    }
});
```

#### Quick Check-in
```javascript
frappe.call({
    method: 'crm.api.site_visit.quick_checkin',
    args: {
        visit_id: 'SV-2025-00001',
        latitude: 19.0760,
        longitude: 72.8777,
        accuracy: 5
    }
});
```

#### Quick Check-out
```javascript
frappe.call({
    method: 'crm.api.site_visit.quick_checkout',
    args: {
        visit_id: 'SV-2025-00001',
        latitude: 19.0760,
        longitude: 72.8777,
        visit_summary: 'Productive meeting',
        lead_quality: 'Hot'
    }
});
```

#### Analytics Data
```javascript
frappe.call({
    method: 'crm.api.site_visit_analytics.get_site_visit_analytics',
    args: {
        from_date: '2025-01-01',
        to_date: '2025-06-14',
        sales_person: 'user@example.com'
    }
});
```

### Dashboard Data
```javascript
frappe.call({
    method: 'crm.api.site_visit.get_visit_dashboard_data',
    callback: function(r) {
        // Returns today's visits, completion rates, pending follow-ups
    }
});
```

## 🎨 Customization Options

### Adding Custom Fields
You can extend the Site Visit DocType with custom fields:

```python
# In patches or custom script
custom_fields = {
    "CRM Site Visit": [
        {
            "fieldname": "competitor_analysis",
            "label": "Competitor Analysis",
            "fieldtype": "Text",
            "insert_after": "visit_summary"
        }
    ]
}
```

### Custom Validation Rules
Add business-specific validations in the controller:

```python
# In crm_site_visit.py
def validate(self):
    super().validate()
    # Add your custom validations
    if self.visit_type == "Contract Signing" and not self.potential_value:
        frappe.throw("Potential value is mandatory for contract signing visits")
```

### Mobile Interface Customization
Modify `/mobile_visit/index.html` to:
- Add custom fields to mobile forms
- Implement company branding
- Add custom analytics widgets
- Integrate with external mapping services

## 📈 Reports & Analytics

### Standard Reports

#### Site Visit Summary
- **Path**: Reports → Site Visit Summary
- **Features**: 
  - Filterable by date range, sales person, status
  - Visual charts for status distribution
  - Export capabilities
  - Summary cards with KPIs

#### Custom Report Creation
Create additional reports using the framework:

```python
# Custom report example
def execute(filters=None):
    columns = [
        {"label": "Sales Person", "fieldname": "sales_person", "width": 150},
        {"label": "Visits This Month", "fieldname": "visits_count", "width": 120},
        {"label": "Conversion Rate", "fieldname": "conversion_rate", "width": 120}
    ]
    
    data = get_sales_performance_data(filters)
    return columns, data
```

### Analytics Features

#### Performance Metrics
- **Completion Rate**: Percentage of visits completed vs planned
- **Average Duration**: Time spent per visit type
- **Lead Quality Distribution**: Hot/Warm/Cold lead breakdown
- **Geographic Analysis**: City/region wise performance
- **Time Trends**: Weekly/monthly visit patterns

#### Advanced Analytics
```python
# Get comprehensive analytics
analytics = frappe.call(
    'crm.api.site_visit_analytics.get_site_visit_analytics',
    args={
        'from_date': '2025-01-01',
        'to_date': '2025-06-14'
    }
)

# Returns:
# - Summary metrics
# - Sales person performance
# - Visit type analysis  
# - City-wise breakdown
# - Weekly trends
```

## 🔧 Technical Architecture

### Database Schema
The Site Visit DocType includes these key field groups:

1. **Basic Info**: Series, dates, type, status, priority
2. **Reference**: Dynamic links to Leads/Deals/Customers  
3. **Sales Team**: Sales person and manager assignment
4. **Location**: Address and GPS coordinates
5. **Check-in/out**: Timestamps and location tracking
6. **Visit Details**: Purpose, agenda, summary
7. **Outcome**: Quality assessment and next steps
8. **Business Impact**: Value and probability tracking

### Integration Points
- **CRM Lead**: Automatic field population and visit history
- **CRM Deal**: Deal progression tracking via visits
- **Contact/Customer**: Address integration
- **ToDo**: Follow-up task creation
- **Email**: Automated reminder system

### Security & Privacy
- **Permission Control**: Role-based access to visit data
- **Location Privacy**: GPS data stored securely
- **Audit Trail**: All changes tracked with timestamps
- **Data Export**: GDPR-compliant data export options

## 🔄 Workflow Integration

### Standard Workflow
1. **Plan Visit** → Status: Planned
2. **Check-in** → Status: In Progress  
3. **Complete Visit** → Status: Completed
4. **Follow-up** → Create ToDo tasks

### Custom Workflow States
Add custom states for your business process:

```python
# Custom status options
"Rescheduled", "Customer Not Available", "Partially Completed"
```

### Integration with Sales Process
- **Lead Qualification**: Update lead scores based on visit outcomes
- **Deal Progression**: Track deal movement through visit activities  
- **Customer Relationship**: Maintain visit history and preferences

## 📱 Mobile Optimization

### Responsive Design
- **Mobile-first UI**: Optimized for phone and tablet use
- **Touch-friendly**: Large buttons and easy navigation
- **Offline Capability**: Basic functionality without internet
- **GPS Integration**: Native device location services

### Performance Features
- **Quick Actions**: One-tap check-in/check-out
- **Minimal Data**: Essential fields only on mobile
- **Fast Loading**: Optimized API calls and caching
- **Battery Efficient**: Smart location tracking

## 🚀 Future Enhancements

### Potential Additions
1. **Route Optimization**: AI-powered visit planning
2. **Offline Sync**: Full offline capability with sync
3. **Voice Notes**: Audio recording for visit summaries
4. **Photo Capture**: Visual documentation of visits
5. **Integration**: CRM system integrations (Salesforce, HubSpot)
6. **AI Analytics**: Predictive visit success scoring
7. **Calendar Sync**: Google/Outlook calendar integration

### Scalability Considerations
- **Database Indexing**: Optimized queries for large datasets
- **API Rate Limiting**: Prevent abuse of mobile endpoints  
- **Caching Strategy**: Redis caching for frequent queries
- **File Storage**: Cloud storage for photos/documents

## 🐛 Troubleshooting

### Common Issues

#### Location Not Working
1. **Check Browser Permissions**: Ensure location access is allowed
2. **HTTPS Required**: Geolocation only works on secure connections
3. **Fallback Option**: Use manual location entry if GPS fails

#### Mobile Performance
1. **Clear Browser Cache**: Refresh mobile interface
2. **Check Network**: Ensure stable internet connection
3. **Update Browser**: Use latest mobile browser version

#### Data Sync Issues
1. **Check Permissions**: Verify user has write access to Site Visit
2. **Validate Data**: Ensure all required fields are filled
3. **Server Logs**: Check Frappe error logs for details

### Debugging Tools
```python
# Enable debug mode for detailed error tracking
frappe.log_error("Site Visit Debug", "Custom message")

# Check permission issues
doc.has_permission('write')

# Validate coordinates
if not (-90 <= latitude <= 90):
    frappe.throw("Invalid latitude value")
```

## 📞 Support

### Getting Help
1. **Documentation**: Refer to this guide for common questions
2. **Frappe Community**: Post issues on Frappe Forum
3. **Error Logs**: Check bench logs for technical issues
4. **Custom Development**: Extend functionality as needed

### Maintenance
- **Regular Backups**: Backup site visit data regularly
- **Performance Monitoring**: Monitor API response times
- **User Training**: Train sales team on mobile features
- **Data Cleanup**: Archive old visit records periodically

---

## 🎉 Conclusion

The CRM Site Visit module provides a complete solution for field sales management with:

- ✅ **Real-time tracking** with GPS accuracy
- ✅ **Mobile optimization** for field teams  
- ✅ **Comprehensive analytics** and reporting
- ✅ **Seamless integration** with existing CRM workflow
- ✅ **Scalable architecture** for growing teams

The implementation follows Frappe best practices and provides a solid foundation for field sales operations. The modular design allows for easy customization and extension based on specific business requirements.

**Ready to boost your field sales productivity!** 🚀
