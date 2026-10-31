import { addEnrichItem } from "../../../frontend/enrich/index.js";

export default {
	onRefresh(page) {
		addEnrichItem(page);
	},
};
