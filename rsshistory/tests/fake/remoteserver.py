remote_server_json = """
[
  {
    "data": {
      "album": null,
      "author": null,
      "date_published": "Wed, 22 Jan 2025 08:49:28 GMT",
      "description": "Google News",
      "language": "en-US",
      "link": "https://news.google.com/rss?topic=h",
      "page_rating": 86,
      "tags": null,
      "thumbnail": "https://lh3.googleusercontent.com/-DR60l-K8vnyi99NZovm9HlXyZwQ85GMDxiwJWzoasZYCUrPuUM_P_4Rb7ei03j-0nRs0c4F=w256",
      "title": "Top stories - Google News"
    },
    "name": "Properties"
  },
  {
    "data": {
      "Text": "dataatatatatatat"
    },
    "name": "Contents"
  },
  {
    "data": {
      "Options Ping": false,
      "Options SSL": true,
      "Options mode mapping": "[{'enabled': True, 'name': 'RequestsCrawler', 'crawler': <class 'rsshistory.webtools.crawlers.RequestsCrawler'>, 'settings': {'timeout_s': 20}}, {'enabled': True, 'name': 'CrawleeScript', 'crawler': <class 'rsshistory.webtools.crawlers.ScriptCrawler'>, 'settings': {'script': 'poetry run python crawleebeautifulsoup.py', 'timeout_s': 40}}, {'enabled': True, 'name': 'PlaywrightScript', 'crawler': <class 'rsshistory.webtools.crawlers.ScriptCrawler'>, 'settings': {'script': 'poetry run python crawleebeautifulsoup.py', 'timeout_s': 40}}, {'enabled': False, 'name': 'SeleniumUndetected', 'crawler': <class 'rsshistory.webtools.crawlers.SeleniumUndetected'>, 'settings': {'driver_executable': '/usr/bin/chromedriver', 'timeout_s': 30}}, {'enabled': False, 'name': 'SeleniumBase', 'crawler': <class 'rsshistory.webtools.crawlers.SeleniumBase'>, 'settings': {}}, {'enabled': False, 'name': 'SeleniumChromeHeadless', 'crawler': <class 'rsshistory.webtools.crawlers.SeleniumChromeHeadless'>, 'settings': {'driver_executable': '/usr/bin/chromedriver', 'timeout_s': 30}}, {'enabled': False, 'name': 'SeleniumChromeFull', 'crawler': <class 'rsshistory.webtools.crawlers.SeleniumChromeFull'>, 'settings': {'driver_executable': '/usr/bin/chromedriver', 'timeout_s': 40}}, {'enabled': True, 'name': 'StealthRequestsCrawler', 'crawler': <class 'rsshistory.webtools.crawlers.StealthRequestsCrawler'>, 'settings': {'timeout_s': 20}}]",
      "Options use browser promotions": true,
      "Options user agent": "None",
      "Page Handler": "HttpPageHandler",
      "Page Type": "RssPage"
    },
    "name": "Settings"
  },
  {
    "data": {
      "Charset": "utf-8",
      "Content-Length": 110398,
      "Content-Type": "application/xml; charset=utf-8",
      "Last-Modified": null,
      "body_hash": "mvuJFx9/IcGamcMZRimFKA==",
      "crawler_data": {
        "crawler": "RequestsCrawler",
        "enabled": true,
        "name": "RequestsCrawler",
        "settings": {
          "timeout_s": 20
        }
      },
      "hash": "ps5UtH1oTRjHyS+PQSqg4Q==",
      "is_valid": true,
      "status_code": 200
    },
    "name": "Response"
  },
  {
    "data": {
      "Accept-CH": "Sec-CH-UA-Arch, Sec-CH-UA-Bitness, Sec-CH-UA-Full-Version, Sec-CH-UA-Full-Version-List, Sec-CH-UA-Model, Sec-CH-UA-WoW64, Sec-CH-UA-Form-Factors, Sec-CH-UA-Platform, Sec-CH-UA-Platform-Version",
      "Accept-Ranges": "none",
      "Alt-Svc": "ma=2592000",
      "Cache-Control": "no-cache, no-store, max-age=0, must-revalidate",
      "Charset": "utf-8",
      "Content-Length": 110398,
      "Content-Security-Policy": "script-src 'nonce-NXhJyskj4EA7aDMPHhRT4w' 'unsafe-inline';object-src 'none';base-uri 'self';report-uri /_/DotsSplashUi/cspreport;worker-src 'self', script-src 'unsafe-inline' 'unsafe-eval' blob: data: 'self' https://apis.google.com https://ssl.gstatic.com https://www.google.com https://www.googletagmanager.com https://www.gstatic.com https://www.google-analytics.com https://support.google.com/inapp/ https://www.google.com/tools/feedback/ https://www.gstatic.com/inproduct_help/ https://www.gstatic.com/support/content/ https://youtube.com https://www.youtube.com https://youtube.googleapis.com https://*.ytimg.com https://ajax.googleapis.com https://www.googleapis.com/appsmarket/v2/installedApps/;report-uri /_/DotsSplashUi/cspreport/allowlist, require-trusted-types-for 'script';report-uri /_/DotsSplashUi/cspreport",
      "Content-Type": "application/xml; charset=utf-8",
      "Cross-Origin-Opener-Policy": "same-origin-allow-popups",
      "Cross-Origin-Resource-Policy": "same-site",
      "Date": "Wed, 22 Jan 2025 08:49:28 GMT",
      "Expires": "Mon, 01 Jan 1990 00:00:00 GMT",
      "Permissions-Policy": "ch-ua-arch=*, ch-ua-bitness=*, ch-ua-full-version=*, ch-ua-full-version-list=*, ch-ua-model=*, ch-ua-wow64=*, ch-ua-form-factors=*, ch-ua-platform=*, ch-ua-platform-version=*",
      "Pragma": "no-cache",
      "Server": "ESF",
      "Strict-Transport-Security": "max-age=31536000",
      "Transfer-Encoding": "chunked",
      "Vary": "Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site,Accept-Encoding",
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "SAMEORIGIN",
      "X-XSS-Protection": "0",
      "reporting-endpoints": "default=/_/DotsSplashUi/web-reports?context=eJzjitDikmJw05BikPj6kkkNiJ3SZ7AGAPHnHTNYW2-eY50MxEZrz7M6AHHSv_OsBUDcUXqB1VDhEqs9EF9Ov8Sq2nOJ1RiIiySusDYAsa_2VVYhHo4Zjw7tYRN48fT_PSYl5aT8wviU_JLi4oKcxOKM4tSistSieCMDI1MDQ0MTPQOz-AJDAIrlNxw"
    },
    "name": "Headers"
  },
  {
    "data": [
      {
        "album": "",
        "author": null,
        "bookmarked": false,
        "date_published": "Tue, 21 Jan 2025 13:24:42 GMT",
        "description": "<ol><li><a href=https://news.google.com/rss/articles/CBMimwFBVV95cUxQM3hQekZ1S2ZxME1uSFJjSEVJX2QwNndtWlBWMElxNTJIY0MtQVpuRGppMXF4UFl3OFdFWUFTdjdEOEZ2SGF0RjVZUkZNdXBONF9NOGFUXzVWOEhQai1MYTlsSkZ5em1oLWJIcm5ETUdJN0hQUi10RUVQXzBEbWNhM1loN2ZFNnZtVHlORVY0S3VraG9xVkN5eXN1cw?oc=5",
        "language": "en-US",
        "link": "https://news.google.com/rss/articles/CBMimwFBVV95cUxQM3hQekZ1S2ZxME1uSFJjSEVJX2QwNndtWlBWMElxNTJIY0MtQVpuRGppMXF4UFl3OFdFWUFTdjdEOEZ2SGF0RjVZUkZNdXBONF9NOGFUXzVWOEhQai1MYTlsSkZ5em1oLWJIcm5ETUdJN0hQUi10RUVQXzBEbWNhM1loN2ZFNnZtVHlORVY0S3VraG9xVkN5eXN1cw?oc=5",
        "page_rating": 86,
        "source": "https://news.google.com/rss?topic=h",
        "tags": null,
        "thumbnail": null,
        "title": "HHS gives Moderna $590M to 'accelerate' bird flu vaccine trials - Fierce Biotech"
      }
    ],
    "name": "Entries"
  }
]
"""

remote_server_json_last_modified = """
[
  {
    "data": {
      "album": null,
      "author": null,
      "date_published": "Wed, 22 Jan 2025 08:49:28 GMT",
      "description": "Google News",
      "language": "en-US",
      "link": "https://news.google.com/rss?topic=h",
      "page_rating": 86,
      "tags": null,
      "thumbnail": "https://lh3.googleusercontent.com/-DR60l-K8vnyi99NZovm9HlXyZwQ85GMDxiwJWzoasZYCUrPuUM_P_4Rb7ei03j-0nRs0c4F=w256",
      "title": "Top stories - Google News"
    },
    "name": "Properties"
  },
  {
    "data": {
      "Contents": "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?><rss version=\"2.0\" xmlns:media=\"http://search.yahoo.com/mrss/\"><channel></rss>"
    },
    "name": "Text"
  },
  {
    "data": {
      "Options Ping": false,
      "Options SSL": true,
      "Options mode mapping": "[{'enabled': True, 'name': 'RequestsCrawler', 'crawler': <class 'rsshistory.webtools.crawlers.RequestsCrawler'>, 'settings': {'timeout_s': 20}}, {'enabled': True, 'name': 'CrawleeScript', 'crawler': <class 'rsshistory.webtools.crawlers.ScriptCrawler'>, 'settings': {'script': 'poetry run python crawleebeautifulsoup.py', 'timeout_s': 40}}, {'enabled': True, 'name': 'PlaywrightScript', 'crawler': <class 'rsshistory.webtools.crawlers.ScriptCrawler'>, 'settings': {'script': 'poetry run python crawleebeautifulsoup.py', 'timeout_s': 40}}, {'enabled': False, 'name': 'SeleniumUndetected', 'crawler': <class 'rsshistory.webtools.crawlers.SeleniumUndetected'>, 'settings': {'driver_executable': '/usr/bin/chromedriver', 'timeout_s': 30}}, {'enabled': False, 'name': 'SeleniumBase', 'crawler': <class 'rsshistory.webtools.crawlers.SeleniumBase'>, 'settings': {}}, {'enabled': False, 'name': 'SeleniumChromeHeadless', 'crawler': <class 'rsshistory.webtools.crawlers.SeleniumChromeHeadless'>, 'settings': {'driver_executable': '/usr/bin/chromedriver', 'timeout_s': 30}}, {'enabled': False, 'name': 'SeleniumChromeFull', 'crawler': <class 'rsshistory.webtools.crawlers.SeleniumChromeFull'>, 'settings': {'driver_executable': '/usr/bin/chromedriver', 'timeout_s': 40}}, {'enabled': True, 'name': 'StealthRequestsCrawler', 'crawler': <class 'rsshistory.webtools.crawlers.StealthRequestsCrawler'>, 'settings': {'timeout_s': 20}}]",
      "Options use browser promotions": true,
      "Options user agent": "None",
      "Page Handler": "HttpPageHandler",
      "Page Type": "RssPage"
    },
    "name": "Settings"
  },
  {
    "data": {
      "Charset": "utf-8",
      "Content-Length": 110398,
      "Content-Type": "application/xml; charset=utf-8",
      "Last-Modified": "Wed, 22 Jan 2025 08:49:28 GMT",
      "body_hash": "mvuJFx9/IcGamcMZRimFKA==",
      "crawler_data": {
        "crawler": "RequestsCrawler",
        "enabled": true,
        "name": "RequestsCrawler",
        "settings": {
          "timeout_s": 20
        }
      },
      "hash": "ps5UtH1oTRjHyS+PQSqg4Q==",
      "is_valid": true,
      "status_code": 200
    },
    "name": "Response"
  },
  {
    "data": {
      "Accept-CH": "Sec-CH-UA-Arch, Sec-CH-UA-Bitness, Sec-CH-UA-Full-Version, Sec-CH-UA-Full-Version-List, Sec-CH-UA-Model, Sec-CH-UA-WoW64, Sec-CH-UA-Form-Factors, Sec-CH-UA-Platform, Sec-CH-UA-Platform-Version",
      "Accept-Ranges": "none",
      "Alt-Svc": "h3=\":443\"; ma=2592000,h3-29=\":443\"; ma=2592000",
      "Cache-Control": "no-cache, no-store, max-age=0, must-revalidate",
      "Charset": "utf-8",
      "Content-Length": 110398,
      "Content-Security-Policy": "script-src 'nonce-NXhJyskj4EA7aDMPHhRT4w' 'unsafe-inline';object-src 'none';base-uri 'self';report-uri /_/DotsSplashUi/cspreport;worker-src 'self', script-src 'unsafe-inline' 'unsafe-eval' blob: data: 'self' https://apis.google.com https://ssl.gstatic.com https://www.google.com https://www.googletagmanager.com https://www.gstatic.com https://www.google-analytics.com https://support.google.com/inapp/ https://www.google.com/tools/feedback/ https://www.gstatic.com/inproduct_help/ https://www.gstatic.com/support/content/ https://youtube.com https://www.youtube.com https://youtube.googleapis.com https://*.ytimg.com https://ajax.googleapis.com https://www.googleapis.com/appsmarket/v2/installedApps/;report-uri /_/DotsSplashUi/cspreport/allowlist, require-trusted-types-for 'script';report-uri /_/DotsSplashUi/cspreport",
      "Content-Type": "application/xml; charset=utf-8",
      "Cross-Origin-Opener-Policy": "same-origin-allow-popups",
      "Cross-Origin-Resource-Policy": "same-site",
      "Date": "Wed, 22 Jan 2025 08:49:28 GMT",
      "Expires": "Mon, 01 Jan 1990 00:00:00 GMT",
      "Permissions-Policy": "ch-ua-arch=*, ch-ua-bitness=*, ch-ua-full-version=*, ch-ua-full-version-list=*, ch-ua-model=*, ch-ua-wow64=*, ch-ua-form-factors=*, ch-ua-platform=*, ch-ua-platform-version=*",
      "Pragma": "no-cache",
      "Server": "ESF",
      "Strict-Transport-Security": "max-age=31536000",
      "Transfer-Encoding": "chunked",
      "Vary": "Sec-Fetch-Dest, Sec-Fetch-Mode, Sec-Fetch-Site,Accept-Encoding",
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "SAMEORIGIN",
      "X-XSS-Protection": "0",
      "reporting-endpoints": "default=\"/_/DotsSplashUi/web-reports?context=eJzjitDikmJw05BikPj6kkkNiJ3SZ7AGAPHnHTNYW2-eY50MxEZrz7M6AHHSv_OsBUDcUXqB1VDhEqs9EF9Ov8Sq2nOJ1RiIiySusDYAsa_2VVYhHo4Zjw7tYRN48fT_PSYl5aT8wviU_JLi4oKcxOKM4tSistSieCMDI1MDQ0MTPQOz-AJDAIrlNxw\""
    },
    "name": "Headers"
  },
  {
    "data": [
      {
        "album": "",
        "author": null,
        "bookmarked": false,
        "date_published": "Tue, 21 Jan 2025 13:24:42 GMT",
        "description": "<ol><li><a href=\"https://news.google.com/rss/articles/CBMimwFBVV95cUxQM3hQekZ1S2ZxME1uSFJjSEVJX2QwNndtWlBWMElxNTJIY0MtQVpuRGppMXF4UFl3OFdFWUFTdjdEOEZ2SGF0RjVZUkZNdXBONF9NOGFUXzVWOEhQai1MYTlsSkZ5em1oLWJIcm5ETUdJN0hQUi10RUVQXzBEbWNhM1loN2ZFNnZtVHlORVY0S3VraG9xVkN5eXN1cw?oc=5\" target=\"_blank\">HHS gives Moderna $590M to 'accelerate' bird flu vaccine trials</a>&nbsp;&nbsp;<font color=\"#6f6f6f\">Fierce Biotech</font></li><li><a href=\"https://news.google.com/rss/articles/CBMijAFBVV95cUxOTFJ2X2V1Z3VJSW1ucWF3UUwxMjB1OEpXVTQ3b205YXlQZWVCY08wQmV3YmMxekEtN09aUmlQUVh3VjJPWlhEQzMycmx3eHdPUlV1T25jcmdmbG0yRlRVNGRuWFJLQWJ0TjNzXzd2cDZCbU5uUmdDZTdnYVVkdWdiVnNtX3ZXMFY0WXJoR9IBkgFBVV95cUxNWERPNDg0S3V1Vk5CY1hYMmFlOEk1UkcxZ0VoS3lIZXp6ZHNTTWx5aENiMzVKZndMUThma04wcUl2SUNnQTNyaFVrWWJZRVppRXRTMHluam52bDRWRERDX1ZHLWRIMzZTcm40QUx6RUZsbTdjUk8wWGJUSndwUmFNMmxqX2V3eFV1bjdyd1FwcFFCZw?oc=5\" target=\"_blank\">Moderna awarded $590M to help accelerate development of mRNA-based bird flu vaccine: HHS</a>&nbsp;&nbsp;<font color=\"#6f6f6f\">ABC News</font></li><li><a href=\"https://news.google.com/rss/articles/CBMitwFBVV95cUxPcWFobWdjYVdQZ0hQOHpDMTB3NFMxX0VJbE05OVlpQ3RNRXhPT0o4anhwX1Z0N0RMd0ltNF83QXMyTHVycV9IekhUbjkzWmZIY1JHQTdwYWxObUk2WmJna2NOYlFVeWk3NXJmVGFDU0dNaElkWnNzdWNCemJHYmJFUC1CbkV3eVBoYjlXaGtSUmVQUWdJZEM0Ny1wZEdldjdxaE9IN0dpTTFUUnV4WGt4ZEJWWFlPMWc?oc=5\" target=\"_blank\">Moderna Stock Jumps as Biotech Gets $590M From US To Develop Bird-Flu Vaccine</a>&nbsp;&nbsp;<font color=\"#6f6f6f\">Investopedia</font></li><li><a href=\"https://news.google.com/rss/articles/CBMihAFBVV95cUxQdUNDZ04wUDRLQUY3Z2xiYmNqTncxQjVBbF9GQVpoalF3TlM0emNDRGN5U2loZnNsUGhWV2VpUUJwYWRQTmV0ZmpfT0Q2M2VCR2JHNjFoal91UUg4V2dNd0hsNVJqekVvQ3BVSldKcFp6Mjk2MzNpNnNJOHJyNUljOVl3ekU?oc=5\" target=\"_blank\">Why Is Moderna Stock Trading Higher On Tuesday?</a>&nbsp;&nbsp;<font color=\"#6f6f6f\">Yahoo Finance</font></li></ol>",
        "language": "en-US",
        "link": "https://news.google.com/rss/articles/CBMimwFBVV95cUxQM3hQekZ1S2ZxME1uSFJjSEVJX2QwNndtWlBWMElxNTJIY0MtQVpuRGppMXF4UFl3OFdFWUFTdjdEOEZ2SGF0RjVZUkZNdXBONF9NOGFUXzVWOEhQai1MYTlsSkZ5em1oLWJIcm5ETUdJN0hQUi10RUVQXzBEbWNhM1loN2ZFNnZtVHlORVY0S3VraG9xVkN5eXN1cw?oc=5",
        "page_rating": 86,
        "source": "https://news.google.com/rss?topic=h",
        "tags": null,
        "thumbnail": null,
        "title": "HHS gives Moderna $590M to 'accelerate' bird flu vaccine trials - Fierce Biotech"
      }
    ],
    "name": "Entries"
  }
]
"""
