import { call, toast } from 'frappe-ui'
import { nextTick } from 'vue'
import { copyToClipboard } from '@/utils'
import { usersStore } from '@/stores/users'

export function recordCommands(context) {
  return [
    assignCommand(context),
    ...assignToMeCommand(context),
    commentCommand(context),
    ...templateCommand(context),
    ...createCommands(context),
    attachCommand(context),
    tabCommand(context),
    ...tabFlatCommands(context),
    ...copyCommands(context),
  ]
}

function id(context, suffix) {
  return `${context.group.toLowerCase()}-${suffix}`
}

function assignCommand(context) {
  return {
    id: id(context, 'assign'),
    title: 'Assign to',
    group: context.group,
    icon: 'user-plus',
    keywords: 'assignee owner delegate',
    children: async () => assigneeChildren(context),
  }
}

function assigneeChildren(context) {
  const { users } = usersStore()
  return (users.data?.crmUsers || []).map((user) => ({
    id: `assign-${user.name}`,
    title: user.full_name || user.name,
    translate: false,
    subtitle: user.name,
    checked: isAssigned(context, user.name),
    perform: () => toggleAssignee(context, user.name),
  }))
}

function assignToMeCommand(context) {
  const { getUser } = usersStore()
  const me = getUser('')
  if (!me?.name || isAssigned(context, me.name)) return []
  return [
    {
      id: id(context, 'assign-me'),
      title: 'Assign to me',
      group: context.group,
      icon: 'user-check',
      keywords: 'assign myself mine',
      perform: () => toggleAssignee(context, me.name),
    },
  ]
}

function isAssigned(context, user) {
  return Boolean(context.assignees.data?.some((a) => a.name === user))
}

async function toggleAssignee(context, user) {
  const assigned = isAssigned(context, user)
  try {
    await (assigned ? removeAssignee : addAssignee)(context, user)
    context.assignees.reload()
  } catch (error) {
    toast.error(error?.messages?.[0] || __('Unable to update assignment'))
  }
}

function addAssignee(context, user) {
  return call('frappe.desk.form.assign_to.add', {
    doctype: context.doctype,
    name: context.docname,
    assign_to: [user],
  })
}

function removeAssignee(context, user) {
  return call('crm.api.doc.remove_assignments', {
    doctype: context.doctype,
    name: context.docname,
    assignees: [user],
  })
}

function commentCommand(context) {
  return {
    id: id(context, 'comment'),
    title: 'Add comment',
    group: context.group,
    icon: 'message-square',
    keywords: 'note remark discuss',
    perform: () => openCommentBox(context),
  }
}

function openCommentBox(context) {
  const activities = context.activities()
  if (!activities) return
  activities.changeTabTo('comments')
  // The box may still be mounting after the tab switch; retry until it's there.
  const open = (attempt = 0) => {
    const box = activities.emailBox
    if (box?.openCommentBox) return box.openCommentBox()
    if (attempt < 5) nextTick(() => open(attempt + 1))
  }
  nextTick(() => open())
}

function templateCommand(context) {
  if (!context.hasEmail()) return []
  return [
    {
      id: id(context, 'email-template'),
      title: 'Insert email template',
      group: context.group,
      icon: 'notepad-text',
      keywords: 'saved reply canned response',
      perform: () => openEmailTemplates(context),
    },
  ]
}

async function openEmailTemplates(context) {
  context.openEmailBox()
  await nextTick()
  context.activities()?.emailBox?.editor?.openTemplateSelector?.()
}

function createCommands(context) {
  return [
    ['task', 'Create task', 'circle-check-big', (m) => m.showTask()],
    ['note', 'Create note', 'notebook-pen', (m) => m.showNote()],
    ['call-log', 'Log a call', 'phone', (m) => m.createCallLog()],
  ].map(([key, title, icon, run]) => ({
    id: id(context, key),
    title,
    group: context.group,
    icon,
    keywords: `new add ${key} on this ${context.group}`,
    perform: () => withModals(context, run),
  }))
}

function withModals(context, run) {
  const modals = context.activities()?.modalRef
  if (modals) run(modals)
}

function attachCommand(context) {
  return {
    id: id(context, 'attach'),
    title: 'Attach a file',
    group: context.group,
    icon: 'paperclip',
    keywords: 'upload document image',
    perform: context.openFileUploader,
  }
}

function tabCommand(context) {
  return {
    id: id(context, 'tabs'),
    title: 'Go to tab',
    group: context.group,
    icon: 'panels-top-left',
    keywords: 'switch section view',
    children: async () => tabChildren(context, false),
  }
}

// Flat rows so "emails" jumps straight to the tab without drilling in.
function tabFlatCommands(context) {
  return tabChildren(context, true)
}

function tabChildren(context, flat) {
  return (context.tabs.value || []).map((tab) => ({
    id: `${id(context, 'tab')}-${tab.name}${flat ? '-flat' : ''}`,
    title: flat ? __('Go to {0}', [tab.label]) : tab.label,
    translate: false,
    group: flat ? context.group : undefined,
    icon: tab.icon,
    hideWhenEmpty: flat,
    keywords: tab.name,
    perform: () => context.changeTabTo(tab.name.toLowerCase()),
  }))
}

function copyCommands(context) {
  return [
    {
      id: id(context, 'copy-id'),
      title: 'Copy ID',
      group: context.group,
      icon: 'hash',
      keywords: 'clipboard name reference',
      perform: () => copyToClipboard(context.docname),
    },
    {
      id: id(context, 'copy-link'),
      title: 'Copy link',
      group: context.group,
      icon: 'link',
      keywords: 'clipboard url share',
      perform: () => copyToClipboard(window.location.href),
    },
  ]
}
