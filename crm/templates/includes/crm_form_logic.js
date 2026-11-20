{#- Conditional logic for CRM web form fields, shared by www/crm_form.html and
www/crm_book.html. Included inside each page's script, which must define FIELDS
(from form_fields_context) and BREAKS beforehand. -#}
        // Field interdependencies: apply the DocType's depends_on / mandatory_depends_on
        // / read_only_depends_on client-side, same rules as the Desk form.
        function collectDoc() {
          var doc = {};
          FIELDS.forEach(function (f) {
            if (BREAKS[f.fieldtype]) return;
            var el = document.getElementById(f.fieldname);
            if (!el) return;
            doc[f.fieldname] = f.fieldtype === "Check" ? (el.checked ? 1 : 0) : el.value;
          });
          return doc;
        }
        // security boundary; tested by frontend/tests/unit/webFormConditionalEval.test.js
        // [conditional-eval:start]
        function coerce(v) {
          return Array.isArray(v) ? v.length > 0 : !!v;
        }
        // Parse (never execute) an "eval:" expression, so stored metadata can't run JS on
        // this public page. Supports doc/parent access, literals, comparisons, && || !,
        // and parentheses; anything else throws → caller's fallback.
        function safeEval(src, doc, parent) {
          var i = 0;
          function ws() {
            while (i < src.length && /\s/.test(src[i])) i++;
          }
          function starts(tok) {
            ws();
            return src.substr(i, tok.length) === tok;
          }
          function primary() {
            ws();
            if (starts("(")) {
              i++;
              var e = orExpr();
              ws();
              if (!starts(")")) throw new Error("expected )");
              i++;
              return e;
            }
            if (starts("!")) {
              i++;
              return !coerce(primary());
            }
            var ch = src[i];
            if (ch === '"' || ch === "'") {
              i++;
              var str = "";
              while (i < src.length && src[i] !== ch) {
                if (src[i] === "\\") i++;
                str += src[i++];
              }
              i++;
              return str;
            }
            var num = /^-?\d+(?:\.\d+)?/.exec(src.slice(i));
            if (num) {
              i += num[0].length;
              return parseFloat(num[0]);
            }
            var id = /^[A-Za-z_$][\w$]*/.exec(src.slice(i));
            if (!id) throw new Error("unexpected token");
            i += id[0].length;
            if (id[0] === "true") return true;
            if (id[0] === "false") return false;
            if (id[0] === "null") return null;
            var base;
            if (id[0] === "doc") base = doc;
            else if (id[0] === "parent") base = parent;
            else throw new Error("unknown identifier: " + id[0]); // no globals reachable
            for (;;) {
              ws();
              if (src[i] === ".") {
                i++;
                var m = /^[A-Za-z_$][\w$]*/.exec(src.slice(i));
                if (!m) throw new Error("bad member");
                i += m[0].length;
                base = base == null ? undefined : base[m[0]];
              } else if (src[i] === "[") {
                i++;
                var key = orExpr();
                ws();
                if (!starts("]")) throw new Error("expected ]");
                i++;
                base = base == null ? undefined : base[key];
              } else break;
            }
            return base;
          }
          function cmp() {
            var l = primary();
            ws();
            var ops = ["===", "!==", "==", "!=", "<=", ">=", "<", ">"];
            for (var k = 0; k < ops.length; k++) {
              if (src.substr(i, ops[k].length) === ops[k]) {
                i += ops[k].length;
                var r = primary();
                switch (ops[k]) {
                  case "===":
                  case "==":
                    return l == r; // eslint-disable-line eqeqeq
                  case "!==":
                  case "!=":
                    return l != r; // eslint-disable-line eqeqeq
                  case "<":
                    return l < r;
                  case "<=":
                    return l <= r;
                  case ">":
                    return l > r;
                  case ">=":
                    return l >= r;
                }
              }
            }
            return l;
          }
          function andExpr() {
            var l = cmp();
            while (starts("&&")) {
              i += 2;
              var r = cmp();
              l = coerce(l) && coerce(r);
            }
            return l;
          }
          function orExpr() {
            var l = andExpr();
            while (starts("||")) {
              i += 2;
              var r = andExpr();
              l = coerce(l) || coerce(r);
            }
            return l;
          }
          var out = orExpr();
          ws();
          if (i < src.length) throw new Error("trailing input");
          return out;
        }
        // `fallback` covers an empty, unsupported, or invalid expression
        function truthy(expr, doc, fallback) {
          var s = expr ? String(expr).trim() : "";
          if (!s) return fallback;
          try {
            if (s.slice(0, 5) === "eval:") return coerce(safeEval(s.slice(5), doc, doc));
            if (s.slice(0, 3) === "fn:") return fallback;
            return coerce(doc[s]);
          } catch (e) {
            return fallback;
          }
        }
        // [conditional-eval:end]
        function isVisible(f, doc) {
          return truthy(f.depends_on, doc, true);
        }
        function isRequired(f, doc) {
          return f.reqd ? true : truthy(f.mandatory_depends_on, doc, false);
        }
        function isReadOnly(f, doc) {
          return truthy(f.read_only_depends_on, doc, false);
        }

        // apply the rules to the DOM: toggle visibility, read-only, and the required *
        function refreshDeps() {
          var doc = collectDoc();
          FIELDS.forEach(function (f) {
            if (BREAKS[f.fieldtype]) return;
            var el = document.getElementById(f.fieldname);
            if (!el) return;
            var wrap = el.closest(".field");
            var visible = isVisible(f, doc);
            if (wrap) wrap.style.display = visible ? "" : "none";

            var ro = isReadOnly(f, doc);
            // selects/checkboxes have no readOnly; disable them (JS still reads .value)
            if (f.fieldtype === "Check" || f.fieldtype === "Select" || f.fieldtype === "Link") {
              el.disabled = ro;
            } else {
              el.readOnly = ro;
            }

            // toggle the * for a conditionally-mandatory field (static ones keep theirs)
            if (wrap && !f.reqd) {
              var star = wrap.querySelector(".req");
              if (star) star.style.display = visible && isRequired(f, doc) ? "" : "none";
            }
          });
        }
