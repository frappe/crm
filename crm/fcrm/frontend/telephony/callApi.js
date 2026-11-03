// The server calls behind the call window: REST API v2 through the framework's `runMethod`.
import { runMethod } from "@framework/ui/api";

const ask = (method, args, options) =>
  runMethod(method, args, options).then(({ data }) => data);

export const callApi = {
  callingMedia: () =>
    ask("crm.integrations.api.get_calling_media", {}, { http: "GET" }),
  token: () => ask("crm.integrations.twilio.api.generate_access_token"),
  contact: (number) =>
    ask(
      "crm.integrations.api.get_contact_by_phone_number",
      { phone_number: number },
      { http: "GET" }
    ),
  link: (callSid, doctype, docname) =>
    ask("crm.integrations.api.link_to_call_log", {
      call_sid: callSid,
      doctype,
      // A CRM Task's name is a number; the method types it as a string.
      docname: String(docname),
    }),
};
