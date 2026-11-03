import { addContactsSection } from "../../../frontend/contacts/index.js";
import { addEnrichItem } from "../../../frontend/enrich/index.js";
import { addQuotationItems } from "../../../frontend/erpnext/index.js";
import { addForecasting, forecastProbability, forecastStatusOnSave } from "../../../frontend/forecasting/index.js";
import { addProductDetails, productHandlers } from "../../../frontend/products/index.js";
import { addLostReasonSection, addStatusControl, askReasonForLostStatus } from "../../../frontend/status/index.js";
import { addCallItem } from "../../../frontend/telephony/makeCall.js";

export default {
	onRefresh(page) {
		page.tabs.order(["activity", "emails"]);
		addStatusControl(page);
		addLostReasonSection(page);
		addCallItem(page);
		addEnrichItem(page);
		addQuotationItems(page);
		addContactsSection(page);
		addForecasting(page);
		addProductDetails(page);
	},
	beforeSave: forecastStatusOnSave,
	status: forecastProbability(askReasonForLostStatus),
	products: productHandlers,
};
