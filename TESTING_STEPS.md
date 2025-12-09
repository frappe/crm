# Testing Order Details Tab - Next Steps

## ✅ Build Complete!

The frontend has been built successfully. Now follow these steps:

## Step 1: Clear Cache and Restart

```bash
cd ~/frappe-bench
bench clear-cache
bench restart
```

## Step 2: Test in Browser

1. **Open CRM**: Go to `http://172.24.107.255:8001/crm` or `http://localhost:8001/crm`
2. **Open a Lead**: Navigate to any CRM Lead
3. **Look for "Order Details" tab**: It should appear after "Attachments" tab, before "WhatsApp" tab
4. **Click the tab**: You should see:
   - "Fetch Order History" button at the top
   - Empty state message if no orders yet
5. **Click "Fetch Order History"**: 
   - Should show success message
   - Should populate the table with order items
   - Status badges should appear with colors

## Step 3: Test with Deal

1. **Open a CRM Deal** (must have a linked Lead)
2. **Check for "Order Details" tab**
3. **Click "Fetch Order History"**
4. **Verify orders appear**

## What You Should See

### Order Details Table Columns:
- Sales Order (clickable link)
- Order Date
- Item (code and name)
- Qty, Rate, Amount
- Delivery Status (colored badge)
- OPS Status (colored badge)
- Material Status (colored badge)
- Production Status (colored badge)
- QA Status (colored badge)

### Status Badge Colors:
- **Green**: APPROVED, READY, DONE, PASS
- **Blue**: WIP, IN PROGRESS
- **Orange**: NEW, AWAITING, NO RECIPE
- **Red**: NOT_AVAILABLE, BLOCKED, FAIL
- **Gray**: Default/N/A

## Troubleshooting

### If tab doesn't appear:
- Hard refresh browser (Ctrl+Shift+R or Cmd+Shift+R)
- Check browser console for errors (F12)
- Verify migrations ran: `bench --site mysite.local migrate`

### If "Fetch Order History" doesn't work:
- Check browser console for API errors
- Verify API endpoint exists: `crm.api.order_history.fetch_lead_order_history`
- Check Error Log in Frappe for backend errors

### If no orders appear:
- Verify the Lead/Deal has a customer name set
- Check if Sales Orders exist for that customer
- Verify Work Orders are linked correctly

