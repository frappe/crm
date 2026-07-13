/**
 * CRM Form — inline embed widget.
 *
 * Renders a published CRM form's fields directly into the host page (no iframe).
 * Usage:
 *   <div data-crm-form="your-route"></div>
 *   <script src="https://YOUR-CRM-HOST/assets/crm/js/crm_form_embed.js" async></script>
 *
 * Multiple forms per page are supported. The API host is derived from this
 * script's own src, so the same snippet works from any site.
 */
(function () {
  "use strict";

  var SELF =
    document.currentScript ||
    document.querySelector('script[src*="crm_form_embed.js"]');
  var API = SELF ? new URL(SELF.src).origin : window.location.origin;

  var STYLE_ID = "crm-embed-style";
  var THEME_ID = "crm-embed-theme";

  // Structure only — always injected. Fields/buttons inherit the host page's
  // styling so the form blends in (no borders/backgrounds/button skin of ours).
  var BASE_CSS =
    ".crm-embed-form{font-family:inherit;color:inherit;max-width:100%;box-sizing:border-box}" +
    ".crm-embed-form *,.crm-embed-form *::before,.crm-embed-form *::after{box-sizing:border-box}" +
    ".crm-embed-form .cf-title{font-weight:600;margin:0 0 6px}" +
    ".crm-embed-form .cf-desc{margin:0 0 16px}" +
    ".crm-embed-form .cf-section-title{font-weight:600;margin:18px 0 12px}" +
    ".crm-embed-form .cf-section:first-child .cf-section-title{margin-top:0}" +
    ".crm-embed-form .cf-cols{display:grid;gap:0 20px}" +
    "@media(max-width:520px){.crm-embed-form .cf-cols{grid-template-columns:1fr !important}}" +
    ".crm-embed-form .cf-field{margin-bottom:16px}" +
    ".crm-embed-form .cf-field label{display:block;margin-bottom:6px}" +
    ".crm-embed-form .cf-req{color:#e03636;margin-left:2px}" +
    ".crm-embed-form .cf-help{margin-top:5px;font-size:.85em;opacity:.75}" +
    ".crm-embed-form input,.crm-embed-form textarea,.crm-embed-form select{width:100%;font:inherit}" +
    ".crm-embed-form textarea{min-height:96px}" +
    ".crm-embed-form .cf-check{display:flex;align-items:center;gap:8px}" +
    ".crm-embed-form .cf-check input{width:auto}" +
    ".crm-embed-form .cf-check label{margin:0}" +
    ".crm-embed-form .cf-submit{margin-top:6px}" +
    ".crm-embed-form .cf-error{display:none;color:#e03636;margin-bottom:12px}" +
    ".crm-embed-form .cf-success{padding:8px 0}" +
    ".crm-embed-form .cf-redirect{margin-top:10px}";

  // Optional skin — injected only when the container has `data-crm-form-theme`.
  var THEME_CSS =
    ".crm-embed-form.cf-themed{--cf-ink:#20242b;--cf-muted:#6b7178;--cf-field:#f2f3f5;--cf-accent:#171717;color:var(--cf-ink)}" +
    ".crm-embed-form.cf-themed .cf-title{font-size:20px}" +
    ".crm-embed-form.cf-themed .cf-desc{font-size:14px;color:var(--cf-muted);line-height:1.5;margin-bottom:20px}" +
    ".crm-embed-form.cf-themed .cf-section-title{font-size:15px}" +
    ".crm-embed-form.cf-themed .cf-field label{font-size:13px;color:var(--cf-muted)}" +
    ".crm-embed-form.cf-themed .cf-help{color:var(--cf-muted)}" +
    ".crm-embed-form.cf-themed input,.crm-embed-form.cf-themed textarea,.crm-embed-form.cf-themed select{font-size:14px;line-height:1.4;color:var(--cf-ink);background:var(--cf-field);border:1px solid transparent;border-radius:8px;padding:8px 10px;outline:none;transition:border-color .12s,box-shadow .12s,background .12s}" +
    ".crm-embed-form.cf-themed textarea{resize:vertical}" +
    ".crm-embed-form.cf-themed input:focus,.crm-embed-form.cf-themed textarea:focus,.crm-embed-form.cf-themed select:focus{border-color:#c7c7cc;background:#fff;box-shadow:0 0 0 2px rgba(23,23,23,.08)}" +
    ".crm-embed-form.cf-themed .cf-submit{width:100%;font-size:14px;font-weight:500;color:#fff;background:var(--cf-accent);border:none;border-radius:8px;padding:10px 16px;cursor:pointer}" +
    ".crm-embed-form.cf-themed .cf-submit:hover{opacity:.9}" +
    ".crm-embed-form.cf-themed .cf-submit:disabled{opacity:.5;cursor:default}" +
    ".crm-embed-form.cf-themed .cf-error{background:#fdecec;border-radius:8px;padding:10px 12px}" +
    ".crm-embed-form.cf-themed .cf-success{text-align:center;padding:16px 4px}" +
    ".crm-embed-form.cf-themed .cf-success h3{font-size:18px}" +
    ".crm-embed-form.cf-themed .cf-success p{color:var(--cf-muted);font-size:14px}";

  function injectStyle(themed) {
    if (!document.getElementById(STYLE_ID)) {
      var s = document.createElement("style");
      s.id = STYLE_ID;
      s.textContent = BASE_CSS;
      (document.head || document.documentElement).appendChild(s);
    }
    if (themed && !document.getElementById(THEME_ID)) {
      var t = document.createElement("style");
      t.id = THEME_ID;
      t.textContent = THEME_CSS;
      (document.head || document.documentElement).appendChild(t);
    }
  }

  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    if (attrs) for (var k in attrs) n.setAttribute(k, attrs[k]);
    if (text != null) n.textContent = text;
    return n;
  }

  function labelFor(f) {
    var lbl = el("label", { for: "cf-" + f.fieldname }, f.label || f.fieldname);
    if (f.reqd) lbl.appendChild(el("span", { class: "cf-req" }, "*"));
    return lbl;
  }

  function buildControl(f) {
    var id = "cf-" + f.fieldname;
    var ft = f.fieldtype;
    if (ft === "Check") {
      var wrap = el("div", { class: "cf-check" });
      wrap.appendChild(el("input", { type: "checkbox", id: id, name: f.fieldname }));
      var l = el("label", { for: id }, f.label || f.fieldname);
      if (f.reqd) l.appendChild(el("span", { class: "cf-req" }, "*"));
      wrap.appendChild(l);
      return { control: wrap, input: wrap.querySelector("input"), noLabel: true };
    }
    var input;
    if (ft === "Small Text" || ft === "Text" || ft === "Long Text") {
      input = el("textarea", { id: id, name: f.fieldname });
      if (f.placeholder) input.placeholder = f.placeholder;
    } else if (ft === "Select") {
      input = el("select", { id: id, name: f.fieldname });
      input.appendChild(el("option", { value: "" }, f.placeholder || "Select…"));
      (f.options || "").split("\n").forEach(function (opt) {
        opt = opt.trim();
        if (opt) input.appendChild(el("option", { value: opt }, opt));
      });
    } else {
      var type = "text";
      if (f.options === "Email") type = "email";
      else if (f.options === "Phone" || ft === "Phone") type = "tel";
      else if (ft === "Int" || ft === "Float" || ft === "Currency") type = "number";
      else if (ft === "Date") type = "date";
      else if (ft === "Datetime") type = "datetime-local";
      input = el("input", { type: type, id: id, name: f.fieldname });
      if (f.placeholder) input.placeholder = f.placeholder;
    }
    if (f.reqd) input.required = true;
    return { control: input, input: input, noLabel: false };
  }

  // group flat fields (with Section/Column breaks) into sections -> columns
  function layout(fields) {
    var sections = [];
    var cur = { label: null, columns: [[]] };
    fields.forEach(function (f) {
      if (f.fieldtype === "Section Break") {
        sections.push(cur);
        cur = { label: f.label || null, columns: [[]] };
      } else if (f.fieldtype === "Column Break") {
        cur.columns.push([]);
      } else {
        cur.columns[cur.columns.length - 1].push(f);
      }
    });
    sections.push(cur);
    return sections.filter(function (s) {
      return s.label || s.columns.some(function (c) { return c.length; });
    });
  }

  function render(container, cfg, themed) {
    var inputs = {}; // fieldname -> { input, field }
    var root = el("div", { class: "crm-embed-form" + (themed ? " cf-themed" : "") });

    var view = el("div");
    if (cfg.title) view.appendChild(el("div", { class: "cf-title" }, cfg.title));
    if (cfg.description) view.appendChild(el("div", { class: "cf-desc" }, cfg.description));

    var errBox = el("div", { class: "cf-error" });
    view.appendChild(errBox);

    var form = el("form", { novalidate: "novalidate" });
    layout(cfg.fields).forEach(function (section) {
      var sec = el("div", { class: "cf-section" });
      if (section.label) sec.appendChild(el("div", { class: "cf-section-title" }, section.label));
      var cols = el("div", { class: "cf-cols" });
      cols.style.gridTemplateColumns = "repeat(" + section.columns.length + ",minmax(0,1fr))";
      section.columns.forEach(function (col) {
        var colEl = el("div");
        col.forEach(function (f) {
          var field = el("div", { class: "cf-field" });
          var built = buildControl(f);
          if (!built.noLabel) field.appendChild(labelFor(f));
          field.appendChild(built.control);
          if (f.description) field.appendChild(el("div", { class: "cf-help" }, f.description));
          colEl.appendChild(field);
          inputs[f.fieldname] = { input: built.input, field: f };
        });
        cols.appendChild(colEl);
      });
      sec.appendChild(cols);
      form.appendChild(sec);
    });

    var btn = el("button", { type: "submit", class: "cf-submit" }, cfg.submit_button_label || "Submit");
    form.appendChild(btn);
    view.appendChild(form);
    root.appendChild(view);

    var success = el("div", { class: "cf-success" });
    success.style.display = "none";
    success.appendChild(el("h3", null, cfg.success_message || "Thank you!"));
    success.appendChild(el("p", null, "Your response has been recorded."));
    var redirectNote = el("p", { class: "cf-redirect" });
    redirectNote.style.display = "none";
    success.appendChild(redirectNote);
    root.appendChild(success);

    function showError(msg) {
      errBox.textContent = msg || "Something went wrong. Please try again.";
      errBox.style.display = "block";
    }

    function collect() {
      var values = {};
      for (var fn in inputs) {
        var it = inputs[fn];
        values[fn] = it.field.fieldtype === "Check" ? (it.input.checked ? 1 : 0) : it.input.value;
      }
      return values;
    }

    function redirectWithCountdown(url) {
      var secs = 5;
      var link = el("a", { href: url }, "Go now");
      redirectNote.style.display = "block";
      function draw() {
        redirectNote.textContent = "Redirecting in " + secs + (secs === 1 ? " second… " : " seconds… ");
        redirectNote.appendChild(link);
      }
      draw();
      var iv = setInterval(function () {
        secs -= 1;
        if (secs <= 0) { clearInterval(iv); window.location.assign(url); return; }
        draw();
      }, 1000);
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      errBox.style.display = "none";
      var values = collect();
      var missing = null;
      for (var fn in inputs) {
        var it = inputs[fn];
        if (it.field.reqd) {
          var v = values[fn];
          if (v === "" || v === null || v === undefined || v === 0 && it.field.fieldtype === "Check") {
            if (it.field.fieldtype === "Check" ? !it.input.checked : String(v).trim() === "") {
              missing = it.field; break;
            }
          }
        }
      }
      if (missing) {
        showError("Please fill in the required field: " + (missing.label || missing.fieldname));
        if (inputs[missing.fieldname].input.focus) inputs[missing.fieldname].input.focus();
        return;
      }

      btn.disabled = true;
      var original = btn.textContent;
      btn.textContent = "Submitting…";

      var body = new URLSearchParams();
      body.set("route", cfg.route);
      body.set("values", JSON.stringify(values));

      fetch(API + "/api/method/crm.api.form.submit_form", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: body.toString(),
      })
        .then(function (r) {
          return r.json().then(function (data) { return { ok: r.ok, data: data }; });
        })
        .then(function (res) {
          if (!res.ok) {
            var m = res.data && res.data._server_messages;
            var msg = "";
            try { msg = m ? JSON.parse(JSON.parse(m)[0]).message : ""; } catch (e) {}
            showError(msg || "Sorry, we couldn't submit your response. Please try again.");
            btn.disabled = false;
            btn.textContent = original;
            return;
          }
          view.style.display = "none";
          success.style.display = "block";
          if (cfg.redirect_url) redirectWithCountdown(cfg.redirect_url);
        })
        .catch(function () {
          showError();
          btn.disabled = false;
          btn.textContent = original;
        });
    });

    container.innerHTML = "";
    container.appendChild(root);
  }

  function mount(container) {
    var route = container.getAttribute("data-crm-form");
    if (!route || container.getAttribute("data-crm-form-mounted")) return;
    container.setAttribute("data-crm-form-mounted", "1");
    // opt into the built-in skin with data-crm-form-theme; default inherits host
    var themed = container.hasAttribute("data-crm-form-theme");
    fetch(API + "/api/method/crm.api.form.get_form?route=" + encodeURIComponent(route))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var cfg = data && data.message;
        if (!cfg) throw new Error("no config");
        injectStyle(themed);
        render(container, cfg, themed);
      })
      .catch(function () {
        container.textContent = "Unable to load form.";
      });
  }

  function init() {
    var nodes = document.querySelectorAll("[data-crm-form]");
    for (var i = 0; i < nodes.length; i++) mount(nodes[i]);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
