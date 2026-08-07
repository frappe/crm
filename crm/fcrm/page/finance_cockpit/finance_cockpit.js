frappe.pages["finance-cockpit"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Finance Cockpit",
        single_column: true,
    });
    $(page.body).html('<div id="finance-cockpit-root" style="height:calc(100vh - 60px);overflow:hidden;"></div>');

    // Bridge frappe-ui's CSRF expectation: frappe-ui reads window.csrf_token,
    // but the Frappe Desk exposes it at frappe.csrf_token.
    window.csrf_token = frappe.csrf_token;

    var base = "/assets/crm/frontend/";
    fetch(base + "finance-cockpit.html")
        .then(function(r) { return r.text(); })
        .then(function(html) {
            var parser = new DOMParser();
            var doc = parser.parseFromString(html, "text/html");
            doc.querySelectorAll('link[rel="stylesheet"]').forEach(function(link) {
                if (!document.querySelector('link[href="' + link.href + '"]')) {
                    document.head.appendChild(link.cloneNode(true));
                }
            });
            doc.querySelectorAll('script[type="module"]').forEach(function(s) {
                var script = document.createElement("script");
                script.type = "module";
                script.src = s.src;
                document.head.appendChild(script);
            });
        });
};
