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
	return String(raw ?? "");
}

// the value once typing ends: an Int input still takes "1.5", which the server refuses
export function settledValue(fieldtype, value) {
	if (fieldtype === "Check") return isChecked(value) ? "1" : "0";
	const text = String(value ?? "");
	if (fieldtype === "Int" && text.trim() && Number.isFinite(Number(text)))
		return String(Math.trunc(Number(text)));
	return text;
}

export const isChecked = (value) => String(value ?? "") === "1";
