import { addConvertButton } from "../../../frontend/convert/index.js";
import { addEnrichItem } from "../../../frontend/enrich/index.js";
import { addProductDetails, productHandlers } from "../../../frontend/products/index.js";
import { addLostReasonSection, addStatusControl, askReasonForLostStatus } from "../../../frontend/status/index.js";
import { addCallItem } from "../../../frontend/telephony/makeCall.js";

export default {
	onRefresh(page) {
		page.tabs.order(["activity", "emails"]);
		addStatusControl(page);
		addLostReasonSection(page);
		addConvertButton(page);
		addCallItem(page);
		addEnrichItem(page);
		addProductDetails(page);
	},
	status: askReasonForLostStatus,
	products: productHandlers,
};
