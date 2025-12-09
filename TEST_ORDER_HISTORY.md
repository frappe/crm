# Testing Order History Feature - Local Testing Guide

## Step 1: Deploy Changes

Run these commands to apply all changes:

```bash
cd ~/frappe-bench

# Run migrations (creates doctypes and adds custom fields)
bench --site mysite.local migrate

# Clear cache
bench clear-cache

# Restart bench
bench restart
```

## Step 2: Verify Installation

After restart, verify the doctypes were created:

```bash
# Check if doctypes exist
bench --site mysite.local console

# In console, run:
# frappe.db.exists("DocType", "CRM Lead Order Item")
# frappe.db.exists("DocType", "CRM Deal Order Item")
# exit()
```

## Step 3: Test in Browser

1. **Access CRM**: Go to `http://172.24.107.255:8001/crm` or `http://localhost:8001/crm`
2. **Open a Lead**:
   - Navigate to a CRM Lead
   - Check if you see:
     - "Order Details" tab
     - "Fetch Order History" button in Actions menu
3. **Test Fetch Order History**:
   - Click "Fetch Order History" button
   - Should show success message
   - Check "Order Details" tab for order items
   - Verify status badges appear (colored badges for QA, OPS, Material, Production)

## Step 4: Test with Deal

1. **Open a CRM Deal**:
   - Navigate to a CRM Deal (must have a linked Lead)
   - Check for "Order Details" tab
   - Click "Fetch Order History"
   - Verify orders appear

## Step 5: Verify Status Badges

In the Order Details table, check:
- **QA Status** - Should have colored badge
- **OPS Status** - Should have colored badge  
- **Material Status** - Should have colored badge
- **Production Status** - Should have colored badge

Badge colors:
- Green: APPROVED, READY, DONE, PASS
- Blue: WIP, IN PROGRESS
- Yellow: NEW, AWAITING, NO RECIPE
- Red: NOT_AVAILABLE, BLOCKED, FAIL
- Gray: Default

## Troubleshooting

### If "Order Details" tab doesn't appear:
```bash
# Check if custom fields were created
bench --site mysite.local console
# frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": "custom_order_history"})
# exit()

# If not, run migrate again
bench --site mysite.local migrate
```

### If button doesn't appear:
- Check browser console for JavaScript errors
- Verify `apps/crm/crm/public/js/order_history.js` exists
- Check `hooks.py` has `doctype_js` configured

### If API call fails:
- Check Error Log in Frappe
- Verify `apps/crm/crm/api/order_history.py` exists
- Check `hooks.py` has `override_whitelisted_methods` configured

### If statuses show defaults:
- Verify Work Order exists for the Sales Order
- Check Work Order is linked to Inter Company SO (not Customer SO)
- Verify Purchase Order has `inter_company_order_reference` set

## Quick Test Checklist

- [ ] Migration completed without errors
- [ ] "Order Details" tab appears in CRM Lead
- [ ] "Order Details" tab appears in CRM Deal
- [ ] "Fetch Order History" button appears
- [ ] Button click shows success message
- [ ] Order items appear in table
- [ ] Status badges are colored correctly
- [ ] Statuses match Work Order statuses

## Test Data Requirements

To properly test, you need:
1. A CRM Lead with a customer name
2. A Sales Order for that customer
3. A Purchase Order created from that Sales Order
4. An Inter Company Sales Order (created by server script from PO)
5. A Work Order created from the Inter Company SO
6. Work Order should have statuses set (QA, OPS, Material, Production)

## Manual API Test

You can test the API directly:

```bash
bench --site mysite.local console
```

Then in console:
```python
import frappe
result = frappe.call('crm.api.order_history.fetch_lead_order_history', {
    'lead_name': 'LEAD-NAME-HERE',
    'customer_name': 'CUSTOMER-NAME-HERE'
})
print(result)
```

