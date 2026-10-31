import { addContactsSection } from "../../../frontend/contacts/index.js";
import { addEnrichItem } from "../../../frontend/enrich/index.js";
import { addStatusControl } from "../../../frontend/status/index.js";

export default {
	onRefresh(page) {
		page.tabs.order(["activity", "emails"]);
		addStatusControl(page);
		addEnrichItem(page);
		addContactsSection(page);
	},
};
