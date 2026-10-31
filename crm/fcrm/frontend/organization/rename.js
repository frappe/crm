// CRM Organization is named by `organization_name`, so an edit to it renames the record, as CRM v1 does.

export async function renameFromOrganizationName(page) {
	if (page.isNew) return
	const name = (page.doc.organization_name ?? '').trim()
	if (name && name !== page.docname && (await page.rename(name))) return
	// `page.rename` saves the edited name first, so a refused rename must put the record's name back.
	page.doc.organization_name = page.docname
	if (page.saved.organization_name !== page.docname) await page.save()
}
