import { addActivityRows } from "../../../frontend/activity/index.js";
import { addContactsSection } from "../../../frontend/contacts/index.js";
import { addEnrichItem } from "../../../frontend/enrich/index.js";
import { addQuotationItems } from "../../../frontend/erpnext/index.js";
import { addForecasting, forecastProbability, forecastStatusOnSave } from "../../../frontend/forecasting/index.js";
import { addProductDetails, productHandlers } from "../../../frontend/products/index.js";
import { addLostReasonSection, addStatusControl, askReasonForLostStatus } from "../../../frontend/status/index.js";

export default {
	onRefresh(page) {
		page.tabs.order(["activity", "emails"]);
		addActivityRows(page);
		addStatusControl(page);
		addLostReasonSection(page);
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
