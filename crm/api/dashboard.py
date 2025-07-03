import frappe
from frappe import _


@frappe.whitelist()
def get_number_card_data(from_date="", to_date="", lead_conds="", deal_conds=""):
	"""
	Get number card data for the dashboard.
	"""

	lead_chart_data = get_lead_count(from_date, to_date, lead_conds)
	deal_chart_data = get_deal_count(from_date, to_date, deal_conds)
	get_won_deal_count_data = get_won_deal_count(from_date, to_date, deal_conds)

	return [
		lead_chart_data,
		deal_chart_data,
		get_won_deal_count_data,
	]


def get_lead_count(from_date, to_date, conds="", return_result=False):
	"""
	Get ticket data for the dashboard.
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	result = frappe.db.sql(
		f"""
		SELECT
            COUNT(CASE
                WHEN creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
                {conds}
                THEN name
                ELSE NULL
            END) as current_month_leads,

            COUNT(CASE
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s
                {conds}
                THEN name
                ELSE NULL
            END) as prev_month_leads
		FROM `tabCRM Lead`
    """,
		{
			"from_date": from_date,
			"to_date": to_date,
			"prev_from_date": frappe.utils.add_days(from_date, -diff),
		},
		as_dict=1,
	)

	if return_result:
		return result

	current_month_leads = result[0].current_month_leads or 0
	prev_month_leads = result[0].prev_month_leads or 0

	delta_in_percentage = (
		(current_month_leads - prev_month_leads) / prev_month_leads * 100 if prev_month_leads else 0
	)

	return {
		"title": "Total Leads",
		"value": current_month_leads,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
		"negativeIsBetter": False,
		"tooltip": "Total number of leads created",
	}


def get_deal_count(from_date, to_date, conds="", return_result=False):
	"""
	Get ticket data for the dashboard.
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	result = frappe.db.sql(
		f"""
		SELECT
            COUNT(CASE
                WHEN creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
                {conds}
                THEN name
                ELSE NULL
            END) as current_month_deals,

            COUNT(CASE
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s
                {conds}
                THEN name
                ELSE NULL
            END) as prev_month_deals
		FROM `tabCRM Deal`
    """,
		{
			"from_date": from_date,
			"to_date": to_date,
			"prev_from_date": frappe.utils.add_days(from_date, -diff),
		},
		as_dict=1,
	)

	if return_result:
		return result

	current_month_deals = result[0].current_month_deals or 0
	prev_month_deals = result[0].prev_month_deals or 0

	delta_in_percentage = (
		(current_month_deals - prev_month_deals) / prev_month_deals * 100 if prev_month_deals else 0
	)

	return {
		"title": "Total Deals",
		"value": current_month_deals,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
		"negativeIsBetter": False,
		"tooltip": "Total number of deals created",
	}


def get_won_deal_count(from_date, to_date, conds="", return_result=False):
	"""
	Get ticket data for the dashboard.
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	result = frappe.db.sql(
		f"""
		SELECT
            COUNT(CASE
                WHEN creation >= %(from_date)s AND creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY) AND status = 'Won'
                {conds}
                THEN name
                ELSE NULL
            END) as current_month_deals,

            COUNT(CASE
                WHEN creation >= %(prev_from_date)s AND creation < %(from_date)s AND status = 'Won'
                {conds}
                THEN name
                ELSE NULL
            END) as prev_month_deals
		FROM `tabCRM Deal`
    """,
		{
			"from_date": from_date,
			"to_date": to_date,
			"prev_from_date": frappe.utils.add_days(from_date, -diff),
		},
		as_dict=1,
	)

	if return_result:
		return result

	current_month_deals = result[0].current_month_deals or 0
	prev_month_deals = result[0].prev_month_deals or 0

	delta_in_percentage = (
		(current_month_deals - prev_month_deals) / prev_month_deals * 100 if prev_month_deals else 0
	)

	return {
		"title": "Won Deals",
		"value": current_month_deals,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
		"negativeIsBetter": False,
		"tooltip": "Total number of deals created",
	}


@frappe.whitelist()
def get_sales_trend_data(from_date="", to_date="", lead_conds="", deal_conds=""):
	# get sales trend data in this format, here leads data comes from `tabCRM Lead`, deals data comes from `tabCRM Deal` & won deals data comes from `tabCRM Deal` with status 'Won'
	# [
	#   { date: new Date('2024-05-01'), leads: 45, deals: 23, won_deals: 12 },
	#   { date: new Date('2024-05-02'), leads: 50, deals: 30, won_deals: 15 },
	#   ...
	# ]
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	result = frappe.db.sql(
		"""
		SELECT
			DATE_FORMAT(date, '%%Y-%%m-%%d') AS date,
			SUM(leads) AS leads,
			SUM(deals) AS deals,
			SUM(won_deals) AS won_deals
		FROM (
			SELECT
				DATE(creation) AS date,
				COUNT(*) AS leads,
				0 AS deals,
				0 AS won_deals
			FROM `tabCRM Lead`
			WHERE DATE(creation) BETWEEN %(from)s AND %(to)s
			%(lead_conds)s
			GROUP BY DATE(creation)

			UNION ALL

			SELECT
				DATE(creation) AS date,
				0 AS leads,
				COUNT(*) AS deals,
				SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) AS won_deals
			FROM `tabCRM Deal`
			WHERE DATE(creation) BETWEEN %(from)s AND %(to)s
			%(deal_conds)s
			GROUP BY DATE(creation)
		) AS daily
		GROUP BY date
		ORDER BY date
		""",
		{"from": from_date, "to": to_date, "lead_conds": lead_conds, "deal_conds": deal_conds},
		as_dict=True,
	)

	return [
		{
			"date": frappe.utils.get_datetime(row.date).strftime("%Y-%m-%d"),
			"leads": row.leads or 0,
			"deals": row.deals or 0,
			"won_deals": row.won_deals or 0,
		}
		for row in result
	]


@frappe.whitelist()
def get_deals_by_salesperson(from_date="", to_date="", deal_conds=""):
	"""
	Get deal data by salesperson for the dashboard.
	[
		{ salesperson: 'John Smith', deals: 45, value: 2300000 },
		{ salesperson: 'Jane Doe', deals: 30, value: 1500000 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	result = frappe.db.sql(
		"""
		SELECT
			IFNULL(u.full_name, d.deal_owner) AS salesperson,
			COUNT(*)                           AS deals,
			SUM(COALESCE(d.deal_value, 0))     AS value
		FROM `tabCRM Deal` AS d
		LEFT JOIN `tabUser` AS u ON u.name = d.deal_owner
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s
		%(deal_conds)s
		GROUP BY d.deal_owner
		ORDER BY value DESC
		""",
		{"from": from_date, "to": to_date, "deal_conds": deal_conds},
		as_dict=True,
	)

	return result or []


@frappe.whitelist()
def get_deals_by_territory(from_date="", to_date="", deal_conds=""):
	"""
	Get deal data by territory for the dashboard.
	[
		{ territory: 'North America', deals: 45, value: 2300000 },
		{ territory: 'Europe', deals: 30, value: 1500000 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	result = frappe.db.sql(
		"""
		SELECT
			IFNULL(d.territory, 'Empty') AS territory,
			COUNT(*) AS deals,
			SUM(COALESCE(d.deal_value, 0)) AS value
		FROM `tabCRM Deal` AS d
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s
		%(deal_conds)s
		GROUP BY d.territory
		ORDER BY value DESC
		""",
		{"from": from_date, "to": to_date, "deal_conds": deal_conds},
		as_dict=True,
	)

	return result or []


@frappe.whitelist()
def get_deals_by_stage(from_date="", to_date="", deal_conds=""):
	"""
	Get deal data by stage for the dashboard.
	[
		{ stage: 'Prospecting', count: 120 },
		{ stage: 'Negotiation', count: 45 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	result = frappe.db.sql(
		"""
		SELECT
			d.status AS stage,
			COUNT(*) AS count
		FROM `tabCRM Deal` AS d
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s
		%(deal_conds)s
		GROUP BY d.status
		ORDER BY count DESC
		""",
		{"from": from_date, "to": to_date, "deal_conds": deal_conds},
		as_dict=True,
	)

	return result or []


@frappe.whitelist()
def get_leads_by_source(from_date="", to_date="", lead_conds=""):
	"""
	Get lead data by source for the dashboard.
	[
		{ source: 'Website', count: 120 },
		{ source: 'Referral', count: 45 },
		...
	]
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	result = frappe.db.sql(
		"""
		SELECT
			IFNULL(source, 'Empty') AS source,
			COUNT(*) AS count
		FROM `tabCRM Lead`
		WHERE DATE(creation) BETWEEN %(from)s AND %(to)s
		%(lead_conds)s
		GROUP BY source
		ORDER BY count DESC
		""",
		{"from": from_date, "to": to_date, "lead_conds": lead_conds},
		as_dict=True,
	)

	return result or []
