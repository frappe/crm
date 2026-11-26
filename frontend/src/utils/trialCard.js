import { formatDate } from '@/utils'

const URGENT_DAYS = 3

function endsInTitle(daysLeft) {
  if (daysLeft <= 0) return __('Your trial ends today')
  if (daysLeft === 1) return __('Your trial ends tomorrow')
  return __('Your trial ends in {0} days', [String(daysLeft)])
}

export function trialCardContent(trial) {
  if (trial.state === 'Ended') {
    return {
      theme: 'red',
      title: __('Your trial has ended'),
      description: trial.deletes_on
        ? __('Your site will be deleted on {0}. Choose a plan to keep it.', [
            formatDate(trial.deletes_on, 'D MMM'),
          ])
        : __('Choose a plan to keep using your site.'),
      action: __('Choose a plan'),
      dismissible: false,
    }
  }
  if (trial.held) {
    return {
      theme: 'amber',
      title: __('Your plan is over your spending limit'),
      description: __(
        'Raise the limit or choose a smaller plan to end your trial.',
      ),
      action: __('Manage billing'),
      dismissible: true,
    }
  }
  return {
    theme: trial.days_left <= URGENT_DAYS ? 'amber' : 'gray',
    title: endsInTitle(trial.days_left),
    description: __('Choose a plan to keep your site after the trial.'),
    action: __('Choose a plan'),
    dismissible: true,
  }
}
