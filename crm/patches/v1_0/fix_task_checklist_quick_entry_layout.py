from crm.patches.v1_0.add_advanced_task_fields_to_layout import execute as update_task_layout


def execute():
	"""Add Task checklist/progress sections that an earlier tabbed-layout patch missed."""
	update_task_layout()
