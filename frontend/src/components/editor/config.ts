import {
  RichTextKit,
  Paragraph,
  HeadingGroup,
  Separator,
  Bold,
  Italic,
  BulletList,
  OrderedList,
  AlignLeft,
  AlignCenter,
  AlignRight,
  FontColor,
  InsertImage,
  InsertVideo,
  InsertLink,
  Blockquote,
  InlineCode,
  HorizontalRule,
  InsertTable,
  Strike,
  type MenuItem,
  type CommandMenuItem,
} from 'frappe-ui/editor'
import { useFileUpload } from 'frappe-ui'
import type { Extension } from '@tiptap/core'
import { markRaw, type MaybeRefOrGetter } from 'vue'
import EditorMoreMenu from '@/components/editor/EditorMoreMenu.vue'

/** A mentionable user as the editor expects it. `value` is the email; the editor
 *  stores it as `data-id`, which `extract_mentions` (crm/api/comment.py) reads. */
export interface MentionItem {
  value: string
  label: string
}

/**
 * Extension list for a CRM rich-text editor.
 *
 * Pass `mentions` as a getter, not a snapshot — the `@` list then stays in sync
 * as users load.
 */
export function buildEditorExtensions(
  options: {
    mentions?: MaybeRefOrGetter<MentionItem[]>
    starterKit?: Record<string, unknown>
    extra?: Extension[]
  } = {},
): Extension[] {
  return [
    RichTextKit.configure({
      heading: { levels: [2, 3, 4, 5, 6] },
      ...(options.mentions ? { mention: { items: options.mentions } } : {}),
      ...(options.starterKit ? { starterKit: options.starterKit } : {}),
    }),
    ...(options.extra ?? []),
  ]
}

/** Composer toolbar — ports the v0 `textEditorMenuButtons`. In-table operations
 *  now live in the contextual `EditorTableMenu` instead of a toolbar dropdown. */
export const fullToolbar: MenuItem[] = [
  Paragraph,
  HeadingGroup,
  Separator,
  Bold,
  Italic,
  Separator,
  BulletList,
  OrderedList,
  Separator,
  AlignLeft,
  AlignCenter,
  AlignRight,
  FontColor,
  Separator,
  InsertImage,
  InsertVideo,
  InsertLink,
  Blockquote,
  InlineCode,
  HorizontalRule,
  InsertTable,
]

/** Compact toolbar for inline/ghost fields (generic form fields, grid rows) —
 *  shown in a floating bubble on text selection rather than a fixed bar. */
export const bubbleToolbar: MenuItem[] = [Bold, Italic, Strike, InsertLink]

/** Rarer formatting, shown under the More (⋯) button of the form toolbar. */
export const moreToolbarItems: CommandMenuItem[] = [
  AlignLeft,
  AlignCenter,
  AlignRight,
  FontColor,
  InlineCode,
  HorizontalRule,
  InsertVideo,
  InsertTable,
]

const MoreMenu: CommandMenuItem = {
  label: 'More',
  icon: 'lucide-ellipsis',
  action: () => {},
  component: markRaw(EditorMoreMenu),
}

/** Toolbar for rich text fields in forms, short enough to fit a dialog. */
export const formToolbar: MenuItem[] = [
  HeadingGroup,
  Separator,
  Bold,
  Italic,
  Strike,
  Separator,
  BulletList,
  OrderedList,
  Separator,
  InsertLink,
  Blockquote,
  InsertImage,
  Separator,
  MoreMenu,
]

/** Upload handler for images/files dropped or pasted into an editor. */
export function uploadFile(
  file: File,
  doctype?: string,
  docname?: string,
  isPrivate = true,
) {
  return useFileUpload().upload(file, {
    private: isPrivate,
    doctype,
    docname,
  })
}
