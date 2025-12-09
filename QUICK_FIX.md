# Quick Fix for Blank Page

## Immediate Steps:

### 1. Check Browser Console
Open DevTools (F12) and check for JavaScript errors. This will tell us what's wrong.

### 2. Temporarily Remove Order Details Tab (if needed)

If the issue is with the new code, temporarily disable it:

**In `apps/crm/frontend/src/pages/Lead.vue`:**
- Comment out lines 483-487 (Order Details tab)

**In `apps/crm/frontend/src/pages/Deal.vue`:**
- Comment out the Order Details tab entry

**In `apps/crm/frontend/src/components/Activities/Activities.vue`:**
- Comment out the Order Details import and section

### 3. Rebuild Frontend
```bash
cd ~/frappe-bench/apps/crm/frontend
yarn build
```

### 4. Restart Bench
```bash
cd ~/frappe-bench
bench restart
```

### 5. Check Logs
```bash
cd ~/frappe-bench
tail -f logs/web.log
```

## Most Likely Issues:

1. **Frontend not built** - Run `yarn build`
2. **Syntax error in Vue file** - Check browser console
3. **Import error** - Check all imports are correct
4. **Bench not running** - Run `bench start`

