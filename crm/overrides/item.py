
from erpnext.stock.doctype.item.item import Item

class CustomItem(Item):
    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "PIN",
                "type": "data",
                "key": "item_code",
                "width": "10rem",
            },
            {
                "label": "Property Title",
                "type": "data",
                "key": "item_name",
                "width": "12rem",
            },
            {
                "label": "Property Type",
                "type": "data",
                "key": "item_group",
                "width": "10rem",
            },
            {
                "label": "Seller",
                "type": "data",
                "key": "custom_seller",
                "width": "8rem",
            },
            {
                "label": "Land Size",
                "type": "currency",
                "key": "custom_land_size",
                "width": "10rem",
            },
        ]
        rows = [
            "item_code",
            "item_name",
            "item_group",
            "custom_seller",
            "custom_land_size",
        ]
        return {"columns": columns, "rows": rows}
