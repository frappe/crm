# ERPNext Customers and CRM Organizations

Keep ERPNext company customers visible in CRM without creating a sales deal for
each customer. Customer synchronization creates or links a CRM Organization and
keeps the saved Customer–Organization identities together across later updates.

Open **Settings → ERPNext Settings → Customers** to synchronize customers and
review their links. This works when ERPNext and CRM share a site or run on
separate sites. Individual Customers keep their existing person and deal flow;
they are not converted into organizations.

## Connect the ERPNext site

Enable and save the ERPNext integration first. For separate sites, save and
verify the site URL, API key and API secret using the existing connection
settings. The ERPNext integration user must be allowed to read the relevant
customers and their related contact and address records and update the customer
link. Both applications must provide the customer synchronization APIs.

Users who can manage the integration can synchronize customers and resolve
review records. Native Organization, Contact and Address permissions still
apply to the records being created or updated.

## Run a synchronization

In the **Customers** tab, select **Sync Customers**. The synchronization runs in
the background, so a large customer list does not have to finish while the
settings dialog is open. Results refresh automatically for up to two minutes;
use **Refresh** to read later results. Closing the settings dialog does not
cancel the background job.

The run status above the list shows whether the background job is queued,
running, completed or failed. A failure before customer processing starts, such
as a connection or permission failure, appears there even when no individual
review records exist. Previous audit rows remain the last saved results. Read
the message, fix its cause, then use **Sync Customers** to retry. A completed
job can still contain customers in **Review** or **Failed** status.

Manual synchronization is available even when automatic synchronization is off.
To enable automatic updates, turn on **Sync ERPNext Customers** in **General
Settings** and save. On a shared site, company Customer updates schedule a
synchronization. Separate sites are checked by the scheduled synchronization.
Background workers and the scheduler must be running.

Save changes to the connection settings before starting a sync or resolving a
customer link. The review list belongs to the saved ERPNext connection.

## Understand the results

Search by Customer name or ID and use **Status** to narrow the paginated review
list. Each row shows the ERPNext Customer, CRM Organization, matching rule,
latest attempt and any message requiring attention. **Review** also shows the
latest successful synchronization.

| Status   | Meaning                                                                                             |
| -------- | --------------------------------------------------------------------------------------------------- |
| Pending  | The customer has not completed reconciliation.                                                      |
| Synced   | A Customer–Organization link and its imported values were saved.                                    |
| Review   | A match, existing reference or changed CRM value needs an explicit decision.                        |
| Failed   | The operation could not finish. Read the message, fix its cause and review the record again.        |
| Ignored  | Automatic synchronization skips this customer until it is explicitly reviewed again.                |
| Unlinked | The association was removed. Automatic synchronization leaves it unlinked until an explicit review. |

Synchronization first respects saved Customer–Organization references, including
compatible links from existing deals. For a customer without a saved reference,
it can use a unique Tax ID or an exact normalized organization name. Ambiguous
or conflicting references require review. After linking, the persisted record
IDs own the relationship; a later display-name change does not create another
identity.

## Review a customer

Open **Review** on the row and choose an action. Available actions depend on its
status and Customer type:

- **Link Organization** associates the Customer with an existing organization
  selected through the native picker and approves applying the imported fields.
- **Create Organization** creates a new organization for an ERPNext company
  Customer. Use this only after checking existing organizations.
- **Resync** approves applying the current ERPNext-owned organization values
  and the related contact and address mappings. Use it to accept an ERPNext
  value after a CRM edit caused a review, or to resume an ignored or unlinked
  customer.
- **Ignore** excludes the Customer from automatic synchronization without
  deleting either record.
- **Unlink** removes the association without deleting the Customer or
  Organization. Automatic synchronization does not recreate it until an
  explicit review.

If a separate ERPNext site's unlink cannot be confirmed, the audit row keeps
its previous Organization reference with **Unlinked** status and a message.
Refresh the results, then choose **Review → Retry Unlink** to finish removing
the remote association. Resync stays unavailable while that unlink is pending.

Review actions use the audit revision you opened. If another process changed
the record, close and refresh the list before reviewing it again. An action
error stays in the dialog and is not retried automatically. If the result could
not be confirmed, refresh and inspect the saved records before making another
change.

## Which application owns the information?

ERPNext owns the imported organization name, website and Tax ID. Industry,
territory and currency can also be imported when the corresponding native
reference exists in CRM. If a populated CRM value has diverged from the last
synchronized value, automatic synchronization records **Review** rather than
silently overwriting the edit. An explicit Link, Create or Resync approves
applying the current ERPNext values.

Contacts and addresses remain separate records. On a shared site, CRM and
ERPNext use the same native records; synchronization does not duplicate or
reparent people. Across separate sites, imported records are identified by their
source site and source record ID. Matching email addresses, phone numbers or
display names do not claim an unrelated existing contact. Automatic updates
preserve divergent local contact and address edits by marking the Customer for
**Review**. Explicit review approves applying the current ERPNext values.
Native renames of linked Contacts or Addresses require manual review of their
saved mappings.

These operations manage CRM organization information and Customer links. They
do not change ERPNext accounting records, create placeholder deals, or turn a
real sales opportunity into an organization record.
