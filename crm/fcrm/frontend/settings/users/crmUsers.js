// What the Users block offers one user for another; crm.api.user refuses the same and stays the boundary.

const ROLES = ['System Manager', 'Sales Manager', 'Sales User']

/** The users the block lists: every CRM user but Administrator, matching `query` by name or email. */
export function listedUsers(users, query = '') {
	const text = query.trim().toLowerCase()
	return users
		.filter((user) => user.name !== 'Administrator')
		.filter(
			(user) =>
				!text ||
				user.name.toLowerCase().includes(text) ||
				(user.full_name || '').toLowerCase().includes(text),
		)
}

/** The roles `viewer` may set on `user`, its current one included; none on their own or a locked row. */
export function roleChoices(viewer, user) {
	if (user.name === viewer.name || locked(viewer, user)) return []
	return ROLES.filter((role) => role === user.role || mayGive(viewer, role))
}

export function removable(viewer, user) {
	return user.name !== viewer.name && !locked(viewer, user)
}

/** The roles `viewer` may give a user they add. */
export function givenRoles(viewer) {
	return ROLES.filter((role) => mayGive(viewer, role))
}

/** The CRM role a holder of `roles` acts as: the highest one they hold. */
export function crmRole(roles) {
	return ROLES.find((role) => roles.includes(role)) ?? ''
}

/** `roles` with the CRM roles each one implies, as `crm.api.user.update_user_role` gives them. */
export function withImpliedRoles(roles) {
	const highest = ROLES.findIndex((role) => roles.includes(role))
	return [...new Set([...roles, ...(highest < 0 ? [] : ROLES.slice(highest))])]
}

function mayGive(viewer, role) {
	return viewer.role === 'System Manager' || role === 'Sales User'
}

function locked(viewer, user) {
	return user.role === 'System Manager' && viewer.role !== 'System Manager'
}
