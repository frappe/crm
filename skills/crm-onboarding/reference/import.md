# Importing data into Frappe CRM

People bring data in two ways: they paste rows into the chat, or they attach a CSV file. Either way, the work is the same: work out what each row is, map the columns to CRM fields, show a preview, then create the records.

## 1. What is each row?

| Their data looks like | Import into | Required |
|---|---|---|
| People they haven't qualified yet (enquiries, sign-ups, event lists) | `CRM Lead` | `first_name` |
| Opportunities with a value or a stage | `CRM Deal` | `status` (a CRM Deal Status) |
| Companies | `CRM Organization` | `organization_name` |
| People at customers they already work with | `Contact` | `first_name` |

If you can't tell, ask. A list of names and emails is usually leads. A list with amounts and stages is usually deals.

## 2. Map the columns

Run `describe` on the target DocType to get its fields, including any their site added, and the choices of each dropdown. Match each column by meaning, not by spelling. These are the usual ones:

- **CRM Lead:** `first_name`, `last_name`, `email`, `mobile_no`, `phone`, `organization` (company name as text), `job_title`, `website`, `source` (CRM Lead Source), `status` (CRM Lead Status), `industry` (CRM Industry), `territory` (CRM Territory), `no_of_employees` (one of its choices from `describe`), `annual_revenue`, `lead_owner` (a User email).
- **CRM Deal:** `organization` (a CRM Organization name), `status`, `deal_value`, `currency`, `expected_closure_date`, `probability`, `deal_owner`, `source`, `territory`, plus the main contact's `first_name`, `last_name`, `email` and `mobile_no`.
- **CRM Organization:** `organization_name`, `website`, `industry`, `territory`, `no_of_employees`, `annual_revenue`.
- **Contact:** `first_name`, `last_name`, `company_name` (a CRM Organization name), `designation`, with emails in `email_ids` (`[{"email_id": ..., "is_primary": 1}]`) and numbers in `phone_nos` (`[{"phone": ..., "is_primary_mobile_no": 1}]`).

A single "Name" column: split it into `first_name` and `last_name` on the last space.

Show the mapping as a short list ("Company → organization", "Stage → status") and name the columns you'll leave out. Ask before going on.

### Values that must already exist

`status`, `source`, `industry`, `territory`, `lost_reason` and `organization` on a deal are links. Gather the distinct values in their data and compare them with what's on the site:

- If a value is close to an existing one ("proposal sent" vs "Proposal"), map it to the existing one.
- If a value is new, list the new ones and ask whether to create them or map them to existing ones.
- A blank lead status is fine: it gets the first Open stage.

For deals, create any missing CRM Organization records first, then the deals.

A plain `create("CRM Deal", ...)` saves the contact fields on the deal but doesn't create or link a Contact. Create deals through CRM's own method with `execute` instead. It finds or creates the contact and organization and links them. Do up to 50 rows per call:

```python
names = []
for row in rows:  # rows: the mapped deal dicts, written out as a list in the code
	names.append(frappe.call("crm.fcrm.doctype.crm_deal.crm_deal.create_deal", doc=row))
result = names
```

If one row fails, the whole call fails and nothing is saved. Fix that row and run it again.

Owners (`lead_owner`, `deal_owner`) must be emails of users on the site. If they aren't, leave the field empty and say so.

### Clean as you go

- Trim spaces, drop fully empty rows, and keep phone numbers as text.
- Dates go in as YYYY-MM-DD. Ask if the day/month order is unclear (03/04/2026).
- Amounts: strip currency symbols and thousands separators.
- Duplicates: read existing leads or contacts with the same emails (`read_records("CRM Lead", {"email": ["in", emails]}, fields=["name", "email"], limit=200)`). Tell them how many already exist and ask whether to skip them.

## 3. Preview

Show the first 3 rows the way they will be saved, plus a count: "38 leads, 2 skipped as duplicates, 3 new sources to create". Wait for a yes.

## 4. Create

### Pasted rows, or up to about 200 rows

Use `create` in batches of up to 50 records. A batch is all or nothing: if one row fails, nothing in that batch is saved. Then fix that row, or leave it out and say so, and retry the batch.

### An attached file, or more than about 200 rows

Use Frappe's Data Import, the same importer the CRM's own setup page uses. It runs in the background and logs each row. It works for leads (CRM Lead), contacts (Contact) and organizations (CRM Organization). Deals need their contact linked, which Data Import can't do, so for deals ask them to paste the rows instead and create them with `create_deal` as above, a batch at a time.

1. Find the uploaded file: `read_records("File", {"file_name": "<their file name>"}, fields=["name", "file_url"], order_by="creation desc", limit=1)`.
2. Create the import for the record type they chose: `create("Data Import", [{"reference_doctype": "<CRM Lead, Contact or CRM Organization>", "import_type": "Insert New Records", "mute_emails": 1, "import_file": "<file_url>"}])`.
3. Check the importer's column matching with `execute`:
   ```python
   result = frappe.call("frappe.core.doctype.data_import.data_import.get_preview_from_template", data_import="<name>", import_file="<file_url>")
   ```
   Each entry in `columns` after the first has a `header_title` and either a `df.fieldname` or `skip_import`.
4. If a column is mapped wrong or not at all, set the mapping. Keys are the column positions starting at "0", and values are field names or "Don't Import":
   `update("Data Import", ["<name>"], {"template_options": "{\"column_to_field_map\": {\"0\": \"first_name\", \"1\": \"email\"}}"})`
5. Start it: `frappe.call("frappe.core.doctype.data_import.data_import.form_start_import", data_import="<name>")`.
6. Check progress with `frappe.call("frappe.core.doctype.data_import.data_import.get_import_status", data_import_name="<name>")`. When it's done, read failed rows from `Data Import Log` (`{"data_import": name, "success": 0}`, fields `row_indexes`, `messages`) and explain them in plain words.

Link values (statuses, sources) must exist before you start a Data Import. It won't create them.

## 5. After the import

Say how many records came in and how many failed, and why. Point them to where the records are: Leads, Deals, Contacts or Organizations in the sidebar.
