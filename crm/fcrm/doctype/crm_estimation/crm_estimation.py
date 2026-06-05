import frappe
from frappe import _
from frappe.model.document import Document


class CRMEstimation(Document):
    def autoname(self):
        from frappe.model.naming import make_autoname

        # Format: EST/0001/CMI/26 — counter per tahun (reset otomatis).
        yy = frappe.utils.now_datetime().strftime("%y")
        counter = make_autoname(f"EST-{yy}-.####.").split("-")[-1]
        name = f"EST/{counter}/CMI/{yy}"
        self.name = name
        self.estimation_no = name

    def validate(self):
        # Purpose wajib Customer/Agent saat disimpan manual.
        # Dikecualikan saat dibuat lewat convert dari quotation (flag from_convert),
        # di mana purpose sengaja diset "Quotation" sebagai penanda.
        if not self.flags.get("from_convert") and self.purpose not in ("Customer", "Agent"):
            frappe.throw(_("Purpose harus dipilih: Customer atau Agent."))

    def before_save(self):
        # Tandai kategori tiap baris (1 child doctype dipakai 2 tabel).
        for d in self.revenue_items:
            d.is_expense = 0
        for d in self.expense_items:
            d.is_expense = 1

        income = sum((d.amount or 0) for d in self.revenue_items)
        expense = sum((d.amount or 0) for d in self.expense_items)
        self.rev_inc_tax = income
        self.est_profit = income - expense

        if self.is_new():
            self.created_by = frappe.session.user
            self.create_date = frappe.utils.now()

        self.last_mod_by = frappe.session.user
        self.last_mod = frappe.utils.now()

    @staticmethod
    def default_list_data():
        columns = [
            {"label": "Number", "type": "Data", "key": "name", "width": "12rem"},
            {"label": "Customer", "type": "Data", "key": "customer_id", "width": "16rem"},
            {"label": "Type", "type": "Data", "key": "estimation_type", "width": "8rem"},
            {"label": "Purpose", "type": "Select", "key": "purpose", "width": "8rem"},
            {"label": "Expired Date", "type": "Date", "key": "expired_date", "width": "9rem"},
            {"label": "Est. Profit", "type": "Currency", "key": "est_profit", "width": "10rem"},
            {"label": "Created By", "type": "Link", "key": "owner", "width": "10rem"},
            {"label": "Last Modified", "type": "Datetime", "key": "modified", "width": "8rem"},
        ]
        rows = [
            "name",
            "estimation_no",
            "customer_id",
            "estimation_type",
            "purpose",
            "expired_date",
            "est_profit",
            "owner",
            "modified",
        ]
        return {"columns": columns, "rows": rows}
