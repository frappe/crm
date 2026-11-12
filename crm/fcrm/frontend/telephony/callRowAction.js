// "Make a call" in the "⋯" menu of a Lead or Deal list row: the row's mobile number, else its phone.
import { __ } from "frappe/i18n";
import { MAKE_A_CALL } from "./makeCall.js";

export const callRowAction = {
	name: "make_a_call",
	label: __("Make a call"),
	icon: "lucide-phone",
	fields: ["mobile_no", "phone"],
	when: (page, row) => Boolean(numberOf(row)),
	run: (page, row) => page.run(MAKE_A_CALL, numberOf(row)),
};

function numberOf(row) {
	return row.mobile_no || row.phone;
}
