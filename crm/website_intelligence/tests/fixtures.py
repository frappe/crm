"""Offline HTML fixtures for deterministic, network-free tests."""

HOMEPAGE = """
<!doctype html>
<html>
<head>
  <title>Acme Analytics | AI powered SaaS</title>
  <meta name="description" content="Acme is an AI powered analytics platform.">
  <meta property="og:site_name" content="Acme Analytics">
  <meta property="og:description" content="Real-time analytics for modern teams.">
  <meta property="og:image" content="https://acme.example/logo.png">
  <script type="application/ld+json">
  {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "Acme Analytics Inc.",
    "description": "AI powered analytics SaaS for product teams.",
    "logo": {"url": "https://acme.example/ld-logo.png"},
    "sameAs": [
      "https://www.linkedin.com/company/acme-analytics",
      "https://twitter.com/acmeanalytics",
      "https://github.com/acme"
    ],
    "address": {
      "@type": "PostalAddress",
      "streetAddress": "100 Market St",
      "addressLocality": "San Francisco",
      "addressRegion": "CA",
      "postalCode": "94103",
      "addressCountry": "US"
    }
  }
  </script>
  <script src="/_next/static/chunk.js"></script>
  <script src="https://www.googletagmanager.com/gtag/js?id=G-XXededXX"></script>
</head>
<body>
  <h1>AI powered analytics</h1>
  <h2>We are hiring across engineering</h2>
  <nav>
    <a href="/about">About</a>
    <a href="/contact">Contact</a>
    <a href="/team">Team</a>
    <a href="/careers">Careers</a>
    <a href="https://facebook.com/sharer?u=x">Share</a>
    <a href="https://instagram.com/acmeanalytics">Instagram</a>
    <a href="https://external-site.com/page">External</a>
  </nav>
  <p>Contact us at hello@acme.example or call <a href="tel:+1 415 555 0142">us</a>.</p>
  <p>Our subscription pricing plans start free. Customer relationship tooling.</p>
</body>
</html>
"""

ABOUT = """
<!doctype html>
<html><head><title>About Acme</title></head>
<body>
  <h1>About Acme</h1>
  <p>We raised a Series A round and are backed by great investors.</p>
  <div class="team">
    <div class="member"><div class="name">Jane Doe</div><div class="role">CEO &amp; Co-Founder</div></div>
    <div class="member"><div class="name">John Smith</div><div class="role">CTO</div></div>
    <div class="member"><div class="name">Senior Vice President</div><div class="role">VP</div></div>
    <div class="member"><div class="name">About Acme</div><div class="role">Director</div></div>
  </div>
  <p>Reach finance at billing@acme.example.</p>
</body></html>
"""

CONTACT = """
<!doctype html>
<html><head><title>Contact Acme</title></head>
<body>
  <h1>Contact</h1>
  <p>Head office: 100 Market St, San Francisco, CA, 94103, United States</p>
  <p>Email: sales@acme.example</p>
  <p>Phone: +1 (415) 555-0199</p>
</body></html>
"""

WORDPRESS = """
<html><head><meta name="generator" content="WordPress 6.4"></head>
<body><img src="/wp-content/uploads/x.png"><script src="/wp-json/index.js"></script></body></html>
"""

EMPTY = "<html><head></head><body></body></html>"

BROKEN_JSON_LD = """
<html><head>
<script type="application/ld+json">{ this is not valid json ]</script>
<title>Broken Co</title>
</head><body><h1>Broken</h1></body></html>
"""
