// CRM Organization is named by `organization_name`, so an edit to it renames the record, as CRM v1 does.

/** The `organization_name` field handler: renames the saved record to the edited name. */
export async function renameFromOrganizationName(page) {
	const name = (page.doc.organization_name ?? '').trim()
	if (page.isNew || name === page.docname) return
	if (name && (await page.rename(name))) return
	// The rename saved the edited name first; a refused one must not leave it apart from the record's name.
	page.doc.organization_name = page.docname
	if (page.saved.organization_name !== page.docname) await page.save()
}
