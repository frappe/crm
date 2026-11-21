# Contact tabs from other apps

The contact page shows a **Deals** tab next to the side panel. Any installed app can add
more tabs after it, on desktop and mobile, by declaring them in its `hooks.py` under
`crm_contact_tabs`. With no app declaring tabs the page is unchanged.

```python
# my_app/hooks.py
crm_contact_tabs = [
	{
		"name": "invoices",
		"label": "Invoices",
		"icon": "lucide-receipt",
		"doctype": "Sales Invoice",
		"method": "my_app.contact_tabs.get_invoices",
		"columns": [
			{"label": "Date", "key": "posting_date", "fieldtype": "Date", "width": "9rem"},
			{"label": "Status", "key": "status", "width": "8rem"},
			{"label": "Total", "key": "grand_total", "fieldtype": "Currency", "align": "right"},
		],
	},
]
```

## Descriptor keys

| Key | Required | Meaning |
|---|---|---|
| `name` | yes | Unique id of the tab, used to fetch its rows. `details` and `deals` (any case) are reserved for the page's own tabs. |
| `label` | yes | Tab title; translated with `__()` on the page. |
| `method` | yes | Dotted path to the provider function (below). It is never sent to the browser. |
| `icon` | no | A lucide icon name with its `lucide-` prefix, such as `lucide-receipt`. |
| `doctype` | no | When set, the tab is shown only to users who can read this DocType (`frappe.has_permission(doctype, "read")`), and its rows are refused to others. |
| `columns` | no | List view columns, in order (default: none). Each has `label`, `key` (the row key it shows), and optionally `width` (CSS width such as `9rem`), `align` (`left`, `center`, `right`), `fieldtype` and `options`. |

A descriptor without `name` or `method`, with a reserved name, with a `name` already used by an
earlier descriptor, or with a `doctype` that does not exist is skipped, and a warning goes to the
`crm` log.

A column with a `fieldtype` is formatted on the server with `frappe.format_value(value, df, doc=row)`,
so dates, datetimes, numbers and currencies follow the user's settings. For `Currency`, `options`
names the row key holding the currency code and defaults to `currency`. Columns without a
`fieldtype` are shown as the provider returns them.

## Provider

The page fetches rows a page at a time (20 rows) through the whitelisted
`crm.api.contact.get_contact_tab_rows(contact, tab, start, page_length)`. It checks that the user
can read the contact and the tab's `doctype`, looks `tab` up by `name` among the declared tabs
(a client cannot call any other method), caps `page_length` at 100, and then calls:

```python
def get_invoices(contact: str, start: int, page_length: int) -> dict:
	...
	return {"rows": rows, "total_count": total}
```

- `rows`: list of dicts, one per row. Each needs a unique `name`, plus a value for every column
  `key`. An optional `url` opens when the row is clicked: a path under `/crm/` navigates inside
  the CRM app, any other path (for example `/app/sales-invoice/SINV-0001`) opens in a new tab.
  Only same-origin paths are kept: the `url` must start with a single `/` (not `//`) and contain
  no backslash, whitespace or control character. Any other `url` is dropped from the row.
- `total_count`: number of rows for the contact, used for the tab badge and the "Load More" button.
- For a contact with no rows return `{"rows": [], "total_count": 0}`; never raise.
  If the provider raises anyway, the page shows the tab as empty and an error toast.

The provider does not need to be whitelisted. It should still apply its own permission rules
(for example `frappe.get_list`, which applies user permissions) since it decides which rows to return.

The tab list itself comes from `crm.api.contact.get_contact_tabs(contact)`. Each tab loads its
first page when the page opens, so its count shows in the badge. Above a threshold of three
declared tabs, only the open tab loads; the others load (and show their count) when opened.
