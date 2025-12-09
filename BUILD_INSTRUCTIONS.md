# Building CRM Frontend with Increased Memory

## Quick Fix for "JavaScript heap out of memory" Error

The build script has been updated to use 4GB of memory. Simply run:

```bash
cd ~/frappe-bench/apps/crm/frontend
yarn build
```

## Alternative: Manual Build with Memory Flag

If the package.json update doesn't work, run:

```bash
cd ~/frappe-bench/apps/crm/frontend
NODE_OPTIONS="--max-old-space-size=4096" yarn build
```

## If Still Failing

Try increasing memory further:

```bash
NODE_OPTIONS="--max-old-space-size=6144" yarn build
```

Or use 8GB:

```bash
NODE_OPTIONS="--max-old-space-size=8192" yarn build
```

## After Successful Build

1. Clear cache:
```bash
cd ~/frappe-bench
bench clear-cache
```

2. Restart bench:
```bash
bench restart
```

3. Refresh browser (hard refresh: Ctrl+Shift+R)

