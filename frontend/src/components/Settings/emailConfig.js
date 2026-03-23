import { validateEmail } from '../../utils'

import LogoGmail from '../../../public/images/gmail.png'
import LogoOutlook from '../../../public/images/outlook.png'
import LogoSendgrid from '../../../public/images/sendgrid.png'
import LogoSparkpost from '../../../public/images/sparkpost.webp'
import LogoYahoo from '../../../public/images/yahoo.png'
import LogoYandex from '../../../public/images/yandex.png'
import LogoFrappeMail from '../../../public/images/frappe-mail.svg'

const fixedFields = [
  {
    label: __('Account Name'),
    name: 'email_account_name',
    type: 'text',
    placeholder: __('Support / Sales'),
  },
  {
    label: __('Email ID'),
    name: 'email_id',
    type: 'email',
    placeholder: 'johndoe@example.com',
  },
]

export const incomingOutgoingFields = [
  {
    label: __('Enable Incoming'),
    name: 'enable_incoming',
    type: 'checkbox',
    description: __('If enabled, emails will be pulled from this account.'),
  },
  {
    label: __('Enable Outgoing'),
    name: 'enable_outgoing',
    type: 'checkbox',
    description: __(
      'If enabled, outgoing emails can be sent from this account.',
    ),
  },
  {
    label: __('Default Incoming'),
    name: 'default_incoming',
    type: 'checkbox',
    description: __(
      'If enabled, all replies to your company (eg: replies@yourcompany.com) will come to this account. Note: Only one account can be default incoming.',
    ),
  },
  {
    label: __('Default Outgoing'),
    name: 'default_outgoing',
    type: 'checkbox',
    description: __(
      'If enabled, all outgoing emails will be sent from this account. Note: Only one account can be default outgoing.',
    ),
  },
  {
    label: __('Create Lead from Incoming Emails'),
    name: 'create_lead_from_incoming_email',
    type: 'checkbox',
    description: __(
      'If enabled, a lead will be automatically created when an incoming email is received from an unknown contact.',
    ),
    condition: (state) => state.enable_incoming,
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
    label: __('Frappe Mail Site'),
    name: 'frappe_mail_site',
    type: 'text',
    placeholder: 'https://frappemail.com',
  },
  {
    label: __('API Key'),
    name: 'api_key',
    type: 'text',
    placeholder: '********',
  },
  {
    label: __('API Secret'),
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
      'Setting up GMail requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://support.google.com/accounts/answer/185833',
    custom: false,
  },
  {
    name: 'Outlook',
    icon: LogoOutlook,
    info: __(
      'Setting up Outlook requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://support.microsoft.com/en-us/account-billing/how-to-get-and-use-app-passwords-5896ed9b-4263-e681-128a-a6f2979a7944',
    custom: false,
  },
  {
    name: 'Sendgrid',
    icon: LogoSendgrid,
    info: __(
      'Setting up Sendgrid requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://sendgrid.com/docs/ui/account-and-settings/two-factor-authentication/',
    custom: false,
  },
  {
    name: 'SparkPost',
    icon: LogoSparkpost,
    info: __(
      'Setting up Sparkpost requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://support.sparkpost.com/docs/my-account-and-profile/enabling-two-factor-authentication',
    custom: false,
  },
  {
    name: 'Yahoo',
    icon: LogoYahoo,
    info: __(
      'Setting up Yahoo requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://help.yahoo.com/kb/SLN15241.html',
    custom: false,
  },
  {
    name: 'Yandex',
    icon: LogoYandex,
    info: __(
      'Setting up Yandex requires you to enable two factor authentication and app specific passwords. Read more',
    ),
    link: 'https://yandex.com/support/id/authorization/app-passwords.html',
    custom: false,
  },
  {
    name: 'Frappe Mail',
    icon: LogoFrappeMail,
    info: __(
      'Setting up Frappe Mail requires you to have an API key and API Secret of your email account. Read more',
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
