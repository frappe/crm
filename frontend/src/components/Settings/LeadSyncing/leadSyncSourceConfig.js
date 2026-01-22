import LogoFacebook from '@/components/Icons/FacebookIcon.vue'

export const supportedSourceTypes = [
  {
    label: 'Facebook',
    value: 'Facebook',
    icon: LogoFacebook,
    info: __(
      'You will need a Meta developer account and an access token to sync leads from facebook. Read more',
    ),
    link: 'https://www.facebook.com/business/help/503306463479099?id=2190812977867143',
    custom: false,
  },
]

export const sourceIcon = {
  Facebook: LogoFacebook,
}

export const fbSourceFields = [
  {
    name: 'name',
    label: __('Name'),
    type: 'text',
    placeholder: __('Add a name for your source'),
  },
  {
    name: 'access_token',
    label: __('Access token'),
    type: 'password',
    placeholder: __('Enter your facebook access token'),
  },
]
