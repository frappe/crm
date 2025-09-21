export interface EmailAccount {
  email_account_name: string
  email_id: string
  service: string
  api_key?: string
  api_secret?: string
  password?: string
  frappe_mail_site?: string
  enable_outgoing?: boolean
  enable_incoming?: boolean
  default_outgoing?: boolean
  default_incoming?: boolean
}
