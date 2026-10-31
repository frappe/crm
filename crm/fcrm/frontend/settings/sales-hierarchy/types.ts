export interface HierarchyNode {
	name: string;
	user: string;
	full_name?: string;
	reports_to?: string | null;
	modified: string;
}

export interface HierarchyUser {
	name: string;
	full_name?: string;
	user_image?: string;
	role: string;
}

export interface HierarchyRow extends HierarchyNode {
	depth: number;
	full_name: string;
	user_image?: string;
	role: string;
	reports: number;
}
