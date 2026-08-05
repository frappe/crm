# PRD: Mutation Feedback — Visual Progress for Save / Create / Delete / Update

**Status:** ready-for-dev  
**Author:** Salim  
**Date:** 2026-08-04  
**Scope:** Vue frontend (`frontend/src/`)  
**Epic ID:** `epic-mutation-feedback`

---

## Problem Statement

Every create, save, update, and delete operation in the CRM fires an async network call. Currently most of these operations are **visually silent** — the triggering control (button, field, drag handle) shows no in-progress state while the call is in flight. Users:

- Cannot tell whether the action registered.
- May click again (double-fire risk on conversions and deletes).
- Get no feedback when the operation fails silently (rename, kanban drag, linked-doc unlink).

The Convert-to-Deal flow is the most egregious: clicking Convert shows nothing for 1–4 seconds, then redirects — no progress, no confirmation, no error surface if the call fails.

---

## Design Principles

1. **Every mutation that takes > 0 ms must produce a visual state change within the same frame the user acts.** Loading spinners on buttons, skeleton pulses on inline fields, or progress toasts — pick the right affordance per surface.

2. **Silence is indistinguishable from failure.** If a mutation succeeds silently, the user will click again. If it fails silently, they'll have no idea. Both paths destroy trust.

3. **Idempotency guard:** any button that triggers a network call must be `disabled` or `loading` from click until resolution to prevent double-fire.

4. **Error must always surface.** Every call must have a `.catch` or `onError` that shows a `toast.error`. No silent `.then`-only chains.

5. **Leverage what exists.** The codebase already has: `toast.promise`, `toast.success`, `toast.error`, `document.save.loading` (boolean on every `createDocumentResource`), and `<Button :loading="bool">` from frappe-ui. The fix for most gaps is threading these together — not building new infrastructure.

6. **Do not over-toast.** Inline field saves (SidePanelLayout) already fire a toast on every keystroke-triggered save. Consider suppressing the success toast for routine inline field edits (they always succeed) and reserving toasts for explicit user-initiated actions (modal saves, conversions, deletes).

---

## Component Vocabulary (existing — use, don't rebuild)

| Pattern | When to use |
|---|---|
| `<Button :loading="bool" disabled>` | Any button that triggers a single mutation — the button disables and shows a spinner while in flight |
| `toast.promise(call(...), { loading, success, error })` | Long-running or background calls where the user should see progress in the notification stack (delete, send, conversion) |
| `toast.error(msg)` | Catch handler for any failed call |
| `document.save.loading` | Boolean on every frappe-ui `createDocumentResource` — bind to the triggering control |
| Per-field spinner (inline) | `<Spinner v-if="document.save.loading" size="xs" />` adjacent to a field being saved; field becomes `readonly` while `save.loading` is true |

---

## Surface-by-Surface Specification

### S1 — Convert to Deal Modal

**File:** `frontend/src/components/Modals/ConvertToDealModal.vue`

**Current:** Convert button has no `:loading` prop. The `convertToDeal` async function awaits a server call for 1–4 s with no visual change.

**Required:**

```vue
<!-- script -->
const converting = ref(false)

async function convertToDeal() {
  if (converting.value) return          // idempotency guard
  converting.value = true
  try {
    let _deal = await call('crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal', { ... })
    // existing redirect logic
  } catch (e) {
    toast.error(e.messages?.[0] || __('Conversion failed'))
  } finally {
    converting.value = false
  }
}

<!-- template -->
<Button
  :label="__('Convert')"
  variant="solid"
  :loading="converting"
  :disabled="converting"
  @click="convertToDeal"
/>
```

**Acceptance criteria:**
- Button shows spinner and is non-clickable from click until redirect or error.
- On server error, toast.error fires and button re-enables. Modal stays open.
- Double-click cannot fire the call twice.

---

### S2 — Lost Reason Modal Save Button

**File:** `frontend/src/components/Modals/LostReasonModal.vue`

**Current:** Save button has no `:loading` prop. `document.save.loading` exists but is unused.

**Required:**

```vue
<Button
  variant="solid"
  :label="__('Save')"
  :loading="props.document.save.loading"
  :disabled="props.document.save.loading"
  @click="save"
/>
```

Also add an `onError` handler to the `save()` call if not already present:

```js
props.document.save.submit(null, {
  onError: (e) => toast.error(e.messages?.[0] || __('Failed to save'))
})
```

**Acceptance criteria:**
- Button spins while `document.save` is in flight.
- Error toasts on failure; modal stays open.

---

### S3 — Inline Field Save (SidePanelLayout)

**File:** `frontend/src/components/SidePanelLayout.vue`

**Current:** Every right-panel field edit triggers `document.save.submit`. The field stays interactive and editable during the in-flight save. Rapid edits can race. The global success toast fires for every single field change (noisy).

**Required:**

1. **Per-field loading indicator:** show a small spinner adjacent to the field being saved. Since `document.save.loading` is per-document (not per-field), track the active field:

```js
const savingField = ref(null)   // tracks which fieldname is currently saving

async function updateField(df, value) {
  savingField.value = df.fieldname
  document.doc[df.fieldname] = value
  document.save.submit(null, {
    onSuccess: () => {
      savingField.value = null
      emit('afterFieldChange', { [df.fieldname]: value })
    },
    onError: (e) => {
      savingField.value = null
      toast.error(e.messages?.[0] || __('Failed to save field'))
    }
  })
}
```

2. **Field lockout:** set the input to `readonly` / `disabled` while `savingField.value === df.fieldname`.

3. **Suppress routine inline success toast:** Remove or gate the global `toast.success('Document updated successfully')` in `data/document.js` for silent field saves. Instead surface a subtle check-icon animation on the field itself (or keep the toast but debounce it — only fire if no further save starts within 2 s). _Defer to implementation judgment; the key requirement is the field-level lockout and error toast._

**Acceptance criteria:**
- A small spinner appears beside (or inside) the field while its save is in flight.
- The field cannot be edited again until the current save resolves.
- On error, toast.error fires and the field reverts to its pre-edit value.
- Rapid edits do not enqueue racing saves.

---

### S4 — Lead / Deal Status Change and Field Update

**Files:** `frontend/src/pages/Lead.vue`, `frontend/src/pages/Deal.vue`

**Current:** `updateField`, `setLostReason`, `beforeStatusChange` all call `document.save.submit` with no loading state on the triggering dropdown or button.

**Required:**

- Thread `document.save.loading` to the status dropdown trigger and any "Save" call-to-action in the status change flow.
- While `document.save.loading` is true: disable the status dropdown and any field that is being saved.
- Error handling already partially exists (`onError: toast.error`) — verify it covers all three save paths.

**Acceptance criteria:**
- Status dropdown is non-interactive while a save is in flight.
- On save error, toast.error fires and the status reverts to its previous value.

---

### S5 — Task Delete and Task Status Change

**Files:** `frontend/src/components/Activities/AllModals.vue`, `frontend/src/pages/Tasks.vue`

**Current:** Both `deleteTask` and `updateTaskStatus` are bare `call(...)` or `call(...).then(reload)` with zero feedback.

**Required (deleteTask):**

```js
async function deleteTask(taskName) {
  await toast.promise(
    call('frappe.client.delete', { doctype: 'CRM Task', name: taskName }),
    {
      loading: __('Deleting task…'),
      success: __('Task deleted'),
      error: (e) => e?.messages?.[0] || __('Failed to delete task'),
    }
  )
  reload()
}
```

**Required (updateTaskStatus):**

```js
async function updateTaskStatus(taskName, status) {
  await toast.promise(
    call('frappe.client.set_value', { doctype: 'CRM Task', name: taskName, fieldname: 'status', value: status }),
    {
      loading: __('Updating…'),
      success: __('Status updated'),
      error: (e) => e?.messages?.[0] || __('Failed to update status'),
    }
  )
  reload()
}
```

**Acceptance criteria:**
- Task delete shows "Deleting task…" toast while in flight, then success or error.
- Task status change shows "Updating…" toast while in flight, then success or error.
- Neither operation can be double-fired.

---

### S6 — Note Delete (Notes.vue page-level)

**File:** `frontend/src/pages/Notes.vue`

**Current:** `deleteNote` at line 158 calls `frappe.client.delete` with no toast and no loading indicator. (`NoteArea.vue` uses `toast.promise` correctly — match that pattern.)

**Required:** Mirror the `NoteArea.vue` pattern:

```js
async function deleteNote(noteName) {
  await toast.promise(
    call('frappe.client.delete', { doctype: 'FCRM Note', name: noteName }),
    {
      loading: __('Deleting note…'),
      success: __('Note deleted'),
      error: (e) => e?.messages?.[0] || __('Failed to delete note'),
    }
  )
  reload()
}
```

**Acceptance criteria:**
- Toast shows "Deleting note…" during deletion, resolves to success or error message.

---

### S7 — Comment Delete

**File:** `frontend/src/components/Activities/CommentArea.vue`

**Current:** `saveEdit` correctly uses a `saving` ref and `:loading`. `deleteComment` does not — it's a bare `await call(...)` with no loading on the menu item.

**Required:**

```js
const deletingComment = ref(false)

async function deleteComment(commentName) {
  if (deletingComment.value) return
  deletingComment.value = true
  try {
    await call('frappe.client.delete', { doctype: 'Comment', name: commentName })
    reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Failed to delete comment'))
  } finally {
    deletingComment.value = false
  }
}
```

Bind `deletingComment` to the delete menu item's disabled/loading state.

**Acceptance criteria:**
- Delete menu item is non-interactive while delete is in flight.
- On error, toast.error fires.

---

### S8 — Delete Linked Doc Modal

**File:** `frontend/src/components/DeleteLinkedDocModal.vue`

**Current:** Two bugs:
1. `isDealCreating` is referenced on the Delete button's `:loading` prop but is never declared — always `undefined`.
2. `deleteDoc` (line 251) has no loading state, no success toast, no `.catch`.
3. `unlinkLinkedDoc` / `removeDocLinks` have no error handling.

**Required:**

1. Declare or remove `isDealCreating`. If the button is for deleting, bind the actual loading state:

```js
const isDeleting = ref(false)
```

```vue
<Button
  :label="__('Delete')"
  variant="solid"
  :loading="isDeleting"
  :disabled="isDeleting"
  @click="deleteDoc"
/>
```

2. Wrap `deleteDoc`:

```js
async function deleteDoc() {
  isDeleting.value = true
  try {
    await call('frappe.client.delete', { doctype, name })
    toast.success(__('Document deleted'))
    emit('success')
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Failed to delete document'))
  } finally {
    isDeleting.value = false
  }
}
```

3. Add `.catch(e => toast.error(...))` to `unlinkLinkedDoc` and `removeDocLinks`.

**Acceptance criteria:**
- Delete button shows spinner and is non-clickable while in flight.
- Success and error both produce toasts.
- Unlink errors produce a toast.

---

### S9 — Organization Rename

**File:** `frontend/src/pages/Organization.vue` (line 466)

**Current:** `call('frappe.client.rename_doc', ...).then(router.push)` — no `.catch`, no loading state on the name field.

**Required:**

```js
const isRenaming = ref(false)

async function renameOrganization(newName) {
  if (isRenaming.value) return
  isRenaming.value = true
  try {
    await call('frappe.client.rename_doc', {
      doctype: 'CRM Organization',
      old_name: organization.doc.name,
      new_name: newName,
      merge: false,
    })
    router.push({ name: 'Organization', params: { organizationId: newName } })
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Rename failed'))
  } finally {
    isRenaming.value = false
  }
}
```

Show a spinner on the name field input while `isRenaming` is true and set it to `readonly`.

**Acceptance criteria:**
- Name field is locked during rename.
- On error, toast.error fires, field re-enables, value reverts.
- On success, redirect happens normally.

---

### S10 — Assign To Popover

**File:** `frontend/src/components/AssignToBody.vue`

**Current:** `addAssignees.submit` and `removeAssignees.submit` have no loading indicator in the popover.

**Required:**

The resources already expose a `.loading` boolean from frappe-ui. Thread it:

```vue
<Button
  :label="__('Apply')"
  :loading="addAssignees.loading || removeAssignees.loading"
  :disabled="addAssignees.loading || removeAssignees.loading"
  @click="save"
/>
```

Also add `onError`:

```js
addAssignees.submit(users, {
  onError: (e) => toast.error(e?.messages?.[0] || __('Failed to assign'))
})
```

**Acceptance criteria:**
- Assign/remove buttons spin while calls are in flight.
- Errors produce a toast.

---

### S11 — Kanban Card Drag Status Change

**File:** `frontend/src/components/ViewControls.vue` (line 988)

**Current:** `call('frappe.client.set_value', ...)` is not awaited and has no error handler. If the server rejects the status change (permission error, validation), the card stays in the wrong column with no feedback.

**Required:**

```js
async function onDrop(data) {
  try {
    await call('frappe.client.set_value', {
      doctype: props.doctype,
      name: data.item,
      fieldname: view.value.column_field,
      value: data.to,
    })
    // optimistic UI already updated — no success toast needed (too noisy on kanban)
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Failed to update status'))
    // rollback: move card back to data.from column
    revertCardMove(data)
  }
}
```

The `revertCardMove` implementation should restore the card to its original column in the view data. Exact implementation depends on the kanban data structure — the key requirement is that the card does not silently stay in the wrong column.

**Acceptance criteria:**
- If server call fails, toast.error fires with the error message.
- Card reverts to its original column on failure.
- No success toast on drag (optimistic UI is sufficient for the happy path).

---

### S12 — Deal Contact Add / Remove / Set Primary

**File:** `frontend/src/pages/Deal.vue` (lines 756, 767, 778)

**Current:** All three operations already show result toasts (`toast.success`, `toast.error`). The only gap is no in-flight spinner on the triggering dropdown item.

**Required:**

Add a `contactAction` ref to track which contact operation is in flight:

```js
const contactActionLoading = ref(false)

async function addContact(contact) {
  contactActionLoading.value = true
  try {
    await call('crm.fcrm.doctype.crm_deal.crm_deal.add_contact', { deal: props.dealId, contact })
    toast.success(__('Contact added'))
    reload()
  } catch (e) {
    toast.error(e?.messages?.[0] || __('Failed to add contact'))
  } finally {
    contactActionLoading.value = false
  }
}
// mirror for removeContact and setPrimaryContact
```

Disable the contact picker / dropdown while `contactActionLoading` is true.

**Acceptance criteria:**
- Contact add/remove/set-primary controls are non-interactive while the call is in flight.
- Errors continue to produce toast.error (already present — keep).

---

## Stories

The following stories implement the above. Each is an independent vertical slice.

| Story ID | Surface | Effort |
|---|---|---|
| `mf-s1-convert-to-deal` | ConvertToDealModal loading state + error surface | XS |
| `mf-s2-lost-reason-modal` | LostReasonModal Save button loading | XS |
| `mf-s3-inline-field-save` | SidePanelLayout per-field spinner + lockout | S |
| `mf-s4-status-change` | Lead/Deal status dropdown + field save loading | S |
| `mf-s5-task-mutations` | Task delete + status change toast.promise | XS |
| `mf-s6-note-delete` | Notes.vue delete toast.promise | XS |
| `mf-s7-comment-delete` | CommentArea.vue delete loading + error | XS |
| `mf-s8-delete-linked-doc` | DeleteLinkedDocModal loading fix + error surface | S |
| `mf-s9-org-rename` | Organization rename loading + rollback | XS |
| `mf-s10-assign-to` | AssignToBody submit loading | XS |
| `mf-s11-kanban-drag` | Kanban drag error surface + card rollback | S |
| `mf-s12-deal-contacts` | Deal contact mutations loading state | XS |

Stories S1, S2, S5, S6, S7, S9, S10 are pure mechanical (< 30 lines each).  
Stories S3, S4, S8, S11, S12 require a small amount of state threading.

---

## Out of Scope

- Optimistic UI updates (beyond the existing kanban drag). Server-confirmed state is correct for a CRM.
- Global mutation loading bar (e.g., top progress bar NProgress-style) — individual surface feedback is sufficient and more informative.
- Undo/undo-snackbar for deletes — future story.
- Mobile views (`MobileLead.vue`, `MobileDeal.vue`, etc.) — separate audit; follow-up after desktop surfaces are fixed.

---

## Verification per Story

Each story's PR must include:
- **Before/after screenshot or screen recording** of the surface showing the loading state.
- `pnpm build` passes with zero warnings.
- Manual browser test: trigger the operation on a slow network (DevTools → Network throttling: Slow 3G) and confirm the loading state is visible.
