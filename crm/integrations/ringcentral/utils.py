from frappe.utils import get_url

def get_public_url(path: str | None = None):
    """Get the public URL for the given path."""
    base_url = get_url()  # e.g., https://your-ngrok-url.ngrok.io or http://localhost:8000
    # Remove trailing slash from base_url and leading slash from path for clean concatenation
    base_url = base_url.rstrip('/')
    path = path.lstrip('/') if path else ''
    return f"{base_url}/{path}" if path else base_url

def merge_dicts(d1: dict, d2: dict):
    """Merge two dictionaries, prioritizing d2 values for overlapping keys."""
    result = d1.copy()
    result.update(d2)
    return result