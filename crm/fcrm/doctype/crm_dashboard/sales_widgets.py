# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Sales widgets follow /dashboard's rules, not the Home scopes: agents count the deals they own,
managers everyone's. Amounts are in the base currency."""

from datetime import timedelta
from itertools import accumulate

import frappe
from frappe import _
from frappe.query_builder import Case, DocType, Order
from frappe.query_builder.functions import Coalesce, IfNull, Sum
from frappe.utils import getdate, now_datetime

from crm.api.dashboard import get_base_currency_symbol, get_funnel_conversion
from crm.fcrm.doctype.crm_dashboard.home_layout import DEFAULT_PERIOD, PERIOD_DAYS, role_for
from crm.fcrm.doctype.crm_dashboard.home_widgets import ROW_LIMIT, Widget

TREND_POINTS = 8
OPEN_TYPES = ("Open", "Ongoing")


class SalesWidget(Widget):
	def __init__(self, doctypes: tuple, scope, period: str = DEFAULT_PERIOD):
		super().__init__(doctypes, scope)
		if period not in PERIOD_DAYS:
			frappe.throw(_("Unknown period {0}").format(period))
		self.days = PERIOD_DAYS[period]
		self.owner = None if role_for(scope.user) == "manager" else scope.user
		self.deal = DocType("CRM Deal")
		self.status = DocType("CRM Deal Status")
		self.today = getdate()

	def deals(self, *types):
		deal, status = self.deal, self.status
		query = frappe.qb.from_(deal).join(status).on(deal.status == status.name)
		if types:
			query = query.where(status.type.isin(types))
		if self.owner:
			query = query.where(deal.deal_owner == self.owner)
		return query

	def value(self):
		return IfNull(self.deal.deal_value, 0) * IfNull(self.deal.exchange_rate, 1)


class FunnelConversion(SalesWidget):
	"""The /dashboard funnel over the period; Home's one deliberate copy of a /dashboard chart."""

	def summary(self) -> dict:
		since = self.today - timedelta(days=self.days - 1)
		stages = get_funnel_conversion(since, self.today, self.owner)["data"]
		return {"rows": stages if any(stage["count"] for stage in stages) else []}


class Won(SalesWidget):
	"""Value won over the period, against the period before it."""

	def summary(self) -> dict:
		start = self.today - timedelta(days=self.days - 1)
		won = self.won_by_day(start - timedelta(days=self.days), self.today)
		days = [start + timedelta(days=day) for day in range(self.days)]
		running = list(accumulate(won.get(day, 0) for day in days))
		value = running[-1]
		before = sum(amount for day, amount in won.items() if day < start)
		return {
			"value": value,
			"delta": percent_change(value, before),
			"currency": get_base_currency_symbol(),
			"sparkline": running,
		}

	def won_by_day(self, since, until) -> dict:
		closed = self.deal.closed_date
		rows = (
			self.deals("Won")
			.where(closed.between(since, until))
			.select(closed, Sum(self.value()))
			.groupby(closed)
			.run()
		)
		return {getdate(day): amount or 0 for day, amount in rows}


class ExpectedRevenue(SalesWidget):
	"""Expected Deal Value of open deals weighted by the win probability of their stage, now and across
	the period. A deal's stage at a past moment comes from its status log; its value is today's.
	Expected Deal Value is only required while forecasting is on, so the widget needs it."""

	def summary(self) -> dict:
		if not frappe.db.get_single_value("FCRM Settings", "enable_forecasting"):
			return {"forecasting": False}
		points = self.weighted_over_period()
		return {
			"forecasting": True,
			"value": points[-1],
			"delta": percent_change(points[-1], points[0]),
			"currency": get_base_currency_symbol(),
			"sparkline": points,
		}

	def weighted_over_period(self) -> list:
		deal, status = self.deal, self.status
		log = DocType("CRM Status Change Log")
		now = now_datetime()
		step = timedelta(days=self.days) / (TREND_POINTS - 1)
		points = [now - step * (TREND_POINTS - 1 - point) for point in range(TREND_POINTS)]
		expected = IfNull(deal.expected_deal_value, 0) * IfNull(deal.exchange_rate, 1)
		weighted = expected * IfNull(status.probability, 0) / 100

		def in_stage_at(at):
			return (log.from_date <= at) & (log.to_date.isnull() | (log.to_date > at))

		query = (
			frappe.qb.from_(log)
			.join(deal)
			.on(deal.name == log.parent)
			.join(status)
			.on(status.name == log["from"])
			.where(
				(log.parenttype == "CRM Deal")
				& status.type.isin(OPEN_TYPES)
				& (log.to_date.isnull() | (log.to_date > points[0]))
			)
			.select(*(Sum(Case().when(in_stage_at(at), weighted).else_(0)) for at in points))
		)
		if self.owner:
			query = query.where(deal.deal_owner == self.owner)
		return [amount or 0 for amount in query.run()[0]]


class TopOpenDeals(SalesWidget):
	def summary(self) -> dict:
		deal = self.deal
		organization = DocType("CRM Organization")
		rows = (
			self.deals(*OPEN_TYPES)
			.left_join(organization)
			.on(organization.name == deal.organization)
			.select(
				deal.name,
				deal.status,
				Coalesce(deal.organization, deal.lead_name).as_("title"),
				Coalesce(deal.organization_logo, organization.organization_logo).as_("logo"),
				self.value().as_("value"),
			)
			.where(deal.deal_value > 0)
			.orderby(self.value(), order=Order.desc)
			.limit(ROW_LIMIT)
			.run(as_dict=True)
		)
		return {
			"rows": [{**row, "doctype": "CRM Deal"} for row in rows],
			"currency": get_base_currency_symbol(),
		}


SALES_WIDGET_DATA = {
	"funnel_conversion": FunnelConversion,
	"won_this_month": Won,
	"expected_revenue": ExpectedRevenue,
	"top_open_deals": TopOpenDeals,
}


def percent_change(now: float, before: float) -> float | None:
	return (now - before) / before * 100 if before else None
