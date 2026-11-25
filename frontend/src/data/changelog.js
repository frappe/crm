import { computed, ref } from 'vue'
import { call } from 'frappe-ui'
import { useUserSettings } from '@/data/userSettings'

// Entries are Markdown files in src/changelog/ with `title`, `version` and an optional
// `media` file in the frontmatter. New entries use `version: unreleased`; the release
// stamps the version and date (.github/helpers/stamp_changelog.py). A `<name>.dark.<ext>`
// beside the media file is shown in dark mode.

const sources = import.meta.glob('../changelog/*.md', {
  eager: true,
  query: '?raw',
  import: 'default',
})
const mediaUrls = import.meta.glob(
  '../changelog/*.{png,jpg,jpeg,gif,webp,mp4,webm}',
  { eager: true, query: '?url', import: 'default' },
)

const VIDEO_EXTENSIONS = ['mp4', 'webm']
const NEW_FOR_DAYS = 30
const SETTINGS_DOCTYPE = 'FCRM Settings'
const SEEN_KEY = 'changelog_seen'

export const changelogEntries = Object.entries(sources)
  .map(([path, source]) => parseEntry(path, source))
  .sort(compareEntries)

export const changelogReleases = groupByRelease(changelogEntries)

const { get: getUserSettings, save: saveUserSettings } = useUserSettings()
const seenEntryIds = ref(null)
const seenLoaded = ref(false)

const unseenEntries = computed(() => {
  if (!seenLoaded.value) return []
  const seen = seenEntryIds.value
  if (Array.isArray(seen)) {
    return changelogEntries.filter((entry) => !seen.includes(entry.id))
  }
  return changelogEntries.filter(isRecent)
})

export const hasUnseenEntries = computed(() => unseenEntries.value.length > 0)

export const showChangelogDialog = ref(false)

export function openChangelog() {
  showChangelogDialog.value = true
  seenEntryIds.value = changelogEntries.map((entry) => entry.id)
  saveUserSettings(SETTINGS_DOCTYPE, SEEN_KEY, seenEntryIds.value)
}

export async function openChangelogIfReleased(user) {
  const [settings, creation] = await Promise.all([
    getUserSettings(SETTINGS_DOCTYPE),
    getUserCreation(user),
  ])
  seenEntryIds.value = settings[SEEN_KEY] ?? null
  seenLoaded.value = true
  if (unseenEntries.value.some((entry) => releasedAfter(entry, creation))) {
    openChangelog()
  }
}

async function getUserCreation(user) {
  const { creation } = await call('frappe.client.get_value', {
    doctype: 'User',
    filters: user,
    fieldname: 'creation',
  })
  return creation
}

// New users only see releases that shipped after they joined
function releasedAfter(entry, creation) {
  return Boolean(entry.date && creation && entry.date > creation.slice(0, 10))
}

function parseEntry(path, source) {
  const id = path.split('/').pop().replace(/\.md$/, '')
  const { fields, body } = splitFrontmatter(source)
  const version =
    fields.version && fields.version !== 'unreleased'
      ? fields.version
      : undefined
  return {
    id,
    title: fields.title || id,
    version,
    date: version ? fields.date : undefined,
    media: fields.media ? resolveMedia(fields.media) : undefined,
    body,
  }
}

function splitFrontmatter(source) {
  const match = source.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/)
  if (!match) return { fields: {}, body: source }

  const fields = {}
  for (const line of match[1].split('\n')) {
    const separator = line.indexOf(':')
    if (separator === -1) continue
    fields[line.slice(0, separator).trim()] = line.slice(separator + 1).trim()
  }
  return { fields, body: match[2] }
}

function resolveMedia(fileName) {
  const url = mediaUrls[`../changelog/${fileName}`]
  if (!url) return undefined
  const extension = fileName.split('.').pop().toLowerCase()
  const darkFileName = fileName.replace(/\.[^.]+$/, `.dark.${extension}`)
  return {
    url,
    darkUrl: mediaUrls[`../changelog/${darkFileName}`],
    kind: VIDEO_EXTENSIONS.includes(extension) ? 'video' : 'image',
  }
}

function compareEntries(a, b) {
  if (!a.version || !b.version) {
    return Number(Boolean(a.version)) - Number(Boolean(b.version))
  }
  return compareVersions(b.version, a.version) || a.title.localeCompare(b.title)
}

function compareVersions(a, b) {
  const left = a.split('.').map(Number)
  const right = b.split('.').map(Number)
  for (let i = 0; i < Math.max(left.length, right.length); i++) {
    const difference = (left[i] ?? 0) - (right[i] ?? 0)
    if (difference) return difference
  }
  return 0
}

function groupByRelease(entries) {
  const releases = []
  for (const entry of entries) {
    const last = releases[releases.length - 1]
    if (last && last.version === entry.version) {
      last.entries.push(entry)
    } else {
      releases.push({
        version: entry.version,
        date: entry.date,
        entries: [entry],
      })
    }
  }
  return releases
}

function isRecent(entry) {
  if (!entry.date) return true
  const ageInDays = (Date.now() - new Date(entry.date).getTime()) / 86_400_000
  return ageInDays <= NEW_FOR_DAYS
}
