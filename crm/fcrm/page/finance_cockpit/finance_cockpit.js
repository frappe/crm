frappe.pages["finance-cockpit"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "Finance Cockpit",
        single_column: true,
    });
    // Inject the Vue mount target
    $(page.body).html('<div id="finance-cockpit-root" style="height:calc(100vh - 60px);overflow:hidden;"></div>');
    // Load the Finance Cockpit bundle. Frappe's frappe.require resolves asset paths
    // via the manifest. The HTML entry (finance-cockpit.html) is served at
    // /assets/crm/frontend/finance-cockpit.html and contains the hashed script/css refs.
    // We inject them directly here so they work without an iframe.
    var base = "/assets/crm/frontend/";
    fetch(base + "finance-cockpit.html")
        .then(function(r) { return r.text(); })
        .then(function(html) {
            var parser = new DOMParser();
            var doc = parser.parseFromString(html, "text/html");
            // Inject CSS links
            doc.querySelectorAll('link[rel="stylesheet"]').forEach(function(link) {
                if (!document.querySelector('link[href="' + link.href + '"]')) {
                    document.head.appendChild(link.cloneNode(true));
                }
            });
            // Inject module script
            doc.querySelectorAll('script[type="module"]').forEach(function(s) {
                var script = document.createElement("script");
                script.type = "module";
                script.src = s.src;
                document.head.appendChild(script);
            });
        });
};
