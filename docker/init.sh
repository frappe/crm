#!/bin/bash

if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Bench already exists, skipping init"
    cd frappe-bench
    bench start
else
    echo "Creating new bench..."
fi

# Use Python 3.11 or 3.12 explicitly to avoid compatibility issues with pypika (Python 3.14 removed ast.Str)
# The issue is that uv venv uses 'python3' which resolves to Python 3.14.2 in the latest frappe/bench image
# We need to ensure python3 points to Python 3.11 or 3.12

echo "Checking Python version compatibility..."

# Initialize pyenv if available
if command -v pyenv &> /dev/null; then
    # Initialize pyenv in the current shell
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    eval "$(pyenv init -)"
    
    # Check for Python 3.11 or 3.12 via pyenv
    PYTHON_311=$(pyenv versions --bare 2>/dev/null | grep -E "^3\.11\." | head -1)
    PYTHON_312=$(pyenv versions --bare 2>/dev/null | grep -E "^3\.12\." | head -1)
    
    if [ -n "$PYTHON_311" ]; then
        echo "Found Python $PYTHON_311 via pyenv, setting as local version"
        pyenv local $PYTHON_311 2>/dev/null || pyenv global $PYTHON_311
        export PYENV_VERSION=$PYTHON_311
        # Refresh PATH to ensure python3 points to the right version
        eval "$(pyenv init -)"
    elif [ -n "$PYTHON_312" ]; then
        echo "Found Python $PYTHON_312 via pyenv, setting as local version"
        pyenv local $PYTHON_312 2>/dev/null || pyenv global $PYTHON_312
        export PYENV_VERSION=$PYTHON_312
        # Refresh PATH to ensure python3 points to the right version
        eval "$(pyenv init -)"
    else
        echo "Warning: Python 3.11 or 3.12 not found in pyenv"
        echo "Available pyenv versions: $(pyenv versions --bare 2>/dev/null | tr '\n' ' ' || echo 'none')"
        
        # Try to install Python 3.11 if pyenv-install is available
        if command -v pyenv-install &> /dev/null || pyenv install --help &> /dev/null; then
            echo "Attempting to install Python 3.11 via pyenv..."
            if pyenv install 3.11.10 2>/dev/null || pyenv install 3.11.9 2>/dev/null; then
                PYTHON_311=$(pyenv versions --bare 2>/dev/null | grep -E "^3\.11\." | head -1)
                if [ -n "$PYTHON_311" ]; then
                    echo "Successfully installed $PYTHON_311, setting as local version"
                    pyenv local $PYTHON_311
                    export PYENV_VERSION=$PYTHON_311
                    eval "$(pyenv init -)"
                fi
            else
                echo "Failed to install Python 3.11 via pyenv (build dependencies may be missing)"
            fi
        fi
    fi
fi

# Verify Python version before proceeding
PYTHON_VER=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
if [ -n "$PYTHON_VER" ]; then
    MAJOR=$(echo "$PYTHON_VER" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VER" | cut -d. -f2)
    
    if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 14 ]; then
        # Last resort: check if python3.11 or python3.12 exist as separate commands
        if command -v python3.11 &> /dev/null; then
            echo "Python 3.14 detected, but found python3.11. Creating symlink/workaround..."
            # Create a wrapper or update PATH to prefer python3.11
            export PATH="/usr/bin:$PATH"
            # Try to use python3.11 directly if available
            if python3.11 --version &> /dev/null; then
                echo "Using python3.11 as fallback"
                alias python3=python3.11
                # Create a temporary symlink in a directory early in PATH
                mkdir -p /tmp/python_wrapper
                ln -sf $(which python3.11) /tmp/python_wrapper/python3 2>/dev/null || true
                export PATH="/tmp/python_wrapper:$PATH"
            fi
        elif command -v python3.12 &> /dev/null; then
            echo "Python 3.14 detected, but found python3.12. Creating symlink/workaround..."
            export PATH="/usr/bin:$PATH"
            if python3.12 --version &> /dev/null; then
                echo "Using python3.12 as fallback"
                alias python3=python3.12
                mkdir -p /tmp/python_wrapper
                ln -sf $(which python3.12) /tmp/python_wrapper/python3 2>/dev/null || true
                export PATH="/tmp/python_wrapper:$PATH"
            fi
        fi
        
        # Re-check Python version after fallback attempts
        PYTHON_VER=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        MAJOR=$(echo "$PYTHON_VER" | cut -d. -f1)
        MINOR=$(echo "$PYTHON_VER" | cut -d. -f2)
        
        if [ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 14 ]; then
            echo ""
            echo "=========================================="
            echo "ERROR: Python 3.14+ detected!"
            echo "=========================================="
            echo "Current Python version: $(python3 --version)"
            echo ""
            echo "Python 3.14+ is not compatible with pypika==0.48.9 (used by Frappe v15)"
            echo "The pypika package uses deprecated AST APIs that were removed in Python 3.14"
            echo ""
            echo "Solutions:"
            echo "1. Use a Frappe Docker image with Python 3.11 or 3.12"
            echo "2. Install Python 3.11 or 3.12 via pyenv in the container"
            echo "3. Wait for Frappe to update pypika to a compatible version"
            echo ""
            exit 1
        fi
    fi
    echo "✓ Using Python version: $(python3 --version)"
fi

bench init --skip-redis-config-generation frappe-bench --version version-15

cd frappe-bench

# Use containers instead of localhost
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Remove redis, watch from Procfile
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

bench get-app crm --branch main

bench new-site crm.localhost \
    --force \
    --mariadb-root-password 123 \
    --admin-password admin \
    --no-mariadb-socket

bench --site crm.localhost install-app crm
bench --site crm.localhost set-config developer_mode 1
bench --site crm.localhost set-config mute_emails 1
bench --site crm.localhost set-config server_script_enabled 1
bench --site crm.localhost clear-cache
bench use crm.localhost

bench start
