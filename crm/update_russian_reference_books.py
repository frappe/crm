import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    add_default_lead_statuses()
    add_default_deal_statuses()
    add_default_communication_statuses()
    add_default_fields_layout()
    add_property_setter()
    add_email_template_custom_fields()
    add_default_industries()
    add_default_lead_sources()
    add_territories()
    add_field_options()
    frappe.db.commit()

def add_default_lead_statuses():
    statuses = {
        "Новый": {
            "color": "gray",
            "position": 1,
        },
        "Связались": {
            "color": "orange",
            "position": 2,
        },
        "Развитие": {
            "color": "blue",
            "position": 3,
        },
        "Квалифицирован": {
            "color": "green",
            "position": 4,
        },
        "Не квалифицирован": {
            "color": "red",
            "position": 5,
        },
        "Спам": {
            "color": "purple",
            "position": 6,
        },
    }

    for status in statuses:
        if frappe.db.exists("CRM Lead Status", status):
            continue

        doc = frappe.new_doc("CRM Lead Status")
        doc.lead_status = status
        doc.color = statuses[status]["color"]
        doc.position = statuses[status]["position"]
        doc.insert(ignore_permissions=True)

def add_default_deal_statuses():
    statuses = {
        "Квалификация": {
            "color": "gray",
            "position": 1,
        },
        "Демонстрация": {
            "color": "orange",
            "position": 2,
        },
        "Предложение/КП": {
            "color": "blue",
            "position": 3,
        },
        "Переговоры": {
            "color": "yellow",
            "position": 4,
        },
        "Готов к закрытию": {
            "color": "purple",
            "position": 5,
        },
        "Выиграна": {
            "color": "green",
            "position": 6,
        },
        "Проиграна": {
            "color": "red",
            "position": 7,
        },
    }

    for status in statuses:
        if frappe.db.exists("CRM Deal Status", status):
            continue

        doc = frappe.new_doc("CRM Deal Status")
        doc.deal_status = status
        doc.color = statuses[status]["color"]
        doc.position = statuses[status]["position"]
        doc.insert(ignore_permissions=True)

def add_default_communication_statuses():
    statuses = {
        "Открыт": {
            "color": "gray",
            "position": 1,
        },
        "В работе": {
            "color": "orange",
            "position": 2,
        },
        "Завершен": {
            "color": "green",
            "position": 3,
        },
    }

    for status in statuses:
        if frappe.db.exists("CRM Communication Status", status):
            continue

        doc = frappe.new_doc("CRM Communication Status")
        doc.status = status
        doc.color = statuses[status]["color"]
        doc.position = statuses[status]["position"]
        doc.insert(ignore_permissions=True)

def add_default_fields_layout(force=False):
    quick_entry_layouts = {
        "CRM Lead-Quick Entry": {
            "doctype": "CRM Lead",
            "layout": '[{"no_tabs":true,"sections":[{"label":"Основное","name":"basic","opened":true,"fields":["organization","first_name","last_name","email","mobile_no","source","lead_owner"]}]}]',
        },
        "CRM Deal-Quick Entry": {
            "doctype": "CRM Deal",
            "layout": '[{"no_tabs":true,"sections":[{"label":"Основное","name":"basic","opened":true,"fields":["organization","deal_title","expected_closing_date","pipeline","stage","deal_owner"]}]}]',
        },
    }

    sidebar_fields_layouts = {
        "CRM Lead-Side Panel": {
            "doctype": "CRM Lead",
            "layout": '[{"no_tabs":true,"sections":[{"label":"Основное","name":"basic","opened":true,"fields":["organization","first_name","last_name","email","mobile_no","source","lead_owner"]}]}]',
        },
        "CRM Deal-Side Panel": {
            "doctype": "CRM Deal",
            "layout": '[{"no_tabs":true,"sections":[{"label":"Основное","name":"basic","opened":true,"fields":["organization","deal_title","expected_closing_date","pipeline","stage","deal_owner"]}]}]',
        },
    }

    data_fields_layouts = {
        "CRM Lead-Data Fields": {
            "doctype": "CRM Lead",
            "layout": '[{"no_tabs":true,"sections":[{"label": "Детали", "name": "details", "opened": true, "fields": ["organization", "website", "territory", "industry", "job_title", "source", "lead_owner"]}, {"label": "Контакт", "name": "person_tab", "opened": true, "fields": ["salutation", "first_name", "last_name", "email", "mobile_no"]}]}]',
        },
        "CRM Deal-Data Fields": {
            "doctype": "CRM Deal",
            "layout": '[{"no_tabs":true,"sections":[{"label":"Детали организации","name":"organization_tab","opened":true,"fields":["organization","website","territory","annual_revenue","close_date","probability","next_step","deal_owner"]}]}]',
        },
    }

    for layout in quick_entry_layouts:
        if frappe.db.exists("CRM Fields Layout", layout):
            if force:
                frappe.delete_doc("CRM Fields Layout", layout)
            else:
                continue

        doc = frappe.new_doc("CRM Fields Layout")
        doc.type = "Quick Entry"
        doc.dt = quick_entry_layouts[layout]["doctype"]
        doc.layout = quick_entry_layouts[layout]["layout"]
        doc.insert(ignore_permissions=True)

    for layout in sidebar_fields_layouts:
        if frappe.db.exists("CRM Fields Layout", layout):
            if force:
                frappe.delete_doc("CRM Fields Layout", layout)
            else:
                continue

        doc = frappe.new_doc("CRM Fields Layout")
        doc.type = "Side Panel"
        doc.dt = sidebar_fields_layouts[layout]["doctype"]
        doc.layout = sidebar_fields_layouts[layout]["layout"]
        doc.insert(ignore_permissions=True)

    for layout in data_fields_layouts:
        if frappe.db.exists("CRM Fields Layout", layout):
            if force:
                frappe.delete_doc("CRM Fields Layout", layout)
            else:
                continue

        doc = frappe.new_doc("CRM Fields Layout")
        doc.type = "Data Fields"
        doc.dt = data_fields_layouts[layout]["doctype"]
        doc.layout = data_fields_layouts[layout]["layout"]
        doc.insert(ignore_permissions=True)

def add_property_setter():
    if not frappe.db.exists("Property Setter", {"name": "Contact-main-search_fields"}):
        doc = frappe.new_doc("Property Setter")
        doc.doctype_or_field = "DocType"
        doc.doc_type = "Contact"
        doc.property = "search_fields"
        doc.property_type = "Data"
        doc.value = "email_id"
        doc.insert(ignore_permissions=True)

def add_email_template_custom_fields():
    if not frappe.get_meta("Email Template").has_field("enabled"):
        create_custom_fields(
            {
                "Email Template": [
                    {
                        "default": "0",
                        "fieldname": "enabled",
                        "fieldtype": "Check",
                        "label": "Включено",
                        "insert_after": "",
                    },
                    {
                        "fieldname": "reference_doctype",
                        "fieldtype": "Link",
                        "label": "Тип документа",
                        "options": "DocType",
                        "insert_after": "enabled",
                    },
                ]
            }
        )
        frappe.clear_cache(doctype="Email Template")

def add_default_industries():
    industries = [
        "Бухгалтерия",
        "Реклама",
        "Аэрокосмическая",
        "Сельское хозяйство",
        "Авиакомпания",
        "Одежда и аксессуары",
        "Автомобильная",
        "Банковское дело",
        "Биотехнологии",
        "Вещание",
        "Брокерская деятельность",
        "Химическая",
        "Компьютерная",
        "Консалтинг",
        "Потребительские товары",
        "Косметика",
        "Оборона",
        "Универмаги",
        "Образование",
        "Электроника",
        "Энергетика",
        "Развлечения и досуг",
        "Финансовые услуги",
        "Продукты питания",
        "Напитки и табак",
        "Продуктовые магазины",
        "Здравоохранение",
        "Интернет-издательство",
        "Инвестиционный банкинг",
        "Юридические услуги",
        "Производство",
        "Кино и видео",
        "Музыка",
        "Газетные издатели",
        "Онлайн-аукционы",
        "Пенсионные фонды",
        "Фармацевтика",
        "Частный капитал",
        "Издательское дело",
        "Недвижимость",
        "Розничная и оптовая торговля",
        "Биржи ценных бумаг и товаров",
        "Сервис",
        "Мыло и моющие средства",
        "Программное обеспечение",
        "Спорт",
        "Технологии",
        "Телекоммуникации",
        "Телевидение",
        "Транспорт",
        "Венчурный капитал",
    ]

    for industry in industries:
        if frappe.db.exists("CRM Industry", industry):
            continue

        doc = frappe.new_doc("CRM Industry")
        doc.industry = industry
        doc.insert(ignore_permissions=True)

def add_default_lead_sources():
    lead_sources = [
        "Существующий клиент",
        "Рекомендация",
        "Реклама",
        "Холодный звонок",
        "Выставка",
        "Рекомендация поставщика",
        "Массовая рассылка",
        "Поставщик клиента",
        "Кампания",
        "Посещение",
    ]

    for source in lead_sources:
        if frappe.db.exists("CRM Lead Source", source):
            continue

        doc = frappe.new_doc("CRM Lead Source")
        doc.source_name = source
        doc.insert(ignore_permissions=True)

def add_territories():
    territories = [
        "Адыгея",
        "Алтайский край",
        "Республика Алтай",
        "Амурская область",
        "Архангельская область",
        "Астраханская область",
        "Башкортостан",
        "Белгородская область",
        "Брянская область",
        "Бурятия",
        "Чеченская Республика",
        "Челябинская область",
        "Чукотский АО",
        "Чувашия",
        "Дагестан",
        "Ингушетия",
        "Иркутская область",
        "Ивановская область",
        "Еврейская АО",
        "Кабардино-Балкария",
        "Калининградская область",
        "Калмыкия",
        "Калужская область",
        "Камчатский край",
        "Карачаево-Черкесия",
        "Карелия",
        "Кемеровская область",
        "Хабаровский край",
        "Хакасия",
        "Ханты-Мансийский АО",
        "Кировская область",
        "Коми",
        "Костромская область",
        "Краснодарский край",
        "Красноярский край",
        "Курганская область",
        "Курская область",
        "Ленинградская область",
        "Липецкая область",
        "Магаданская область",
        "Марий Эл",
        "Мордовия",
        "Москва",
        "Московская область",
        "Мурманская область",
        "Ненецкий АО",
        "Нижегородская область",
        "Северная Осетия",
        "Новгородская область",
        "Новосибирская область",
        "Омская область",
        "Оренбургская область",
        "Орловская область",
        "Пензенская область",
        "Пермский край",
        "Приморский край",
        "Псковская область",
        "Республика Крым",
        "Ростовская область",
        "Рязанская область",
        "Санкт-Петербург",
        "Саха (Якутия)",
        "Сахалинская область",
        "Самарская область",
        "Саратовская область",
        "Севастополь",
        "Смоленская область",
        "Ставропольский край",
        "Свердловская область",
        "Тамбовская область",
        "Татарстан",
        "Томская область",
        "Тульская область",
        "Тыва",
        "Тверская область",
        "Тюменская область",
        "Удмуртия",
        "Ульяновская область",
        "Владимирская область",
        "Волгоградская область",
        "Вологодская область",
        "Воронежская область",
        "Ямало-Ненецкий АО",
        "Ярославская область",
        "Забайкальский край"
    ]

    for territory in territories:
        if not frappe.db.exists("CRM Territory", {"territory_name": territory}):
            doc = frappe.get_doc({
                "doctype": "CRM Territory",
                "territory_name": territory,
            })
            doc.insert(ignore_permissions=True)

def add_field_options():
    field_options = {
        "Contact": {
            "phone_type": "Рабочий\nМобильный\nДомашний\nОсновной\nДругой",
            "email_type": "Рабочий\nЛичный\nДругой"
        },
        "Address": {
            "address_type": "Юридический\nФактический\nДоставки\nМагазин\nОфис\nЛичный\nПроизводство\nСклад\nДругой"
        },
        "CRM Organization": {
            "organization_type": "Компания\nФизическое лицо\nПартнерство\nГосударственное учреждение\nТраст\nНКО"
        }
    }

    for doctype, fields in field_options.items():
        for field, options in fields.items():
            if not frappe.db.exists("Property Setter", {"doc_type": doctype, "field_name": field, "property": "options"}):
                frappe.get_doc({
                    "doctype": "Property Setter",
                    "doctype_or_field": "DocField",
                    "doc_type": doctype,
                    "field_name": field,
                    "property": "options",
                    "value": options,
                    "property_type": "Text"
                }).insert(ignore_permissions=True)