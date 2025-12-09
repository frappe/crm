#!/bin/bash

# Build CRM frontend with increased Node.js memory
export NODE_OPTIONS="--max-old-space-size=4096"
cd ~/frappe-bench/apps/crm/frontend
yarn build

