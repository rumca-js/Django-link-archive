youtube_robots_txt = """
# robots.txt file for YouTube
# Created in the distant future (the year 2000) after
# the robotic uprising of the mid 90's which wiped out all humans.

User-agent: Mediapartners-Google*
Disallow:

User-agent: *
Disallow: /comment
Disallow: /feeds/videos.xml
Disallow: /get_video
Disallow: /get_video_info
Disallow: /get_midroll_info
Disallow: /live_chat
Disallow: /login
Disallow: /qr
Disallow: /results
Disallow: /signup
Disallow: /t/terms
Disallow: /timedtext_video
Disallow: /verify_age
Disallow: /watch_ajax
Disallow: /watch_fragments_ajax
Disallow: /watch_popup
Disallow: /watch_queue_ajax

Sitemap: https://www.youtube.com/sitemaps/sitemap.xml
Sitemap: https://www.youtube.com/product/sitemap.xml
"""

youtube_sitemap_sitemaps = """
<?xml version='1.0' encoding='UTF-8'?>
<sitemapindex xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>
  <sitemap>
    <loc>https://www.youtube.com/ads/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/sitemaps/misc.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/kids/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/trends/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://about.youtube/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/jobs/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/creators/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/csai-match/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/originals/guidelines/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://contributors.youtube.com/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://socialimpact.youtube.com/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://vr.youtube.com/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://artists.youtube/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/measurementprogram/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/go/family/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/yt/terms/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/howyoutubeworks/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://www.youtube.com/myfamily/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://health.youtube/sitemap.xml</loc>
  </sitemap>
  <sitemap>
    <loc>https://news.youtube/sitemap.xml</loc>
  </sitemap>
</sitemapindex>
"""

youtube_sitemap_product = """
<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <sitemap>
        <loc>https://www.youtube.com/product/sitemap-files/sitemap-001.xml.gz</loc>
    </sitemap>
    <sitemap>
        <loc>https://www.youtube.com/product/sitemap-files/sitemap-002.xml.gz</loc>
    </sitemap>
    <sitemap>
        <loc>https://www.youtube.com/product/sitemap-files/sitemap-003.xml.gz</loc>
    </sitemap>
    <sitemap>
        <loc>https://www.youtube.com/product/sitemap-files/sitemap-004.xml.gz</loc>
    </sitemap>
    <sitemap>
        <loc>https://www.youtube.com/product/sitemap-files/sitemap-005.xml.gz</loc>
    </sitemap>
</sitemapindex>
"""
