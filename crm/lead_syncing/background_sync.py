import frappe


def sync_leads_from_all_enabled_sources(frequency: str | None = None) -> None:
	enabled_sources = frappe.get_all(
		"Lead Sync Source", filters={"enabled": 1, "background_sync_frequency": frequency}, pluck="name"
	)
	for source in enabled_sources:
		lead_sync_source = frappe.get_cached_doc("Lead Sync Source", source)
		try:
			lead_sync_source._sync_leads()
		except Exception as _:
			frappe.log_error(f"Error syncing leads for source {source}")


def sync_leads_from_sources_5_minutes() -> None:
	sync_leads_from_all_enabled_sources("Every 5 Minutes")


def sync_leads_from_sources_10_minutes() -> None:
	sync_leads_from_all_enabled_sources("Every 10 Minutes")


def sync_leads_from_sources_15_minutes() -> None:
	sync_leads_from_all_enabled_sources("Every 15 Minutes")


def sync_leads_from_sources_hourly() -> None:
	sync_leads_from_all_enabled_sources("Hourly")


def sync_leads_from_sources_daily() -> None:
	sync_leads_from_all_enabled_sources("Daily")


def sync_leads_from_sources_monthly() -> None:
	sync_leads_from_all_enabled_sources("Monthly")
