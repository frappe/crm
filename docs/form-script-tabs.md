# Custom Tabs in Form Scripts

A Form Script can add its own tab to the Lead and Deal pages, beside the
built-in Activity, Emails, Comments, Data, Calls, Tasks, Notes and Attachments
tabs. This is how another app — a support inbox, a telephony app, a shipping
tracker — puts its own screen inside the record your sales team is already
looking at, instead of making them switch apps.

Create the script from **Settings → Form Scripts**, or insert a `CRM Form
Script` record from your own app.

## A minimal tab

```js
class CRMDeal {
  onLoad() {
    this.tabs.push({
      name: "Shipping",
      label: __("Shipping"),
      component: {
        props: ["doctype", "docname", "doc"],
        setup(props) {
          return () =>
            h("div", { class: "p-5 text-ink-gray-8" }, [
              `Tracking for ${props.doc.organization}`,
            ]);
        },
      },
    });
  }
}
```

Form Scripts run without a template compiler, so build the pane with the `h`
helper (Vue's `createElement`) rather than a `template` string. `h` is
available in every script, like `call` and `toast`.

## Embedding another app

Because the pane is yours, an iframe pointing at your own app works too:

```js
class CRMDeal {
  onLoad() {
    this.tabs.push({
      name: "Inbox",
      label: __("Inbox"),
      component: {
        props: ["docname"],
        setup(props) {
          return () =>
            h("iframe", {
              src: `/my-app/deal/${props.docname}`,
              class: "w-full h-full border-0",
            });
        },
      },
    });
  }
}
```

## Options

| Key         | Type      | Description                                                                                                |
| ----------- | --------- | ---------------------------------------------------------------------------------------------------------- |
| `name`      | string    | **Required.** Unique key for the tab. Also drives the `#hash` in the URL and the "last visited tab" memory |
| `label`     | string    | Text shown in the tab bar. Wrap it in `__()` so it can be translated                                       |
| `icon`      | component | Optional icon component                                                                                    |
| `component` | component | The pane. Receives `doctype`, `docname`, `doc` and `tab` as props                                          |
| `condition` | function  | Optional. Return a falsy value to hide the tab                                                             |

## How it behaves

- **A tab owns its whole pane.** When a tab has a `component`, none of the
  built-in furniture is rendered for it: not the activity timeline, not the
  empty state, not the reply box, and not the header's action button. That
  holds even when you patch a built-in tab such as `Emails` or `WhatsApp`.
- **Matching an existing name patches that tab** rather than adding a second
  one. Pushing `{ name: "Emails", label: "Inbox" }` relabels the built-in
  Emails tab and leaves everything else about it alone.
- **A broken tab is skipped, not fatal.** Entries without a `name` are ignored,
  and a `condition` that throws hides only that tab.
- **Mobile is included.** The same tab appears on the mobile Lead and Deal
  pages.
- **Order is stable.** Built-in tabs keep their positions; your tab is appended
  after them.

## Where the tab is remembered

CRM stores the last tab you were on per doctype and reflects it in the URL
hash, so `#shipping` links straight to your tab. That lookup is by `name`, so
keep `name` stable across releases of your app — changing it will drop users
back to the first tab.
