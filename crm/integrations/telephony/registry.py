# crm/integrations/telephony/registry.py
from __future__ import annotations

from typing import ClassVar

import frappe
from frappe import _

from crm.integrations.telephony.base import TelephonyProvider


class TelephonyRegistry:
	_providers: ClassVar[dict[str, TelephonyProvider]] = {}

	@classmethod
	def register(cls, provider: TelephonyProvider):
		cls._providers[provider.provider_name] = provider

	@classmethod
	def get_provider(cls, name: str) -> TelephonyProvider | None:
		return cls._providers.get(name)

	@classmethod
	def get_enabled_providers(cls) -> list[TelephonyProvider]:
		return [p for p in cls._providers.values() if p.is_enabled()]

	@classmethod
	def is_any_enabled(cls) -> bool:
		return any(p.is_enabled() for p in cls._providers.values())

	@classmethod
	def get_recording_credentials(cls, medium: str) -> tuple[str, str]:
		provider = cls.get_provider(medium)
		if not provider:
			frappe.throw(
				_("Unknown telephony medium: {0}").format(medium),
				frappe.ValidationError,
			)
		return provider.get_recording_credentials()

	@classmethod
	def status_summary(cls) -> dict[str, bool]:
		return {name: p.is_enabled() for name, p in cls._providers.items()}

	@classmethod
	def discover(cls):
		cls._clear_cache()
		cls._discover_provider("Twilio", "crm.integrations.twilio.twilio_handler", "TwilioProvider")
		cls._discover_provider("Exotel", "crm.integrations.exotel.handler", "ExotelProvider")

	@classmethod
	def _discover_provider(cls, name: str, module_path: str, class_name: str):
		try:
			import importlib
			mod = importlib.import_module(module_path)
			provider_cls = getattr(mod, class_name)
			provider = provider_cls.from_settings()
			if provider:
				cls.register(provider)
		except ImportError:
			frappe.log_error(
				title=f"Telephony provider {name}: module not found",
				message=f"Could not import {module_path}.{class_name}. "
				        "Check that the required package is installed.",
			)
		except Exception:
			frappe.log_error(
				title=f"Telephony provider {name}: discovery failed",
				message=frappe.get_traceback(),
			)

	@classmethod
	def _clear_cache(cls):
		cls._providers = {}
