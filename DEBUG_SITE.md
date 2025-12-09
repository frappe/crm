# Debugging Site Issues

## If the site shows a blank page:

### Step 1: Check if bench is running
```bash
cd ~/frappe-bench
bench start
```

### Step 2: Check browser console for errors
- Open browser DevTools (F12)
- Check Console tab for JavaScript errors
- Check Network tab for failed requests

### Step 3: Check if frontend is built
```bash
cd ~/frappe-bench/apps/crm/frontend
yarn build
```

### Step 4: Check bench logs
```bash
cd ~/frappe-bench
tail -f logs/web.log
# Or check error logs
tail -f logs/error.log
```

### Step 5: Clear cache and restart
```bash
cd ~/frappe-bench
bench clear-cache
bench restart
```

### Step 6: Check for syntax errors in Vue files
```bash
cd ~/frappe-bench/apps/crm/frontend
yarn build 2>&1 | grep -i error
```

### Step 7: Temporarily disable Order Details tab
If the issue is with the new Order Details component, you can temporarily comment it out:

1. In `apps/crm/frontend/src/pages/Lead.vue`, comment out the Order Details tab
2. In `apps/crm/frontend/src/pages/Deal.vue`, comment out the Order Details tab
3. In `apps/crm/frontend/src/components/Activities/Activities.vue`, comment out the Order Details section
4. Rebuild: `yarn build`
5. Restart: `bench restart`

### Common Issues:

1. **Import errors**: Check all imports are correct
2. **Missing components**: Ensure all referenced components exist
3. **Build errors**: Check `yarn build` output
4. **Port conflicts**: Ensure port 8001 is not in use by another process

