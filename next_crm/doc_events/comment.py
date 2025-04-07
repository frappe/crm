from next_crm.api.comment import notify_mentions


def on_update(doc, method=None):
    notify_mentions(doc)
