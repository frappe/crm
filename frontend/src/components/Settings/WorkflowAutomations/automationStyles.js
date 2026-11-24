import { registerAutomationStyles } from '@framework/ui/components/AutomationBuilder'
import AlarmIcon from '~icons/lucide/alarm-clock'
import BadgeCheckIcon from '~icons/lucide/badge-check'
import ConvertIcon from '~icons/lucide/handshake'
import DealLostIcon from '~icons/lucide/circle-x'
import EmailIcon from '~icons/lucide/mail'
import InboxIcon from '~icons/lucide/inbox'
import NotifyIcon from '~icons/lucide/bell-ring'
import ScoreIcon from '~icons/lucide/gauge'
import StageIcon from '~icons/lucide/git-branch'
import TemperatureIcon from '~icons/lucide/thermometer'

registerAutomationStyles({
  actions: {
    SendCRMNotification: { icon: NotifyIcon, tone: 'amber' },
    AdjustLeadScore: { icon: ScoreIcon, tone: 'orange' },
    SetLeadTemperature: { icon: TemperatureIcon, tone: 'red' },
    ConvertLeadToDeal: { icon: ConvertIcon, tone: 'purple' },
    SendCRMEmail: { icon: EmailIcon, tone: 'violet' },
  },
  events: {
    'crm.prospect_message_sent': { icon: EmailIcon, tone: 'blue' },
    'crm.prospect_message_received': { icon: InboxIcon, tone: 'teal' },
    'crm.lead_qualified': { icon: BadgeCheckIcon, tone: 'green' },
    'crm.lead_converted': { icon: ConvertIcon, tone: 'purple' },
    'crm.deal_stage_changed': { icon: StageIcon, tone: 'violet' },
    'crm.deal_won': { icon: ConvertIcon, tone: 'green' },
    'crm.deal_lost': { icon: DealLostIcon, tone: 'red' },
    'crm.task_overdue': { icon: AlarmIcon, tone: 'amber' },
  },
})
