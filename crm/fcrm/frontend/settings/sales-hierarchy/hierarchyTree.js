// The rank and placeable-role rules are UI-only, as in CRM v1; the server refuses only loops and duplicate users.

const ROLE_RANK = { 'System Manager': 0, 'Sales Manager': 0, 'Sales User': 1 }
const PLACEABLE_ROLES = ['Sales Manager', 'Sales User']

/** The rows to draw, parents before their reports, each with its depth and its user's name, image and role. */
export function treeRows(nodes, users, query = '') {
	const byUser = new Map(users.map((user) => [user.name, user]))
	const children = childrenByManager(nodes)
	const rows = []
	const visit = (node, depth) => {
		const reports = children.get(node.name) || []
		const user = byUser.get(node.user) || {}
		const row = {
			...node,
			depth,
			full_name: user.full_name || node.full_name || node.user,
			user_image: user.user_image,
			role: user.role || '',
			reports: reports.length,
		}
		const start = rows.push(row)
		reports.forEach((child) => visit(child, depth + 1))
		if (!matches(row, query) && rows.length === start) rows.pop()
	}
	roots(nodes).forEach((node) => visit(node, 0))
	return rows
}

/** The nodes `node` may report to: not itself or one of its own reports, and not ranked below it. */
export function managerChoices(nodes, node, users) {
	const children = childrenByManager(nodes)
	const below = new Set()
	const collect = (each) => {
		below.add(each.name)
		;(children.get(each.name) || []).forEach(collect)
	}
	collect(node)
	const rank = ranker(users)
	return nodes.filter((each) => !below.has(each.name) && rank(each.user) <= rank(node.user))
}

/** The CRM users that may join under `manager` (a node, or null for the top level). */
export function addCandidates(users, nodes, manager) {
	const placed = new Set(nodes.map((node) => node.user))
	const floor = manager ? ranker(users)(manager.user) : 0
	return users.filter(
		(user) =>
			PLACEABLE_ROLES.includes(user.role) &&
			!placed.has(user.name) &&
			ROLE_RANK[user.role] >= floor
	)
}

export function reportsOf(nodes, node) {
	return nodes.filter((each) => each.reports_to === node.name)
}

function roots(nodes) {
	const names = new Set(nodes.map((node) => node.name))
	return nodes.filter((node) => !node.reports_to || !names.has(node.reports_to))
}

function childrenByManager(nodes) {
	const children = new Map()
	for (const node of nodes) {
		if (!node.reports_to) continue
		if (!children.has(node.reports_to)) children.set(node.reports_to, [])
		children.get(node.reports_to).push(node)
	}
	return children
}

function ranker(users) {
	const roles = new Map(users.map((user) => [user.name, user.role]))
	return (name) => ROLE_RANK[roles.get(name)] ?? 1
}

function matches(row, query) {
	const text = query.trim().toLowerCase()
	return (
		!text || row.user.toLowerCase().includes(text) || row.full_name.toLowerCase().includes(text)
	)
}
