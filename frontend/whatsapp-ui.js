import { execFileSync } from 'child_process'
import fs from 'fs'
import path from 'path'

// The whatsapp release that CRM builds @whatsapp/ui from when the app is not beside CRM,
// as in the prebuilt assets. Bump it when CRM starts using code from a newer release.
const WHATSAPP_TAG = 'v1.4.0'

const sibling = path.resolve(import.meta.dirname, '../../whatsapp')
const pinned = path.resolve(
  import.meta.dirname,
  '.cache/whatsapp',
  WHATSAPP_TAG,
)

// The whatsapp app is optional on a site, so CRM always builds its WhatsApp screens and
// shows them only where the app is installed.
export function whatsappUISource() {
  const checkout = fs.existsSync(path.join(sibling, 'ui/src'))
    ? sibling
    : clonePinnedRelease()
  return path.join(checkout, 'ui/src')
}

function clonePinnedRelease() {
  if (!fs.existsSync(path.join(pinned, 'ui/src'))) {
    fs.rmSync(pinned, { recursive: true, force: true })
    execFileSync(
      'git',
      [
        'clone',
        '--quiet',
        '--depth',
        '1',
        '--branch',
        WHATSAPP_TAG,
        'https://github.com/frappe/whatsapp',
        pinned,
      ],
      { stdio: 'inherit' },
    )
  }
  return pinned
}
