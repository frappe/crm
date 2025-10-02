import LogoFacebook from '@/images/facebook.png'


export const supportedSourceTypes = [
  {
    name: 'Facebook',
    icon: LogoFacebook,
    info: __("You will need a Meta developer account and an access token to sync leads from Facebook. Read more "),
    link: 'https://www.facebook.com/business/help/503306463479099?id=2190812977867143',
    custom: false,
  }
]

export const sourceIcon = {
  'Facebook': LogoFacebook
}