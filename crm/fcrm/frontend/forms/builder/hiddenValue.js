// A hidden row's value control, and the value it stores. The stored value is a string in
// the format `crm.api.form._hidden_value_fits` accepts (Check "0"/"1", ISO dates, numbers).

const CONTROLS = {
	Select: "select",
	Link: "select",
	Date: "date",
	Datetime: "datetime",
	Time: "time",
	Int: "number",
	Float: "number",
	Currency: "number",
	Percent: "number",
	Check: "checkbox",
};

export const valueControl = (fieldtype) => CONTROLS[fieldtype] || "text";

// a new row's value: a Check row is valued as soon as it shows, unticked
export const initialValue = (fieldtype) => (fieldtype === "Check" ? "0" : "");

export function storedValue(fieldtype, raw) {
	if (fieldtype === "Check") return raw ? "1" : "0";
	const value = String(raw ?? "");
	// a number input still lets "1.5" into an Int, which the server refuses
	if (fieldtype === "Int" && value.trim() && Number.isFinite(Number(value)))
		return String(Math.trunc(Number(value)));
	return value;
}

export const isChecked = (value) => String(value ?? "") === "1";
