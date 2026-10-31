import { addConvertButton } from "../../../frontend/convert/index.js";
import { addEnrichItem } from "../../../frontend/enrich/index.js";
import { addStatusControl, askReasonForLostStatus } from "../../../frontend/status/index.js";

export default {
	onRefresh(page) {
		page.tabs.order(["activity", "emails"]);
		addStatusControl(page);
		addConvertButton(page);
		addEnrichItem(page);
	},
	status: askReasonForLostStatus,
};
