import hmac
import json
from hashlib import sha256

from frappe.tests import UnitTestCase

from crm.antek_materials.integrations.fastapi_sync import build_signature


class UnitTestBuildSignature(UnitTestCase):
	def test_build_signature_matches_hmac_sha256(self):
		payload = {"contract_id": "HD-3B-2026-001", "current_debt": 1000}
		secret = "secret-key"
		expected = hmac.new(
			secret.encode(),
			json.dumps(payload, separators=(",", ":"), sort_keys=True).encode(),
			sha256,
		).hexdigest()
		self.assertEqual(build_signature(payload, secret), expected)
