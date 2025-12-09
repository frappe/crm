#!/bin/bash

# Script to verify and run migrations for Order History feature

echo "=========================================="
echo "Order History Feature - Migration Check"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "bench" ] && [ ! -f "../bench" ]; then
    echo "Error: Please run this from frappe-bench directory"
    exit 1
fi

# Get to frappe-bench root
if [ -f "../bench" ]; then
    cd ..
fi

SITE_NAME="mysite.local"

echo "Step 1: Checking if doctypes exist..."
bench --site $SITE_NAME console <<EOF
import frappe
frappe.init(site="$SITE_NAME")
frappe.connect()

lead_item_exists = frappe.db.exists("DocType", "CRM Lead Order Item")
deal_item_exists = frappe.db.exists("DocType", "CRM Deal Order Item")

print(f"CRM Lead Order Item exists: {lead_item_exists}")
print(f"CRM Deal Order Item exists: {deal_item_exists}")

# Check custom fields
lead_tab_exists = frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": "custom_order_details_tab"})
lead_table_exists = frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": "custom_order_history"})
deal_tab_exists = frappe.db.exists("Custom Field", {"dt": "CRM Deal", "fieldname": "custom_order_details_tab"})
deal_table_exists = frappe.db.exists("Custom Field", {"dt": "CRM Deal", "fieldname": "custom_order_history"})

print(f"CRM Lead Order Details tab exists: {lead_tab_exists}")
print(f"CRM Lead Order History table exists: {lead_table_exists}")
print(f"CRM Deal Order Details tab exists: {deal_tab_exists}")
print(f"CRM Deal Order History table exists: {deal_table_exists}")

frappe.db.close()
EOF

echo ""
echo "Step 2: Running migrations..."
bench --site $SITE_NAME migrate

echo ""
echo "Step 3: Clearing cache..."
bench clear-cache

echo ""
echo "=========================================="
echo "Migration complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Restart bench: bench restart"
echo "2. Refresh your browser"
echo "3. Open a CRM Lead or Deal"
echo "4. Look for 'Order Details' tab (after 'Log' tab)"
echo "5. Check for 'Fetch Order History' button in Actions menu"

