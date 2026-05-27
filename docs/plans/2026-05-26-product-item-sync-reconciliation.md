# CRM Product ↔ ERPNext Item Reconciliation & True Bidirectional Sync

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Automatically reconcile pre-existing CRM Product / ERPNext Item duplicates, make the sync truly bidirectional (CRM → ERPNext create works), break the on_update echo loop, surface orphan unlinks to the user, and add rename / delete guards.

**Architecture:** All sync writes happen from the CRM side using core Frappe APIs (`frappe.get_doc(...).insert()`, `frappe.db.set_value(...)`). **No changes to the ERPNext repo.** ERPNext Item lifecycle hooks (after_insert, on_update, after_rename, on_trash) are attached by overriding the Item DocType class via `override_doctype_class` — same pattern as Helpdesk PR frappe/helpdesk#3361. `User Permission` and `DocShare` are mirrored the same way using a `MirrorSyncMixin` lifted from the HD PR. Reconciliation runs as a background job (`frappe.enqueue`, `queue="long"`) on the first `enabled` transition and via a post-model patch for existing sites. Matching is one rule (exact `item_code == product_code`). Conflicts resolve ERPNext-wins, except `product_name` which keeps CRM's value when both sides are non-empty. **Same-site only** — `is_erpnext_in_different_site` paths early-return for product sync.

## Permissions model (intentional)

- **User-triggered writes** (CRM Product create/edit/delete via UI, dismissing sync issues) → call `doc.insert()` / `doc.save()` / `doc.delete()` *without* `ignore_permissions`. ERPNext's "Item" perms enforce on the CRM-side write that creates the Item; CRM Product perms enforce on the reverse.
- **Sync-triggered writes** (mirror creates from lifecycle hooks, bulk reconciliation job) → use `ignore_permissions=True` and `flags.ignore_erpnext_sync = True`. Mirrors are system actions, not user actions — same as HD PR. The user already passed perms on the *originating* write.
- **Link bookkeeping** (`erpnext_item_code`, `crm_product_code` Data fields) → `frappe.db.set_value(..., update_modified=False)`. These are integration metadata, not user data; bypassing perms is intentional and matches HD's `set_links` helper.
- **Framework `User Permission` / `DocShare`** → mirrored end-to-end (Tasks 9 + 10) so an Item restricted to user X is also restricted to the linked CRM Product for user X.

**Tech Stack:** Frappe Framework, ERPNext (Item DocType subclassed but not modified), Vue 3 frontend.

---

## Reference

Pattern lifted from `frappe/helpdesk#3361`:
- `helpdesk/integrations/erpnext/customer.py` — `override_doctype_class` for `Customer` → `CustomCustomer` with lifecycle hooks
- `helpdesk/integrations/erpnext/utils.py` — `find_target_for`, `set_links`, `validate_rename_conflict`, `cascade_rename`, `CASCADE_FLAG`, `should_sync`
- `helpdesk/integrations/erpnext/mirror_sync.py` — `MirrorSyncMixin` (generic, reusable as-is)
- `helpdesk/integrations/erpnext/user_permission.py` — `CustomUserPermission(MirrorSyncMixin, UserPermission)` + `sync_user_permissions` bulk function
- `helpdesk/integrations/erpnext/doc_share.py` — `CustomDocShare(MirrorSyncMixin, DocShare)` + `sync_shared_docs` bulk function

We adapt all of these for `Item` ↔ `CRM Product`. Mixin is copied verbatim; only `ALLOWED_DOCTYPES` and link-field map differ.

---

## Current branch status (as of 2026-05-27)

The branch is 22 commits ahead of `develop`. Most of Tasks 1, 2, 4, 5, 6, 7, 8 landed in another conversation. Remaining: rename-cascade (Task 3 + refactor of Task 4 hooks), frontend banner (Task 9), and the two mirror tasks (10, 11). Detailed task-level status below.

| # | Task | Status | Notes |
|---|---|---|---|
| 1 | Item.crm_product_code reverse field | ✅ Done | `erpnext_crm_settings.py:create_custom_fields_in_frappe_crm` + patch in `create_custom_fields_for_product_item_sync.py` |
| 2 | `payload_differs` + sync gate | ✅ Done with rename pending | `sync_utils.py` exists. Function `same_site_sync_active` will be renamed to `should_sync` (HD parity) as part of Task 3. Callers in `crm_product.py` and `reconcile_job.py` migrate too. |
| 3 | Cascade-rename utils (`crm/integrations/erpnext/utils.py`) | ❌ Pending | Directory exists but no `utils.py`. No `CASCADE_FLAG`, `set_links`, `validate_rename_conflict`, `cascade_rename`, `find_target_for`. |
| 4 | `CustomItem` override | ⚠️ Partial | `item.py` exists with `after_insert` / `on_update` / `after_rename` / `on_trash`. **Missing:** `before_rename` (no conflict check), `after_rename` doesn't cascade-rename the CRM Product, `on_trash` only nulls link (doesn't delete linked product). Needs refactor to use Task 3 helpers. |
| 5 | Pure reconciliation rules | ✅ Done | `reconciliation.py` |
| 6 | Background reconciliation job + Sync Issue child doctype | ✅ Done | `reconcile_job.py`, `crm_product_sync_issue/`, `sync_issues` child table, `enqueue_reconciliation` on enable transition, `run_product_sync` whitelisted method, "Sync Now" button in `ERPNextSettings.vue`. |
| 7 | CRM → ERPNext create on insert | ✅ Done | `_create_item_from_product` + `_push_to_item` in `crm_product.py`. **Missing:** `before_rename` / `after_rename` on CRM Product. |
| 8 | Delete guard on CRM Product | ✅ Done | `on_trash` checks `Quotation Item`. |
| 9 | Surface orphans in UI | ⚠️ Backend only | `get_open_sync_issues` and `dismiss_sync_issue` exist on settings.py. **Missing:** frontend banner component, mount on products list. |
| 10 | `MirrorSyncMixin` + `CustomUserPermission` | ❌ Pending | Not started. |
| 11 | `CustomDocShare` | ❌ Pending | Not started. |

**Function-name reconciliation:** Task 3 introduces `should_sync()` in `crm/integrations/erpnext/utils.py` (HD parity). The existing `same_site_sync_active()` in `crm/fcrm/doctype/crm_product/sync_utils.py` is **renamed** to `should_sync` and re-exported from utils.py. Callers in `crm_product.py` (3 sites) and `reconcile_job.py` (none — gate is inline) are migrated as part of Task 3.

**Task 6 note (out-of-plan changes that landed):** the patch `sync_existing_items_to_crm_products.py` was deleted (the original plan's step 5 rewrote it to enqueue). It is **superseded** by two equivalent triggers that both landed: (a) auto-enqueue inside `ERPNextCRMSettings.validate` on the `enabled` transition, and (b) the manual "Sync Now" button in `ERPNextSettings.vue` calling the `run_product_sync` whitelisted method. No patch needed; behaviour is the same.

**Skip these tasks during execution:** 1, 2 (rename only — done inside Task 3), 5, 6, 7, 8. Execute these: 3, 4 (refactor only), 9 (frontend only), 10, 11.

---

## Task 1: Reverse-link field on Item (local create path) — ✅ DONE, SKIP

**Files:**
- Modify: `crm/patches/v1_0/create_custom_fields_for_product_item_sync.py`
- Modify: `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py:88-108` `create_custom_fields_in_frappe_crm`

**Why:** `sync_existing_items_to_crm_products.py:15` conditionally uses `Item.crm_product_code`, but the field is only created via the ERPNext-side `create_custom_fields_for_frappe_crm`. We need a guaranteed local-create path so reconciliation has a reliable reverse link without relying on the ERPNext repo.

**Step 1: Write failing test**

Create `crm/fcrm/doctype/crm_product/test_product_item_sync.py`:

```python
import frappe
from frappe.tests.utils import FrappeTestCase


class TestReverseLinkField(FrappeTestCase):
    def test_item_has_crm_product_code_field(self):
        if not frappe.db.exists("DocType", "Item"):
            self.skipTest("ERPNext not installed")
        # Force the field to be created
        from crm.patches.v1_0.create_custom_fields_for_product_item_sync import execute
        execute()
        self.assertTrue(frappe.db.has_column("Item", "crm_product_code"))
```

**Step 2: Run test**

```
bench --site analytics.localhost run-tests --module crm.fcrm.doctype.crm_product.test_product_item_sync
```
Expected: FAIL (column missing).

**Step 3: Add Item field to both code paths**

In `erpnext_crm_settings.py:create_custom_fields_in_frappe_crm`, add an `Item` block to the dict — guarded by `if frappe.db.exists("DocType", "Item")`:

```python
if frappe.db.exists("DocType", "Item"):
    custom_fields["Item"] = [
        {
            "fieldname": "crm_product_code",
            "fieldtype": "Data",
            "label": "CRM Product",
            "read_only": 1,
            "no_copy": 1,
            "insert_after": "item_code",
        }
    ]
```

Mirror the same block into `create_custom_fields_for_product_item_sync.py`.

**Step 4: Re-run, commit**

Expected: PASS.

```bash
git add crm/patches/v1_0/create_custom_fields_for_product_item_sync.py \
        crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py \
        crm/fcrm/doctype/crm_product/test_product_item_sync.py
git commit -m "feat(product-sync): ensure Item.crm_product_code is created from CRM side"
```

---

## Task 2: Compare-before-write helper (echo-loop fix) — ✅ DONE, SKIP

**Files:**
- Create: `crm/fcrm/doctype/crm_product/sync_utils.py`

**Why:** `flags.ignore_*_sync` only suppresses the originating write — when the *other* system writes back, its lifecycle fires fresh and bounces. A no-op when the payload matches current target state breaks the loop deterministically.

**Step 1: Failing tests** (in `test_product_item_sync.py`)

```python
class TestEchoLoopBreaker(FrappeTestCase):
    def test_payload_identical_to_target_is_noop(self):
        from crm.fcrm.doctype.crm_product.sync_utils import payload_differs
        self.assertFalse(payload_differs(
            {"item_name": "Widget", "standard_rate": 10, "disabled": 0},
            {"item_name": "Widget", "standard_rate": 10, "disabled": 0},
        ))

    def test_payload_differs_when_any_field_changed(self):
        from crm.fcrm.doctype.crm_product.sync_utils import payload_differs
        self.assertTrue(payload_differs(
            {"item_name": "Widget", "standard_rate": 12},
            {"item_name": "Widget", "standard_rate": 10},
        ))

    def test_none_and_empty_string_treated_as_equal(self):
        from crm.fcrm.doctype.crm_product.sync_utils import payload_differs
        self.assertFalse(payload_differs({"description": ""}, {"description": None}))
```

**Step 2: Run, expect FAIL** (module missing).

**Step 3: Implement**

```python
# sync_utils.py
def payload_differs(payload: dict, target: dict) -> bool:
    """True if any field in payload has a meaningfully different value in target.

    Treats None and empty string as equal — Frappe round-trips empties inconsistently.
    """
    for key, new_value in payload.items():
        if (new_value or None) != (target.get(key) or None):
            return True
    return False
```

(`same_site_sync_active()` lives in `crm/integrations/erpnext/utils.py` — see Task 3. Sole gate for "is product sync active right now"; mirrors HD's `should_sync`.)

**Step 4: Run, commit**

Expected: PASS.

```bash
git add crm/fcrm/doctype/crm_product/sync_utils.py \
        crm/fcrm/doctype/crm_product/test_product_item_sync.py
git commit -m "feat(product-sync): payload comparison helper + same-site gate"
```

---

## Task 3: Integration utils (link map, cascade rename, sync gate) — 🟢 PENDING

**Files:**
- Create: `crm/integrations/erpnext/utils.py` (the `__init__.py` files already exist on the branch)

**Why:** Lift HD's `utils.py` near-verbatim. Centralises the `(Item, CRM Product)` ↔ link-field map, the `CASCADE_FLAG` re-entrancy guard, `validate_rename_conflict` / `cascade_rename` for proper rename/merge handling, and `set_links` for permission-bypassing link bookkeeping with `update_modified=False`.

**Step 1: Failing tests** (`crm/integrations/erpnext/test_utils.py`)

```python
import frappe
from frappe.tests.utils import FrappeTestCase


class TestFindTargetFor(FrappeTestCase):
    def test_returns_none_for_unknown_doctype(self):
        from crm.integrations.erpnext.utils import find_target_for
        self.assertIsNone(find_target_for("Some Other DocType", "X"))

    def test_returns_none_when_inputs_missing(self):
        from crm.integrations.erpnext.utils import find_target_for
        self.assertIsNone(find_target_for(None, "X"))
        self.assertIsNone(find_target_for("Item", None))


class TestCascadeFlag(FrappeTestCase):
    def test_flag_round_trip(self):
        from crm.integrations.erpnext.utils import CASCADE_FLAG, in_cascade
        self.assertFalse(in_cascade())
        frappe.flags[CASCADE_FLAG] = True
        try:
            self.assertTrue(in_cascade())
        finally:
            frappe.flags[CASCADE_FLAG] = False
```

**Step 2: Run, expect FAIL.**

**Step 3: Implement `crm/integrations/erpnext/utils.py`**

```python
import frappe
from frappe import _
from frappe.model.rename_doc import rename_doc

CASCADE_FLAG = "crm_product_item_cascade_in_progress"
ALLOWED_DOCTYPES = ("CRM Product", "Item")


def should_sync() -> bool:
    """Product sync runs only when integration is enabled AND same-site.
    HD parity — replaces the earlier same_site_sync_active() in sync_utils.py.
    """
    if "erpnext" not in frappe.get_installed_apps():
        return False
    settings = frappe.get_cached_doc("ERPNext CRM Settings")
    return bool(settings.enabled) and not settings.is_erpnext_in_different_site


def in_cascade() -> bool:
    return bool(frappe.flags.get(CASCADE_FLAG))


def set_links(item_code: str, crm_product_name: str) -> None:
    """Permission-bypassing link bookkeeping. Mirrors HD's set_links."""
    frappe.db.set_value("CRM Product", crm_product_name, "erpnext_item_code",
                        item_code, update_modified=False)
    frappe.db.set_value("Item", item_code, "crm_product_code",
                        crm_product_name, update_modified=False)


def _other_side(self_doctype: str) -> tuple[str, str]:
    if self_doctype == "CRM Product":
        return "Item", "crm_product_code"
    return "CRM Product", "erpnext_item_code"


def find_target_for(doctype: str | None, value: str | None) -> tuple[str, str] | None:
    if not doctype or not value:
        return None
    if doctype == "CRM Product":
        item = frappe.db.get_value("Item", {"crm_product_code": value}, "name")
        return ("Item", item) if item else None
    if doctype == "Item":
        prod = frappe.db.get_value("CRM Product", {"erpnext_item_code": value}, "name")
        return ("CRM Product", prod) if prod else None
    return None


def validate_rename_conflict(self_doctype, olddn, newdn, merge):
    if in_cascade() or not same_site_sync_active():
        return
    other_doctype, other_link_field = _other_side(self_doctype)
    linked = frappe.db.get_value(other_doctype, {other_link_field: olddn}, "name")
    if not linked:
        return
    if merge:
        surviving = frappe.db.get_value(other_doctype, {other_link_field: newdn}, "name")
        if surviving:
            return  # M2: cascade-merge into surviving
    if linked == newdn:
        return
    if frappe.db.exists(other_doctype, newdn):
        existing_link = frappe.db.get_value(other_doctype, newdn, other_link_field)
        if existing_link != olddn:
            frappe.throw(_(
                "Cannot rename: an unrelated {0} '{1}' already exists on the "
                "other side. Resolve manually first."
            ).format(other_doctype, newdn))


def cascade_rename(self_doctype, olddn, newdn, merge):
    if in_cascade() or not same_site_sync_active():
        return
    other_doctype, other_link_field = _other_side(self_doctype)
    linked = frappe.db.get_value(other_doctype, {other_link_field: olddn}, "name")
    if not linked:
        return
    frappe.flags[CASCADE_FLAG] = True
    try:
        if merge:
            surviving = frappe.db.get_value(other_doctype, {other_link_field: newdn}, "name")
            if surviving and surviving != linked:
                rename_doc(other_doctype, linked, surviving, merge=True, ignore_permissions=True)
                target = surviving
            else:
                if linked != newdn:
                    rename_doc(other_doctype, linked, newdn, ignore_permissions=True)
                target = newdn
        else:
            if linked != newdn:
                rename_doc(other_doctype, linked, newdn, ignore_permissions=True)
            target = newdn
        _resync_links(self_doctype, newdn, target)
    finally:
        frappe.flags[CASCADE_FLAG] = False


def _resync_links(self_doctype, self_name, other_name):
    if self_doctype == "CRM Product":
        prod, item = self_name, other_name
    else:
        prod, item = other_name, self_name
    if frappe.db.exists("CRM Product", prod):
        frappe.db.set_value("CRM Product", prod, "erpnext_item_code", item, update_modified=False)
    if frappe.db.exists("Item", item):
        frappe.db.set_value("Item", item, "crm_product_code", prod, update_modified=False)
```

**Step 4: Migrate callers — rename `same_site_sync_active` → `should_sync`**

Delete `same_site_sync_active` from `crm/fcrm/doctype/crm_product/sync_utils.py` (leave `payload_differs` there).

Update import + call sites:

- `crm/fcrm/doctype/crm_product/crm_product.py` — change import to `from crm.integrations.erpnext.utils import should_sync`, replace 3 call sites (`after_insert`, `on_update`, `on_trash`).
- `crm/integrations/erpnext/item.py` — change import to `from crm.integrations.erpnext.utils import should_sync, set_links, in_cascade, validate_rename_conflict, cascade_rename` (the rest used in Task 4). Update `_should_sync` body.
- `crm/fcrm/doctype/crm_product/reconcile_job.py` — gate is inline (`settings.enabled` / `is_erpnext_in_different_site`); leave as-is unless you prefer to swap to `should_sync()` for consistency.

Run existing tests:

```
bench --site analytics.localhost run-tests --module crm.fcrm.doctype.crm_product.test_product_item_sync
```
Expected: PASS (only the function name changed).

**Step 5: Commit**

```bash
git add crm/integrations/erpnext/utils.py \
        crm/integrations/erpnext/test_utils.py \
        crm/fcrm/doctype/crm_product/sync_utils.py \
        crm/fcrm/doctype/crm_product/crm_product.py \
        crm/integrations/erpnext/item.py
git commit -m "feat(product-sync): integration utils + rename sync gate to should_sync"
```

---

## Task 4: CustomItem override — replace doc_events with class hooks — 🟡 REFACTOR ONLY

**Status:** `CustomItem` class exists (`crm/integrations/erpnext/item.py`) with `after_insert`, `on_update`, `after_rename`, `on_trash`. `override_doctype_class["Item"]` is wired in `hooks.py`. `sync_item_to_crm_product` has been removed from `crm_product.py`.

**What's missing:**
1. `before_rename` to call `validate_rename_conflict` (Task 3 helper).
2. `after_rename` currently just updates `erpnext_item_code` on the linked CRM Product; it must instead call `cascade_rename` so that renaming `Item: A → B` also renames `CRM Product: A → B`. Mirrors HD's `after_rename(olddn, newdn, merge)`.
3. `on_trash` currently nulls the back-link only. To match HD's pattern, it should **delete** the linked `CRM Product` (with `CASCADE_FLAG` to prevent re-entry through `CRMProduct.on_trash`'s delete guard).
4. Mirror methods on `CRMProduct` side: `before_rename` and `after_rename`, and `on_trash` must `in_cascade()`-bail-out when a cascade delete is already in progress.

**Step 1: Update `crm/integrations/erpnext/item.py`** — replace the existing class with:

**Why:** Mirrors Helpdesk PR pattern. Gives us `after_insert`, `on_update`, `on_rename`, `on_trash` on Item without modifying ERPNext. Consolidates Item-side logic into one class.

**Step 1: Failing tests**

```python
class TestItemHooks(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("DocType", "Item"):
            self.skipTest("ERPNext not installed")
        from crm.fcrm.doctype.crm_product.sync_utils import same_site_sync_active
        if not same_site_sync_active():
            self.skipTest("Integration not enabled or cross-site")
        frappe.db.delete("CRM Product", {"product_code": ["like", "HOOK-%"]})
        frappe.db.delete("Item", {"item_code": ["like", "HOOK-%"]})

    def test_item_insert_creates_linked_crm_product(self):
        item = frappe.get_doc({"doctype": "Item", "item_code": "HOOK-1",
                               "item_name": "From ERP", "standard_rate": 30}).insert()
        self.assertTrue(frappe.db.exists("CRM Product", {"erpnext_item_code": "HOOK-1"}))
        # Reverse link set
        self.assertEqual(frappe.db.get_value("Item", "HOOK-1", "crm_product_code"), "HOOK-1")

    def test_item_rename_updates_crm_product_link(self):
        frappe.get_doc({"doctype": "Item", "item_code": "HOOK-2", "item_name": "X"}).insert()
        frappe.rename_doc("Item", "HOOK-2", "HOOK-2-NEW")
        self.assertEqual(
            frappe.db.get_value("CRM Product", {"erpnext_item_code": "HOOK-2-NEW"}, "erpnext_item_code"),
            "HOOK-2-NEW",
        )

    def test_item_delete_removes_link_on_crm_product(self):
        frappe.get_doc({"doctype": "Item", "item_code": "HOOK-3", "item_name": "Z"}).insert()
        frappe.delete_doc("Item", "HOOK-3")
        product = frappe.db.get_value("CRM Product", {"product_code": "HOOK-3"},
                                       ["erpnext_item_code"], as_dict=True)
        self.assertIsNone(product.erpnext_item_code)
```

**Step 2: Run, expect FAIL**

**Step 3: Implement `crm/integrations/erpnext/item.py`**

```python
import frappe
from erpnext.stock.doctype.item.item import Item

from crm.fcrm.doctype.crm_product.sync_utils import payload_differs
from crm.integrations.erpnext.utils import (
    cascade_rename, in_cascade, set_links, should_sync, validate_rename_conflict,
)

CATALOGUE_FIELDS = ("standard_rate", "image", "disabled", "description")


class CustomItem(Item):
    def after_insert(self):
        super().after_insert()
        if not self._same_site_sync_active():
            return
        if frappe.db.get_value("CRM Product", {"erpnext_item_code": self.name}):
            return
        product = frappe.get_doc({
            "doctype": "CRM Product",
            "product_code": self.item_code,
            "product_name": self.item_name,
            **{f: self.get(f) for f in CATALOGUE_FIELDS},
        })
        product.flags.ignore_erpnext_sync = True
        product.insert(ignore_permissions=True)  # mirror = system action
        set_links(self.name, product.name)

    def on_update(self):
        super().on_update()
        if not self._same_site_sync_active():
            return
        product_name = frappe.db.get_value("CRM Product", {"erpnext_item_code": self.name})
        if not product_name:
            return
        data = {"product_name": self.item_name,
                **{f: self.get(f) for f in CATALOGUE_FIELDS}}
        current = frappe.db.get_value("CRM Product", product_name, list(data.keys()), as_dict=True) or {}
        if not payload_differs(data, current):
            return
        # Mirror is a system write — use db.set_value, no perm check
        frappe.db.set_value("CRM Product", product_name, data)

    def before_rename(self, olddn, newdn, merge=False):
        super().before_rename(olddn, newdn, merge)
        validate_rename_conflict("Item", olddn, newdn, merge)

    def after_rename(self, olddn, newdn, merge=False):
        super().after_rename(olddn, newdn, merge)
        cascade_rename("Item", olddn, newdn, merge)

    def on_trash(self):
        super().on_trash()
        if in_cascade() or not self._same_site_sync_active():
            return
        product = frappe.db.get_value("CRM Product", {"erpnext_item_code": self.name})
        if product:
            # Clear back-link first so CRMProduct.on_trash won't try to delete this Item
            frappe.db.set_value("CRM Product", product, "erpnext_item_code", None)
            frappe.delete_doc("CRM Product", product, ignore_permissions=True)

    def _should_sync(self) -> bool:
        return same_site_sync_active() and not self.flags.get("ignore_crm_sync")
```

**Mirror this on the CRM Product side** (`crm_product.py` — add to `CRMProduct` class):

```python
def before_rename(self, olddn, newdn, merge=False):
    from crm.integrations.erpnext.utils import validate_rename_conflict
    validate_rename_conflict("CRM Product", olddn, newdn, merge)

def after_rename(self, olddn, newdn, merge=False):
    from crm.integrations.erpnext.utils import cascade_rename
    cascade_rename("CRM Product", olddn, newdn, merge)
```

(Task 7 — `on_trash` — already exists on CRMProduct; just ensure it checks `in_cascade()` to avoid re-entering during a cascaded delete from CustomItem.)

**Step 4: Update `hooks.py`**

```python
override_doctype_class = {
    "Contact": "crm.overrides.contact.CustomContact",
    "Email Template": "crm.overrides.email_template.CustomEmailTemplate",
    "Item": "crm.integrations.erpnext.item.CustomItem",
}
```

Remove the `"Item": {...}` block from `doc_events`. Delete `sync_item_to_crm_product` from `crm_product.py` (it's superseded by `CustomItem.after_insert` / `on_update`).

**Step 5: Run, commit**

```bash
git add crm/integrations/ crm/hooks.py crm/fcrm/doctype/crm_product/crm_product.py \
        crm/fcrm/doctype/crm_product/test_product_item_sync.py
git commit -m "feat(product-sync): CustomItem override with rename and delete hooks"
```

---

## Task 5: Reconciliation pure rules — ✅ DONE, SKIP

**Files:**
- Create: `crm/fcrm/doctype/crm_product/reconciliation.py`

**Why:** Pure functions for matching + conflict resolution + orphan detection. Unit-testable without ERPNext running.

**Step 1: Failing tests**

```python
class TestReconciliationRules(FrappeTestCase):
    def test_already_linked_pair_is_skipped(self):
        from crm.fcrm.doctype.crm_product.reconciliation import classify_pair
        item = {"item_code": "A", "crm_product_code": "A"}
        product = {"name": "A", "product_code": "A", "erpnext_item_code": "A"}
        self.assertEqual(classify_pair(item, product).rule, "already_linked")

    def test_exact_code_match_resolves_erpnext_wins_for_catalogue(self):
        from crm.fcrm.doctype.crm_product.reconciliation import classify_pair
        item = {"item_code": "B", "item_name": "From ERP", "standard_rate": 100}
        product = {"name": "B", "product_code": "B", "product_name": "From CRM", "standard_rate": 80}
        result = classify_pair(item, product)
        self.assertEqual(result.rule, "exact_code")
        self.assertEqual(result.crm_updates["standard_rate"], 100)
        # CRM name preserved when both non-empty
        self.assertNotIn("product_name", result.crm_updates)

    def test_crm_name_filled_in_when_empty(self):
        from crm.fcrm.doctype.crm_product.reconciliation import classify_pair
        item = {"item_code": "C", "item_name": "Filled"}
        product = {"name": "C", "product_code": "C", "product_name": None}
        result = classify_pair(item, product)
        self.assertEqual(result.crm_updates["product_name"], "Filled")

    def test_orphan_detection(self):
        from crm.fcrm.doctype.crm_product.reconciliation import detect_orphan
        self.assertTrue(detect_orphan({"erpnext_item_code": "GONE"}, {"OTHER"}))
        self.assertFalse(detect_orphan({"erpnext_item_code": "HERE"}, {"HERE"}))
        self.assertFalse(detect_orphan({"erpnext_item_code": None}, set()))
```

**Step 2: Run, expect FAIL.**

**Step 3: Implement**

```python
# reconciliation.py
from dataclasses import dataclass, field
from typing import Literal

CATALOGUE_FIELDS = ("standard_rate", "image", "disabled", "description")
Rule = Literal["already_linked", "exact_code", "no_match"]


@dataclass
class PairAction:
    rule: Rule
    crm_updates: dict = field(default_factory=dict)
    item_updates: dict = field(default_factory=dict)


def classify_pair(item: dict, product: dict) -> PairAction:
    if (
        item.get("crm_product_code") == product.get("name")
        and product.get("erpnext_item_code") == item.get("item_code")
    ):
        return PairAction(rule="already_linked")

    if item.get("item_code") == product.get("product_code"):
        updates = {"erpnext_item_code": item["item_code"]}
        for f in CATALOGUE_FIELDS:
            updates[f] = item.get(f)
        if not product.get("product_name") and item.get("item_name"):
            updates["product_name"] = item["item_name"]
        return PairAction(
            rule="exact_code",
            crm_updates=updates,
            item_updates={"crm_product_code": product["name"]},
        )

    return PairAction(rule="no_match")


def detect_orphan(product: dict, existing_item_codes: set[str]) -> bool:
    linked = product.get("erpnext_item_code")
    return bool(linked) and linked not in existing_item_codes
```

**Step 4: Run, commit**

```bash
git add crm/fcrm/doctype/crm_product/reconciliation.py \
        crm/fcrm/doctype/crm_product/test_product_item_sync.py
git commit -m "feat(product-sync): pure reconciliation rules (exact-code + orphan)"
```

---

## Task 6: Background reconciliation job + Sync Issue child doctype — ✅ DONE, SKIP

**Already implemented** in `reconcile_job.py`, `crm_product_sync_issue/`, and `ERPNextSettings.vue` (Sync Now button via `run_product_sync` whitelisted method). Steps below are kept for reference only.

**Files:**
- Create: `crm/fcrm/doctype/crm_product_sync_issue/` (`crm_product_sync_issue.json`, `__init__.py`, `crm_product_sync_issue.py`)
- Modify: `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.json` — add `sync_issues` child table
- Create: `crm/fcrm/doctype/crm_product/reconcile_job.py`
- Modify: `crm/patches/v1_0/sync_existing_items_to_crm_products.py` — replace inline logic with enqueue
- Modify: `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py:50` `validate` — enqueue on enable transition

**Why:** Item lists may be huge → `queue="long"`. Orphans surface to UI via standard child table.

**Child DocType `CRM Product Sync Issue`** (`istable: 1`):
- `product` (Link → CRM Product, read_only)
- `kind` (Select: `unlinked_orphan`, read_only)
- `detail` (Small Text, read_only)
- `detected_on` (Datetime, read_only, default `now`)
- `dismissed` (Check, default 0)

**Step 1: Failing integration tests**

```python
class TestReconcileJob(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("DocType", "Item"):
            self.skipTest("ERPNext not installed")
        frappe.db.delete("CRM Product", {"product_code": ["like", "JOB-%"]})
        frappe.db.delete("Item", {"item_code": ["like", "JOB-%"]})
        settings = frappe.get_single("ERPNext CRM Settings")
        settings.sync_issues = []
        settings.save(ignore_permissions=True)

    def test_unlinked_duplicates_get_linked(self):
        from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation
        frappe.get_doc({"doctype": "Item", "item_code": "JOB-A",
                        "item_name": "Widget", "standard_rate": 50}).insert(ignore_permissions=True)
        frappe.get_doc({"doctype": "CRM Product", "product_code": "JOB-A",
                        "product_name": "Widget"}).insert(ignore_permissions=True)

        summary = run_reconciliation()
        self.assertEqual(summary["linked_by_exact_code"], 1)
        self.assertEqual(frappe.db.get_value("CRM Product", "JOB-A", "erpnext_item_code"), "JOB-A")
        self.assertEqual(frappe.db.get_value("Item", "JOB-A", "crm_product_code"), "JOB-A")
        self.assertEqual(frappe.db.get_value("CRM Product", "JOB-A", "standard_rate"), 50)

    def test_orphan_link_is_unlinked_and_recorded(self):
        from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation
        frappe.get_doc({"doctype": "CRM Product", "product_code": "JOB-ORPHAN",
                        "product_name": "Orphan",
                        "erpnext_item_code": "DELETED-ITEM"}).insert(ignore_permissions=True)
        run_reconciliation()
        self.assertIsNone(frappe.db.get_value("CRM Product", "JOB-ORPHAN", "erpnext_item_code"))
        issues = frappe.get_all("CRM Product Sync Issue",
                                 filters={"parent": "ERPNext CRM Settings", "product": "JOB-ORPHAN"},
                                 fields=["kind"])
        self.assertEqual(len(issues), 1)
        self.assertEqual(issues[0]["kind"], "unlinked_orphan")

    def test_skipped_when_cross_site(self):
        from crm.fcrm.doctype.crm_product.reconcile_job import run_reconciliation
        settings = frappe.get_single("ERPNext CRM Settings")
        settings.is_erpnext_in_different_site = 1
        settings.save(ignore_permissions=True)
        try:
            self.assertEqual(run_reconciliation(), {"skipped": "cross_site_not_supported"})
        finally:
            settings.is_erpnext_in_different_site = 0
            settings.save(ignore_permissions=True)
```

**Step 2: Run, expect FAIL** (missing module + doctype).

**Step 3: Create child doctype + add child table field to settings.**

Hand-author `crm_product_sync_issue.json` (`istable: 1`, fields as above, empty permissions). Add to settings JSON:

```json
{
  "fieldname": "sync_issues",
  "fieldtype": "Table",
  "options": "CRM Product Sync Issue",
  "label": "Product Sync Issues",
  "read_only": 1
}
```

Insert into `field_order` after `enabled`.

**Step 4: Implement `reconcile_job.py`**

```python
import frappe
from frappe import _

from crm.fcrm.doctype.crm_product.reconciliation import (
    CATALOGUE_FIELDS, classify_pair, detect_orphan,
)
from crm.fcrm.doctype.crm_product.sync_utils import same_site_sync_active


def enqueue_reconciliation():
    frappe.enqueue(
        "crm.fcrm.doctype.crm_product.reconcile_job.run_reconciliation",
        queue="long",
        timeout=1200,
        job_name="crm_product_item_reconciliation",
        deduplicate=True,
    )


def run_reconciliation() -> dict:
    if not frappe.db.exists("DocType", "Item"):
        return {"skipped": "erpnext_not_installed"}

    settings = frappe.get_single("ERPNext CRM Settings")
    if not settings.enabled:
        return {"skipped": "integration_disabled"}
    if settings.is_erpnext_in_different_site:
        return {"skipped": "cross_site_not_supported"}

    summary = {"already_linked": 0, "linked_by_exact_code": 0,
               "created_in_crm": 0, "created_in_erpnext": 0,
               "unlinked_orphans": 0}

    items = {i["item_code"]: i for i in frappe.db.get_all(
        "Item",
        fields=["item_code", "item_name", "standard_rate", "image",
                "disabled", "description", "crm_product_code"],
    )}
    products = {p["product_code"]: p for p in frappe.db.get_all(
        "CRM Product",
        fields=["name", "product_code", "product_name", "standard_rate", "image",
                "disabled", "description", "erpnext_item_code"],
    )}

    issues = []

    for code, item in items.items():
        product = products.get(code)
        if not product:
            _create_crm_product_from_item(item)
            summary["created_in_crm"] += 1
            continue
        action = classify_pair(item, product)
        if action.rule == "already_linked":
            summary["already_linked"] += 1
        else:
            summary["linked_by_exact_code"] += 1
        if action.crm_updates:
            frappe.db.set_value("CRM Product", product["name"], action.crm_updates)
        if action.item_updates:
            frappe.db.set_value("Item", item["item_code"], action.item_updates)

    existing_item_codes = set(items.keys())

    # Push CRM-only products to ERPNext
    for code, product in products.items():
        if code in existing_item_codes:
            continue
        if detect_orphan(product, existing_item_codes):
            frappe.db.set_value("CRM Product", product["name"], "erpnext_item_code", None)
            issues.append({
                "product": product["name"],
                "kind": "unlinked_orphan",
                "detail": _("Linked Item {0} no longer exists").format(product["erpnext_item_code"]),
            })
            summary["unlinked_orphans"] += 1
            continue
        if product.get("erpnext_item_code"):
            continue  # Linked to a *different* item_code than its product_code; leave alone
        doc = frappe.get_doc("CRM Product", product["name"])
        _create_item_from_product(doc)
        summary["created_in_erpnext"] += 1

    _record_issues(settings, issues)
    frappe.publish_realtime("crm_product_sync_complete", user=frappe.session.user)
    frappe.log_error(message=frappe.as_json(summary), title="CRM Product Reconciliation")
    return summary


def _create_crm_product_from_item(item):
    product = frappe.new_doc("CRM Product")
    product.product_code = item["item_code"]
    product.erpnext_item_code = item["item_code"]
    product.product_name = item.get("item_name")
    for f in CATALOGUE_FIELDS:
        product.set(f, item.get(f))
    product.flags.ignore_erpnext_sync = True
    product.insert(ignore_permissions=True)
    frappe.db.set_value("Item", item["item_code"], "crm_product_code", product.name)


def _create_item_from_product(product_doc):
    """Direct write to Item via core Frappe — no ERPNext-side method."""
    item = frappe.get_doc({
        "doctype": "Item",
        "item_code": product_doc.product_code,
        "item_name": product_doc.product_name or product_doc.product_code,
        "standard_rate": product_doc.standard_rate,
        "image": product_doc.image,
        "disabled": product_doc.disabled,
        "description": product_doc.description,
        "crm_product_code": product_doc.name,
        # Sensible defaults so Item passes validation:
        "item_group": frappe.db.get_single_value("Stock Settings", "item_group") or "All Item Groups",
        "stock_uom": frappe.db.get_single_value("Stock Settings", "stock_uom") or "Nos",
        "is_stock_item": 0,
    })
    item.flags.ignore_crm_sync = True
    item.insert(ignore_permissions=True)
    frappe.db.set_value("CRM Product", product_doc.name, "erpnext_item_code", item.name)


def _record_issues(settings, issues):
    if not issues:
        return
    for issue in issues:
        settings.append("sync_issues", issue)
    settings.save(ignore_permissions=True)
```

**Step 5: Replace patch body with enqueue**

```python
# create_existing_items_to_crm_products.py (rewrite)
import frappe
from crm.fcrm.doctype.crm_product.reconcile_job import enqueue_reconciliation


def execute():
    if not frappe.db.exists("DocType", "Item"):
        return
    settings = frappe.get_single("ERPNext CRM Settings")
    if not settings.enabled or settings.is_erpnext_in_different_site:
        return
    enqueue_reconciliation()
```

**Step 6: Enqueue on enable transition**

In `erpnext_crm_settings.py:validate`, capture old state before doing existing work:

```python
def validate(self):
    old = self.get_doc_before_save()
    was_enabled = bool(old and old.enabled and not old.is_erpnext_in_different_site)
    if self.enabled:
        self.validate_if_erpnext_installed()
        self.add_quotation_to_option()
        self.create_custom_fields()
        self.create_crm_form_script()
        self.setup_quotation_prefill_script()
        if not was_enabled and not self.is_erpnext_in_different_site:
            from crm.fcrm.doctype.crm_product.reconcile_job import enqueue_reconciliation
            enqueue_reconciliation()
```

**Step 7: Run tests, commit**

```bash
git add crm/fcrm/doctype/crm_product_sync_issue/ \
        crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.json \
        crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py \
        crm/fcrm/doctype/crm_product/reconcile_job.py \
        crm/patches/v1_0/sync_existing_items_to_crm_products.py \
        crm/fcrm/doctype/crm_product/test_product_item_sync.py
git commit -m "feat(product-sync): background reconciliation job + orphan recording"
```

---

## Task 7: CRM → ERPNext create on insert (no ERPNext API) — ✅ DONE, SKIP

**Files:**
- Modify: `crm/fcrm/doctype/crm_product/crm_product.py` — drop `before_insert` block, drop the import of `erpnext.crm.frappe_crm_api.update_item_from_crm_product`, replace with direct write

**Why:** Currently `before_insert` (crm_product.py:27-36) blocks CRM-side creates and tells users "go to ERPNext." Replace with `after_insert` that creates the Item directly via `frappe.get_doc({"doctype": "Item", ...}).insert()`. `on_update` already updates the Item — switch it from importing the ERPNext-side method to writing directly.

**Step 1: Failing tests**

```python
class TestCRMToERPNextCreate(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("DocType", "Item"):
            self.skipTest("ERPNext not installed")
        frappe.db.delete("CRM Product", {"product_code": ["like", "PUSH-%"]})
        frappe.db.delete("Item", {"item_code": ["like", "PUSH-%"]})

    def test_inserting_crm_product_creates_item(self):
        p = frappe.get_doc({"doctype": "CRM Product", "product_code": "PUSH-1",
                            "product_name": "Pushed", "standard_rate": 25}).insert()
        self.assertEqual(p.erpnext_item_code, "PUSH-1")
        self.assertTrue(frappe.db.exists("Item", "PUSH-1"))
        self.assertEqual(frappe.db.get_value("Item", "PUSH-1", "standard_rate"), 25)
        self.assertEqual(frappe.db.get_value("Item", "PUSH-1", "crm_product_code"), "PUSH-1")

    def test_update_crm_product_updates_item(self):
        p = frappe.get_doc({"doctype": "CRM Product", "product_code": "PUSH-2",
                            "product_name": "X", "standard_rate": 10}).insert()
        p.standard_rate = 99
        p.save()
        self.assertEqual(frappe.db.get_value("Item", "PUSH-2", "standard_rate"), 99)
```

**Step 2: Run, expect FAIL** (`before_insert` throws).

**Step 3: Rewrite `crm_product.py`**

```python
import frappe
from frappe import _
from frappe.model.document import Document

from crm.fcrm.doctype.crm_product.sync_utils import payload_differs
from crm.fcrm.doctype.crm_product.sync_utils import same_site_sync_active

CATALOGUE_FIELDS = ("standard_rate", "image", "disabled", "description")


class CRMProduct(Document):
    # ... auto-generated types unchanged ...

    def validate(self):
        self.set_product_name()

    def set_product_name(self):
        self.product_name = (self.product_name or self.product_code or "").strip()

    def after_insert(self):
        if self.flags.get("ignore_erpnext_sync"):
            return
        if not same_site_sync_active():
            return
        if self.get("erpnext_item_code"):
            return
        _create_item_from_product(self)

    def on_update(self):
        if self.flags.get("ignore_erpnext_sync"):
            return
        if not self.get("erpnext_item_code"):
            return
        if not same_site_sync_active():
            return
        _push_to_item(self)


def _create_item_from_product(doc):
    if frappe.db.exists("Item", doc.product_code):
        # Item exists; let reconciliation handle linking. Avoid race-create.
        return
    item = frappe.get_doc({
        "doctype": "Item",
        "item_code": doc.product_code,
        "item_name": doc.product_name or doc.product_code,
        "standard_rate": doc.standard_rate,
        "image": doc.image,
        "disabled": doc.disabled,
        "description": doc.description,
        "crm_product_code": doc.name,
        "item_group": frappe.db.get_single_value("Stock Settings", "item_group") or "All Item Groups",
        "stock_uom": frappe.db.get_single_value("Stock Settings", "stock_uom") or "Nos",
        "is_stock_item": 0,
    })
    item.flags.ignore_crm_sync = True
    item.insert()  # honour caller's permissions
    frappe.db.set_value("CRM Product", doc.name, "erpnext_item_code", item.name)


def _push_to_item(doc):
    item_code = doc.erpnext_item_code
    if not frappe.db.exists("Item", item_code):
        frappe.db.set_value("CRM Product", doc.name, "erpnext_item_code", None)
        return
    data = {"item_name": doc.product_name, **{f: doc.get(f) for f in CATALOGUE_FIELDS}}
    current = frappe.db.get_value("Item", item_code, list(data.keys()), as_dict=True) or {}
    if not payload_differs(data, current):
        return
    item = frappe.get_doc("Item", item_code)
    item.update(data)
    item.flags.ignore_crm_sync = True
    item.save()
```

**Notes:** Remove `before_insert`. Remove `push_product_to_erpnext_item`. Remove the now-unused `sync_item_to_crm_product` (moved to `CustomItem` in Task 3). `insert()` and `save()` honour the caller's permissions — addressing the permission-bypass edge case from the previous review.

**Step 4: Run, commit**

```bash
git add crm/fcrm/doctype/crm_product/crm_product.py \
        crm/fcrm/doctype/crm_product/test_product_item_sync.py
git commit -m "feat(product-sync): CRM-side create/update writes Item directly via core APIs"
```

---

## Task 8: Delete guard on CRM Product — ✅ DONE, SKIP

**Note:** existing `on_trash` in `crm_product.py:55-69` checks `Quotation Item` and throws. Task 4 refactor will add an `in_cascade()` early-return so the cascade-delete from `CustomItem.on_trash` doesn't trip this guard.

**Files:**
- Modify: `crm/fcrm/doctype/crm_product/crm_product.py` — add `on_trash`

**Why:** Closes the "delete on CRM while Item is referenced in Quotation" gap. Item-side guard already comes for free via standard `LinkExistsError`, but the CRM side has no awareness today.

**Step 1: Failing test**

```python
def test_cannot_delete_crm_product_with_referenced_item(self):
    if not frappe.db.exists("DocType", "Quotation"):
        self.skipTest("ERPNext not installed")
    frappe.db.delete("CRM Product", {"product_code": "DEL-1"})
    frappe.db.delete("Item", {"item_code": "DEL-1"})
    p = frappe.get_doc({"doctype": "CRM Product", "product_code": "DEL-1",
                        "product_name": "X"}).insert()
    # Create a Quotation referencing the Item
    frappe.get_doc({
        "doctype": "Quotation", "quotation_to": "Customer",
        "party_name": "_Test Customer", "items": [
            {"item_code": "DEL-1", "qty": 1, "rate": 10}
        ],
    }).insert(ignore_permissions=True)
    with self.assertRaises(frappe.ValidationError):
        frappe.delete_doc("CRM Product", "DEL-1")
```

**Step 2: Run, expect FAIL.**

**Step 3: Implement**

```python
def on_trash(self):
    if not self.get("erpnext_item_code"):
        return
    if not same_site_sync_active():
        return
    if frappe.db.sql(
        "SELECT 1 FROM `tabQuotation Item` WHERE item_code=%s LIMIT 1",
        self.erpnext_item_code,
    ):
        frappe.throw(_(
            "Cannot delete: linked ERPNext Item {0} is referenced by a Quotation. "
            "Remove the reference or delete the Item in ERPNext first."
        ).format(self.erpnext_item_code))
```

**Step 4: Run, commit**

```bash
git commit -am "feat(product-sync): block CRM Product delete when linked Item is referenced"
```

---

## Task 9: Surface orphan unlinks in UI — 🟡 FRONTEND ONLY

**Status:** Backend endpoints (`get_open_sync_issues`, `dismiss_sync_issue`) are already implemented in `erpnext_crm_settings.py:198-228`. `reconcile_job.py` fires `frappe.publish_realtime("crm_product_sync_complete")` on completion. Frontend banner is the only remaining piece.

**Files:**
- Locate: products list view in `frontend/src/`
- Create: `frontend/src/components/SyncIssuesBanner.vue`

**Step 1: Locate the products list**

```
grep -rn "CRM Product" frontend/src/router frontend/src/pages 2>/dev/null
```

Confirm path. (Skip the test for the page path — that's not testable without a browser.)

**Step 2: Endpoints + tests**

```python
@frappe.whitelist()
def get_open_sync_issues():
    if not frappe.has_permission("CRM Product", "read"):
        return []
    settings = frappe.get_single("ERPNext CRM Settings")
    return [
        {"name": i.name, "product": i.product, "kind": i.kind,
         "detail": i.detail, "detected_on": i.detected_on}
        for i in settings.sync_issues if not i.dismissed
    ]


@frappe.whitelist()
def dismiss_sync_issue(issue_name: str):
    settings = frappe.get_single("ERPNext CRM Settings")
    for issue in settings.sync_issues:
        if issue.name == issue_name:
            issue.dismissed = 1
            settings.save()  # honour caller's permissions
            return True
    return False
```

**Step 3: Banner component**

Yellow banner above the product list: "N products were unlinked from ERPNext. Review →". Click opens a modal listing each with a Dismiss button. Use existing CRM toast/dialog primitives.

Subscribe to `frappe.publish_realtime("crm_product_sync_complete")` to refresh.

**Step 4: Manual UI verification.** Per CLAUDE.md no build/typecheck — ask user to load products page and trigger reconciliation.

**Step 5: Commit**

```bash
git commit -am "feat(product-sync): banner surfaces orphan unlinks in product list"
```

---

## Task 10: MirrorSyncMixin + CustomUserPermission — 🟢 PENDING

**Files:**
- Create: `crm/integrations/erpnext/mirror_sync.py` (verbatim from HD with `ALLOWED_DOCTYPES` swap)
- Create: `crm/integrations/erpnext/user_permission.py`
- Modify: `crm/hooks.py` — `override_doctype_class["User Permission"] = "crm.integrations.erpnext.user_permission.CustomUserPermission"`
- Modify: `crm/fcrm/doctype/crm_product/reconcile_job.py:run_reconciliation` — call `sync_user_permissions()` at the end

**Why:** Without this, a User Permission restricting user X to `Item: ABC` doesn't restrict them to `CRM Product: ABC` (or vice versa). Closes the framework-level perms gap.

**Step 1: Failing tests**

```python
class TestUserPermissionMirror(FrappeTestCase):
    def setUp(self):
        if not frappe.db.exists("DocType", "Item"):
            self.skipTest("ERPNext not installed")
        from crm.fcrm.doctype.crm_product.sync_utils import same_site_sync_active
        if not same_site_sync_active():
            self.skipTest("Integration not enabled")
        # Establish a linked pair
        frappe.db.delete("CRM Product", {"product_code": ["like", "PERM-%"]})
        frappe.db.delete("Item", {"item_code": ["like", "PERM-%"]})
        frappe.db.delete("User Permission", {"for_value": ["like", "PERM-%"]})
        frappe.get_doc({"doctype": "Item", "item_code": "PERM-1", "item_name": "P"}).insert(ignore_permissions=True)

    def test_user_permission_on_item_mirrors_to_crm_product(self):
        frappe.get_doc({"doctype": "User Permission", "user": "Administrator",
                        "allow": "Item", "for_value": "PERM-1",
                        "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)
        self.assertTrue(frappe.db.exists("User Permission",
            {"user": "Administrator", "allow": "CRM Product", "for_value": "PERM-1"}))

    def test_user_permission_on_crm_product_mirrors_to_item(self):
        frappe.get_doc({"doctype": "User Permission", "user": "Administrator",
                        "allow": "CRM Product", "for_value": "PERM-1",
                        "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)
        self.assertTrue(frappe.db.exists("User Permission",
            {"user": "Administrator", "allow": "Item", "for_value": "PERM-1"}))

    def test_delete_user_permission_deletes_mirror(self):
        p = frappe.get_doc({"doctype": "User Permission", "user": "Administrator",
                            "allow": "Item", "for_value": "PERM-1",
                            "apply_to_all_doctypes": 1}).insert(ignore_permissions=True)
        p.delete(ignore_permissions=True)
        self.assertFalse(frappe.db.exists("User Permission",
            {"user": "Administrator", "allow": "CRM Product", "for_value": "PERM-1"}))
```

**Step 2: Run, expect FAIL.**

**Step 3: Copy `mirror_sync.py` verbatim from HD**

Source: `helpdesk/integrations/erpnext/mirror_sync.py` (158 lines in PR #3361). The only change:

```python
# At top of file, replace the HD import:
from crm.integrations.erpnext.utils import ALLOWED_DOCTYPES, find_target_for, should_sync
```

The `MirrorSyncMixin` itself is generic — no other edits needed.

**Step 4: Implement `user_permission.py`** (adapted from HD's `user_permission.py`):

```python
import frappe
from frappe.core.doctype.user_permission.user_permission import UserPermission
from frappe.utils import cstr

from crm.integrations.erpnext.mirror_sync import MirrorSyncMixin
from crm.fcrm.doctype.crm_product.sync_utils import same_site_sync_active


class CustomUserPermission(MirrorSyncMixin, UserPermission):
    """Mirror User Permissions between Item and CRM Product."""

    DOCTYPE_FIELD = "allow"
    VALUE_FIELD = "for_value"

    def before_validate(self):
        old = self.get_doc_before_save()
        if old and self.has_data_updated(old) and self.sync_active():
            self.delete_mirror_for(old)

    def after_insert(self):
        if self.should_mirror():
            self.create_mirror()

    def on_update(self):
        super().on_update()
        if not self.should_mirror():
            return
        old = self.get_doc_before_save()
        if old and self.has_data_updated(old):
            self.create_mirror()
        else:
            self.sync_state_to_mirror()

    def on_trash(self):
        super().on_trash()
        if not self.should_mirror():
            return
        mirror = self.find_mirror()
        if not mirror:
            return
        self.set_mirror_flags(mirror)
        mirror.delete(ignore_permissions=True)

    def dedup_filter(self, target_doctype: str, target_value: str) -> dict:
        # Match Frappe's 5-key dup check in validate_user_permission()
        return {
            **super().dedup_filter(target_doctype, target_value),
            "applicable_for": cstr(self.applicable_for),
            "apply_to_all_doctypes": self.apply_to_all_doctypes,
        }


def sync_user_permissions():
    """Bulk-sync User Permissions between Item and CRM Product. Idempotent."""
    if not same_site_sync_active():
        return

    product_perms = frappe.get_list("User Permission",
                                     filters={"allow": "CRM Product"}, fields=["*"])
    item_perms = frappe.get_list("User Permission",
                                  filters={"allow": "Item"}, fields=["*"])
    existing_product = {(p.user, p.for_value) for p in product_perms}
    existing_item = {(p.user, p.for_value) for p in item_perms}

    # Item → CRM Product
    for perm in item_perms:
        product = frappe.db.get_value("Item", perm.for_value, "crm_product_code")
        if not product or (perm.user, product) in existing_product:
            continue
        doc = frappe.get_doc({**perm, "doctype": "User Permission",
                              "allow": "CRM Product", "for_value": product})
        doc.flags.ignore_erpnext_sync = True
        doc.insert(ignore_permissions=True)
        existing_product.add((perm.user, product))

    # CRM Product → Item
    for perm in product_perms:
        item = frappe.db.get_value("CRM Product", perm.for_value, "erpnext_item_code")
        if not item or (perm.user, item) in existing_item:
            continue
        doc = frappe.get_doc({**perm, "doctype": "User Permission",
                              "allow": "Item", "for_value": item})
        doc.flags.ignore_erpnext_sync = True
        doc.insert(ignore_permissions=True)
        existing_item.add((perm.user, item))
```

**Step 5: Wire into `hooks.py` and `reconcile_job.py`**

```python
# hooks.py
override_doctype_class = {
    ...,
    "User Permission": "crm.integrations.erpnext.user_permission.CustomUserPermission",
}
```

```python
# reconcile_job.py — at end of run_reconciliation, before publish_realtime:
from crm.integrations.erpnext.user_permission import sync_user_permissions
sync_user_permissions()
```

**Step 6: Run, commit**

```bash
git add crm/integrations/erpnext/mirror_sync.py \
        crm/integrations/erpnext/user_permission.py \
        crm/hooks.py crm/fcrm/doctype/crm_product/reconcile_job.py \
        crm/fcrm/doctype/crm_product/test_product_item_sync.py
git commit -m "feat(product-sync): mirror User Permissions between Item and CRM Product"
```

---

## Task 11: CustomDocShare — 🟢 PENDING

**Files:**
- Create: `crm/integrations/erpnext/doc_share.py`
- Modify: `crm/hooks.py` — `override_doctype_class["DocShare"] = "crm.integrations.erpnext.doc_share.CustomDocShare"`
- Modify: `crm/fcrm/doctype/crm_product/reconcile_job.py:run_reconciliation` — call `sync_shared_docs()` at end

**Why:** Sharing an Item with user X should share the linked CRM Product with X too, and vice versa.

**Step 1: Failing tests** (mirror Task 10's tests for shape; replace `User Permission` with `DocShare`, `allow`→`share_doctype`, `for_value`→`share_name`).

**Step 2: Run, expect FAIL.**

**Step 3: Implement `doc_share.py`** — adapt HD's `doc_share.py` near-verbatim:

```python
import frappe
from frappe.core.doctype.docshare.docshare import DocShare

from crm.integrations.erpnext.mirror_sync import MirrorSyncMixin
from crm.fcrm.doctype.crm_product.sync_utils import same_site_sync_active


class CustomDocShare(MirrorSyncMixin, DocShare):
    DOCTYPE_FIELD = "share_doctype"
    VALUE_FIELD = "share_name"

    def before_validate(self):
        old = self.get_doc_before_save()
        if old and self.has_data_updated(old) and self.sync_active():
            self.delete_mirror_for(old)

    def after_insert(self):
        super().after_insert()
        if self.should_mirror():
            self.create_mirror()

    def on_update(self):
        if not self.should_mirror():
            return
        old = self.get_doc_before_save()
        if old and self.has_data_updated(old):
            self.create_mirror()
        else:
            self.sync_state_to_mirror()

    def on_trash(self):
        super().on_trash()
        if not self.should_mirror():
            return
        mirror = self.find_mirror()
        if not mirror:
            return
        self.set_mirror_flags(mirror)
        mirror.delete(ignore_permissions=True)

    def set_mirror_flags(self, mirror):
        super().set_mirror_flags(mirror)
        mirror.flags.ignore_share_permission = True


def sync_shared_docs():
    if not same_site_sync_active():
        return
    product_shares = frappe.get_list("DocShare",
                                      filters={"share_doctype": "CRM Product"}, fields=["*"])
    item_shares = frappe.get_list("DocShare",
                                   filters={"share_doctype": "Item"}, fields=["*"])
    existing_product = {(s.user, s.share_name) for s in product_shares}
    existing_item = {(s.user, s.share_name) for s in item_shares}

    for share in item_shares:
        product = frappe.db.get_value("Item", share.share_name, "crm_product_code")
        if not product or (share.user, product) in existing_product:
            continue
        doc = frappe.get_doc({**share, "doctype": "DocShare",
                              "share_doctype": "CRM Product", "share_name": product})
        doc.flags.ignore_share_permission = True
        doc.flags.ignore_erpnext_sync = True
        doc.insert(ignore_permissions=True)
        existing_product.add((share.user, product))

    for share in product_shares:
        item = frappe.db.get_value("CRM Product", share.share_name, "erpnext_item_code")
        if not item or (share.user, item) in existing_item:
            continue
        doc = frappe.get_doc({**share, "doctype": "DocShare",
                              "share_doctype": "Item", "share_name": item})
        doc.flags.ignore_share_permission = True
        doc.flags.ignore_erpnext_sync = True
        doc.insert(ignore_permissions=True)
        existing_item.add((share.user, item))
```

**Step 4: Wire + commit**

```bash
git add crm/integrations/erpnext/doc_share.py \
        crm/hooks.py crm/fcrm/doctype/crm_product/reconcile_job.py \
        crm/fcrm/doctype/crm_product/test_product_item_sync.py
git commit -m "feat(product-sync): mirror DocShares between Item and CRM Product"
```

---

## Final verification before PR

1. `bench --site analytics.localhost run-tests --module crm.fcrm.doctype.crm_product.test_product_item_sync` — all green.
2. Manual: enable integration on a fresh site with pre-existing dupes → confirm linking + reconciliation summary in Error Log.
3. Manual: create a CRM Product → confirm Item appears in ERPNext desk.
4. Manual: rename an Item → confirm CRM Product's `erpnext_item_code` follows.
5. Manual: delete an Item referenced in a Quotation → expect standard Frappe LinkExistsError on Item side.
6. Manual: delete an Item with no references → CRM Product unlink survives + banner appears.
7. Manual: delete a CRM Product whose Item is referenced → expect our `frappe.throw`.
8. Manual: create a User Permission for `Item: X` → confirm mirror on `CRM Product: X` appears, edit it → confirm mirror updates, delete it → confirm mirror gone.
9. Manual: share an Item with a teammate → confirm DocShare mirror on linked CRM Product.
10. `git log develop..HEAD --oneline` — confirm focused commits.

---

## Out of scope (separate plans)

- **Cross-site sync** (`is_erpnext_in_different_site = 1`) — disabled for products in this plan.
- **Manual "Sync Now" button** in settings (reconciliation runs on enable + via patch; manual trigger is a future addition).
- **Product image in list view thumbnails** — pure UI concern, separate ticket.
