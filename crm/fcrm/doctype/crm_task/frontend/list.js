// The Task list as CRM v1 draws it: a status icon, a priority badge and a dated calendar cell.
export default {
	columns: [
		{ fieldname: "title" },
		{ fieldname: "status" },
		{ fieldname: "priority" },
		{ fieldname: "due_date" },
		{ fieldname: "assigned_to" },
		{ fieldname: "modified" },
	],
	onRefresh(page) {
		page.columns.update("status", {
			icons: {
				Backlog: "lucide-circle-dashed",
				Todo: "lucide-circle",
				"In Progress": "lucide-contrast",
				Done: "lucide-circle-check",
				Canceled: "lucide-circle-x",
			},
		});
		page.columns.update("priority", { badge: { High: "red", Medium: "orange", Low: "gray" } });
		page.columns.update("due_date", { icon: "lucide-calendar", format: "D MMM, hh:mm a" });
	},
};
