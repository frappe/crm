from frappe.core.doctype.data_import.data_import import DataImport


class DataImportListView:
	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": "ID",
				"type": "Data",
				"key": "name",
				"width": "16rem",
			},
			{
				"label": "Status",
				"type": "Select",
				"key": "status",
				"width": "10rem",
			},
			{
				"label": "Document Type",
				"type": "Link",
				"key": "reference_doctype",
				"width": "12rem",
			},
			{
				"label": "Import Type",
				"type": "Select",
				"key": "import_type",
				"width": "12rem",
			},
			{
				"label": "Import File",
				"type": "Attach",
				"key": "import_file",
				"width": "16rem",
			},
			{
				"label": "Last Modified",
				"type": "Datetime",
				"key": "modified",
				"width": "8rem",
			},
		]
		rows = [
			"name",
			"status",
			"reference_doctype",
			"import_type",
			"import_file",
			"google_sheets_url",
			"modified",
		]
		return {"columns": columns, "rows": rows}


class DataImportV15(DataImportListView, DataImport):
	pass
