import { addContactsSection } from "../../../frontend/contacts/index.js";
import { addEnrichItem } from "../../../frontend/enrich/index.js";
import { addLostReasonSection, addStatusControl, askReasonForLostStatus } from "../../../frontend/status/index.js";

export default {
	onRefresh(page) {
		page.tabs.order(["activity", "emails"]);
		addStatusControl(page);
		addLostReasonSection(page);
		addEnrichItem(page);
		addContactsSection(page);
	},
	status: askReasonForLostStatus,
};
