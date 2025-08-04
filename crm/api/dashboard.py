import json

import frappe
from frappe import _

from crm.fcrm.doctype.crm_dashboard.crm_dashboard import create_default_manager_dashboard
from crm.utils import sales_user_only


@frappe.whitelist()
def reset_to_default():
	frappe.only_for("System Manager")
	create_default_manager_dashboard(force=True)


@frappe.whitelist()
@sales_user_only
def get_dashboard(from_date="", to_date="", user=""):
	"""
	Get the dashboard data for the CRM dashboard.
	"""

	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	roles = frappe.get_roles(frappe.session.user)
	is_sales_user = "Sales User" in roles and "Sales Manager" not in roles and "System Manager" not in roles
	if is_sales_user and not user:
		user = frappe.session.user

	dashboard = frappe.db.exists("CRM Dashboard", "Manager Dashboard")

	layout = []

	if not dashboard:
		layout = json.loads(create_default_manager_dashboard())
		frappe.db.commit()
	else:
		layout = json.loads(frappe.db.get_value("CRM Dashboard", "Manager Dashboard", "layout") or "[]")

	for l in layout:
		method_name = f"get_{l['name']}"
		if hasattr(frappe.get_attr("crm.api.dashboard"), method_name):
			method = getattr(frappe.get_attr("crm.api.dashboard"), method_name)
			l["data"] = method(from_date, to_date, user)
		else:
			l["data"] = None

	return layout


@frappe.whitelist()
@sales_user_only
def get_chart(name, type, from_date="", to_date="", user=""):
	"""
	Get number chart data for the dashboard.
	"""
	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	roles = frappe.get_roles(frappe.session.user)
	is_sales_user = "Sales User" in roles and "Sales Manager" not in roles and "System Manager" not in roles
	if is_sales_user and not user:
		user = frappe.session.user

	method_name = f"get_{name}"
	if hasattr(frappe.get_attr("crm.api.dashboard"), method_name):
		method = getattr(frappe.get_attr("crm.api.dashboard"), method_name)
		return method(from_date, to_date, user)
	else:
		return {"error": _("Invalid chart name")}


def get_total_leads(from_date, to_date, user=""):
	"""
	Get lead count for the dashboard.
	"""
	conds = ""

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

	current_month_leads = result[0].current_month_leads or 0
	prev_month_leads = result[0].prev_month_leads or 0

	delta_in_percentage = (
		(current_month_leads - prev_month_leads) / prev_month_leads * 100 if prev_month_leads else 0
	)

	return {
		"title": _("Total leads"),
		"tooltip": _("Total number of leads"),
		"value": current_month_leads,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
	}


def get_ongoing_deals(from_date, to_date, user=""):
	"""
	Get ongoing deal count for the dashboard, and also calculate average deal value for ongoing deals.
	"""
	conds = ""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	if user:
		conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			COUNT(CASE
				WHEN d.creation >= %(from_date)s AND d.creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
					AND s.type NOT IN ('Won', 'Lost')
					{conds}
				THEN d.name
				ELSE NULL
			END) as current_month_deals,

			COUNT(CASE
				WHEN d.creation >= %(prev_from_date)s AND d.creation < %(from_date)s
					AND s.type NOT IN ('Won', 'Lost')
					{conds}
				THEN d.name
				ELSE NULL
			END) as prev_month_deals
		FROM `tabCRM Deal` d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
	""",
		{
			"from_date": from_date,
			"to_date": to_date,
			"prev_from_date": frappe.utils.add_days(from_date, -diff),
		},
		as_dict=1,
	)

	current_month_deals = result[0].current_month_deals or 0
	prev_month_deals = result[0].prev_month_deals or 0

	delta_in_percentage = (
		(current_month_deals - prev_month_deals) / prev_month_deals * 100 if prev_month_deals else 0
	)

	return {
		"title": _("Ongoing deals"),
		"tooltip": _("Total number of non won/lost deals"),
		"value": current_month_deals,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
	}


def get_average_ongoing_deal_value(from_date, to_date, user=""):
	"""
	Get ongoing deal count for the dashboard, and also calculate average deal value for ongoing deals.
	"""
	conds = ""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	if user:
		conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			AVG(CASE
				WHEN d.creation >= %(from_date)s AND d.creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
					AND s.type NOT IN ('Won', 'Lost')
					{conds}
				THEN d.deal_value * IFNULL(d.exchange_rate, 1)
				ELSE NULL
			END) as current_month_avg_value,

			AVG(CASE
				WHEN d.creation >= %(prev_from_date)s AND d.creation < %(from_date)s
					AND s.type NOT IN ('Won', 'Lost')
					{conds}
				THEN d.deal_value * IFNULL(d.exchange_rate, 1)
				ELSE NULL
			END) as prev_month_avg_value
		FROM `tabCRM Deal` d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
    """,
		{
			"from_date": from_date,
			"to_date": to_date,
			"prev_from_date": frappe.utils.add_days(from_date, -diff),
		},
		as_dict=1,
	)

	current_month_avg_value = result[0].current_month_avg_value or 0
	prev_month_avg_value = result[0].prev_month_avg_value or 0

	avg_value_delta = current_month_avg_value - prev_month_avg_value if prev_month_avg_value else 0

	return {
		"title": _("Avg. ongoing deal value"),
		"tooltip": _("Average deal value of non won/lost deals"),
		"value": current_month_avg_value,
		"delta": avg_value_delta,
		"prefix": get_base_currency_symbol(),
	}


def get_won_deals(from_date, to_date, user=""):
	"""
	Get won deal count for the dashboard, and also calculate average deal value for won deals.
	"""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	conds = ""

	if user:
		conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			COUNT(CASE
				WHEN d.closed_date >= %(from_date)s AND d.closed_date < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
					AND s.type = 'Won'
					{conds}
				THEN d.name
				ELSE NULL
			END) as current_month_deals,

			COUNT(CASE
				WHEN d.closed_date >= %(prev_from_date)s AND d.closed_date < %(from_date)s
					AND s.type = 'Won'
					{conds}
				THEN d.name
				ELSE NULL
			END) as prev_month_deals
		FROM `tabCRM Deal` d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
		""",
		{
			"from_date": from_date,
			"to_date": to_date,
			"prev_from_date": frappe.utils.add_days(from_date, -diff),
		},
		as_dict=1,
	)

	current_month_deals = result[0].current_month_deals or 0
	prev_month_deals = result[0].prev_month_deals or 0

	delta_in_percentage = (
		(current_month_deals - prev_month_deals) / prev_month_deals * 100 if prev_month_deals else 0
	)

	return {
		"title": _("Won deals"),
		"tooltip": _("Total number of won deals based on its closure date"),
		"value": current_month_deals,
		"delta": delta_in_percentage,
		"deltaSuffix": "%",
	}


def get_average_won_deal_value(from_date, to_date, user=""):
	"""
	Get won deal count for the dashboard, and also calculate average deal value for won deals.
	"""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	conds = ""

	if user:
		conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			AVG(CASE
				WHEN d.closed_date >= %(from_date)s AND d.closed_date < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
					AND s.type = 'Won'
					{conds}
				THEN d.deal_value * IFNULL(d.exchange_rate, 1)
				ELSE NULL
			END) as current_month_avg_value,

			AVG(CASE
				WHEN d.closed_date >= %(prev_from_date)s AND d.closed_date < %(from_date)s
					AND s.type = 'Won'
					{conds}
				THEN d.deal_value * IFNULL(d.exchange_rate, 1)
				ELSE NULL
			END) as prev_month_avg_value
		FROM `tabCRM Deal` d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
		""",
		{
			"from_date": from_date,
			"to_date": to_date,
			"prev_from_date": frappe.utils.add_days(from_date, -diff),
		},
		as_dict=1,
	)

	current_month_avg_value = result[0].current_month_avg_value or 0
	prev_month_avg_value = result[0].prev_month_avg_value or 0

	avg_value_delta = current_month_avg_value - prev_month_avg_value if prev_month_avg_value else 0

	return {
		"title": _("Avg. won deal value"),
		"tooltip": _("Average deal value of won deals"),
		"value": current_month_avg_value,
		"delta": avg_value_delta,
		"prefix": get_base_currency_symbol(),
	}


def get_average_deal_value(from_date, to_date, user=""):
	"""
	Get average deal value for the dashboard.
	"""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	conds = ""

	if user:
		conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			AVG(CASE
				WHEN d.creation >= %(from_date)s AND d.creation < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
					AND s.type != 'Lost'
					{conds}
				THEN d.deal_value * IFNULL(d.exchange_rate, 1)
				ELSE NULL
			END) as current_month_avg,

			AVG(CASE
				WHEN d.creation >= %(prev_from_date)s AND d.creation < %(from_date)s
					AND s.type != 'Lost'
					{conds}
				THEN d.deal_value * IFNULL(d.exchange_rate, 1)
				ELSE NULL
			END) as prev_month_avg
		FROM `tabCRM Deal` AS d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
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
		"title": _("Avg. deal value"),
		"tooltip": _("Average deal value of ongoing & won deals"),
		"value": current_month_avg,
		"prefix": get_base_currency_symbol(),
		"delta": delta,
		"deltaSuffix": "%",
	}


def get_average_time_to_close_a_lead(from_date, to_date, user=""):
	"""
	Get average time to close deals for the dashboard.
	"""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	conds = ""

	if user:
		conds += f" AND d.deal_owner = '{user}'"

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	prev_to_date = from_date

	result = frappe.db.sql(
		f"""
		SELECT
			AVG(CASE WHEN d.closed_date >= %(from_date)s AND d.closed_date < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
				THEN TIMESTAMPDIFF(DAY, COALESCE(l.creation, d.creation), d.closed_date) END) as current_avg_lead,
			AVG(CASE WHEN d.closed_date >= %(prev_from_date)s AND d.closed_date < %(prev_to_date)s
				THEN TIMESTAMPDIFF(DAY, COALESCE(l.creation, d.creation), d.closed_date) END) as prev_avg_lead
		FROM `tabCRM Deal` AS d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
		LEFT JOIN `tabCRM Lead` l ON d.lead = l.name
		WHERE d.closed_date IS NOT NULL AND s.type = 'Won'
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

	current_avg_lead = result[0].current_avg_lead or 0
	prev_avg_lead = result[0].prev_avg_lead or 0
	delta_lead = current_avg_lead - prev_avg_lead if prev_avg_lead else 0

	return {
		"title": _("Avg. time to close a lead"),
		"tooltip": _("Average time taken from lead creation to deal closure"),
		"value": current_avg_lead,
		"suffix": " days",
		"delta": delta_lead,
		"deltaSuffix": " days",
		"negativeIsBetter": True,
	}


def get_average_time_to_close_a_deal(from_date, to_date, user=""):
	"""
	Get average time to close deals for the dashboard.
	"""

	diff = frappe.utils.date_diff(to_date, from_date)
	if diff == 0:
		diff = 1

	conds = ""

	if user:
		conds += f" AND d.deal_owner = '{user}'"

	prev_from_date = frappe.utils.add_days(from_date, -diff)
	prev_to_date = from_date

	result = frappe.db.sql(
		f"""
		SELECT
			AVG(CASE WHEN d.closed_date >= %(from_date)s AND d.closed_date < DATE_ADD(%(to_date)s, INTERVAL 1 DAY)
				THEN TIMESTAMPDIFF(DAY, d.creation, d.closed_date) END) as current_avg_deal,
			AVG(CASE WHEN d.closed_date >= %(prev_from_date)s AND d.closed_date < %(prev_to_date)s
				THEN TIMESTAMPDIFF(DAY, d.creation, d.closed_date) END) as prev_avg_deal
		FROM `tabCRM Deal` AS d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
		LEFT JOIN `tabCRM Lead` l ON d.lead = l.name
		WHERE d.closed_date IS NOT NULL AND s.type = 'Won'
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

	current_avg_deal = result[0].current_avg_deal or 0
	prev_avg_deal = result[0].prev_avg_deal or 0
	delta_deal = current_avg_deal - prev_avg_deal if prev_avg_deal else 0

	return {
		"title": _("Avg. time to close a deal"),
		"tooltip": _("Average time taken from deal creation to deal closure"),
		"value": current_avg_deal,
		"suffix": " days",
		"delta": delta_deal,
		"deltaSuffix": " days",
		"negativeIsBetter": True,
	}


def get_sales_trend(from_date="", to_date="", user=""):
	"""
	Get sales trend data for the dashboard.
	[
		{ date: new Date('2024-05-01'), leads: 45, deals: 23, won_deals: 12 },
		{ date: new Date('2024-05-02'), leads: 50, deals: 30, won_deals: 15 },
		...
	]
	"""

	lead_conds = ""
	deal_conds = ""

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
				DATE(d.creation) AS date,
				0 AS leads,
				COUNT(*) AS deals,
				SUM(CASE WHEN s.type = 'Won' THEN 1 ELSE 0 END) AS won_deals
			FROM `tabCRM Deal` d
			JOIN `tabCRM Deal Status` s ON d.status = s.name
			WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s
			{deal_conds}
			GROUP BY DATE(d.creation)
		) AS daily
		GROUP BY date
		ORDER BY date
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)

	sales_trend = [
		{
			"date": frappe.utils.get_datetime(row.date).strftime("%Y-%m-%d"),
			"leads": row.leads or 0,
			"deals": row.deals or 0,
			"won_deals": row.won_deals or 0,
		}
		for row in result
	]

	return {
		"data": sales_trend,
		"title": _("Sales trend"),
		"subtitle": _("Daily performance of leads, deals, and wins"),
		"xAxis": {
			"title": _("Date"),
			"key": "date",
			"type": "time",
			"timeGrain": "day",
		},
		"yAxis": {
			"title": _("Count"),
		},
		"series": [
			{"name": "leads", "type": "line", "showDataPoints": True},
			{"name": "deals", "type": "line", "showDataPoints": True},
			{"name": "won_deals", "type": "line", "showDataPoints": True},
		],
	}


def get_forecasted_revenue(from_date="", to_date="", user=""):
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
	deal_conds = ""

	if user:
		deal_conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			DATE_FORMAT(d.expected_closure_date, '%Y-%m')                        AS month,
			SUM(
				CASE
					WHEN s.type = 'Lost' THEN d.expected_deal_value * IFNULL(d.exchange_rate, 1)
					ELSE d.expected_deal_value * IFNULL(d.probability, 0) / 100 * IFNULL(d.exchange_rate, 1)  -- forecasted
				END
			)                                                       AS forecasted,
			SUM(
				CASE
					WHEN s.type = 'Won' THEN d.deal_value * IFNULL(d.exchange_rate, 1)            -- actual
					ELSE 0
				END
			)                                                       AS actual
		FROM `tabCRM Deal` AS d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
		WHERE d.expected_closure_date >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
		{deal_conds}
		GROUP BY DATE_FORMAT(d.expected_closure_date, '%Y-%m')
		ORDER BY month
		""",
		as_dict=True,
	)

	for row in result:
		row["month"] = frappe.utils.get_datetime(row["month"]).strftime("%Y-%m-01")
		row["forecasted"] = row["forecasted"] or ""
		row["actual"] = row["actual"] or ""

	return {
		"data": result or [],
		"title": _("Forecasted revenue"),
		"subtitle": _("Projected vs actual revenue based on deal probability"),
		"xAxis": {
			"title": _("Month"),
			"key": "month",
			"type": "time",
			"timeGrain": "month",
		},
		"yAxis": {
			"title": _("Revenue") + f" ({get_base_currency_symbol()})",
		},
		"series": [
			{"name": "forecasted", "type": "line", "showDataPoints": True},
			{"name": "actual", "type": "line", "showDataPoints": True},
		],
	}


def get_funnel_conversion(from_date="", to_date="", user=""):
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
	lead_conds = ""
	deal_conds = ""

	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	if user:
		lead_conds += f" AND lead_owner = '{user}'"
		deal_conds += f" AND deal_owner = '{user}'"

	result = []

	# Get total leads
	total_leads = frappe.db.sql(
		f"""
			SELECT COUNT(*) AS count
			FROM `tabCRM Lead`
			WHERE DATE(creation) BETWEEN %(from)s AND %(to)s
			{lead_conds}
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)
	total_leads_count = total_leads[0].count if total_leads else 0

	result.append({"stage": "Leads", "count": total_leads_count})

	result += get_deal_status_change_counts(from_date, to_date, deal_conds)

	return {
		"data": result or [],
		"title": _("Funnel conversion"),
		"subtitle": _("Lead to deal conversion pipeline"),
		"xAxis": {
			"title": _("Stage"),
			"key": "stage",
			"type": "category",
		},
		"yAxis": {
			"title": _("Count"),
		},
		"swapXY": True,
		"series": [
			{
				"name": "count",
				"type": "bar",
				"echartOptions": {
					"colorBy": "data",
				},
			},
		],
	}


def get_deals_by_stage_axis(from_date="", to_date="", user=""):
	"""
	Get deal data by stage for the dashboard.
	[
		{ stage: 'Prospecting', count: 120 },
		{ stage: 'Negotiation', count: 45 },
		...
	]
	"""
	deal_conds = ""

	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	if user:
		deal_conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			d.status AS stage,
			COUNT(*) AS count,
			s.type AS status_type
		FROM `tabCRM Deal` AS d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s AND s.type NOT IN ('Lost')
		{deal_conds}
		GROUP BY d.status
		ORDER BY count DESC
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)

	return {
		"data": result or [],
		"title": _("Deals by ongoing & won stage"),
		"xAxis": {
			"title": _("Stage"),
			"key": "stage",
			"type": "category",
		},
		"yAxis": {"title": _("Count")},
		"series": [
			{"name": "count", "type": "bar"},
		],
	}


def get_deals_by_stage_donut(from_date="", to_date="", user=""):
	"""
	Get deal data by stage for the dashboard.
	[
		{ stage: 'Prospecting', count: 120 },
		{ stage: 'Negotiation', count: 45 },
		...
	]
	"""
	deal_conds = ""

	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	if user:
		deal_conds += f" AND d.deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			d.status AS stage,
			COUNT(*) AS count,
			s.type AS status_type
		FROM `tabCRM Deal` AS d
		JOIN `tabCRM Deal Status` s ON d.status = s.name
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s
		{deal_conds}
		GROUP BY d.status
		ORDER BY count DESC
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)

	return {
		"data": result or [],
		"title": _("Deals by stage"),
		"subtitle": _("Current pipeline distribution"),
		"categoryColumn": "stage",
		"valueColumn": "count",
	}


def get_lost_deal_reasons(from_date="", to_date="", user=""):
	"""
	Get lost deal reasons for the dashboard.
	[
		{ reason: 'Price too high', count: 20 },
		{ reason: 'Competitor won', count: 15 },
		...
	]
	"""

	deal_conds = ""

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
		JOIN `tabCRM Deal Status` s ON d.status = s.name
		WHERE DATE(d.creation) BETWEEN %(from)s AND %(to)s AND s.type = 'Lost'
		{deal_conds}
		GROUP BY d.lost_reason
		HAVING reason IS NOT NULL AND reason != ''
		ORDER BY count DESC
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)

	return {
		"data": result or [],
		"title": _("Lost deal reasons"),
		"subtitle": _("Common reasons for losing deals"),
		"xAxis": {
			"title": _("Reason"),
			"key": "reason",
			"type": "category",
		},
		"yAxis": {
			"title": _("Count"),
		},
		"series": [
			{"name": "count", "type": "bar"},
		],
	}


def get_leads_by_source(from_date="", to_date="", user=""):
	"""
	Get lead data by source for the dashboard.
	[
		{ source: 'Website', count: 120 },
		{ source: 'Referral', count: 45 },
		...
	]
	"""
	lead_conds = ""

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

	return {
		"data": result or [],
		"title": _("Leads by source"),
		"subtitle": _("Lead generation channel analysis"),
		"categoryColumn": "source",
		"valueColumn": "count",
	}


def get_deals_by_source(from_date="", to_date="", user=""):
	"""
	Get deal data by source for the dashboard.
	[
		{ source: 'Website', count: 120 },
		{ source: 'Referral', count: 45 },
		...
	]
	"""
	deal_conds = ""

	if not from_date or not to_date:
		from_date = frappe.utils.get_first_day(from_date or frappe.utils.nowdate())
		to_date = frappe.utils.get_last_day(to_date or frappe.utils.nowdate())

	if user:
		deal_conds += f" AND deal_owner = '{user}'"

	result = frappe.db.sql(
		f"""
		SELECT
			IFNULL(source, 'Empty') AS source,
			COUNT(*) AS count
		FROM `tabCRM Deal`
		WHERE DATE(creation) BETWEEN %(from)s AND %(to)s
		{deal_conds}
		GROUP BY source
		ORDER BY count DESC
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)

	return {
		"data": result or [],
		"title": _("Deals by source"),
		"subtitle": _("Deal generation channel analysis"),
		"categoryColumn": "source",
		"valueColumn": "count",
	}


def get_deals_by_territory(from_date="", to_date="", user=""):
	"""
	Get deal data by territory for the dashboard.
	[
		{ territory: 'North America', deals: 45, value: 2300000 },
		{ territory: 'Europe', deals: 30, value: 1500000 },
		...
	]
	"""
	deal_conds = ""

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
			SUM(COALESCE(d.deal_value, 0) * IFNULL(d.exchange_rate, 1)) AS value
		FROM `tabCRM Deal` AS d
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
		"title": _("Deals by territory"),
		"subtitle": _("Geographic distribution of deals and revenue"),
		"xAxis": {
			"title": _("Territory"),
			"key": "territory",
			"type": "category",
		},
		"yAxis": {
			"title": _("Number of deals"),
		},
		"y2Axis": {
			"title": _("Deal value") + f" ({get_base_currency_symbol()})",
		},
		"series": [
			{"name": "deals", "type": "bar"},
			{"name": "value", "type": "line", "showDataPoints": True, "axis": "y2"},
		],
	}


def get_deals_by_salesperson(from_date="", to_date="", user=""):
	"""
	Get deal data by salesperson for the dashboard.
	[
		{ salesperson: 'John Smith', deals: 45, value: 2300000 },
		{ salesperson: 'Jane Doe', deals: 30, value: 1500000 },
		...
	]
	"""
	deal_conds = ""

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
			SUM(COALESCE(d.deal_value, 0) * IFNULL(d.exchange_rate, 1)) AS value
		FROM `tabCRM Deal` AS d
		LEFT JOIN `tabUser` AS u ON u.name = d.deal_owner
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
		"title": _("Deals by salesperson"),
		"subtitle": _("Number of deals and total value per salesperson"),
		"xAxis": {
			"title": _("Salesperson"),
			"key": "salesperson",
			"type": "category",
		},
		"yAxis": {
			"title": _("Number of deals"),
		},
		"y2Axis": {
			"title": _("Deal value") + f" ({get_base_currency_symbol()})",
		},
		"series": [
			{"name": "deals", "type": "bar"},
			{"name": "value", "type": "line", "showDataPoints": True, "axis": "y2"},
		],
	}


def get_base_currency_symbol():
	"""
	Get the base currency symbol from the system settings.
	"""
	base_currency = frappe.db.get_single_value("FCRM Settings", "currency") or "USD"
	return frappe.db.get_value("Currency", base_currency, "symbol") or ""


def get_deal_status_change_counts(from_date, to_date, deal_conds=""):
	"""
	Get count of each status change (to) for each deal, excluding deals with current status type 'Lost'.
	Order results by status position.
	Returns:
	[
	  {"status": "Qualification", "count": 120},
	  {"status": "Negotiation", "count": 85},
	  ...
	]
	"""
	result = frappe.db.sql(
		f"""
		SELECT
			scl.to AS stage,
			COUNT(*) AS count
		FROM
			`tabCRM Status Change Log` scl
		JOIN
			`tabCRM Deal` d ON scl.parent = d.name
		JOIN
			`tabCRM Deal Status` s ON d.status = s.name
		JOIN
			`tabCRM Deal Status` st ON scl.to = st.name
		WHERE
			scl.to IS NOT NULL
			AND scl.to != ''
			AND s.type != 'Lost'
			AND DATE(d.creation) BETWEEN %(from)s AND %(to)s
			{deal_conds}
		GROUP BY
			scl.to, st.position
		ORDER BY
			st.position ASC
		""",
		{"from": from_date, "to": to_date},
		as_dict=True,
	)
	return result or []
