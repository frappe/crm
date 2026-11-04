import { addActivityRows } from "../../../frontend/activity/index.js";
import { addConvertButton } from "../../../frontend/convert/index.js";
import { addEnrichItem } from "../../../frontend/enrich/index.js";
import { addProductDetails, productHandlers } from "../../../frontend/products/index.js";
import { addLostReasonSection, addStatusControl, askReasonForLostStatus } from "../../../frontend/status/index.js";

export default {
	onRefresh(page) {
		page.tabs.order(["activity", "emails"]);
		addActivityRows(page);
		addStatusControl(page);
		addLostReasonSection(page);
		addConvertButton(page);
		addEnrichItem(page);
		addProductDetails(page);
	},
	status: askReasonForLostStatus,
	products: productHandlers,
};
