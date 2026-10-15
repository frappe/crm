import Icon from '@/components/Icon.vue'
import { h } from 'vue'

// Tailwind only makes a lucide-* class for names written in the source, so icon names known only at runtime render from the sprite
export function spriteIcon(icon) {
  return typeof icon === 'string' && icon ? () => h(Icon, { icon }) : icon
}
