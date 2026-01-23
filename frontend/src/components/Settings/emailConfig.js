import { validateEmail } from '../../utils'

import LogoGmail from '@/images/gmail.png'
import LogoOutlook from '@/images/outlook.png'
import LogoSendgrid from '@/images/sendgrid.png'
import LogoSparkpost from '@/images/sparkpost.webp'
import LogoYahoo from '@/images/yahoo.png'
import LogoYandex from '@/images/yandex.png'
import LogoFrappeMail from '@/images/frappe-mail.svg'

const fixedFields = [
  {
    label: __('Account name'),
    name: 'email_account_name',
    type: 'text',
    placeholder: __('Support / Sales'),
  },
  {
    label: 'Email ID',
    name: 'email_id',
    type: 'email',
    placeholder: 'johndoe@example.com',
  },
]

export const incomingOutgoingFields = [
  {
    label: __('Enable incoming'),
    name: 'enable_incoming',
    type: 'checkbox',
    description: __(
      'If enabled, records can be created from the incoming emails on this account.',
    ),
  },
  {
    label: __('Enable outgoing'),
    name: 'enable_outgoing',
    type: 'checkbox',
    description: __(
      'If enabled, outgoing emails can be sent from this account.',
    ),
  },
  {
    label: __('Default incoming'),
    name: 'default_incoming',
    type: 'checkbox',
    description: __(
      'If enabled, all replies to your company (eg: replies@yourcomany.com) will come to this account. Note: Only one account can be default incoming.',
    ),
  },
  {
    label: __('Default iutgoing'),
    name: 'default_outgoing',
    type: 'checkbox',
    description: __(
      'If enabled, all outgoing emails will be sent from this account. Note: Only one account can be default outgoing.',
    ),
  },
]

export const popularProviderFields = [
  ...fixedFields,
  {
    label: __('Password'),
    name: 'password',
    type: 'password',
    placeholder: '********',
  },
]

export const customProviderFields = [
  ...fixedFields,
  {
    label: __('Frappe mail site'),
    name: 'frappe_mail_site',
    type: 'text',
    placeholder: 'https://frappemail.com',
  },
  {
    label: __('API key'),
    name: 'api_key',
    type: 'text',
    placeholder: '********',
  },
  {
    label: __('API secret'),
    name: 'api_secret',
    type: 'password',
    placeholder: '********',
  },
]

export const services = [
  {
    name: 'GMail',
    icon: LogoGmail,
    info: __(
      'Setting up gmail requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://support.google.com/accounts/answer/185833',
    custom: false,
  },
  {
    name: 'Outlook',
    icon: LogoOutlook,
    info: __(
      'Setting up outlook requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://support.microsoft.com/en-us/account-billing/how-to-get-and-use-app-passwords-5896ed9b-4263-e681-128a-a6f2979a7944',
    custom: false,
  },
  {
    name: 'Sendgrid',
    icon: LogoSendgrid,
    info: __(
      'Setting up sendgrid requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://sendgrid.com/docs/ui/account-and-settings/two-factor-authentication/',
    custom: false,
  },
  {
    name: 'SparkPost',
    icon: LogoSparkpost,
    info: __(
      'Setting up sparkpost requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://support.sparkpost.com/docs/my-account-and-profile/enabling-two-factor-authentication',
    custom: false,
  },
  {
    name: 'Yahoo',
    icon: LogoYahoo,
    info: __(
      'Setting up yahoo requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://help.yahoo.com/kb/SLN15241.html',
    custom: false,
  },
  {
    name: 'Yandex',
    icon: LogoYandex,
    info: __(
      'Setting up yandex requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://yandex.com/support/id/authorization/app-passwords.html',
    custom: false,
  },
  {
    name: 'Frappe Mail',
    icon: LogoFrappeMail,
    info: __(
      'Setting up frappe mail requires you to have an API key and API Secret of your email account. Read more',
    ),
    link: 'https://github.com/frappe/mail',
    custom: true,
  },
]

export const emailIcon = {
  GMail: LogoGmail,
  Outlook: LogoOutlook,
  Sendgrid: LogoSendgrid,
  SparkPost: LogoSparkpost,
  Yahoo: LogoYahoo,
  Yandex: LogoYandex,
  'Frappe Mail': LogoFrappeMail,
}

export function validateInputs(state, isCustom) {
  if (!state.email_account_name) {
    return __('Account name is required')
  }
  if (!state.email_id) {
    return __('Email ID is required')
  }
  const validEmail = validateEmail(state.email_id)
  if (!validEmail) {
    return __('Invalid email ID')
  }
  if (!isCustom && !state.password) {
    return __('Password is required')
  }
  if (isCustom) {
    if (!state.api_key) {
      return __('API key is required')
    }
    if (!state.api_secret) {
      return
    }
  }
  return ''
}
