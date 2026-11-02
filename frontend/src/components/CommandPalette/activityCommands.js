import CommentIcon from '@/components/Icons/CommentIcon.vue'
import EmailIcon from '@/components/Icons/EmailIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import { stripMarks } from '@/utils/markedText'

const SOURCES = {
  Comment: { label: 'Comment', icon: CommentIcon },
  'FCRM Note': { label: 'Note', icon: NoteIcon },
  Communication: { label: 'Email', icon: EmailIcon },
}

// A fixed rank keeps the index's order, and keeps typo-corrected hits that
// contain the query nowhere.
export function activityCommand(hit, open) {
  const source = SOURCES[hit.source_doctype]
  const title = stripMarks(hit.title)
  return {
    id: `activity-${hit.source_doctype}-${hit.source_name}`,
    title: title ? `${hit.parent_title} — ${title}` : hit.parent_title,
    translate: false,
    snippet: hit.snippet,
    subtitle: `${__(hit.route)} · ${__(source.label)}`,
    group: 'In activity',
    icon: source.icon,
    rank: 0,
    perform: () => open(hit),
  }
}
