import { addEnrichItem } from "../../../frontend/enrich/index.js";
import { addOrganizationTabs } from "../../../frontend/organization/index.js";

export default {
	onRefresh(page) {
		addOrganizationTabs(page);
		addEnrichItem(page);
	},
};
