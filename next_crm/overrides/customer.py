# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from erpnext.selling.doctype.customer.customer import Customer

class Customer(Customer):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.accounts.doctype.allowed_to_transact_with.allowed_to_transact_with import AllowedToTransactWith
		from erpnext.accounts.doctype.party_account.party_account import PartyAccount
		from erpnext.selling.doctype.customer_credit_limit.customer_credit_limit import CustomerCreditLimit
		from erpnext.selling.doctype.sales_team.sales_team import SalesTeam
		from erpnext.utilities.doctype.portal_user.portal_user import PortalUser
		from frappe.types import DF

		account_manager: DF.Link | None
		accounts: DF.Table[PartyAccount]
		companies: DF.Table[AllowedToTransactWith]
		credit_limits: DF.Table[CustomerCreditLimit]
		customer_details: DF.Text | None
		customer_group: DF.Link | None
		customer_name: DF.Data
		customer_pos_id: DF.Data | None
		customer_primary_address: DF.Link | None
		customer_primary_contact: DF.Link | None
		customer_type: DF.Literal["Company", "Individual", "Proprietorship", "Partnership"]
		default_bank_account: DF.Link | None
		default_commission_rate: DF.Float
		default_currency: DF.Link | None
		default_price_list: DF.Link | None
		default_sales_partner: DF.Link | None
		disabled: DF.Check
		dn_required: DF.Check
		email_id: DF.ReadOnly | None
		gender: DF.Link | None
		image: DF.AttachImage | None
		industry: DF.Link | None
		is_frozen: DF.Check
		is_internal_customer: DF.Check
		language: DF.Link | None
		lead_name: DF.Link | None
		loyalty_program: DF.Link | None
		loyalty_program_tier: DF.Data | None
		market_segment: DF.Link | None
		mobile_no: DF.ReadOnly | None
		naming_series: DF.Literal["CUST-.YYYY.-"]
		opportunity_name: DF.Link | None
		payment_terms: DF.Link | None
		portal_users: DF.Table[PortalUser]
		primary_address: DF.Text | None
		represents_company: DF.Link | None
		sales_team: DF.Table[SalesTeam]
		salutation: DF.Link | None
		so_required: DF.Check
		tax_category: DF.Link | None
		tax_id: DF.Data | None
		tax_withholding_category: DF.Link | None
		territory: DF.Link | None
		website: DF.Data | None
	# end: auto-generated types
		@staticmethod
		def default_list_data():
			columns = [
				{
					'label': 'Customer',
					'type': 'Data',
					'key': 'customer_name',
					'width': '16rem',
				},
				{
					'label': 'Website',
					'type': 'Data',
					'key': 'website',
					'width': '14rem',
				},
				{
					'label': 'Industry',
					'type': 'Link',
					'key': 'industry',
					'options': 'Industry Type',
					'width': '14rem',
				},
				{
					'label': 'Annual Revenue',
					'type': 'Currency',
					'key': 'annual_revenue',
					'width': '14rem',
				},
				{
					'label': 'Last Modified',
					'type': 'Datetime',
					'key': 'modified',
					'width': '8rem',
				},
			]
			rows = [
				"name",
				"customer_name",
				"image",
				"website",
				"industry",
				"default_currency",
				"annual_revenue",
				"modified",
			]
			return {'columns': columns, 'rows': rows}