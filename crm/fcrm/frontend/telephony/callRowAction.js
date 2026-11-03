// "Make a call" in the "⋯" menu of a Lead or Deal list row: the row's mobile number, else its phone.
export const callRowAction = {
	act: "shell.crm.make_a_call",
	fields: ["mobile_no", "phone"],
	value: (row) => row.mobile_no || row.phone,
	when: (row) => Boolean(row.mobile_no || row.phone),
};
