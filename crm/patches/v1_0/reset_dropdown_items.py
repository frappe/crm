import frappe
from crm.install import add_standard_dropdown_items

def execute():
    """Reset dropdown items to standard values after update"""
    add_standard_dropdown_items() 