> **Archived.** This file is superseded. See [SPEC.md](../SPEC.md), [PLAN.md](../PLAN.md), [ARCHIVE.md](../ARCHIVE.md), or [feats/form-scripting/](../feats/form-scripting/).

---

# Writing CRM Form Scripts

> **Who is this for?**
>
> - **[Part 1](#part-1-using-form-scripts)** — CRM customizers and admins who want to add behaviour to their CRM deployment without modifying source code. No build step required.
> - **[Part 2](#part-2-how-the-engine-works-internal)** — Core contributors who need to understand the script evaluation pipeline, `createDocProxy`, the `save.submit` patch, and `triggerOnChange` internals.

---

# Part 1: Using Form Scripts

CRM Form Scripts let you attach JavaScript behaviour to any CRM document — without modifying source code. You write a plain ES class, define lifecycle hooks and field change handlers, and CRM wires it to the live form automatically.

---

## Creating a Form Script

1. Open **CRM Settings → Form Scripts** (or navigate to the `CRM Form Script` DocType).
2. Click **New**.
3. Fill in:
    - **Name** — a descriptive label (e.g. `Lead Qualification Rules`)
    - **DocType (dt)** — which document this script applies to (e.g. `CRM Lead`)
    - **View** — `Form` (the only supported value currently)
    - **Enabled** — check this to activate
4. Write your class in the **Script** field.
5. Save.

Changes take effect on the next page load — no rebuild needed.

---

## The Class Contract

Your script must define at least one ES class. The class name must match the DocType name with **all spaces removed**:

| DocType            | Class name        |
| ------------------ | ----------------- |
| `CRM Lead`         | `CRMLead`         |
| `CRM Deal`         | `CRMDeal`         |
| `Contact`          | `Contact`         |
| `CRM Organization` | `CRMOrganization` |

```js
class CRMLead {
	// hooks go here
}
```

The class does not need to extend anything. An empty class is valid (useful as a placeholder while you build out logic).

---

## Reading and Writing Field Values

Inside any hook, `this.doc` is a live proxy to the document. Read and write fields directly — no `.value`, no reactivity boilerplate:

```js
class CRMLead {
	onLoad() {
		console.log(this.doc.lead_name); // read a Text / Data field
		console.log(this.doc.no_of_employees); // read an Int field
		console.log(this.doc.is_deal_created); // read a Check field (true/false)

		this.doc.status = "New"; // write — marks doc dirty, triggers re-render
		this.doc.lead_owner = "admin"; // write a Link field (store the name/id)
	}
}
```

`this.doc` always reflects the current saved + unsaved state. There is no separate "form value" vs "doc value" — they are the same thing.

### Field Types and Their Values

| Fieldtype                  | Value type in `this.doc`                 | Notes                                            |
| -------------------------- | ---------------------------------------- | ------------------------------------------------ |
| Data / Text                | `string`                                 |                                                  |
| Int                        | `number`                                 |                                                  |
| Float / Currency / Percent | `number`                                 |                                                  |
| Check                      | `true` / `false`                         | Not `0`/`1` on the client side                   |
| Select                     | `string` (the option value)              |                                                  |
| Link                       | `string` (the linked doc name)           | To display label, call `frappe.client.get_value` |
| Date                       | `"YYYY-MM-DD"` string                    |                                                  |
| Datetime                   | `"YYYY-MM-DD HH:MM:SS"` string           |                                                  |
| Duration                   | `number` (seconds)                       |                                                  |
| Rating                     | `number` (0–5)                           |                                                  |
| Attach / Attach Image      | `string` (file URL)                      | Set to a public file URL                         |
| Table                      | `array` of row objects                   | Mutate rows directly; see child table section    |
| HTML                       | Not in `this.doc` — use `setFieldHtml`   | See HTML field section                           |
| Button                     | Not a data field — triggers a click hook | See button section                               |
| Geolocation                | GeoJSON `object`                         | `{ type: "FeatureCollection", features: [...] }` |

---

## Lifecycle Hooks

All hooks are optional. Define only what you need. Each hook supports a camelCase and a snake_case alias — whichever you define first wins.

### `onLoad` / `on_load`

Fires **once** when the document first loads from the server. Best for one-time setup: default values, actions, calculated fields.

```js
class CRMLead {
	onLoad() {
		// Default the owner to the logged-in user if unset
		if (!this.doc.lead_owner) {
			this.doc.lead_owner = frappe.session?.user;
		}

		// Set a default rating
		if (!this.doc.lead_quality) {
			this.doc.lead_quality = 3;
		}

		// Register page header buttons
		this.actions = [
			{
				label: "Send Intro Email",
				onClick: async () => await this.doc.trigger("_sendIntroEmail")
			}
		];
	}
}
```

> `onLoad` does **not** re-fire when you navigate away and come back. Use `onRender` for that.

### `onRender` / `on_render`

Fires **every time the page renders** — on first visit and on every re-visit. Use this for route-aware side-effects such as defaulting to a tab or refreshing a summary banner.

```js
class CRMLead {
	async onRender() {
		// Always refresh the HTML summary banner
		await this.doc.trigger("_renderSummary");

		// Only jump to the Emails tab when arriving from a *different* page
		const prevPath = router.previousRoute?.path;
		const currPath = router.currentRoute.value.path;
		if (prevPath === currPath) return; // same-page re-render — skip

		router.replace({ ...router.currentRoute.value, hash: "#emails" });
	}
}
```

> **Compare `.path` not `.fullPath`** — `fullPath` includes the hash, so `#activity` ≠ `#emails`.
> **Use `router.replace` not `router.push`** — `replace` avoids adding a browser history entry.

### `onValidate` / `on_validate`

Fires **before every save**. Throw a `new Error` (or call `throwError`) to block the save — the error message is shown as a toast automatically.

```js
class CRMLead {
	onValidate() {
		// Require at least one contact method
		if (!this.doc.email && !this.doc.mobile_no) {
			throwError("Provide at least one contact method (email or mobile)");
		}

		// Validate a number field
		if (this.doc.annual_revenue < 0) {
			throwError("Annual revenue cannot be negative");
		}

		// Validate a Check field
		if (!this.doc.is_gdpr_consent && this.doc.source === "Website") {
			throwError("GDPR consent is required for website leads");
		}
	}
}
```

If the hook returns without throwing, the save continues normally.

> `onValidate` can be `async` — the engine awaits it before proceeding to save.

### `onSave` / `on_save`

Fires **after a successful save**. Use this for post-save backend calls, notifications, or follow-up actions.

```js
class CRMLead {
	async onSave() {
		// Only run for specific statuses
		if (this.doc.status === "Qualified") {
			await call("crm.api.lead.notify_manager", { lead: this.doc.name });
			toast.success("Manager notified");
		}
	}
}
```

### `onError` / `on_error`

Fires when a save fails (server returned an error). The doc is reverted automatically by the framework.

```js
class CRMLead {
	onError() {
		// Custom message on top of the framework's error toast
		toast.error("Could not save — please refresh and try again");
	}
}
```

### `onBeforeCreate` / `on_before_create`

Fires **before a new document is created** via a modal (e.g. the New Lead dialog). Use this to validate or pre-fill data before the document is written to the database.

```js
class CRMLead {
	onBeforeCreate() {
		if (!this.doc.lead_name?.trim()) {
			throwError("Lead name is required");
		}
		// Stamp the source automatically
		if (!this.doc.source) {
			this.doc.source = "Manual";
		}
	}
}
```

### `onCreateLead` / `on_create_lead` _(CRM Lead only)_

Fires when a lead is being created through the CRM Lead creation flow.

```js
class CRMLead {
	onCreateLead(leadData) {
		console.log("Creating lead with data:", leadData);
	}
}
```

### `convertToDeal` / `convert_to_deal` _(CRM Lead only)_

Fires when a lead is converted to a deal.

```js
class CRMLead {
	convertToDeal(dealData) {
		toast.info(`Converting ${this.doc.lead_name} to a deal`);
	}
}
```

---

## Field Change Hooks

Define a method named **exactly the same as the fieldname** to react when that field changes. This works for all fieldtypes except Button (which has its own section).

```js
class CRMLead {
	// Select field
	status() {
		if (this.doc.status === "Lost") {
			toast.info("Please add a note explaining why this lead was lost");
		}
	}

	// Link field
	lead_owner() {
		toast.info(`Owner changed to ${this.doc.lead_owner}`);
	}

	// Data / Text field
	website() {
		// Auto-prefix https:// if missing
		if (this.doc.website && !this.doc.website.startsWith("http")) {
			this.doc.website = "https://" + this.doc.website;
		}
	}

	// Check field
	is_deal_created() {
		if (this.doc.is_deal_created) {
			this.doc.status = "Qualified";
		}
	}
}
```

### `this.value` and `this.oldValue`

Inside any field hook, two extra properties are available:

| Property        | Description            |
| --------------- | ---------------------- |
| `this.value`    | The new value just set |
| `this.oldValue` | The previous value     |

```js
class CRMLead {
	// Int / Float / Currency field
	annual_revenue() {
		if (this.oldValue && this.value > this.oldValue * 2) {
			toast.info(
				"Revenue more than doubled — double-check before saving"
			);
		}
	}

	// Rating field (0–5)
	lead_quality() {
		if (this.value >= 4) {
			toast.success("High quality lead — consider fast-tracking");
		}
	}

	// Date field
	followup_date() {
		const today = new Date().toISOString().split("T")[0];
		if (this.value < today) {
			toast.error("Follow-up date cannot be in the past");
			this.doc.followup_date = today;
		}
	}

	// Attach / Attach Image field
	profile_photo() {
		// this.value is the new file URL, this.oldValue is the previous URL
		if (this.value) {
			toast.success("Photo updated");
		}
	}

	// Duration field (value is in seconds)
	estimated_duration() {
		const hours = Math.round(this.value / 3600);
		if (hours > 40) {
			toast.info(`That's ${hours} hours — is that right?`);
		}
	}
}
```

---

## Calling Your Own Methods

To call a helper you've defined on your class, use `this.doc.trigger('methodName')`. **Direct calls like `this._helper()` do not work** — the engine invokes hooks through the `this.doc` proxy, and methods called outside that path lose their bound context.

```js
class CRMLead {
	async status() {
		await this.doc.trigger("_renderSummary"); // calls _renderSummary on this controller
	}

	_renderSummary() {
		this.setFieldHtml("lead_summary", `<b>${this.doc.status || "—"}</b>`);
	}
}
```

> `this.doc.trigger()` returns the method's return value. For `async` helpers, `await` the call and mark the calling hook `async`.

### Calling Methods from a Child Table Class

Inside a child table class, `this.doc.trigger()` routes to the **parent** controller — not the child. To call methods defined on your child class, use a row proxy from `this.getRow()`:

```js
class CRMProducts {
	async qty() {
		const row = this.getRow("products", this.currentRowIdx);
		if (row) await row.trigger("_recalc"); // calls _recalc on CRMProducts
	}

	async rate() {
		const row = this.getRow("products", this.currentRowIdx);
		if (row) await row.trigger("_recalc");
	}

	_recalc() {
		const row = this.getRow("products", this.currentRowIdx);
		if (row) row.amount = (row.qty || 0) * (row.rate || 0);
	}
}
```

---

## Button Field Hooks

For a field of type **Button**, the hook fires on click — without marking the doc dirty.

Define a method named after the fieldname:

```js
class CRMLead {
	// Button field with fieldname 'send_brochure'
	send_brochure() {
		if (!this.doc.email) {
			throwError("No email address on this lead");
		}
		call("crm.api.lead.send_brochure", {
			lead: this.doc.name,
			email: this.doc.email
		}).then(() => toast.success("Brochure sent to " + this.doc.email));
	}

	// Button field with fieldname 'make_phone_call'
	make_phone_call() {
		if (!this.doc.mobile_no) {
			throwError("No mobile number on this lead");
		}
		crm.makePhoneCall(this.doc.mobile_no);
	}
}
```

> Writing to `this.doc` inside a button hook will dirty the form — only do it intentionally.

---

## HTML Field — Dynamic Content via `setFieldHtml`

For fields of type **HTML**, use `this.setFieldHtml(fieldname, html)` to inject reactive HTML. The field re-renders whenever you call it.

```js
class CRMLead {
	async onLoad() {
		await this.doc.trigger("_renderBanner");
	}

	// Re-render the banner whenever relevant fields change
	async status() {
		await this.doc.trigger("_renderBanner");
	}
	async lead_owner() {
		await this.doc.trigger("_renderBanner");
	}
	async annual_revenue() {
		await this.doc.trigger("_renderBanner");
	}

	_renderBanner() {
		const status = this.doc.status || "—";
		const owner = this.doc.lead_owner || "Unassigned";
		const revenue = this.doc.annual_revenue
			? `$${Number(this.doc.annual_revenue).toLocaleString()}`
			: "—";
		const colorMap = {
			Qualified: "green",
			Lost: "red",
			New: "blue",
			Contacted: "yellow"
		};
		const color = colorMap[status] ?? "gray";

		this.setFieldHtml(
			"lead_summary", // fieldname of the HTML field in your DocType
			`<div class="flex gap-4 text-sm text-${color}-700 font-medium py-2 px-1">
         <span>Status: ${status}</span>
         <span>·</span>
         <span>Owner: ${owner}</span>
         <span>·</span>
         <span>Revenue: ${revenue}</span>
       </div>`
		);
	}
}
```

**Static template alternative:** If you don't call `setFieldHtml`, the HTML field renders the static **Options** text from the DocType field definition, with `{{ fieldname }}` tokens substituted from the current doc:

```
<!-- Entered in the field's Options: -->
<b>{{ lead_name }}</b> — {{ status }}
```

---

## Child Table (Table Field) Hooks

### Row Added — `[parentfield]_add`

Called after a row is added. `this.value` is the new row object.

```js
class CRMDeal {
	// Table field with fieldname 'products'
	products_add() {
		const row = this.value;
		row.qty = row.qty || 1;
		row.discount = 0;
		// Automatically calculate amount
		if (row.rate) {
			row.amount = row.qty * row.rate;
		}
	}
}
```

### Row Removed — `[parentfield]_remove`

Called after row(s) are deleted. `this.selectedRows` is an array of removed row names; `this.rows` is the remaining rows.

```js
class CRMDeal {
	products_remove() {
		const total = this.rows.reduce((sum, r) => sum + (r.amount || 0), 0);
		toast.info(
			`${this.rows.length} product(s) remaining — new total: $${total.toLocaleString()}`
		);
	}
}
```

### Field Change in a Row

Field change hooks fire for child table rows too. Use `this.getRow(parentfield, idx)` to access the specific row being edited:

```js
class CRMDeal {
	// Fires when 'qty' changes in any products row
	qty() {
		const row = this.getRow("products", this.currentRowIdx);
		if (row) {
			row.amount = (row.qty || 0) * (row.rate || 0);
		}
	}

	rate() {
		const row = this.getRow("products", this.currentRowIdx);
		if (row) {
			row.amount = (row.qty || 0) * (row.rate || 0);
		}
	}
}
```

---

## Child DocType Scripts

If your DocType has a child table, write a **separate class for the child DocType** in the same script file. The class name is the child DocType name (spaces removed).

**Rule: define the parent class before the child class.** If the child uses `extends ParentClass`, it will throw `ReferenceError` if the parent is defined later in the file.

```js
// ── Parent DocType: CRM Deal ──────────────────────────────────────────────────
class CRMDeal {
	async onLoad() {
		await this.doc.trigger("_recalcTotal");
	}

	async onSave() {
		await this.doc.trigger("_recalcTotal");
	}

	_recalcTotal() {
		const products = this.doc.products || [];
		const total = products.reduce((sum, r) => sum + (r.amount || 0), 0);
		this.doc.total_value = total;
	}
}

// ── Child DocType: CRM Products ───────────────────────────────────────────────
class CRMProducts {
	qty() {
		const row = this.getRow("products", this.currentRowIdx);
		if (row) row.amount = (row.qty || 0) * (row.rate || 0);
	}

	rate() {
		const row = this.getRow("products", this.currentRowIdx);
		if (row) row.amount = (row.qty || 0) * (row.rate || 0);
	}
}
```

---

## Making Backend Calls

Use the injected `call` helper for any `@frappe.whitelist()` Python method:

```js
class CRMLead {
	async onSave() {
		const result = await call("crm.api.lead.get_lead_score", {
			lead: this.doc.name
		});
		this.setFieldHtml(
			"score_display",
			`<div class="text-lg font-bold">Lead Score: ${result.score}/100</div>`
		);
	}

	async industry() {
		// Look up the average deal size for this industry
		const data = await call("frappe.client.get_value", {
			doctype: "CRM Industry Benchmark",
			fieldname: "avg_deal_size",
			filters: { industry: this.doc.industry }
		});
		if (data?.avg_deal_size) {
			toast.info(
				`Industry avg deal size: $${data.avg_deal_size.toLocaleString()}`
			);
		}
	}
}
```

---

## Dynamic Actions (Page Header Buttons)

Set `this.actions` to an array of button definitions. Each button appears in the page header.

```js
class CRMLead {
	onLoad() {
		this.actions = [
			{
				label: "Send Intro Email",
				onClick: () => {
					call("crm.api.lead.send_intro_email", {
						lead: this.doc.name
					}).then(() => toast.success("Intro email sent"));
				}
			},
			{
				label: "View on Map",
				onClick: () => {
					const addr = encodeURIComponent(
						this.doc.city + ", " + this.doc.country
					);
					window.open(`https://maps.google.com/?q=${addr}`, "_blank");
				}
			}
		];
	}
}
```

---

## Dynamic Statuses (Status Dropdown)

Set `this.statuses` to an array of status objects to replace the default status dropdown options.

```js
class CRMLead {
	onLoad() {
		this.statuses = [
			{ name: "New", color: "blue" },
			{ name: "Contacted", color: "yellow" },
			{ name: "Qualified", color: "green" },
			{ name: "Nurturing", color: "purple" },
			{ name: "Lost", color: "red" }
		];
	}
}
```

---

## Showing Dialogs

Use the injected `createDialog` helper to open a frappe-ui dialog:

```js
class CRMLead {
	// Button field with fieldname 'mark_as_lost'
	mark_as_lost() {
		createDialog({
			title: "Mark Lead as Lost",
			message: "Please confirm — this will notify the lead owner.",
			actions: [
				{
					label: "Confirm",
					theme: "red",
					onClick: async ({ close }) => {
						this.doc.status = "Lost";
						await call("crm.api.lead.notify_owner_lost", {
							lead: this.doc.name
						});
						close();
						toast.success("Marked as lost");
					}
				},
				{
					label: "Cancel",
					onClick: ({ close }) => close()
				}
			]
		});
	}
}
```

---

## Realtime Updates via `socket`

Use the injected `socket` (Socket.io) to listen for or emit realtime events:

```js
class CRMLead {
	onLoad() {
		// Listen for a server-side realtime event
		socket.on("lead_score_updated", (data) => {
			if (data.lead === this.doc.name) {
				this.setFieldHtml(
					"score_display",
					`<b>Score updated: ${data.score}</b>`
				);
			}
		});
	}
}
```

---

## `throwError` — Safe Abort Helper

`throwError(message)` is a shorthand that both shows a red toast **and** throws, stopping execution immediately. Use it instead of a separate `toast.error` + `throw` combination:

```js
class CRMLead {
	onValidate() {
		if (!this.doc.lead_name?.trim()) {
			throwError("Lead name cannot be empty");
			// execution stops here — everything below is not reached
		}
		if (this.doc.annual_revenue < 0) {
			throwError("Annual revenue cannot be negative");
		}
	}

	send_brochure() {
		if (!this.doc.email) {
			throwError("No email address — cannot send brochure");
		}
		// only reached if email exists
		call("crm.api.lead.send_brochure", { lead: this.doc.name });
	}
}
```

---

## Available Helpers (Quick Reference)

All helpers are available as bare names everywhere in your script — no imports needed.

| Helper                      | Description                                                                  |
| --------------------------- | ---------------------------------------------------------------------------- |
| `router`                    | Vue Router — `router.replace()`, `router.push()`, `router.currentRoute`      |
| `router.previousRoute`      | The route navigated _from_ — compare `.path` to detect cross-page navigation |
| `toast.success(msg)`        | Green toast notification                                                     |
| `toast.error(msg)`          | Red toast notification                                                       |
| `toast.info(msg)`           | Info toast notification                                                      |
| `call(method, params)`      | Frappe backend RPC — returns a `Promise`                                     |
| `createDialog(options)`     | Open a frappe-ui dialog modal                                                |
| `socket`                    | Socket.io instance for realtime events                                       |
| `throwError(message)`       | `toast.error` + `throw` in one call — stops execution                        |
| `crm.makePhoneCall(number)` | Initiate a phone call via the CRM call integration                           |
| `crm.openSettings(page)`    | Open the CRM settings panel to a specific page                               |

---

## Full Realistic Example

This script covers all major hook types, multiple fieldtypes, an HTML field, a Button field, dynamic actions, and validation:

```js
class CRMLead {
	// ─── Lifecycle ───────────────────────────────────────────────────────────────

	async onLoad() {
		// Default owner (Link field)
		if (!this.doc.lead_owner) {
			this.doc.lead_owner = frappe.session?.user;
		}
		// Default rating (Rating field)
		if (!this.doc.lead_quality) {
			this.doc.lead_quality = 3;
		}

		await this.doc.trigger("_renderSummary");

		// Page header buttons
		this.actions = [
			{
				label: "Send Intro Email",
				onClick: async () => await this.doc.trigger("_sendIntroEmail")
			}
		];

		// Custom status dropdown
		this.statuses = [
			{ name: "New", color: "blue" },
			{ name: "Contacted", color: "yellow" },
			{ name: "Qualified", color: "green" },
			{ name: "Nurturing", color: "purple" },
			{ name: "Lost", color: "red" }
		];
	}

	async onRender() {
		await this.doc.trigger("_renderSummary");

		// Jump to Emails tab only when arriving from a different page
		const prevPath = router.previousRoute?.path;
		const currPath = router.currentRoute.value.path;
		if (prevPath !== currPath) {
			router.replace({ ...router.currentRoute.value, hash: "#emails" });
		}
	}

	onValidate() {
		if (!this.doc.lead_name?.trim()) {
			throwError("Lead name is required");
		}
		if (!this.doc.email && !this.doc.mobile_no) {
			throwError("Provide at least one contact method (email or mobile)");
		}
		if (this.doc.annual_revenue < 0) {
			throwError("Annual revenue cannot be negative");
		}
	}

	async onSave() {
		if (this.doc.status === "Qualified") {
			await call("crm.api.lead.notify_manager", { lead: this.doc.name });
			toast.success("Manager notified");
		}
	}

	onError() {
		toast.error("Save failed — please check your input and try again");
	}

	// ─── Field change hooks ──────────────────────────────────────────────────────

	// Select field
	async status() {
		await this.doc.trigger("_renderSummary");
		if (this.doc.status === "Lost") {
			toast.info("Please add a note explaining why this lead was lost");
		}
	}

	// Link field
	async lead_owner() {
		await this.doc.trigger("_renderSummary");
	}

	// Currency / Float field
	async annual_revenue() {
		await this.doc.trigger("_renderSummary");
		if (this.value > 0 && this.value < 1000) {
			toast.info("Annual revenue looks low — did you mean thousands?");
		}
	}

	// Rating field (0–5)
	lead_quality() {
		if (this.value >= 4) {
			toast.success("High quality lead!");
		}
	}

	// Check field
	is_gdpr_consent() {
		if (!this.value && this.doc.source === "Website") {
			toast.error("GDPR consent is required for website leads");
		}
	}

	// Date field
	followup_date() {
		const today = new Date().toISOString().split("T")[0];
		if (this.value < today) {
			toast.error("Follow-up date cannot be in the past");
			this.doc.followup_date = today;
		}
	}

	// ─── Button field hooks ───────────────────────────────────────────────────────

	// Button field: fieldname 'make_phone_call'
	make_phone_call() {
		if (!this.doc.mobile_no) {
			throwError("No mobile number on this lead");
		}
		crm.makePhoneCall(this.doc.mobile_no);
	}

	// Button field: fieldname 'send_brochure'
	send_brochure() {
		if (!this.doc.email) {
			throwError("No email address on this lead");
		}
		createDialog({
			title: "Send Brochure",
			message: `Send brochure to ${this.doc.email}?`,
			actions: [
				{
					label: "Send",
					theme: "blue",
					onClick: ({ close }) => {
						call("crm.api.lead.send_brochure", {
							lead: this.doc.name
						}).then(() => {
							close();
							toast.success("Brochure sent");
						});
					}
				}
			]
		});
	}

	// ─── Private helpers ──────────────────────────────────────────────────────────

	_renderSummary() {
		const status = this.doc.status || "—";
		const owner = this.doc.lead_owner || "Unassigned";
		const revenue = this.doc.annual_revenue
			? `$${Number(this.doc.annual_revenue).toLocaleString()}`
			: "—";
		const quality =
			"★".repeat(this.doc.lead_quality || 0) +
			"☆".repeat(5 - (this.doc.lead_quality || 0));

		const colorMap = {
			Qualified: "green",
			Lost: "red",
			New: "blue",
			Contacted: "yellow",
			Nurturing: "purple"
		};
		const color = colorMap[status] ?? "gray";

		this.setFieldHtml(
			"lead_summary",
			`<div class="flex flex-wrap gap-4 text-sm text-${color}-700 font-medium py-2 px-1">
         <span>Status: ${status}</span>
         <span>·</span>
         <span>Owner: ${owner}</span>
         <span>·</span>
         <span>Revenue: ${revenue}</span>
         <span>·</span>
         <span>Quality: ${quality}</span>
       </div>`
		);
	}

	async _sendIntroEmail() {
		await call("crm.api.lead.send_intro_email", { lead: this.doc.name });
		toast.success("Intro email sent");
	}
}
```

---

## Common Pitfalls

| Mistake                                               | Fix                                                                                                                 |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Class name doesn't match DocType                      | `CRM Lead` → `CRMLead` (remove spaces, keep exact casing)                                                           |
| Child class defined before parent                     | Parent class must appear first in the script                                                                        |
| `this.doc.fieldname.value`                            | `this.doc` is a plain proxy — no `.value` needed                                                                    |
| `this._myHelper()` inside a hook                      | Use `this.doc.trigger('_myHelper')` — in child classes use `row.trigger('_myHelper')` on a row from `this.getRow()` |
| Throwing a string in `onValidate` — `throw 'msg'`     | Use `throw new Error('msg')` or `throwError('msg')`                                                                 |
| `router.push` to change the active tab                | Use `router.replace` — `push` adds a browser history entry                                                          |
| Writing to `this.doc` in a button hook by accident    | Only write to `this.doc` if you want to dirty the form                                                              |
| Comparing `router.previousRoute?.fullPath` to current | Compare `.path` only — `fullPath` includes the hash                                                                 |
| `async` field hook without `await` on `call`          | `call` returns a Promise — add `await` or use `.then()`                                                             |

---

---

# Part 2: How the Engine Works (Internal)

> This section is for **core contributors** who maintain the CRM frontend. It describes the script evaluation pipeline, `createDocProxy`, the `save.submit` patch, and the `triggerOnChange` flow. Customizers do not need to read this.

---

## Script Loading Pipeline

When a CRM Lead/Deal/Contact/Organization page mounts, `setupFormScript()` in `document.js` runs:

```
setupFormScript()
  → scripts resource: fetch CRM Form Script records (dt = X, view = 'Form', enabled = 1)
  → for each script record: evaluateFormClass(script, helpers)
  → setupHelperMethods(FormClass)
  → setupFormController(FormClass, document)
  → store instance in controllersCache[doctype][docname]
```

`controllersCache` is keyed by `[doctype][docname]`, so `setupFormScript()` is a no-op on re-visits. `triggerOnRender` still fires on every visit because it is called directly by the page component's `onMounted` hook.

---

## Script Evaluation — `new Function`

Each form script string is wrapped in a `new Function` call with all helpers injected as named parameters:

```js
// evaluateFormClass() in script.js
const wrappedScript = `
  ${script}
  return ${className};
`;
const FormClass = new Function(...helperKeys, wrappedScript)(...helperValues);
```

- `getClassNames(script)` extracts class names via regex `/class\s+([A-Za-z0-9_]+)/g` (skips comments)
- Each class is extracted and instantiated separately
- Helpers (`router`, `toast`, `call`, `createDialog`, `socket`, `throwError`, `crm`) are closed over as local variables — never leaked onto `window`

---

## `createDocProxy` — The `this.doc` Mechanism

Controllers access `this.doc` which is a `Proxy` created by `createDocProxy(source, instance)`. The proxy intercepts both field access **and** the `trigger()` method:

```js
// Simplified from script.js
function createDocProxy(source, instance) {
	const getData = () => (typeof source === "function" ? source() : source);
	return new Proxy(
		{},
		{
			get(_, prop) {
				if (prop === "trigger") {
					// Calls the named method on the controller instance
					return (methodName, ...args) => {
						const method = instance[methodName];
						if (typeof method === "function")
							return method.apply(instance, args);
					};
				}
				return getData()[prop]; // field value read
			},
			set(_, prop, value) {
				getData()[prop] = value; // field value write
				return true;
			}
		}
	);
}
```

- **`this.doc.fieldname`** — reads the live field value from the reactive data
- **`this.doc.fieldname = x`** — writes directly on the reactive object, triggering Vue reactivity
- **`this.doc.trigger('method', ...args)`** — calls `instance[method].apply(instance, args)` — the correct way to call methods defined on your class
- **Child controllers**: `this.doc` is created with `instance = parentController`, so `this.doc.trigger()` calls parent methods. Use a row proxy from `this.getRow()` to call methods on the child class
- No `.value` needed because the data object is a plain reactive object (not a `ref`)

---

## `save.submit` Patch — Why Not `setValue.validate`

After `createDocumentResource`, `document.js` patches `save.submit` to run pre-save hooks:

```
document.save.submit(...args)
  → await triggerOnValidate()     // controller.onValidate?.() — throw to block
  → checkMandatory(doc)           // client-side mandatory field check
  → _originalSubmit(...args)      // only reached if both pass
```

**Why not use frappe-ui's `setValue.validate` config?**
frappe-ui's `documentResource.js` calls the validate option as:

```js
validate(data) { options.setValue?.validate?.call(vm, data) }
// no `return`, no `await` — any returned value is silently discarded
```

Any value returned from `setValue.validate` is discarded and never blocks the save. Patching `save.submit` directly is the only reliable approach for async validation.

---

## `triggerOnChange` Flow

```
triggerOnChange(fieldname, value, row?)
  → useAttachments.trackOldFile(oldValue, newValue)  // flag old file URL for cleanup
  → document.doc[fieldname] = value                  // reactive write
  → controller[fieldname]?.()                        // fire per-field hook if defined
```

The hook receives `this.value` and `this.oldValue` because `document.js` sets them on the controller instance before calling `controller[fieldname]()`:

```js
controller.value = value;
controller.oldValue = document.doc[fieldname]; // read before write
controller.currentRowIdx = row?.idx;
```

---

## `triggerOnRender` — First Visit vs Re-visit

`App.vue` uses `:key="$route.fullPath"` on `<router-view>` — every navigation creates a **new component instance**. But `setupFormScript` is guarded by `controllersCache` and only runs once per `doctype+docname`.

| Visit       | What happens                                                                                             |
| ----------- | -------------------------------------------------------------------------------------------------------- |
| First visit | `setupFormScript` runs → `triggerOnLoad()` then `triggerOnRender()`                                      |
| Re-visit    | `setupFormScript` is a no-op (cached). Page `onMounted` runs `if (document.doc) await triggerOnRender()` |

The `if (document.doc)` guard prevents a double-fire on the first visit: on first visit, `document.doc` is `null` until the resource loads. Once loaded, `triggerOnRender` was already called from within `setupFormScript`.

All 8 page components wire this: **Lead, Deal, MobileLead, MobileDeal, Contact, Organization, MobileContact, MobileOrganization**.

---

## `setFieldHtml` — How It Stays Isolated from Dirty-Tracking

```js
setFieldHtml(fieldname, html) {
  document.fieldHtmlMap[fieldname] = html
}
```

`fieldHtmlMap` is a plain `{}` added directly to the `reactive()` cache entry. Vue's reactivity system tracks property writes on a `reactive()` object automatically, so `Field.vue` and `SidePanelLayout.vue` re-render when it changes.

`triggerOnChange` and `setValue` never touch `fieldHtmlMap` — so writing HTML never marks the doc dirty or triggers a save.

---

## Further Reading

- [`document.js` source](../frontend/src/data/document.js) — `documentsCache`, `useDocument`, `save.submit` patch
- [`script.js` source](../frontend/src/data/script.js) — `setupScript`, `evaluateFormClass`, `createDocProxy`, `setupHelperMethods`
- [architecture.md skill reference](../.github/skills/crm-dev/references/architecture.md) — authoritative internal reference for core contributors
