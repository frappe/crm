/**
 * Automation Flow steps are stored flat: a child row points at the `idx` of the `If` row it
 * belongs to (`parent_step`) and which arm it sits in (`branch`). The builder edits a tree
 * instead, and flattens it on save — that is what keeps `parent_step` pointing at an earlier
 * row and every branch child ordered after its `If`.
 */

// The canvas runs top to bottom: each step is a row, an If's arms split horizontally.
const ROW_HEIGHT = 150
const BRANCH_OFFSET = 280

let uid = 0

export function newStep(values = {}) {
  return {
    _id: `step-${++uid}`,
    doctype: 'Automation Action',
    step_type: 'Action',
    action_type: '',
    step_key: '',
    target: 'trigger',
    output_alias: '',
    params: '{}',
    step_condition: '',
    related_condition: '',
    children: { If: [], Else: [] },
    ...values,
  }
}

export function toTree(rows = []) {
  const nodes = rows.map((row) =>
    newStep({ ...row, children: { If: [], Else: [] } }),
  )
  const byIdx = new Map(
    nodes.map((node, index) => [rowIdx(rows[index], index), node]),
  )
  const roots = []
  nodes.forEach((node, index) => {
    const parent = rows[index].parent_step && byIdx.get(rows[index].parent_step)
    if (parent) parent.children[armOf(rows[index])].push(node)
    else roots.push(node)
  })
  return roots
}

export function toRows(tree) {
  const rows = []
  appendRows(tree, rows, 0, '')
  return rows
}

function appendRows(nodes, rows, parentIdx, branch) {
  nodes.forEach((node) => {
    const { children, ...row } = node
    delete row._id
    rows.push({
      ...row,
      idx: rows.length + 1,
      parent_step: parentIdx,
      branch: parentIdx ? branch : '',
    })
    const idx = rows.length
    if (node.step_type !== 'If') return
    appendRows(children.If, rows, idx, 'If')
    appendRows(children.Else, rows, idx, 'Else')
  })
}

/** Depth-first list of every node with its canvas position, in flattened (idx) order. */
export function layoutSteps(tree) {
  const placed = []
  place(tree, ROW_HEIGHT, 0, placed)
  return placed
}

// Arms of a nested If sit closer together than their parent's, keeping nested branches compact.
function place(nodes, y, x, placed, spread = BRANCH_OFFSET) {
  nodes.forEach((node) => {
    placed.push({ node, position: { x, y } })
    y += ROW_HEIGHT
    if (node.step_type !== 'If') return
    const ifEnd = place(node.children.If, y, x - spread, placed, spread / 2)
    const elseEnd = place(node.children.Else, y, x + spread, placed, spread / 2)
    y = Math.max(ifEnd, elseEnd)
  })
  return y
}

/** The array a node lives in, so callers can insert a sibling or splice it out. */
export function listOf(tree, node) {
  if (tree.includes(node)) return tree
  for (const candidate of tree) {
    if (candidate.step_type !== 'If') continue
    const found =
      listOf(candidate.children.If, node) ||
      listOf(candidate.children.Else, node)
    if (found) return found
  }
  return null
}

export function removeStep(tree, node) {
  const list = listOf(tree, node)
  if (list) list.splice(list.indexOf(node), 1)
}

export function insertAfter(tree, node, step) {
  const list = listOf(tree, node) || tree
  list.splice(list.indexOf(node) + 1, 0, step)
  return step
}

/** Steps that run before `node`, i.e. the ones whose outputs it may reference. */
export function stepsBefore(tree, node) {
  const earlier = []
  // A node that isn't in this tree has no earlier steps — never fall back to "all of them",
  // or the target picker would offer outputs that don't exist yet at that point in the run.
  return collectBefore(tree, node, earlier) ? earlier : []
}

function collectBefore(nodes, target, earlier) {
  for (const node of nodes) {
    if (node === target) return true
    earlier.push(node)
    if (node.step_type !== 'If') continue
    if (collectBefore(node.children.If, target, earlier)) return true
    if (collectBefore(node.children.Else, target, earlier)) return true
  }
  return false
}

function armOf(row) {
  return row.branch === 'Else' ? 'Else' : 'If'
}

function rowIdx(row, index) {
  return row.idx || index + 1
}
