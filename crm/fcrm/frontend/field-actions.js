import { __ } from "frappe/i18n";

export default [
	{
		fieldtype: "Phone",
		act: "shell.crm.make_a_call",
		get quickActionLabel() {
			return __("Call");
		},
	},
];
