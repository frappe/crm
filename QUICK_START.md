# Quick Start - Order Details Tab

## The tab won't appear until you run migrations!

### Run these commands in your terminal:

```bash
cd ~/frappe-bench

# 1. Run migrations (creates doctypes and adds custom fields)
bench --site mysite.local migrate

# 2. Clear cache
bench clear-cache

# 3. Restart bench
bench restart
```

### After restart:

1. **Refresh your browser** (hard refresh: Ctrl+Shift+R or Cmd+Shift+R)
2. **Open a CRM Lead** (like the one you're viewing: CRM-LEAD-2025-00708)
3. **Look for the "Order Details" tab** - it should appear **after the "Log" tab**
4. **Check the Actions menu** - you should see "Fetch Order History" button

### If tab still doesn't appear:

Check if custom fields were created:

```bash
bench --site mysite.local console
```

Then in console:
```python
import frappe
frappe.init(site="mysite.local")
frappe.connect()

# Check if custom fields exist
print("Lead tab:", frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": "custom_order_details_tab"}))
print("Lead table:", frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": "custom_order_history"}))
print("Deal tab:", frappe.db.exists("Custom Field", {"dt": "CRM Deal", "fieldname": "custom_order_details_tab"}))
print("Deal table:", frappe.db.exists("Custom Field", {"dt": "CRM Deal", "fieldname": "custom_order_history"}))

frappe.db.close()
exit()
```

All should return `True`. If any return `False`, run migrate again.

### Tab Location:

The "Order Details" tab will appear in this order:
- Activity
- Emails  
- Comments
- Data
- Calls
- Tasks
- Notes
- Attachments
- **Log** ← (existing tab)
- **Order Details** ← (NEW - appears after Log)
- Products ← (existing tab)

