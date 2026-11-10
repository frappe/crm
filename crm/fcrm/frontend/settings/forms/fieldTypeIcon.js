// The lucide class shown next to a field's label, shared by the field cards and the hidden-fields list.
export function fieldTypeIcon(field) {
	if (field?.options === "Email") return "lucide-mail";
	switch (field?.fieldtype) {
		case "Select":
			return "lucide-chevrons-up-down";
		case "Int":
		case "Float":
		case "Currency":
			return "lucide-hash";
		case "Percent":
			return "lucide-percent";
		case "Date":
			return "lucide-calendar";
		case "Datetime":
			return "lucide-calendar-clock";
		case "Time":
			return "lucide-clock";
		case "Color":
			return "lucide-palette";
		case "Check":
			return "lucide-square-check";
		case "Phone":
			return "lucide-phone";
		case "Small Text":
		case "Text":
		case "Long Text":
		case "Text Editor":
		case "HTML Editor":
		case "Markdown Editor":
			return "lucide-align-left";
		case "Link":
			return "lucide-link";
		default:
			return "lucide-type";
	}
}

export function fieldTypeLabel(field) {
	return field?.options === "Email" ? "Email" : field?.fieldtype;
}
