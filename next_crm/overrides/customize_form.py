from frappe.custom.doctype.customize_form.customize_form import (
    CustomizeForm as _CustomizeForm,
)


class CustomizeFormOverride(_CustomizeForm):

    def allow_property_change(self, prop, meta_df, df):
        if prop == "fieldtype":
            return True
        return super().allow_property_change(prop, meta_df, df)
