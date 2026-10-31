import { addEnrichItem } from "../../../frontend/enrich/index.js";
import { addOrganizationTabs } from "../../../frontend/organization/index.js";
import { renameFromOrganizationName } from "../../../frontend/organization/rename.js";

export default {
	onRefresh(page) {
		addOrganizationTabs(page);
		addEnrichItem(page);
	},
	organization_name: renameFromOrganizationName,
};
