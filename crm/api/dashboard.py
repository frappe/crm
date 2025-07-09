import frappe
from frappe import _

from crm.utils import sales_user_only


@frappe.whitelist()
@sales_user_only
def get_number_card_data(from_date="", to_date="", user="", lead_conds="", deal_conds=""):
	"""
	Get number card data for the dashboard.
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	is_sales_user = "Sales User" in frappe.get_roles(frappe.session.user)
	if is_sales_user and not user:
		user = frappe.session.user

	lead_chart_data = get_lead_count(from_date, to_date, user, lead_conds)
	deal_chart_data = get_deal_count(from_date, to_date, user, deal_conds)
	get_won_deal_count_data = get_won_deal_count(from_date, to_date, user, deal_conds)
	get_average_deal_value_data = get_average_deal_value(from_date, to_date, user, deal_conds)
	get_average_time_to_close_data = get_average_time_to_close(from_date, to_date, user, deal_conds)

	return [
		lead_chart_data,
		deal_chart_data,
		get_won_deal_count_data,
		get_average_deal_value_data,
		get_average_time_to_close_data,
	]


def get_lead_count(from_date, to_date, user="", conds="", return_result=False):
	"""
	Get lead count for the dashboard.
	"""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	if user:
		conds += f" AND lead_owner = '{user}'"

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
		"title": _("Total Leads"),
		"value": current_month_leads,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
		"negativeIsBetter": False,
		"tooltip": _("Total number of leads"),
	}


def get_deal_count(from_date, to_date, user="", conds="", return_result=False):
	"""
	Get deal count for the dashboard.
	"""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	if user:
		conds += f" AND deal_owner = '{user}'"

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
		"title": _("Total Deals"),
		"value": current_month_deals,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
		"negativeIsBetter": False,
		"tooltip": _("Total number of deals"),
	}


def get_won_deal_count(from_date, to_date, user="", conds="", return_result=False):
	"""
	Get won deal count for the dashboard.
	"""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	if user:
		conds += f" AND deal_owner = '{user}'"

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
		"title": _("Won Deals"),
		"value": current_month_deals,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
		"negativeIsBetter": False,
		"tooltip": _("Total number of won deals"),
	}


def get_average_deal_value(from_date, to_date, user="", conds="", return_result=False):
	"""
	Get average deal value for the dashboard.
	"""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	if user:
		conds += f" AND deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			AVG(CASE
				WHEN d.creation >= %(from_date)s AND d.creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY) AND d.status != 'Lost'
				{conds}
				THEN d.deal_value * IFNULL(e.exchange_rate, 1)
				ELSE NULL
			END) as current_month_avg,

			AVG(CASE
				WHEN d.creation >= %(prev_from_date)s AND d.creation < %(from_date)s AND d.status != 'Lost'
				{conds}
				THEN d.deal_value * IFNULL(e.exchange_rate, 1)
				ELSE NULL
			END) as prev_month_avg
		FROM `tabCRM Deal` d
		LEFT JOIN `tabCRM Currency Exchange` e ON d.currency_exchange = e.name
		""",
		{
			"from_date": from_date,
			"to_date": to_date,
			"prev_from_date": frappe.utils.add_days(from_date, -diff),
		},
		as_dict=1,
	)

	current_month_avg = result[0].current_month_avg or 0
	prev_month_avg = result[0].prev_month_avg or 0

	delta = current_month_avg - prev_month_avg if prev_month_avg else 0

	return {
		"title": _("Avg Deal Value"),
		"value": current_month_avg,
		"tooltip": _("Average deal value of ongoing & won deals"),
		"prefix": get_base_currency_symbol(),
		# "suffix": "K",
		"delta": delta,
		"deltaSuffix": "%",
	}


def get_average_time_to_close(from_date, to_date, user="", conds="", return_result=False):
	"""
	Get average time to close deals for the dashboard.
	"""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	if user:
		conds += f" AND d.deal_owner = '{user}'"

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	prev_to_date = from_date

	result = frappe.db.sql(
		f"""
		SELECT
			AVG(CASE WHEN d.closed_on >= %(from_date)s AND d.closed_on < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
				THEN TIMESTAMPDIFF(DAY, COALESCE(l.creation, d.creation), d.closed_on) END) as current_avg,
			AVG(CASE WHEN d.closed_on >= %(prev_from_date)s AND d.closed_on < %(prev_to_date)s
				THEN TIMESTAMPDIFF(DAY, COALESCE(l.creation, d.creation), d.closed_on) END) as prev_avg
		FROM `tabCRM Deal` d
		LEFT JOIN `tabCRM Lead` l ON d.lead = l.name
		WHERE d.status = 'Won' AND d.closed_on IS NOT NULL
			{conds}
		""",
		{
			"from_date": from_date,
			"to_date": to_date,
			"prev_from_date": prev_from_date,
			"prev_to_date": prev_to_date,
		},
		as_dict=1,
	)

	if return_result:
		return result

	current_avg = result[0].current_avg or 0
	prev_avg = result[0].prev_avg or 0
	delta = current_avg - prev_avg if prev_avg else 0

	return {
		"title": _("Avg Time to Close"),
		"value": current_avg,
		"tooltip": _("Average time taken to close deals"),
		"suffix": " days",
		"delta": delta,
		"deltaSuffix": " days",
		"negativeIsBetter": True,
	}


@frappe.whitelist()
def get_sales_trend_data(from_date="", to_date="", user="", lead_conds="", deal_conds=""):
	"""
	Get sales trend data for the dashboard.
	[
		{ date: new Date('2024-05-01'), leads: 45, deals: 23, won_deals: 12 },
		{ date: new Date('2024-05-02'), leads: 50, deals: 30, won_deals: 15 },
		...
	]
	"""

	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	if user:
		lead_conds += f" AND lead_owner = '{user}'"
		deal_conds += f" AND deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
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
			{lead_conds}
			GROUP BY DATE(creation)

			UNION ALL

			SELECT
				DATE(creation) AS date,
				0 AS leads,
				COUNT(*) AS deals,
				SUM(CASE WHEN status = 'Won' THEN 1 ELSE 0 END) AS won_deals
			FROM `tabCRM Deal`
			WHERE DATE(creation) BETWEEN %(from)s AND %(to)s
			{deal_conds}
			GROUP BY DATE(creation)
		) AS daily
		GROUP BY date
		ORDER BY date
		""",
		{"from": from_date, "to": to_date},
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
def get_deals_by_salesperson(from_date="", to_date="", user="", deal_conds=""):
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

	if user:
		deal_conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			IFNULL(u.full_name, d.deal_owner) AS salesperson,
			COUNT(*)                           AS deals,
			SUM(COALESCE(d.deal_value, 0) * IFNULL(e.exchange_rate, 1)) AS value
		FROM `tabCRM Deal` AS d
		LEFT JOIN `tabUser` AS u ON u.name = d.deal_owner
		LEFT JOIN `tabCRM Currency Exchange` AS e ON d.currency_exchange = e.name
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s
		{deal_conds}
		GROUP BY d.deal_owner
		ORDER BY value DESC
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)

	return {
		"data": result or [],
		"currency_symbol": get_base_currency_symbol(),
	}


@frappe.whitelist()
def get_deals_by_territory(from_date="", to_date="", user="", deal_conds=""):
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

	if user:
		deal_conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			IFNULL(d.territory, 'Empty') AS territory,
			COUNT(*) AS deals,
			SUM(COALESCE(d.deal_value, 0) * IFNULL(e.exchange_rate, 1)) AS value
		FROM `tabCRM Deal` AS d
		LEFT JOIN `tabCRM Currency Exchange` AS e ON d.currency_exchange = e.name
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s
		{deal_conds}
		GROUP BY d.territory
		ORDER BY value DESC
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)

	return {
		"data": result or [],
		"currency_symbol": get_base_currency_symbol(),
	}


@frappe.whitelist()
def get_lost_deal_reasons(from_date="", to_date="", user="", deal_conds=""):
	"""
	Get lost deal reasons for the dashboard.
	[
		{ reason: 'Price too high', count: 20 },
		{ reason: 'Competitor won', count: 15 },
		...
	]
	"""

	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	if user:
		deal_conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			d.lost_reason AS reason,
			COUNT(*) AS count
		FROM `tabCRM Deal` AS d
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s AND d.status = 'Lost'
		{deal_conds}
		GROUP BY d.lost_reason
		HAVING reason IS NOT NULL AND reason != ''
		ORDER BY count DESC
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)

	return result or []


@frappe.whitelist()
def get_forecasted_revenue(user="", deal_conds=""):
	"""
	Get forecasted revenue for the dashboard.
	[
		{ date: new Date('2024-05-01'), forecasted: 1200000, actual: 980000 },
		{ date: new Date('2024-06-01'), forecasted: 1350000, actual: 1120000 },
		{ date: new Date('2024-07-01'), forecasted: 1600000, actual: "" },
		{ date: new Date('2024-08-01'), forecasted: 1500000, actual: "" },
		...
	]
	"""

	if user:
		deal_conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			DATE_FORMAT(d.close_date, '%Y-%m')                        AS month,
			SUM(
				CASE
					WHEN d.status = 'Lost' THEN d.deal_value * IFNULL(e.exchange_rate, 1)
					ELSE d.deal_value * IFNULL(d.probability, 0) / 100 * IFNULL(e.exchange_rate, 1)  -- forecasted
				END
			)                                                       AS forecasted,
			SUM(
				CASE
					WHEN d.status = 'Won' THEN d.deal_value * IFNULL(e.exchange_rate, 1)            -- actual
					ELSE 0
				END
			)                                                       AS actual
		FROM `tabCRM Deal` AS d
		LEFT JOIN `tabCRM Currency Exchange` AS e ON d.currency_exchange = e.name
		WHERE d.close_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
		{deal_conds}
		GROUP BY DATE_FORMAT(d.close_date, '%Y-%m')
		ORDER BY month
		""",
		as_dict=True,
	)
	if not result:
		return []

	for row in result:
		row["month"] = frappe.utils.get_datetime(row["month"]).strftime("%Y-%m-01")
		row["forecasted"] = row["forecasted"] or ""
		row["actual"] = row["actual"] or ""

	return {
		"data": result or [],
		"currency_symbol": get_base_currency_symbol(),
	}


@frappe.whitelist()
def get_funnel_conversion_data(from_date="", to_date="", user="", lead_conds="", deal_conds=""):
	"""
	Get funnel conversion data for the dashboard.
	[
		{ stage: 'Leads', count: 120 },
		{ stage: 'Qualification', count: 100 },
		{ stage: 'Negotiation', count: 80 },
		{ stage: 'Ready to Close', count: 60 },
		{ stage: 'Won', count: 30 },
		...
	]
	"""

	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	if user:
		lead_conds += f" AND lead_owner = '{user}'"
		deal_conds += f" AND deal_owner = '{user}'"

	result = []

	# Get total leads
	total_leads = frappe.db.sql(
		f"""		SELECT COUNT(*) AS count
			FROM `tabCRM Lead`
			WHERE DATE(creation) BETWEEN %(from)s AND %(to)s
			{lead_conds}
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)
	total_leads_count = total_leads[0].count if total_leads else 0

	result.append({"stage": "Leads", "count": total_leads_count})

	# Get deal stages
	all_deal_stages = frappe.get_all(
		"CRM Deal Status", filters={"name": ["!=", "Lost"]}, order_by="position", pluck="name"
	)

	# Get deal counts for each stage
	for i, stage in enumerate(all_deal_stages):
		stages_to_count = all_deal_stages[i:]
		placeholders = ", ".join(["%s"] * len(stages_to_count))
		query = f"""
			SELECT COUNT(*) as count
			FROM `tabCRM Deal`
			WHERE DATE(creation) BETWEEN %s AND %s
			AND status IN ({placeholders})
			{deal_conds}
		"""
		params = [from_date, to_date, *stages_to_count]
		row = frappe.db.sql(query, params, as_dict=True)
		result.append({"stage": stage, "count": row[0]["count"] if row else 0})

	return result or []


@frappe.whitelist()
def get_deals_by_stage(from_date="", to_date="", user="", deal_conds=""):
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

	if user:
		deal_conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			d.status AS stage,
			COUNT(*) AS count
		FROM `tabCRM Deal` AS d
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s
		{deal_conds}
		GROUP BY d.status
		ORDER BY count DESC
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)

	return result or []


@frappe.whitelist()
def get_leads_by_source(from_date="", to_date="", user="", lead_conds=""):
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

	if user:
		lead_conds += f" AND lead_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			IFNULL(source, 'Empty') AS source,
			COUNT(*) AS count
		FROM `tabCRM Lead`
		WHERE DATE(creation) BETWEEN %(from)s AND %(to)s
		{lead_conds}
		GROUP BY source
		ORDER BY count DESC
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)

	return result or []


def get_base_currency_symbol():
	"""
	Get the base currency symbol from the system settings.
	"""
	base_currency = frappe.db.get_single_value("System Settings", "currency") or "USD"
	return frappe.db.get_value("Currency", base_currency, "symbol") or ""
