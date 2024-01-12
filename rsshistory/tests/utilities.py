"""
This module provides replacement for the Internet.

 - when test make requests to obtain a page, we return artificial data here
 - when there is a request to obtain youtube JSON data, we provide artificial data, etc.
"""

from ..models import PersistentInfo
from ..dateutils import DateUtils


class PageBuilder(object):
    def __init__(self):
        self.charset = "UTF-8"
        self.title = None
        self.title_meta = None
        self.description_meta = None
        self.author = None
        self.keywords = None
        self.og_title = None
        self.og_description = None
        self.body_text = ""

    def build_contents(self):
        html = self.build_html()
        html = self.build_head(html)
        html = self.build_body(html)
        return html

    def build_html(self):
        return """
        <html>
        ${HEAD}
        ${BODY}
        </html>"""

    def build_body(self, html):
        html = html.replace("${BODY}", "<body>{}</body>".format(self.body_text))
        return html

    def build_head(self, html):
        # fmt: off

        meta_info = ""
        if self.title:
            meta_info += '<title>{}</title>\n'.format(self.title)
        if self.title_meta:
            meta_info += '<meta name="title" content="{}">\n'.format(self.title_meta)
        if self.description_meta:
            meta_info += '<meta name="description" content="{}">\n'.format(self.description_meta)
        if self.author:
            meta_info += '<meta name="author" content="{}">\n'.format(self.author)
        if self.keywords:
            meta_info += '<meta name="keywords" content="{}">\n'.format(self.keywords)
        if self.og_title:
            meta_info += '<meta property=”og:title” content="{}">\n'.format(self.og_title)
        if self.og_description:
            meta_info += '<meta property=”og:description” content="{}">\n'.format(self.og_description)

        # fmt: on

        html = html.replace("${HEAD}", "<head>{}</head>".format(meta_info))
        return html


webpage_samtime_youtube_rss = """
<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom" version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
    <title><![CDATA[SAMTIME on Odysee]]></title>
    <subtitle><![CDATA[SAMTIME subtitle]]></subtitle>
    <description><![CDATA[SAMTIME channel description]]></description>
    <link>https://odysee.com/@samtime:1</link>
    <image><url>https://thumbnails.lbry.com/UCd6vEDS3SOhWbXZrxbrf_bw</url>
    <title>SAMTIME on Odysee</title>
    <link>https://odysee.com/@samtime:1</link>
    </image>
    <generator>RSS for Node</generator>
    <lastBuildDate>Tue, 01 Jan 2020 13:57:18 GMT</lastBuildDate>
    <atom:link href="https://odysee.com/$/rss/@samtime:1" rel="self" type="application/rss+xml"/>
    <language><![CDATA[ci]]></language>
    <itunes:author>SAMTIME author</itunes:author><itunes:category text="Leisure"></itunes:category><itunes:image href="https://thumbnails.lbry.com/UCd6vEDS3SOhWbXZrxbrf_bw"/><itunes:owner><itunes:name>SAMTIME name</itunes:name><itunes:email>no-reply@odysee.com</itunes:email></itunes:owner><itunes:explicit>no</itunes:explicit>

    <item><title><![CDATA[First entry title]]></title><description><![CDATA[First entry description]]></description><link>https://odysee.com/youtube-apologises-for-slowing-down:bab8f5ed4fa7bb406264152242bab2558037ee12</link><guid isPermaLink="true">https://odysee.com/youtube-apologises-for-slowing-down:bab8f5ed4fa7bb406264152242bab2558037ee12</guid><pubDate>Mon, 27 Nov 2023 18:50:08 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/youtube-apologises-for-slowing-down/bab8f5ed4fa7bb406264152242bab2558037ee12/1698dc.mp4" length="29028604" type="video/mp4"/><itunes:title>YouTube Apologises For Slowing Down AdBlock Users</itunes:title><itunes:author>SAMTIME x</itunes:author><itunes:image href="https://thumbnails.lbry.com/a51RgbcCutk"/><itunes:duration>161</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[I Installed Android Onto My MacBook]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/WwYo84im3Y0" width="480" alt="thumbnail" title="I Installed Android Onto My MacBook" /></p>Buy UGREEN Nexode 300W Charger ($70 OFF, 11/23-11/27)     https://amzn.to/3FXi6xa<br />UGREEN Nexode 100W Charger   (41% OFF, 11/23-11/27)     https://amzn.to/46oW01m<br />UGREEN Black Friday Deals, Up to 50% OFF    https://amzn.to/3u5gAGo<br />Buy on UGREEN Official Store, Up to 50% OFF    https://bit.ly/47aeWCa<br /><br />I just installed Android onto my wife’s MacBook and… no one is happy.<br /><br />-----------------------------------<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />#Ugreen #UgreenNexode300W<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=WwYo84im3Y0]]></description><link>https://odysee.com/i-installed-android-onto-my-macbook:1975c73f65423692d318b6860950f186277519b9</link><guid isPermaLink="true">https://odysee.com/i-installed-android-onto-my-macbook:1975c73f65423692d318b6860950f186277519b9</guid><pubDate>Fri, 24 Nov 2023 18:00:29 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/i-installed-android-onto-my-macbook/1975c73f65423692d318b6860950f186277519b9/e1f8a4.mp4" length="138220717" type="video/mp4"/><itunes:title>I Installed Android Onto My MacBook</itunes:title><itunes:author>SAMTIME y</itunes:author><itunes:image href="https://thumbnails.lbry.com/WwYo84im3Y0"/><itunes:duration>544</itunes:duration><itunes:explicit>no</itunes:explicit>
    </item><item><title><![CDATA[Apple Reacts to Having to Allow Sideloading]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/RZhVgD2fPZg" width="480" alt="thumbnail" title="Apple Reacts to Having to Allow Sideloading" /></p>Apple will allow iPhone users to install apps from outside their App Store in 2024. Apple ain’t happy about it!<br /><br />Apple Explains Why MacBook Only Has 8GB RAM: https://youtu.be/eKm5-jUTRMM<br /><br />Sideloading Article: https://www.macrumors.com/2023/11/13/eu-iphone-app-sideloading-coming-2024/<br />Craig Federighi Talk: https://www.youtube.com/watch?v=f0Gum8UkyoI<br />Jon Prosser video: https://youtu.be/R1J6Qsi_Fsk?si=rJEnQJpXPw_G5zWb<br />Woman hiding in closet: https://www.reddit.com/r/nightvale/comments/x1whrl/homeless_woman_lived_in_a_mans_closet_for_a_year/<br /><br />-----------------------------------<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />#iPhoneSideloading #DigitalMarketsAct #UnhappyApple<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=RZhVgD2fPZg]]></description><link>https://odysee.com/apple-reacts-to-having-to-allow:c1c7e8b36c1519e260e81ca7b71dc855e8c4a480</link><guid isPermaLink="true">https://odysee.com/apple-reacts-to-having-to-allow:c1c7e8b36c1519e260e81ca7b71dc855e8c4a480</guid><pubDate>Wed, 22 Nov 2023 19:52:19 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/apple-reacts-to-having-to-allow/c1c7e8b36c1519e260e81ca7b71dc855e8c4a480/64b55b.mp4" length="53821224" type="video/mp4"/><itunes:title>Apple Reacts to Having to Allow Sideloading</itunes:title><itunes:author>SAMTIME 1</itunes:author><itunes:image href="https://thumbnails.lbry.com/RZhVgD2fPZg"/><itunes:duration>206</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Apple Responds to Crackling iPhone 15 Speaker]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/z06e9QMd60U" width="480" alt="thumbnail" title="Apple Responds to Crackling iPhone 15 Speaker" /></p>Turns out there's another iPhone 15 problem. This time with a rattling earpiece speaker. Now this isn't music to Apple's ears XD<br /><br />MORE iPhone 15 Issues Playlist: https://www.youtube.com/playlist?list=PLHSLJI8oVymwR_Zx8zi_0Ao2iSGSXuytu<br /><br />ARTICLE: https://9to5mac.com/2023/10/03/iphone-15-crackling-sound-speakers/<br /><br />Angry Redditor Clips are Boogie2988: https://www.youtube.com/watch?v=Kwo58m4JqY8<br /><br />-----------------------------------<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=z06e9QMd60U]]></description><link>https://odysee.com/apple-responds-to-crackling-iphone-15:483c58ed5d701eed5622e223803b0736d7cb9c80</link><guid isPermaLink="true">https://odysee.com/apple-responds-to-crackling-iphone-15:483c58ed5d701eed5622e223803b0736d7cb9c80</guid><pubDate>Mon, 20 Nov 2023 18:00:35 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/apple-responds-to-crackling-iphone-15/483c58ed5d701eed5622e223803b0736d7cb9c80/e2cad7.mp4" length="44287318" type="video/mp4"/><itunes:title>Apple Responds to Crackling iPhone 15 Speaker</itunes:title><itunes:author>SAMTIME 2</itunes:author><itunes:image href="https://thumbnails.lbry.com/z06e9QMd60U"/><itunes:duration>181</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Apple Explains Why MacBook Pro Only Has 8GB RAM]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/eKm5-jUTRMM" width="480" alt="thumbnail" title="Apple Explains Why MacBook Pro Only Has 8GB RAM" /></p>Apple used their reality distortion field to explain why 8GB RAM on the new MacBook Pro is actually as good as 16GB.<br /><br />ARTICLE: https://www.macrumors.com/2023/11/08/8gb-ram-m3-macbook-pro-like-16-gb-pc/<br /><br />Max Tech 8GB vs 16GB MacBook Pro Test: https://youtu.be/hmWPd7uEYEY?si=pUzg-KFlhXvYoJKb<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />#MacBookPro #MacBookProBlem<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=eKm5-jUTRMM]]></description><link>https://odysee.com/apple-explains-why-macbook-pro-only-has:cf8f2d2c724a2e2dea05cc9e7b819f926d5acc52</link><guid isPermaLink="true">https://odysee.com/apple-explains-why-macbook-pro-only-has:cf8f2d2c724a2e2dea05cc9e7b819f926d5acc52</guid><pubDate>Wed, 15 Nov 2023 19:27:30 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/apple-explains-why-macbook-pro-only-has/cf8f2d2c724a2e2dea05cc9e7b819f926d5acc52/da9c24.mp4" length="45292390" type="video/mp4"/><itunes:title>Apple Explains Why MacBook Pro Only Has 8GB RAM</itunes:title><itunes:author>SAMTIME 4</itunes:author><itunes:image href="https://thumbnails.lbry.com/eKm5-jUTRMM"/><itunes:duration>227</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[YouTube is Sorry for Banning AdBlock]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/M_2Sh700w_E" width="480" alt="thumbnail" title="YouTube is Sorry for Banning AdBlock" /></p>YouTube is very sorry that they banned AdBlockers… because it made AdBlockers much more powerful!<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />#YouTube #AdBlock #SadBlock<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=M_2Sh700w_E]]></description><link>https://odysee.com/youtube-is-sorry-for-banning-adblock:61f2c4f92c36c76d7e8caf6a26123e79bf0d49eb</link><guid isPermaLink="true">https://odysee.com/youtube-is-sorry-for-banning-adblock:61f2c4f92c36c76d7e8caf6a26123e79bf0d49eb</guid><pubDate>Mon, 13 Nov 2023 17:00:25 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/youtube-is-sorry-for-banning-adblock/61f2c4f92c36c76d7e8caf6a26123e79bf0d49eb/532a85.mp4" length="49293717" type="video/mp4"/><itunes:title>YouTube is Sorry for Banning AdBlock</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/M_2Sh700w_E"/><itunes:duration>174</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[I Try to Fix My Old MacBook]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/l1kCgKwU4Cs" width="480" alt="thumbnail" title="I Try to Fix My Old MacBook" /></p>Get genuine parts to fix your Apple MacBook at https://appleparts.io/<br />Use codeword SAMTIME to get 20% at checkout!!<br /><br />How To Fix Your MacBook Pro on the Cheap: https://youtu.be/C0o5BrBSUSM<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=l1kCgKwU4Cs]]></description><link>https://odysee.com/i-try-to-fix-my-old-macbook:2dd51a62e201d54aa7ce0436e58e20de14f3ddf8</link><guid isPermaLink="true">https://odysee.com/i-try-to-fix-my-old-macbook:2dd51a62e201d54aa7ce0436e58e20de14f3ddf8</guid><pubDate>Thu, 09 Nov 2023 17:24:49 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/i-try-to-fix-my-old-macbook/2dd51a62e201d54aa7ce0436e58e20de14f3ddf8/5bd2d1.mp4" length="181789747" type="video/mp4"/><itunes:title>I Try to Fix My Old MacBook</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/l1kCgKwU4Cs"/><itunes:duration>586</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Tim Cook Finally Answers Hard Questions]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/BeHs9eGzsB8" width="480" alt="thumbnail" title="Tim Cook Finally Answers Hard Questions" /></p>I sat down with Tim Cook to finally make him answer the hard questions<br /><br />MORE INTERVIEWS: https://www.youtube.com/playlist?list=PLHSLJI8oVymzqoJi-_RQGI2K55QqF2ZxI<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />#TimCook #TimApple #TheHardQuestions<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=BeHs9eGzsB8]]></description><link>https://odysee.com/tim-cook-finally-answers-hard-questions:9e8ac9f2879e81ebb07c82e3d6f6795a75fa9451</link><guid isPermaLink="true">https://odysee.com/tim-cook-finally-answers-hard-questions:9e8ac9f2879e81ebb07c82e3d6f6795a75fa9451</guid><pubDate>Tue, 07 Nov 2023 18:32:03 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/tim-cook-finally-answers-hard-questions/9e8ac9f2879e81ebb07c82e3d6f6795a75fa9451/c6c463.mp4" length="65672356" type="video/mp4"/><itunes:title>Tim Cook Finally Answers Hard Questions</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/BeHs9eGzsB8"/><itunes:duration>271</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[M3 MacBook Pro PARODY - “Taking out the Pro”]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/Z5HkmZp-96k" width="480" alt="thumbnail" title="M3 MacBook Pro PARODY - “Taking out the Pro”" /></p>Introducing the all new Apple M3 MacBook Pros. Now available without the “Pro”!!<br /><br />Microsoft Reacts to Apple's New MacBooks: https://youtu.be/dhnozZ_rVJY<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=Z5HkmZp-96k]]></description><link>https://odysee.com/m3-macbook-pro-parody-%E2%80%9Ctaking-out-the:b9b024a3871cc7ba70d46818cd8530917ba6bbde</link><guid isPermaLink="true">https://odysee.com/m3-macbook-pro-parody-%E2%80%9Ctaking-out-the:b9b024a3871cc7ba70d46818cd8530917ba6bbde</guid><pubDate>Tue, 31 Oct 2023 18:44:28 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/m3-macbook-pro-parody-“taking-out-the/b9b024a3871cc7ba70d46818cd8530917ba6bbde/cf42ab.mp4" length="32870166" type="video/mp4"/><itunes:title>M3 MacBook Pro PARODY - “Taking out the Pro”</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/Z5HkmZp-96k"/><itunes:duration>198</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Microsoft Reacts to Apple’s New MacBooks]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/dhnozZ_rVJY" width="480" alt="thumbnail" title="Microsoft Reacts to Apple’s New MacBooks" /></p>Microsoft just bluescreened over Apple’s upcoming M3 MacBook Pros.<br /><br />Subscribe for the Apple M3 event PARODY VIDEO coming this Wednesday!<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=dhnozZ_rVJY]]></description><link>https://odysee.com/microsoft-reacts-to-apple%E2%80%99s-new:95165fbe1687d85ce7e697c652723db677d3d5bd</link><guid isPermaLink="true">https://odysee.com/microsoft-reacts-to-apple%E2%80%99s-new:95165fbe1687d85ce7e697c652723db677d3d5bd</guid><pubDate>Mon, 30 Oct 2023 09:00:10 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/microsoft-reacts-to-apple’s-new/95165fbe1687d85ce7e697c652723db677d3d5bd/e019a6.mp4" length="35376274" type="video/mp4"/><itunes:title>Microsoft Reacts to Apple’s New MacBooks</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/dhnozZ_rVJY"/><itunes:duration>161</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Samsung Reacts to OnePlus Folding Phone]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/heZoeirmqgw" width="480" alt="thumbnail" title="Samsung Reacts to OnePlus Folding Phone" /></p>Samsung responds to the new OnePlus Open folding phone. They’re not impressed!<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=heZoeirmqgw]]></description><link>https://odysee.com/samsung-reacts-to-oneplus-folding-phone:1b185b09135e7ed38965642f0f95f2b26e6331ae</link><guid isPermaLink="true">https://odysee.com/samsung-reacts-to-oneplus-folding-phone:1b185b09135e7ed38965642f0f95f2b26e6331ae</guid><pubDate>Tue, 24 Oct 2023 17:11:56 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/samsung-reacts-to-oneplus-folding-phone/1b185b09135e7ed38965642f0f95f2b26e6331ae/04d025.mp4" length="46183132" type="video/mp4"/><itunes:title>Samsung Reacts to OnePlus Folding Phone</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/heZoeirmqgw"/><itunes:duration>184</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Apple Introduces Apple Pencil With a Cord]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/-1yi7DqDUr8" width="480" alt="thumbnail" title="Apple Introduces Apple Pencil With a Cord" /></p>Apple just introduced the Apple Pencil USB-C. For when wireless charging is just too dang convenient!<br /><br />Yes, this is a real product: https://www.apple.com/shop/product/MUWA3AM/A/apple-pencil-usb-c<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=-1yi7DqDUr8]]></description><link>https://odysee.com/apple-introduces-apple-pencil-with-a:36a5fad1b47e74d2795b7bb33cf084917089fd76</link><guid isPermaLink="true">https://odysee.com/apple-introduces-apple-pencil-with-a:36a5fad1b47e74d2795b7bb33cf084917089fd76</guid><pubDate>Thu, 19 Oct 2023 17:56:02 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/apple-introduces-apple-pencil-with-a/36a5fad1b47e74d2795b7bb33cf084917089fd76/dc4d47.mp4" length="30185132" type="video/mp4"/><itunes:title>Apple Introduces Apple Pencil With a Cord</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/-1yi7DqDUr8"/><itunes:duration>196</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Apple Responds to iPhone 15 Screen Burn In]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/CVUMiyl1GVY" width="480" alt="thumbnail" title="Apple Responds to iPhone 15 Screen Burn In" /></p>Apple responds to the screen burn-in issue on the new iPhone 15 Pro Max. Looks like the phone is turning into an iPhone 15 PROblems!<br /><br />ARTICLE: https://www.dailymail.co.uk/sciencetech/article-12636027/iPhone-15-Pro-Max-screen-burn-issues-image-display-Apple.html<br /><br />Apple Responds to iPhone 15 Pro Bending: https://youtu.be/va9NjxmoyJU<br />Apple Responds to iPhone 15 Pro Overheating: https://youtu.be/75bxg24Od_U<br />Apple Responds to Fine Woven Case Issue: https://youtu.be/eMEahWU4mrM<br /><br />-----------------------------------<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=CVUMiyl1GVY]]></description><link>https://odysee.com/apple-responds-to-iphone-15-screen-burn:dc3690d028b73fb0026d0610dda41531844d2342</link><guid isPermaLink="true">https://odysee.com/apple-responds-to-iphone-15-screen-burn:dc3690d028b73fb0026d0610dda41531844d2342</guid><pubDate>Tue, 17 Oct 2023 17:40:04 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/apple-responds-to-iphone-15-screen-burn/dc3690d028b73fb0026d0610dda41531844d2342/0ef216.mp4" length="31056471" type="video/mp4"/><itunes:title>Apple Responds to iPhone 15 Screen Burn In</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/CVUMiyl1GVY"/><itunes:duration>147</itunes:duration><itunes:explicit>no</itunes:explicit></item>
</channel>
</rss>
"""

webpage_simple_rss_page = """
<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom" version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
    <title><![CDATA[Simple title]]></title>
    <subtitle><![CDATA[Simple subtitle]]></subtitle>
    <description><![CDATA[Simple description]]></description>
    <link>https://odysee.com/@samtime:1</link>
    <image><url>https://thumbnails.lbry.com/UCd6vEDS3SOhWbXZrxbrf_bw</url>
    <title>SAMTIME on Odysee</title>
    <link>https://odysee.com/@samtime:1</link>
    </image>
    <generator>RSS for Node</generator>
    <lastBuildDate>Tue, 01 Jan 2020 13:57:18 GMT</lastBuildDate>
    <atom:link href="https://odysee.com/$/rss/@samtime:1" rel="self" type="application/rss+xml"/>
    <language><![CDATA[ci]]></language>
    <itunes:author>SAMTIME author</itunes:author><itunes:category text="Leisure"></itunes:category><itunes:image href="https://thumbnails.lbry.com/UCd6vEDS3SOhWbXZrxbrf_bw"/><itunes:owner><itunes:name>SAMTIME name</itunes:name><itunes:email>no-reply@odysee.com</itunes:email></itunes:owner><itunes:explicit>no</itunes:explicit>

    <item><title><![CDATA[First entry title]]></title><description><![CDATA[First entry description]]></description><link>https://odysee.com/youtube-apologises-for-slowing-down:bab8f5ed4fa7bb406264152242bab2558037ee12</link><guid isPermaLink="true">https://odysee.com/youtube-apologises-for-slowing-down:bab8f5ed4fa7bb406264152242bab2558037ee12</guid><pubDate>Mon, 27 Nov 2023 18:50:08 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/youtube-apologises-for-slowing-down/bab8f5ed4fa7bb406264152242bab2558037ee12/1698dc.mp4" length="29028604" type="video/mp4"/><itunes:title>YouTube Apologises For Slowing Down AdBlock Users</itunes:title><itunes:author>SAMTIME x</itunes:author><itunes:image href="https://thumbnails.lbry.com/a51RgbcCutk"/><itunes:duration>161</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[I Installed Android Onto My MacBook]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/WwYo84im3Y0" width="480" alt="thumbnail" title="I Installed Android Onto My MacBook" /></p>Buy UGREEN Nexode 300W Charger ($70 OFF, 11/23-11/27)     https://amzn.to/3FXi6xa<br />UGREEN Nexode 100W Charger   (41% OFF, 11/23-11/27)     https://amzn.to/46oW01m<br />UGREEN Black Friday Deals, Up to 50% OFF    https://amzn.to/3u5gAGo<br />Buy on UGREEN Official Store, Up to 50% OFF    https://bit.ly/47aeWCa<br /><br />I just installed Android onto my wife’s MacBook and… no one is happy.<br /><br />-----------------------------------<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />#Ugreen #UgreenNexode300W<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=WwYo84im3Y0]]></description><link>https://odysee.com/i-installed-android-onto-my-macbook:1975c73f65423692d318b6860950f186277519b9</link><guid isPermaLink="true">https://odysee.com/i-installed-android-onto-my-macbook:1975c73f65423692d318b6860950f186277519b9</guid><pubDate>Fri, 24 Nov 2023 18:00:29 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/i-installed-android-onto-my-macbook/1975c73f65423692d318b6860950f186277519b9/e1f8a4.mp4" length="138220717" type="video/mp4"/><itunes:title>I Installed Android Onto My MacBook</itunes:title><itunes:author>SAMTIME y</itunes:author><itunes:image href="https://thumbnails.lbry.com/WwYo84im3Y0"/><itunes:duration>544</itunes:duration><itunes:explicit>no</itunes:explicit>
    </item><item><title><![CDATA[Apple Reacts to Having to Allow Sideloading]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/RZhVgD2fPZg" width="480" alt="thumbnail" title="Apple Reacts to Having to Allow Sideloading" /></p>Apple will allow iPhone users to install apps from outside their App Store in 2024. Apple ain’t happy about it!<br /><br />Apple Explains Why MacBook Only Has 8GB RAM: https://youtu.be/eKm5-jUTRMM<br /><br />Sideloading Article: https://www.macrumors.com/2023/11/13/eu-iphone-app-sideloading-coming-2024/<br />Craig Federighi Talk: https://www.youtube.com/watch?v=f0Gum8UkyoI<br />Jon Prosser video: https://youtu.be/R1J6Qsi_Fsk?si=rJEnQJpXPw_G5zWb<br />Woman hiding in closet: https://www.reddit.com/r/nightvale/comments/x1whrl/homeless_woman_lived_in_a_mans_closet_for_a_year/<br /><br />-----------------------------------<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />#iPhoneSideloading #DigitalMarketsAct #UnhappyApple<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=RZhVgD2fPZg]]></description><link>https://odysee.com/apple-reacts-to-having-to-allow:c1c7e8b36c1519e260e81ca7b71dc855e8c4a480</link><guid isPermaLink="true">https://odysee.com/apple-reacts-to-having-to-allow:c1c7e8b36c1519e260e81ca7b71dc855e8c4a480</guid><pubDate>Wed, 22 Nov 2023 19:52:19 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/apple-reacts-to-having-to-allow/c1c7e8b36c1519e260e81ca7b71dc855e8c4a480/64b55b.mp4" length="53821224" type="video/mp4"/><itunes:title>Apple Reacts to Having to Allow Sideloading</itunes:title><itunes:author>SAMTIME 1</itunes:author><itunes:image href="https://thumbnails.lbry.com/RZhVgD2fPZg"/><itunes:duration>206</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Apple Responds to Crackling iPhone 15 Speaker]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/z06e9QMd60U" width="480" alt="thumbnail" title="Apple Responds to Crackling iPhone 15 Speaker" /></p>Turns out there's another iPhone 15 problem. This time with a rattling earpiece speaker. Now this isn't music to Apple's ears XD<br /><br />MORE iPhone 15 Issues Playlist: https://www.youtube.com/playlist?list=PLHSLJI8oVymwR_Zx8zi_0Ao2iSGSXuytu<br /><br />ARTICLE: https://9to5mac.com/2023/10/03/iphone-15-crackling-sound-speakers/<br /><br />Angry Redditor Clips are Boogie2988: https://www.youtube.com/watch?v=Kwo58m4JqY8<br /><br />-----------------------------------<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=z06e9QMd60U]]></description><link>https://odysee.com/apple-responds-to-crackling-iphone-15:483c58ed5d701eed5622e223803b0736d7cb9c80</link><guid isPermaLink="true">https://odysee.com/apple-responds-to-crackling-iphone-15:483c58ed5d701eed5622e223803b0736d7cb9c80</guid><pubDate>Mon, 20 Nov 2023 18:00:35 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/apple-responds-to-crackling-iphone-15/483c58ed5d701eed5622e223803b0736d7cb9c80/e2cad7.mp4" length="44287318" type="video/mp4"/><itunes:title>Apple Responds to Crackling iPhone 15 Speaker</itunes:title><itunes:author>SAMTIME 2</itunes:author><itunes:image href="https://thumbnails.lbry.com/z06e9QMd60U"/><itunes:duration>181</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Apple Explains Why MacBook Pro Only Has 8GB RAM]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/eKm5-jUTRMM" width="480" alt="thumbnail" title="Apple Explains Why MacBook Pro Only Has 8GB RAM" /></p>Apple used their reality distortion field to explain why 8GB RAM on the new MacBook Pro is actually as good as 16GB.<br /><br />ARTICLE: https://www.macrumors.com/2023/11/08/8gb-ram-m3-macbook-pro-like-16-gb-pc/<br /><br />Max Tech 8GB vs 16GB MacBook Pro Test: https://youtu.be/hmWPd7uEYEY?si=pUzg-KFlhXvYoJKb<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />#MacBookPro #MacBookProBlem<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=eKm5-jUTRMM]]></description><link>https://odysee.com/apple-explains-why-macbook-pro-only-has:cf8f2d2c724a2e2dea05cc9e7b819f926d5acc52</link><guid isPermaLink="true">https://odysee.com/apple-explains-why-macbook-pro-only-has:cf8f2d2c724a2e2dea05cc9e7b819f926d5acc52</guid><pubDate>Wed, 15 Nov 2023 19:27:30 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/apple-explains-why-macbook-pro-only-has/cf8f2d2c724a2e2dea05cc9e7b819f926d5acc52/da9c24.mp4" length="45292390" type="video/mp4"/><itunes:title>Apple Explains Why MacBook Pro Only Has 8GB RAM</itunes:title><itunes:author>SAMTIME 4</itunes:author><itunes:image href="https://thumbnails.lbry.com/eKm5-jUTRMM"/><itunes:duration>227</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[YouTube is Sorry for Banning AdBlock]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/M_2Sh700w_E" width="480" alt="thumbnail" title="YouTube is Sorry for Banning AdBlock" /></p>YouTube is very sorry that they banned AdBlockers… because it made AdBlockers much more powerful!<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />#YouTube #AdBlock #SadBlock<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=M_2Sh700w_E]]></description><link>https://odysee.com/youtube-is-sorry-for-banning-adblock:61f2c4f92c36c76d7e8caf6a26123e79bf0d49eb</link><guid isPermaLink="true">https://odysee.com/youtube-is-sorry-for-banning-adblock:61f2c4f92c36c76d7e8caf6a26123e79bf0d49eb</guid><pubDate>Mon, 13 Nov 2023 17:00:25 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/youtube-is-sorry-for-banning-adblock/61f2c4f92c36c76d7e8caf6a26123e79bf0d49eb/532a85.mp4" length="49293717" type="video/mp4"/><itunes:title>YouTube is Sorry for Banning AdBlock</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/M_2Sh700w_E"/><itunes:duration>174</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[I Try to Fix My Old MacBook]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/l1kCgKwU4Cs" width="480" alt="thumbnail" title="I Try to Fix My Old MacBook" /></p>Get genuine parts to fix your Apple MacBook at https://appleparts.io/<br />Use codeword SAMTIME to get 20% at checkout!!<br /><br />How To Fix Your MacBook Pro on the Cheap: https://youtu.be/C0o5BrBSUSM<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=l1kCgKwU4Cs]]></description><link>https://odysee.com/i-try-to-fix-my-old-macbook:2dd51a62e201d54aa7ce0436e58e20de14f3ddf8</link><guid isPermaLink="true">https://odysee.com/i-try-to-fix-my-old-macbook:2dd51a62e201d54aa7ce0436e58e20de14f3ddf8</guid><pubDate>Thu, 09 Nov 2023 17:24:49 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/i-try-to-fix-my-old-macbook/2dd51a62e201d54aa7ce0436e58e20de14f3ddf8/5bd2d1.mp4" length="181789747" type="video/mp4"/><itunes:title>I Try to Fix My Old MacBook</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/l1kCgKwU4Cs"/><itunes:duration>586</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Tim Cook Finally Answers Hard Questions]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/BeHs9eGzsB8" width="480" alt="thumbnail" title="Tim Cook Finally Answers Hard Questions" /></p>I sat down with Tim Cook to finally make him answer the hard questions<br /><br />MORE INTERVIEWS: https://www.youtube.com/playlist?list=PLHSLJI8oVymzqoJi-_RQGI2K55QqF2ZxI<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />#TimCook #TimApple #TheHardQuestions<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=BeHs9eGzsB8]]></description><link>https://odysee.com/tim-cook-finally-answers-hard-questions:9e8ac9f2879e81ebb07c82e3d6f6795a75fa9451</link><guid isPermaLink="true">https://odysee.com/tim-cook-finally-answers-hard-questions:9e8ac9f2879e81ebb07c82e3d6f6795a75fa9451</guid><pubDate>Tue, 07 Nov 2023 18:32:03 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/tim-cook-finally-answers-hard-questions/9e8ac9f2879e81ebb07c82e3d6f6795a75fa9451/c6c463.mp4" length="65672356" type="video/mp4"/><itunes:title>Tim Cook Finally Answers Hard Questions</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/BeHs9eGzsB8"/><itunes:duration>271</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[M3 MacBook Pro PARODY - “Taking out the Pro”]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/Z5HkmZp-96k" width="480" alt="thumbnail" title="M3 MacBook Pro PARODY - “Taking out the Pro”" /></p>Introducing the all new Apple M3 MacBook Pros. Now available without the “Pro”!!<br /><br />Microsoft Reacts to Apple's New MacBooks: https://youtu.be/dhnozZ_rVJY<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=Z5HkmZp-96k]]></description><link>https://odysee.com/m3-macbook-pro-parody-%E2%80%9Ctaking-out-the:b9b024a3871cc7ba70d46818cd8530917ba6bbde</link><guid isPermaLink="true">https://odysee.com/m3-macbook-pro-parody-%E2%80%9Ctaking-out-the:b9b024a3871cc7ba70d46818cd8530917ba6bbde</guid><pubDate>Tue, 31 Oct 2023 18:44:28 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/m3-macbook-pro-parody-“taking-out-the/b9b024a3871cc7ba70d46818cd8530917ba6bbde/cf42ab.mp4" length="32870166" type="video/mp4"/><itunes:title>M3 MacBook Pro PARODY - “Taking out the Pro”</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/Z5HkmZp-96k"/><itunes:duration>198</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Microsoft Reacts to Apple’s New MacBooks]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/dhnozZ_rVJY" width="480" alt="thumbnail" title="Microsoft Reacts to Apple’s New MacBooks" /></p>Microsoft just bluescreened over Apple’s upcoming M3 MacBook Pros.<br /><br />Subscribe for the Apple M3 event PARODY VIDEO coming this Wednesday!<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=dhnozZ_rVJY]]></description><link>https://odysee.com/microsoft-reacts-to-apple%E2%80%99s-new:95165fbe1687d85ce7e697c652723db677d3d5bd</link><guid isPermaLink="true">https://odysee.com/microsoft-reacts-to-apple%E2%80%99s-new:95165fbe1687d85ce7e697c652723db677d3d5bd</guid><pubDate>Mon, 30 Oct 2023 09:00:10 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/microsoft-reacts-to-apple’s-new/95165fbe1687d85ce7e697c652723db677d3d5bd/e019a6.mp4" length="35376274" type="video/mp4"/><itunes:title>Microsoft Reacts to Apple’s New MacBooks</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/dhnozZ_rVJY"/><itunes:duration>161</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Samsung Reacts to OnePlus Folding Phone]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/heZoeirmqgw" width="480" alt="thumbnail" title="Samsung Reacts to OnePlus Folding Phone" /></p>Samsung responds to the new OnePlus Open folding phone. They’re not impressed!<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=heZoeirmqgw]]></description><link>https://odysee.com/samsung-reacts-to-oneplus-folding-phone:1b185b09135e7ed38965642f0f95f2b26e6331ae</link><guid isPermaLink="true">https://odysee.com/samsung-reacts-to-oneplus-folding-phone:1b185b09135e7ed38965642f0f95f2b26e6331ae</guid><pubDate>Tue, 24 Oct 2023 17:11:56 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/samsung-reacts-to-oneplus-folding-phone/1b185b09135e7ed38965642f0f95f2b26e6331ae/04d025.mp4" length="46183132" type="video/mp4"/><itunes:title>Samsung Reacts to OnePlus Folding Phone</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/heZoeirmqgw"/><itunes:duration>184</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Apple Introduces Apple Pencil With a Cord]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/-1yi7DqDUr8" width="480" alt="thumbnail" title="Apple Introduces Apple Pencil With a Cord" /></p>Apple just introduced the Apple Pencil USB-C. For when wireless charging is just too dang convenient!<br /><br />Yes, this is a real product: https://www.apple.com/shop/product/MUWA3AM/A/apple-pencil-usb-c<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=-1yi7DqDUr8]]></description><link>https://odysee.com/apple-introduces-apple-pencil-with-a:36a5fad1b47e74d2795b7bb33cf084917089fd76</link><guid isPermaLink="true">https://odysee.com/apple-introduces-apple-pencil-with-a:36a5fad1b47e74d2795b7bb33cf084917089fd76</guid><pubDate>Thu, 19 Oct 2023 17:56:02 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/apple-introduces-apple-pencil-with-a/36a5fad1b47e74d2795b7bb33cf084917089fd76/dc4d47.mp4" length="30185132" type="video/mp4"/><itunes:title>Apple Introduces Apple Pencil With a Cord</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/-1yi7DqDUr8"/><itunes:duration>196</itunes:duration><itunes:explicit>no</itunes:explicit></item>
    <item><title><![CDATA[Apple Responds to iPhone 15 Screen Burn In]]></title><description><![CDATA[<p><img src="https://thumbnails.lbry.com/CVUMiyl1GVY" width="480" alt="thumbnail" title="Apple Responds to iPhone 15 Screen Burn In" /></p>Apple responds to the screen burn-in issue on the new iPhone 15 Pro Max. Looks like the phone is turning into an iPhone 15 PROblems!<br /><br />ARTICLE: https://www.dailymail.co.uk/sciencetech/article-12636027/iPhone-15-Pro-Max-screen-burn-issues-image-display-Apple.html<br /><br />Apple Responds to iPhone 15 Pro Bending: https://youtu.be/va9NjxmoyJU<br />Apple Responds to iPhone 15 Pro Overheating: https://youtu.be/75bxg24Od_U<br />Apple Responds to Fine Woven Case Issue: https://youtu.be/eMEahWU4mrM<br /><br />-----------------------------------<br /><br />SUPPORT: https://funkytime.tv/patriot-signup/<br />MERCH: https://funkytime.tv/shop/<br />FUNKY TIME WEBSITE: https://funkytime.tv<br /><br />FACEBOOK: http://www.facebook.com/SamtimeNews<br />TWITTER: http://twitter.com/SamtimeNews<br />INSTAGRAM: http://instagram.com/samtimenews<br /><br />-----------------------------------<br /><br />'Escape the ordinary. Embrace the FUNKY!'<br /><br />-----------------------------------<br /><br />For sponsorship enquiries: samtime@bossmgmtgrp.com<br />For other business enquiries: business@funkytime.tv<br />Copyright FUNKY TIME PRODUCTIONS 2023<br />...<br />https://www.youtube.com/watch?v=CVUMiyl1GVY]]></description><link>https://odysee.com/apple-responds-to-iphone-15-screen-burn:dc3690d028b73fb0026d0610dda41531844d2342</link><guid isPermaLink="true">https://odysee.com/apple-responds-to-iphone-15-screen-burn:dc3690d028b73fb0026d0610dda41531844d2342</guid><pubDate>Tue, 17 Oct 2023 17:40:04 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/apple-responds-to-iphone-15-screen-burn/dc3690d028b73fb0026d0610dda41531844d2342/0ef216.mp4" length="31056471" type="video/mp4"/><itunes:title>Apple Responds to iPhone 15 Screen Burn In</itunes:title><itunes:author>SAMTIME</itunes:author><itunes:image href="https://thumbnails.lbry.com/CVUMiyl1GVY"/><itunes:duration>147</itunes:duration><itunes:explicit>no</itunes:explicit></item>
</channel>
</rss>
"""

webpage_old_pubdate_rss = """
<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom" version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
    <title><![CDATA[SAMTIME on Odysee]]></title>
    <subtitle><![CDATA[SAMTIME subtitle]]></subtitle>
    <description><![CDATA[SAMTIME channel description]]></description>
    <link>https://odysee.com/@samtime:1</link>
    <image><url>https://thumbnails.lbry.com/UCd6vEDS3SOhWbXZrxbrf_bw</url>
    <title>SAMTIME on Odysee</title>
    <link>https://odysee.com/@samtime:1</link>
    </image>
    <generator>RSS for Node</generator>
    <lastBuildDate>Tue, 01 Jan 2020 13:57:18 GMT</lastBuildDate>
    <atom:link href="https://odysee.com/$/rss/@samtime:1" rel="self" type="application/rss+xml"/>
    <language><![CDATA[ci]]></language>
    <itunes:author>SAMTIME author</itunes:author><itunes:category text="Leisure"></itunes:category><itunes:image href="https://thumbnails.lbry.com/UCd6vEDS3SOhWbXZrxbrf_bw"/><itunes:owner><itunes:name>SAMTIME name</itunes:name><itunes:email>no-reply@odysee.com</itunes:email></itunes:owner><itunes:explicit>no</itunes:explicit>

    <item><title><![CDATA[First entry title]]></title><description><![CDATA[First entry description]]></description><link>https://odysee.com/youtube-apologises-for-slowing-down:bab8f5ed4fa7bb406264152242bab2558037ee12</link><guid isPermaLink="true">https://odysee.com/youtube-apologises-for-slowing-down:bab8f5ed4fa7bb406264152242bab2558037ee12</guid><pubDate>Mon, 01 Jan 2020 18:50:08 GMT</pubDate><enclosure url="https://player.odycdn.com/api/v3/streams/free/youtube-apologises-for-slowing-down/bab8f5ed4fa7bb406264152242bab2558037ee12/1698dc.mp4" length="29028604" type="video/mp4"/><itunes:title>YouTube Apologises For Slowing Down AdBlock Users</itunes:title><itunes:author>SAMTIME x</itunes:author><itunes:image href="https://thumbnails.lbry.com/a51RgbcCutk"/><itunes:duration>161</itunes:duration><itunes:explicit>no</itunes:explicit></item>
</channel>
</rss>
"""

webpage_no_pubdate_rss = """
<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:content="http://purl.org/rss/1.0/modules/content/" xmlns:atom="http://www.w3.org/2005/Atom" version="2.0" xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
<channel>
    <title><![CDATA[SAMTIME on Odysee]]></title>
    <subtitle><![CDATA[SAMTIME subtitle]]></subtitle>
    <description><![CDATA[SAMTIME channel description]]></description>
    <link>https://odysee.com/@samtime:1</link>
    <image><url>https://thumbnails.lbry.com/UCd6vEDS3SOhWbXZrxbrf_bw</url>
    <title>SAMTIME on Odysee</title>
    <link>https://odysee.com/@samtime:1</link>
    </image>
    <generator>RSS for Node</generator>
    <lastBuildDate>Tue, 01 Jan 2020 13:57:18 GMT</lastBuildDate>
    <atom:link href="https://odysee.com/$/rss/@samtime:1" rel="self" type="application/rss+xml"/>
    <language><![CDATA[ci]]></language>
    <itunes:author>SAMTIME author</itunes:author><itunes:category text="Leisure"></itunes:category><itunes:image href="https://thumbnails.lbry.com/UCd6vEDS3SOhWbXZrxbrf_bw"/><itunes:owner><itunes:name>SAMTIME name</itunes:name><itunes:email>no-reply@odysee.com</itunes:email></itunes:owner><itunes:explicit>no</itunes:explicit>

    <item><title><![CDATA[First entry title]]></title><description><![CDATA[First entry description]]></description><link>https://odysee.com/youtube-apologises-for-slowing-down:bab8f5ed4fa7bb406264152242bab2558037ee12</link><guid isPermaLink="true">https://odysee.com/youtube-apologises-for-slowing-down:bab8f5ed4fa7bb406264152242bab2558037ee12</guid><enclosure url="https://player.odycdn.com/api/v3/streams/free/youtube-apologises-for-slowing-down/bab8f5ed4fa7bb406264152242bab2558037ee12/1698dc.mp4" length="29028604" type="video/mp4"/><itunes:title>YouTube Apologises For Slowing Down AdBlock Users</itunes:title><itunes:author>SAMTIME x</itunes:author><itunes:image href="https://thumbnails.lbry.com/a51RgbcCutk"/><itunes:duration>161</itunes:duration><itunes:explicit>no</itunes:explicit></item>
</channel>
</rss>
"""

webpage_airpano = """
<feed>
<link rel="self" href="http://www.youtube.com/feeds/videos.xml?channel_id=UCUSElbgKZpE4Xdh5aFWG-Ig"/>
<id>yt:channel:USElbgKZpE4Xdh5aFWG-Ig</id>
<yt:channelId>USElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>AirPano VR</title>
<link rel="alternate" href="https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2010-02-12T07:04:55+00:00</published>
<entry>
<id>yt:video:dWa5hJGpTN4</id>
<yt:videoId>dWa5hJGpTN4</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>
National Park Moneron Island. 8K 360° virtual travel
</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=dWa5hJGpTN4"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-12-08T05:29:52+00:00</published>
<updated>2023-12-16T01:48:32+00:00</updated>
<media:group>
<media:title>
National Park Moneron Island. 8K 360° virtual travel
</media:title>
<media:content url="https://www.youtube.com/v/dWa5hJGpTN4?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i1.ytimg.com/vi/dWa5hJGpTN4/hqdefault.jpg" width="480" height="360"/>
<media:description>
The Eurasian mainland and Sakhalin Island are separated by the Strait of Tartary, with its largest island known as Moneron. Moneron is influenced by the Tsushima Current, so the water is not only transparent, but also very warm. Besides, the water area abounds with reefs: it is a real paradise for divers! This is not just Russia's first marine park: it is the only island nature park in the country... Don't forget that this is 360 video: you can change the angle of view. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this videoformat to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike regular videos, while watching 360° videos YouTube show us only a specific field of view similar to human eye (by default 100 degrees out of 360). As a result, the resolution of the visible part of 8K video uploaded to our channel is around 2K (1920p). If you watch in 4K mode the resolution of the visible part would be even less - around 1080p (1K). Please note that AirPano team originally shoots its films in 16,12,10,8K resolution, depending on year and cameras used back then. But before upload to YouTube channel we downscale all our videos to 8K. 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com #Moneron #MoneronIsland #UNESCO #nature #relaxing #relaxingvideo #360video #AirpanoNature #VirtualTravel #rockformations #underwater #seals #seacollection #sea #nature #naturelovers #sakhalin
</media:description>
<media:community>
<media:starRating count="182" average="5.00" min="1" max="5"/>
<media:statistics views="54335"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:KkSzad253o0</id>
<yt:videoId>KkSzad253o0</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>
Rio de Janeiro. The Marvelous City. Aerial 360 video in 12K
</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=KkSzad253o0"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-11-24T06:07:40+00:00</published>
<updated>2023-11-29T15:03:20+00:00</updated>
<media:group>
<media:title>
Rio de Janeiro. The Marvelous City. Aerial 360 video in 12K
</media:title>
<media:content url="https://www.youtube.com/v/KkSzad253o0?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i4.ytimg.com/vi/KkSzad253o0/hqdefault.jpg" width="480" height="360"/>
<media:description>
Don't forget that this is 360 video: you can change the angle of view. On a 700-meter high Corcovado mountain stands a giant figure of Christ, his arms are stretched out towards the city, as if blessing the land. Each year, nearly 2 million tourists and residents climb to the top of the mountain to take a photo besides the monument "for good luck". Thanks to AYRTON360 for his help in Rio de Janeiro and for the photo panorama from the top of the statue: https://www.youtube.com/user/AyrtonCamargo If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com Nowadays you need extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this videoformat to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike standard videos, in a 360° video you can see only a part of original image (approximately 30 degrees out of 360). As result, the real resolution of the part you can see isn't bigger than 1.3K. #AirPanoCities #Rio #ChristtheRedeemer #RiodeJaneiro #Brazil #AirPano #Drone #Travel #VirtualTravel #Copacabana #Ipanema #Leblon #copacabanabeach #christredemeer #rio
</media:description>
<media:community>
<media:starRating count="185" average="5.00" min="1" max="5"/>
<media:statistics views="12245"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:q5GXQQo8I-k</id>
<yt:videoId>q5GXQQo8I-k</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>
Virtual travel to Saint Petersburg, Russia. 360 video in 6K
</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=q5GXQQo8I-k"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-11-10T10:12:18+00:00</published>
<updated>2023-11-11T05:58:13+00:00</updated>
<media:group>
<media:title>
Virtual travel to Saint Petersburg, Russia. 360 video in 6K
</media:title>
<media:content url="https://www.youtube.com/v/q5GXQQo8I-k?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i2.ytimg.com/vi/q5GXQQo8I-k/hqdefault.jpg" width="480" height="360"/>
<media:description>
Don't forget that this is 360 video: you can change the angle of view. Saint Petersburg is one of the most famous and beautiful cities of the world. It is the second largest city in Russia after its capital, Moscow. But, at the same time, it is a capital in its own way — it is known as the "Cultural Capital of Russia". Let’s take a virtual journey, have a walk around and fly above this city to enjoy its majestic architectural monuments! All ground scenes in this clip have been shot with Insta360 Titan. It is the best solution for 360° professionals. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! Also here is the answer for a frequently asked question about true resolution of an 6K 360° video. Unlike standard videos, in a 360° video you can see only a part of original image (approximately 60 degrees out of 360). As result, the real resolution of the part you can see isn't bigger than HD (1080p). #AirPanoCities #VirtualTravel #SaintPetersburg #AirPano #360video #Russia #city
</media:description>
<media:community>
<media:starRating count="309" average="5.00" min="1" max="5"/>
<media:statistics views="40219"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:jqq_ZdD5Zwg</id>
<yt:videoId>jqq_ZdD5Zwg</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>
Maldive Paradise. Tropical Beach Relaxation. 360 video in 16K
</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=jqq_ZdD5Zwg"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-11-02T21:23:49+00:00</published>
<updated>2023-11-16T22:57:41+00:00</updated>
<media:group>
<media:title>
Maldive Paradise. Tropical Beach Relaxation. 360 video in 16K
</media:title>
<media:content url="https://www.youtube.com/v/jqq_ZdD5Zwg?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i3.ytimg.com/vi/jqq_ZdD5Zwg/hqdefault.jpg" width="480" height="360"/>
<media:description>
Don't forget that this is 360 video: you can change the angle of view. A gentle beat of waves, snow white sand in addition to the sun, palms and azure blue sea - that's how a perfect picture of a tropical paradise looks like. A new AirPano relaxing video offers you a break from worries, the sound of waves, birds' cries and the stunning beauty of the Maldive seascapes. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com Nowadays you need extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this video format to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike standard videos, in a 360° video you can see only a part of original image (approximately 30 degrees out of 360). As result, the real resolution of the part you can see isn't bigger than 1.3K. Please note that AirPano team originally shoots its films in 16,12,10,8K resolution, depending on year and cameras used back then. But before upload to YouTube channel we downscale all our videos to 8K. #AirPanoNature #Maldives #360video #VR #Beach #Diving #Relax #Relaxation
</media:description>
<media:community>
<media:starRating count="607" average="5.00" min="1" max="5"/>
<media:statistics views="183218"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:uoMVcquLW-I</id>
<yt:videoId>uoMVcquLW-I</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>
Elton Lake, the biggest mineral lake in Europe. 8K aerial 360 video
</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=uoMVcquLW-I"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-10-13T08:33:42+00:00</published>
<updated>2023-11-21T03:55:22+00:00</updated>
<media:group>
<media:title>
Elton Lake, the biggest mineral lake in Europe. 8K aerial 360 video
</media:title>
<media:content url="https://www.youtube.com/v/uoMVcquLW-I?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i2.ytimg.com/vi/uoMVcquLW-I/hqdefault.jpg" width="480" height="360"/>
<media:description>
Don't forget that this is 360 video: you can change the angle of view. There is a drainless salty lake Elton in the north part of the Caspian Depression that lies in the Volgograd region of Russia. The Lake lies 15 meters below sea level. With a surface of 152 square kilometers, it is the biggest mineral lake in Europe. Nowadays you need extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this video format to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike regular videos, while watching 360° videos YouTube show us only a specific field of view similar to human eye (by default 100 degrees out of 360). As a result, the resolution of the visible part of 8K video uploaded to our channel is around 2K (1920p). If you watch in 4K mode the resolution of the visible part would be even less - around 1080p (1K). Please note that AirPano team originally shoots its films in 16,12,10,8K resolution, depending on year and cameras used back then. But before upload to YouTube channel we downscale all our videos to 8K. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com #Lakes #Russia #UNESCO #Elton #saltlake #salt #landscape #nature #360video #AirpanoNature #VirtualTravel #nature #naturelovers #aerial #aerialfootage #aerialvideo #virtualtravel
</media:description>
<media:community>
<media:starRating count="261" average="5.00" min="1" max="5"/>
<media:statistics views="97094"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:Og3smuddg2g</id>
<yt:videoId>Og3smuddg2g</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>
The Maldives. Underwater Paradise. Relaxing 360 video in 8K.
</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=Og3smuddg2g"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-09-29T14:30:26+00:00</published>
<updated>2023-11-22T02:35:00+00:00</updated>
<media:group>
<media:title>
The Maldives. Underwater Paradise. Relaxing 360 video in 8K.
</media:title>
<media:content url="https://www.youtube.com/v/Og3smuddg2g?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i4.ytimg.com/vi/Og3smuddg2g/hqdefault.jpg" width="480" height="360"/>
<media:description>
Endless expanses of water stretching to the horizon, hundreds of shades of blue and tiny coral atolls with white sand: it’s all about the Maldives! Tourists are attracted primarily by the sand beaches and gentle waves of the Indian Ocean. But the genuine treasures are not on the surface: they are hidden from the public eye deep under the water... Don't forget that this is 360 video: you can change the angle of view! Nowadays you need extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this video format to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike standard videos, in a 360° video you can see only a part of original image (approximately 30 degrees out of 360). As result, the real resolution of the part you can see isn't bigger than 1.3K. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com #AirPanoNature #Maldives #360video #Paradise #Underwater #VR #Diving #Relax #Relaxing
</media:description>
<media:community>
<media:starRating count="288" average="5.00" min="1" max="5"/>
<media:statistics views="104227"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:9JR1IekZGUY</id>
<yt:videoId>9JR1IekZGUY</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>
Male, Maldives. Scenic flight over the city. Relaxing aerial 360 video in 8K
</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=9JR1IekZGUY"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-09-15T07:02:40+00:00</published>
<updated>2023-11-08T10:02:59+00:00</updated>
<media:group>
<media:title>
Male, Maldives. Scenic flight over the city. Relaxing aerial 360 video in 8K
</media:title>
<media:content url="https://www.youtube.com/v/9JR1IekZGUY?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i2.ytimg.com/vi/9JR1IekZGUY/hqdefault.jpg" width="480" height="360"/>
<media:description>
Don't forget that this is 360 video: you can change the angle of view. The Republic of Maldives comprises 26 atolls and nearly two thousand coral islands. Most of them are uninhabited and it is the area where nature reigns supreme. Male, the capital of the Maldives, has found itself on the same-name island being 1.87 km long and 1.5 km wide. It is highly urbanized, almost the entire area is built up and the vacant land is sorely lacking: the population is growing steadily. The number of inhabitants has increased from only 5,200 people in 1922 to more than 200,000 a century later. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com Nowadays you need extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this video format to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike regular videos, while watching 360° videos YouTube show us only a specific field of view similar to human eye (by default 100 degrees out of 360). As a result, the resolution of the visible part of 8K video uploaded to our channel is around 2K (1920p). If you watch in 4K mode the resolution of the visible part would be even less - around 1080p (1K). Please note that AirPano team originally shoots its films in 16,12,10,8K resolution, depending on year and cameras used back then. But before upload to YouTube channel we downscale all our videos to 8K. #AirPanoCity #male #maldives #360video #airpano #VR #drone #city #ocean #island #capital #relaxing #relax #relaxation
</media:description>
<media:community>
<media:starRating count="342" average="5.00" min="1" max="5"/>
<media:statistics views="72355"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:2aJ9cOwbzxo</id>
<yt:videoId>2aJ9cOwbzxo</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>Taj Mahal, the Perl of India. 360 video in 16K</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=2aJ9cOwbzxo"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-08-25T08:12:19+00:00</published>
<updated>2023-11-16T18:13:14+00:00</updated>
<media:group>
<media:title>Taj Mahal, the Perl of India. 360 video in 16K</media:title>
<media:content url="https://www.youtube.com/v/2aJ9cOwbzxo?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i3.ytimg.com/vi/2aJ9cOwbzxo/hqdefault.jpg" width="480" height="360"/>
<media:description>
Don't forget that this is 360 video: you can change the angle of view. In The New Seven Wonders Of The World list Taj Mahal, a mosque-mausoleum located in Indian city of Agra, takes a very important place. In spite of its Muslim origin this white marble necropolis became an actual symbol of India. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! Nowadays you need extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this videoformat to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike regular videos, while watching 360° videos YouTube show us only a specific field of view similar to human eye (by default 100 degrees out of 360). As a result, the resolution of the visible part of 8K video uploaded to our channel is around 2K (1920p). If you watch in 4K mode the resolution of the visible part would be even less - around 1080p (1K). Please note that AirPano team originally shoots its films in 16,12,10,8K resolution, depending on year and cameras used back then. But before upload to YouTube channel we downscale all our videos to 8K. 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com #TajMahal #Agra #India #mausoleum #360video #AirpanoCity #VirtualTravel #aerial
</media:description>
<media:community>
<media:starRating count="467" average="5.00" min="1" max="5"/>
<media:statistics views="63820"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:TQGj7Ib_v88</id>
<yt:videoId>TQGj7Ib_v88</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>
Tribes of South Sudan. Explore Africa in 360° VR. 4K teaser.
</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=TQGj7Ib_v88"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-08-11T10:40:47+00:00</published>
<updated>2023-11-09T17:07:12+00:00</updated>
<media:group>
<media:title>
Tribes of South Sudan. Explore Africa in 360° VR. 4K teaser.
</media:title>
<media:content url="https://www.youtube.com/v/TQGj7Ib_v88?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i1.ytimg.com/vi/TQGj7Ib_v88/hqdefault.jpg" width="480" height="360"/>
<media:description>
At the beginning of 2023, we traveled to South Sudan. About 64 ethnic groups live in South Sudan. And although we managed to visit the lands of five tribes only (Larim, Mundari, Lopit, Didinga, Lotuko), the trip to this most interesting African country was very eventful. The full video with narration is expected soon. Don't forget that this is 360 video: you can change the angle of view. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this videoformat to make it watchable for common users. 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com Also here is the answer for a frequently asked question about true resolution of an 4K 360° video. Unlike regular videos, while watching 360° videos YouTube show us only a specific field of view similar to human eye (by default 100 degrees out of 360). As a result, the resolution of the visible part of 4K mode is something about 1080p (1K). #Sudan #Tribes #tribesofafrica #nature #animal #360video #AirpanoNature #VirtualTravel #nature #naturelovers #travel #Africa
</media:description>
<media:community>
<media:starRating count="177" average="5.00" min="1" max="5"/>
<media:statistics views="17137"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:5nCVL_z5Doo</id>
<yt:videoId>5nCVL_z5Doo</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>
Teotihuacan, Mexico. Scenic Hot Air Balloon Flight. 360 video in 16K
</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=5nCVL_z5Doo"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-07-28T16:04:02+00:00</published>
<updated>2023-11-16T22:54:37+00:00</updated>
<media:group>
<media:title>
Teotihuacan, Mexico. Scenic Hot Air Balloon Flight. 360 video in 16K
</media:title>
<media:content url="https://www.youtube.com/v/5nCVL_z5Doo?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i2.ytimg.com/vi/5nCVL_z5Doo/hqdefault.jpg" width="480" height="360"/>
<media:description>
We express our gratitude to Jesús P Becerra for the help in organizing the filming. Teotihuacan, also known as the City of the Gods, is an archeological site located in the Valley of Mexico. Built between the 1st and 7th centuries A.D., it is characterized by the vast size of its monuments — in particular, the Temple of Quetzalcoatl and the Pyramids of the Sun and the Moon, laid out on geometric and symbolic principles. Don't forget that this is 360 video: you can change the angle of view. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com Nowadays you need extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this videoformat to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike regular videos, while watching 360° videos YouTube show us only a specific field of view similar to human eye (by default 100 degrees out of 360). As a result, the resolution of the visible part of 8K video uploaded to our channel is around 2K (1920p). If you watch in 4K mode the resolution of the visible part would be even less - around 1080p (1K). Please note that AirPano team originally shoots its films in 16,12,10,8K resolution, depending on year and cameras used back then. But before upload to YouTube channel we downscale all our videos to 8K. #AirPanoNature #Teotihuacan #Mexico #360video #airpano #VR #drone #ancient #unesco #unescoworldheritage #hotairballoon #worldheritage #worldheritagesites
</media:description>
<media:community>
<media:starRating count="518" average="5.00" min="1" max="5"/>
<media:statistics views="71000"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:JEV_euIuwlY</id>
<yt:videoId>JEV_euIuwlY</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>Red Roofs of Montenegro. 12K 360 aerial video.</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=JEV_euIuwlY"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-07-14T18:12:36+00:00</published>
<updated>2023-12-19T10:24:50+00:00</updated>
<media:group>
<media:title>Red Roofs of Montenegro. 12K 360 aerial video.</media:title>
<media:content url="https://www.youtube.com/v/JEV_euIuwlY?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i3.ytimg.com/vi/JEV_euIuwlY/hqdefault.jpg" width="480" height="360"/>
<media:description>
Don't forget that this is 360 video: you can change the angle of view. There are many Venetian stone buildings in Montenegro. Their pretty red roofs stand out against the forests, mountains, and bright blue sea. Clay tiles have been used by roofers for centuries. They are practical and can last a hundred years! And they are the subject of our walk through Montenegro today – a symbol of serene and warm southern towns. Don't forget that this is 360 video: you can change the angle of view. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! YouTube does not support 12K 360 video yet, so the video was down-sampled from 12K to 8K. But still you need an extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this videoformat to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike standard videos, in a 360° video you can see only a part of original image (approximately 30 degrees out of 360). As result, the real resolution of the part you can see isn't bigger than 1.3K. 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com #Sea #Ocean #Montenegro #360video #AirpanoNature #VirtualTravel #AirpanoCity #Kotor #Perast #Budva #redroof #UNESCO
</media:description>
<media:community>
<media:starRating count="386" average="5.00" min="1" max="5"/>
<media:statistics views="28336"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:Y0eMbkQqg8Y</id>
<yt:videoId>Y0eMbkQqg8Y</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>Between the Worlds. Relaxing 360 video in 12K</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=Y0eMbkQqg8Y"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-06-29T22:36:59+00:00</published>
<updated>2023-11-10T09:38:28+00:00</updated>
<media:group>
<media:title>Between the Worlds. Relaxing 360 video in 12K</media:title>
<media:content url="https://www.youtube.com/v/Y0eMbkQqg8Y?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i2.ytimg.com/vi/Y0eMbkQqg8Y/hqdefault.jpg" width="480" height="360"/>
<media:description>
Don't forget that this is 360 video: you can change the angle of view. This movie was made by AirPano studio, that has been making documentary aerial 360 videos of the most beautiful places of our planet for more than 15 years. However, in this film it was possible to step away from common visual approach and combine impossible techniques: megacities from different parts of the globe, lakes and mountains, the nature of various continents, urban scenery and underwater kingdoms, Winter and Summer. In this movie the viewer can actually fly between different worlds! The magnificent aspects of Hawaii and Miami, the Lapland of Finland and the Chinese mountains of Huangshan, the mystical lake Baikal and the legendary Rio-de-Janeiro. All of them are fascinating. With each new scene the visual part and musical assistance teleports the viewer into another world. Each scene individually is a documentary film, but the movie “Between the worlds” is proudly an unusual work of modern art! If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com #AirPanoCities #AirPano #360video #aerial #fromabove #vr #virtualtravel #world #betweentheworld #nature #bestplaces #bestdestinations #relax, #relaxingvideo
</media:description>
<media:community>
<media:starRating count="994" average="5.00" min="1" max="5"/>
<media:statistics views="684407"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:cg_jfip4pSQ</id>
<yt:videoId>cg_jfip4pSQ</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>
Northern Lights, Teriberka, Kola Peninsula, 12K 360 video
</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=cg_jfip4pSQ"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-06-16T14:10:24+00:00</published>
<updated>2023-11-17T10:17:34+00:00</updated>
<media:group>
<media:title>
Northern Lights, Teriberka, Kola Peninsula, 12K 360 video
</media:title>
<media:content url="https://www.youtube.com/v/cg_jfip4pSQ?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i4.ytimg.com/vi/cg_jfip4pSQ/hqdefault.jpg" width="480" height="360"/>
<media:description>
Don't forget that this is 360 video: you can change the angle of view. In the Northern part of the Kola Peninsula, just near the Murmansk coast, there is the gulf of Teriberka. It is a bay that "cuts" as deep as 9 km inside the land and creates the Teriberka Peninsula. It is a perfect place for Northern lights observation. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com Nowadays you need extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this videoformat to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike regular videos, while watching 360° videos YouTube show us only a specific field of view similar to human eye (by default 100 degrees out of 360). As a result, the resolution of the visible part of 8K video uploaded to our channel is around 2K (1920p). If you watch in 4K mode the resolution of the visible part would be even less - around 1080p (1K). Please note that AirPano team originally shoots its films in 16,12,10,8K resolution, depending on year and cameras used back then. But before upload to YouTube channel we downscale all our videos to 8K. #AirPanoNature #NorthernLights #Teriberka #360video #airpano #VR #BarentsSea #Sea #night #aurora
</media:description>
<media:community>
<media:starRating count="769" average="5.00" min="1" max="5"/>
<media:statistics views="219828"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:kyN623RzFe0</id>
<yt:videoId>kyN623RzFe0</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>Trip to Tokyo, Japan. Aerial 360 video in 8K</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=kyN623RzFe0"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-06-02T10:09:41+00:00</published>
<updated>2023-11-21T19:16:53+00:00</updated>
<media:group>
<media:title>Trip to Tokyo, Japan. Aerial 360 video in 8K</media:title>
<media:content url="https://www.youtube.com/v/kyN623RzFe0?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i4.ytimg.com/vi/kyN623RzFe0/hqdefault.jpg" width="480" height="360"/>
<media:description>
In the 12th century, a fort was built on the southeastern side of Honshu island and later it became a castle. By the 18th century, it had become one of the largest cities in the world, and we are talking about Tokyo, the modern capital of Japan. We invite you to enjoy the flight over this magnificent Japanese city brightened by the illumination! Don't forget that this is 360 video: you can change the angle of view. If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com Nowadays you need extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this videoformat to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike standard videos, in a 360° video you can see only a part of original image (approximately 30 degrees out of 360). As result, the real resolution of the part you can see isn't bigger than 1.3K. #AirPanoCities #AirPano #360video #Tokyo #aerial #fromabove #vr #virtualtravel #triptotokyo
</media:description>
<media:community>
<media:starRating count="2362" average="5.00" min="1" max="5"/>
<media:statistics views="433144"/>
</media:community>
</media:group>
</entry>
<entry>
<id>yt:video:PnfJDgS9VZc</id>
<yt:videoId>PnfJDgS9VZc</yt:videoId>
<yt:channelId>UCUSElbgKZpE4Xdh5aFWG-Ig</yt:channelId>
<title>Everest. Aerial 360 video trailer shot in 16K</title>
<link rel="alternate" href="https://www.youtube.com/watch?v=PnfJDgS9VZc"/>
<author>
<name>AirPano VR</name>
<uri>
https://www.youtube.com/channel/UCUSElbgKZpE4Xdh5aFWG-Ig
</uri>
</author>
<published>2023-05-19T08:49:03+00:00</published>
<updated>2023-11-22T22:31:14+00:00</updated>
<media:group>
<media:title>Everest. Aerial 360 video trailer shot in 16K</media:title>
<media:content url="https://www.youtube.com/v/PnfJDgS9VZc?version=3" type="application/x-shockwave-flash" width="640" height="390"/>
<media:thumbnail url="https://i1.ytimg.com/vi/PnfJDgS9VZc/hqdefault.jpg" width="480" height="360"/>
<media:description>
Don't forget that this is 360 video: you can change the angle of view. Nepal is lucky to have so many extraordinary landmarks. Not only that Nepal is known as the birthplace of Buddha, it also has the majority of highest mountains in the world: 8 out of 14 8K Peaks are located here. Among them is Mount Everest, the highest mountain on planet Earth. It is also known as Chomolungma (or Qomolangma), which is Tibetan for "Holy Mother." If you enjoyed this video please like, share, comment, favorite, subscribe: https://goo.gl/NZMdaz We regularly publish new 360 videos of the most beautiful places on our planet! 360° photos and videos, stories of our shootings, articles and FAQ you can find on our website: http://AirPano.com Nowadays you need extraordinary computer power for watching 8K 360° videos. If you have troubles with watching such videos, choose 4K or HD quality in the settings of your YouTube player. We hope that YouTube will find a solution for optimization this videoformat to make it watchable for common users. Also here is the answer for a frequently asked question about true resolution of an 8K 360° video. Unlike regular videos, while watching 360° videos YouTube show us only a specific field of view similar to human eye (by default 100 degrees out of 360). As a result, the resolution of the visible part of 8K video uploaded to our channel is around 2K (1920p). If you watch in 4K mode the resolution of the visible part would be even less - around 1080p (1K). Please note that AirPano team originally shoots its films in 16,12,10,8K resolution, depending on year and cameras used back then. But before upload to YouTube channel we downscale all our videos to 8K. #AirPanoNature #Everest #Nepal #360video #airpano #VR #drone #mountains #mountain #highestmountain
</media:description>
<media:community>
<media:starRating count="1258" average="5.00" min="1" max="5"/>
<media:statistics views="488810"/>
</media:community>
</media:group>
</entry>
</feed>
"""

webpage_html_favicon = """<html>
 <head>
 <link rel="shortcut icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico" type="image/x-icon"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_32x32.png" sizes="32x32"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_48x48.png" sizes="48x48"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_96x96.png" sizes="96x96"><link rel="icon" href="https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_144x144.png" sizes="144x144">
 <title>YouTube</title>

 </head>
 <body>
 page body
 </body>
"""

webpage_code_project_contents = """
<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0">
  <channel>
    <title>CodeProject Latest News</title>
    <link>https://www.codeproject.com</link>
    <description>Latest News from CodeProject</description>
    <language>en-us</language>
    <image>
      <title>CodeProject Latest News</title>
      <url>https://www.codeproject.com/App_Themes/Std/Img/logo100x30.gif</url>
      <link>https://www.codeproject.com</link>
      <width>100</width>
      <height>30</height>
      <description>CodeProject</description>
    </image>
    <copyright>Copyright  CodeProject, 1999-2023</copyright>
    <webMaster>Webmaster@codeproject.com (Webmaster)</webMaster>
    <lastBuildDate>Wed, 27 Dec 2023 05:00:00 GMT</lastBuildDate>
    <ttl>20</ttl>
    <generator>C# Hand-coded goodness</generator>
    <item>
      <title>Apple is now banned from selling its latest Apple Watches in the US</title>
      <description>Time to start smuggling Apples across the border?</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63692</link>
      <pubDate>Wed, 27 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.theverge.com/2023/12/26/24012382/apple-import-ban-watch-series-9-ultra-2">The Verge</source>
      <category>§Industry News</category>
      <subject>Apple is now banned from selling its latest Apple Watches in the US</subject>
    </item>
    <item>
      <title>Quantum batteries could provide a new kind of energy storage by messing with time</title>
      <description>When in doubt, slap a "quantum" on it. That solves everything.</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63693</link>
      <pubDate>Wed, 27 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.sciencealert.com/quantum-batteries-could-provide-a-new-kind-of-energy-storage-by-messing-with-time">Science Alert</source>
      <category>§Science And Technology</category>
      <subject>Quantum batteries could provide a new kind of energy storage by messing with time</subject>
    </item>
    <item>
      <title>How software engineering will evolve in 2024</title>
      <description>File, New &gt; Year</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63694</link>
      <pubDate>Wed, 27 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.infoworld.com/article/3711801/how-software-engineering-will-evolve-in-2024.html">Infoworld</source>
      <category>§Developer News</category>
      <category>#Headliner</category>
      <subject>How software engineering will evolve in 2024</subject>
    </item>
    <item>
      <title>Writing code is the same thing as writing prose</title>
      <description>Once upon a time, there was a variable named 'i'...</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63695</link>
      <pubDate>Wed, 27 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.gybe.ca/writing-code-is-the-same-thing-as-writing-prose/">Michael Hart</source>
      <category>§Developer News</category>
      <subject>Writing code is the same thing as writing prose</subject>
    </item>
    <item>
      <title>Physics, AI and music all share a common thread. You just have to look closely enough</title>
      <description>Something, something, something, quantum!</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63696</link>
      <pubDate>Wed, 27 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.sciencefocus.com/apple-news-ingest/physics-ai-music-common">Science Focus</source>
      <category>§Science And Technology</category>
      <subject>Physics, AI and music all share a common thread. You just have to look closely enough</subject>
    </item>
    <item>
      <title>The eternal struggle between open source and proprietary software</title>
      <description>Many hands make light work, but many eyes don't guarantee fewer bugs</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63697</link>
      <pubDate>Wed, 27 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://techcrunch.com/2023/12/26/the-eternal-struggle-between-open-source-and-proprietary-software/">Techcrunch</source>
      <category>§Industry News</category>
      <subject>The eternal struggle between open source and proprietary software</subject>
    </item>
    <item>
      <title>Modern C++ programming</title>
      <description>#include &lt;future&gt;</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63698</link>
      <pubDate>Wed, 27 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://github.com/federico-busato/Modern-CPP-Programming">Federico Busato</source>
      <category>§Developer News</category>
      <subject>Modern C++ programming</subject>
    </item>
    <item>
      <title>Burger King giving discounts if facial recognition thinks you're hungover</title>
      <description>Time for brunch</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63699</link>
      <pubDate>Wed, 27 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://gizmodo.com/burger-king-giving-discounts-if-facial-recognition-thin-1851124496">Gizmodo</source>
      <category>§Industry News</category>
      <subject>Burger King giving discounts if facial recognition thinks you're hungover</subject>
    </item>
    <item>
      <title>I think Amazon is losing the plot</title>
      <description>People who had that opinion also had this opinion of Amazon...</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63700</link>
      <pubDate>Wed, 27 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.codeproject.com/Messages/5979507/I-think-Amazon-is-losing-the-plot">CodeProject</source>
      <category>§Hot Threads</category>
      <subject>I think Amazon is losing the plot</subject>
    </item>
    <item>
      <title>WebGPU now available for testing in Safari Technology Preview</title>
      <description>WebGPU is a new standards-compliant API that enables high-performance 3D graphics and general-purpose computations on the Web.</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63678</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://webkit.org/blog/14879/webgpu-now-available-for-testing-in-safari-technology-preview/">WebKit</source>
      <category>§Tips and Tools</category>
      <subject>WebGPU now available for testing in Safari Technology Preview</subject>
    </item>
    <item>
      <title>Is Blazor the Future of Everything Web?</title>
      <description>In this article we’ll learn how .NET 8 has changed Blazor’s position in the market with features that have modernized and future-proofed the framework for years to come.</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63679</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.telerik.com/blogs/is-blazor-future-everything-web">Telerik</source>
      <category>§Tips and Tools</category>
      <category>#Headliner</category>
      <subject>Is Blazor the Future of Everything Web?</subject>
    </item>
    <item>
      <title>Did anyone try using smart glasses for writing code?</title>
      <description>Now in 3-D!</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63680</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.codeproject.com/Messages/5979276/Did-anyone-try-using-smart-glasses-for-writing-cod">CodeProject</source>
      <category>§Hot Threads</category>
      <subject>Did anyone try using smart glasses for writing code?</subject>
    </item>
    <item>
      <title>I was sent this, and..</title>
      <description>"Bring him home, our wise Odysseus, home at last!"</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63681</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.codeproject.com/Messages/5979168/I-was-sent-this-and">CodeProject</source>
      <category>§Hot Threads</category>
      <subject>I was sent this, and..</subject>
    </item>
    <item>
      <title>New AI can predict people’s time of death with high degree of accuracy, study finds</title>
      <description>Especially if it's the one planning your death</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63682</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.independent.co.uk/tech/deathbot-ai-predict-life-death-b2466988.html">Independent</source>
      <category>§Science And Technology</category>
      <subject>New AI can predict people’s time of death with high degree of accuracy, study finds</subject>
    </item>
    <item>
      <title>Windows 11 Moment 5 is allegedly coming February 2024</title>
      <description>Just a moment</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63683</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.neowin.net/news/windows-11-moment-5-is-allegedly-coming-february-2024/">Neowin</source>
      <category>§Industry News</category>
      <subject>Windows 11 Moment 5 is allegedly coming February 2024</subject>
    </item>
    <item>
      <title>We have used too many levels of abstractions and now the future looks bleak</title>
      <description>Time to bring back realism? Surrealism?</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63684</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://unixsheikh.com/articles/we-have-used-too-many-levels-of-abstractions-and-now-the-future-looks-bleak.html">Unix Sheikh</source>
      <category>§Developer News</category>
      <category>#Headliner</category>
      <subject>We have used too many levels of abstractions and now the future looks bleak</subject>
    </item>
    <item>
      <title>Alternate Futures for “Web Components”</title>
      <description>It seems like Web Components are always just on the cusp of finally catching on.</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63685</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://blog.carlana.net/post/2023/web-component-alternative-futures/">The Ethically-Trained Programmer</source>
      <category>§Tips and Tools</category>
      <subject>Alternate Futures for “Web Components”</subject>
    </item>
    <item>
      <title>The 4 metrics every engineering manager should track</title>
      <description>Missing KLoC/fortnight</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63686</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://shiftmag.dev/the-4-metrics-every-engineering-manager-should-track-1329/">Shift magazine</source>
      <category>§Developer News</category>
      <subject>The 4 metrics every engineering manager should track</subject>
    </item>
    <item>
      <title>Microsoft just paid $76 million for a Wisconsin pumpkin farm</title>
      <description>"The Great Pumpkin will appear and I'll be waiting for him!"</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63687</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.theverge.com/2023/12/22/24012534/microsoft-wisconsin-pumpkin-farm-foxconn-76-million-mount-pleasant">The Verge</source>
      <category>§Industry News</category>
      <subject>Microsoft just paid $76 million for a Wisconsin pumpkin farm</subject>
    </item>
    <item>
      <title>Google is testing an 'AI support assistant' for questions about Google services</title>
      <description>It just returns, "that's cancelled" for every query</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63688</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.androidcentral.com/apps-software/google-ai-support-assistant">Android Central</source>
      <category>§Industry News</category>
      <subject>Google is testing an 'AI support assistant' for questions about Google services</subject>
    </item>
    <item>
      <title>Android malware Chameleon disables Fingerprint Unlock to steal PINs</title>
      <description>Good olde 'password' deemed secure</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63689</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://www.bleepingcomputer.com/news/security/android-malware-chameleon-disables-fingerprint-unlock-to-steal-pins/">Bleeping Computer</source>
      <category>§Industry News</category>
      <subject>Android malware Chameleon disables Fingerprint Unlock to steal PINs</subject>
    </item>
    <item>
      <title>Lawrence Livermore National Lab simulates ‘Armageddon’-style nuclear asteroid deflection</title>
      <description>* Bruce Willis not included</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63690</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://techcrunch.com/2023/12/21/national-lab-simulates-armageddon-style-nuclear-asteroid-deflection/amp/">Techcrunch</source>
      <category>§Science And Technology</category>
      <subject>Lawrence Livermore National Lab simulates ‘Armageddon’-style nuclear asteroid deflection</subject>
    </item>
    <item>
      <title>What’s new in our code coverage tooling?</title>
      <description>"Shut the door and cover me"</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63691</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://devblogs.microsoft.com/dotnet/whats-new-in-our-code-coverage-tooling/">.NET</source>
      <category>§Developer News</category>
      <subject>What’s new in our code coverage tooling?</subject>
    </item>
    <item>
      <title>Auth0 Templates for .NET: A New Powerful Version Released</title>
      <description>A new version of the Auth0 Templates for .NET package has been released: discover the new powerful features.</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63668</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://auth0.com/blog/auth0-templates-for-dotnet-powerful-version/">Auth0</source>
      <category>§Tips and Tools</category>
      <subject>Auth0 Templates for .NET: A New Powerful Version Released</subject>
    </item>
    <item>
      <title>v0</title>
      <description>v0 is a generative user interface system by Vercel powered by AI. It generates copy-and-paste friendly React code based on shadcn/ui and Tailwind CSS that people can use in their projects.</description>
      <author>Kent Sharkey</author>
      <link>https://www.codeproject.com/script/News/View.aspx?nwid=63669</link>
      <pubDate>Tue, 26 Dec 2023 05:00:00 GMT</pubDate>
      <source url="https://v0.dev/faq">Vercel</source>
      <category>§Tips and Tools</category>
      <subject>v0</subject>
    </item>
  </channel>
</rss>
"""

instance_entries_json = """
{
  "links": [
    {
      "source": "https://www.lemonde.fr/en/rss/une.xml",
      "title": "Yotam Ottolenghi: 'A cuisine is never static'",
      "description": "The British-Israeli chef",
      "link": "https://www.lemonde.fr/en/lifestyle/article/2024/01/03/yotam-ottolenghi-a-cuisine-is-never-static_6398241_37.html",
      "date_published": "{0}",
      "permanent": false,
      "bookmarked": false,
      "dead": false,
      "artist": "Le Monde",
      "album": "Le Monde",
      "user": null,
      "language": "en-US",
      "thumbnail": null,
      "age": null,
      "page_rating_contents": 0,
      "page_rating_votes": 0,
      "page_rating_visits": 0,
      "page_rating": 0,
      "tags": [
        "testtag1",
        "testtag2"
      ],
      "vote": 0,
      "comments": [
        "comment1",
        "comment2"
      ]
    },
    {
      "source": "https://moxie.foxnews.com/google-publisher/latest.xml",
      "title": "Next hot thing in hot wings, 'trashed' or 'dirty,' breaks the rules of America's favorite bar food",
      "description": "Double-fried wings, called trash wings in Missouri and dirt wings in Connecticut, have been a regional phenomenon for decades and are poised to become a national trend.",
      "link": "https://www.foxnews.com/lifestyle/next-hot-thing-hot-wings-trashed-dirty-breaks-rules-americas-favorite-bar-food",
      "date_published": "{0}",
      "permanent": false,
      "bookmarked": false,
      "dead": false,
      "artist": "Fox News",
      "album": "Fox News",
      "user": null,
      "language": "en-US",
      "thumbnail": "https://global.fncstatic.com/static/orion/styles/img/fox-news/logos/fox-news-desktop.png",
      "age": null,
      "page_rating_contents": 0,
      "page_rating_votes": 0,
      "page_rating_visits": 0,
      "page_rating": 0,
      "tags": [],
      "vote": 0,
      "comments": []
    }
  ]
}
""".replace("{0}", DateUtils.get_datetime_now_iso())

instance_sources_json_empty = """{"sources": []}"""

instance_entries_json_empty = """{"links": []}"""

instance_entries_source_100_json = """
{
  "links": [
    {
      "source": "https://www.lemonde.fr/en/rss/une.xml",
      "title": "Yotam Ottolenghi: 'A cuisine is never static'",
      "description": "The British-Israeli chef",
      "link": "https://www.lemonde.fr/en/lifestyle/article/2024/01/03/yotam-ottolenghi-a-cuisine-is-never-static_6398241_37.html",
      "date_published": "{0}",
      "permanent": false,
      "bookmarked": false,
      "dead": false,
      "artist": "Le Monde",
      "album": "Le Monde",
      "user": null,
      "language": "en-US",
      "thumbnail": null,
      "age": null,
      "page_rating_contents": 0,
      "page_rating_votes": 0,
      "page_rating_visits": 0,
      "page_rating": 0,
      "tags": [
        "testtag1",
        "testtag2"
      ],
      "vote": 0,
      "comments": [
        "comment1",
        "comment2"
      ]
    }
  ]
}
""".replace("{0}", DateUtils.get_datetime_now_iso())

instance_source_100_url = "https://www.lemonde.fr/en/rss/une.xml"
instance_source_100_json = """
{
  "source": {
    "id": 100,
    "url": "https://www.lemonde.fr/en/rss/une.xml",
    "title": "Source100",
    "category": "Source 100 Category",
    "subcategory": "Source 100 Subcategory",
    "dead": false,
    "export_to_cms": true,
    "remove_after_days": "0",
    "language": "en-US",
    "favicon": "https://yt3.ggpht.com/ytc/AGIKgqMox432cx8APsB9u4UELfpZTjZlzO8nGU_M3PZ_nw=s48-c-k-c0x00ffffff-no-rj",
    "on_hold": false,
    "fetch_period": 3600,
    "source_type": "BaseRssPlugin"
  }
}
"""


from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler


class YouTubeVideoHandlerMock(YouTubeVideoHandler):
    def __init__(self, url=None):
        super().__init__(url)

    def download_details_youtube(self):
        print("Mocked YouTube request URL: {}".format(self.url))

        if self.url.find("v=1234") >= 0:
            self.yt_text = """{"_filename" : "1234 test file name",
            "title" : "1234 test title",
            "description" : "1234 test description",
            "channel_url" : "https://youtube.com/channel/1234-channel",
            "channel" : "1234-channel",
            "id" : "1234-id",
            "channel_id" : "1234-channel-id",
            "thumbnail" : "https://youtube.com/files/1234-thumbnail.png",
            "upload_date" : "20231113",
            "live_status" : "False"
            }"""
            return True
        if self.url.find("v=666") >= 0:
            return False
        if self.url.find("v=555555") >= 0:
            self.yt_text = """{"_filename" : "555555 live video.txt",
            "title" : "555555 live video",
            "description" : "555555 live video description",
            "channel_url" : "https://youtube.com/channel/test.txt",
            "channel" : "JoYoe",
            "id" : "3433",
            "channel_id" : "JoYoe",
            "thumbnail" : "https://youtube.com/files/whatever.png",
            "upload_date" : "20231113",
            "live_status" : "True"
            }"""
        else:
            self.yt_text = """{"_filename" : "test.txt",
            "title" : "test.txt",
            "description" : "test.txt",
            "channel_url" : "https://youtube.com/channel/test.txt",
            "channel" : "JoYoe",
            "id" : "3433",
            "channel_id" : "JoYoe",
            "thumbnail" : "https://youtube.com/files/whatever.png",
            "upload_date" : "20231113",
            "live_status" : "False"
            }"""
        return True

    def download_details_return_dislike(self):
        self.rd_text = """{}"""
        return True


class TestRequestObjectMock(object):
    def __init__(self, url, headers, timeout):
        self.status_code = 200
        self.apparent_encoding = "utf-8"
        self.encoding = "utf-8"

        contents = self.get_contents(url)

        self.text = contents
        self.content = contents
        self.headers = {}

    def get_contents(self, url):
        if url.startswith("https://youtube.com/channel/"):
            return self.get_contents_youtube_channel(url)

        if url.startswith("https://www.youtube.com/feeds"):
            return webpage_samtime_youtube_rss

        if url.startswith("https://isocpp.org/blog/rss/category/news"):
            return webpage_samtime_youtube_rss

        if url.startswith("https://cppcast.com/feed.rss"):
            return webpage_samtime_youtube_rss

        elif url == "https://multiple-favicons/page.html":
            return webpage_html_favicon

        elif url == "https://rsspage.com/rss.xml":
            return webpage_samtime_youtube_rss

        elif url == "https://simple-rss-page.com/rss.xml":
            return webpage_simple_rss_page

        elif url == "https://empty-page.com":
            return ""

        elif url == "https://www.codeproject.com/WebServices/NewsRSS.aspx":
            return webpage_code_project_contents

        elif url == "https://page-with-two-links.com":
            b = PageBuilder()
            b.title_meta = "Page title"
            b.description_meta = "Page description"
            b.og_title = "Page og_title"
            b.og_description = "Page og_description"
            b.body = """<a href="https://link1.com">Link1</a>
                     <a href="https://link2.com">Link2</a>"""

            return b.build_contents()

        elif url == "https://page-with-http-status-500.com":
            self.status_code = 500

        elif url == "https://page-with-http-status-400.com":
            self.status_code = 400

        elif url == "https://page-with-http-status-300.com":
            self.status_code = 300

        elif url == "https://page-with-http-status-200.com":
            self.status_code = 200

        elif url == "https://page-with-http-status-100.com":
            self.status_code = 100

        elif url.startswith("https://instance.com/apps/rsshistory"):
            return self.get_contents_instance(url)

        elif url == "https://title-in-head.com":
            b = PageBuilder()
            b.title = "Page title"
            b.description_meta = "Page description"
            b.og_description = "Page og_description"
            b.body = """Something in the way"""
            return b.build_contents()

        elif url == "https://title-in-meta.com":
            b = PageBuilder()
            b.title = "Page title"
            b.description_meta = "Page description"
            b.og_description = "Page og_description"
            b.body = """Something in the way"""
            return b.build_contents()

        elif url == "https://title-in-og.com":
            b = PageBuilder()
            b.og_title = "Page title"
            b.description_meta = "Page description"
            b.og_description = "Page og_description"
            b.body = """Something in the way"""
            return b.build_contents()

        elif url == "https://linkedin.com":
            b = PageBuilder()
            b.title_meta = "LinkedIn Page title"
            b.description_meta = "LinkedIn Page description"
            b.og_title = "LinkedIn Page og:title"
            b.og_description = "LinkedIn Page og:description"
            return b.build_contents()

        elif url.endswith("robots.txt"):
            return """  """

        b = PageBuilder()
        b.title_meta = "Page title"
        b.description_meta = "Page description"
        b.og_title = "Page og_title"
        b.og_description = "Page og_description"

        return b.build_contents()

    def get_contents_youtube_channel(self, url):
        if url == "https://youtube.com/channel/samtime/rss.xml":
            return webpage_samtime_youtube_rss

        elif url == "https://youtube.com/channel/2020-year-channel/rss.xml":
            return webpage_old_pubdate_rss

        elif url == "https://youtube.com/channel/no-pubdate-channel/rss.xml":
            return webpage_no_pubdate_rss

        elif url == "https://youtube.com/channel/airpano/rss.xml":
            return webpage_airpano

        elif (
            url
            == "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"
        ):
            return webpage_samtime_youtube_rss

    def get_contents_instance(self, url):
        if url == "https://instance.com/apps/rsshistory/entries-json/?query_type=recent":
            return instance_entries_json

        elif url == "https://instance.com/apps/rsshistory/entries-json/?query_type=recent&source_title=Source100":
            return instance_entries_source_100_json

        elif url == "https://instance.com/apps/rsshistory/entries-json/?query_type=recent&page=1":
            return """{}"""

        elif url == "https://instance.com/apps/rsshistory/sources-json/?page=1":
            return """{}"""

        elif url == "https://instance.com/apps/rsshistory/source-json/100":
            return instance_source_100_json

        elif url == "https://instance.com/apps/rsshistory/entry-json/1912018":
            return """{}"""

        elif "/sources-json/":
            return instance_sources_json_empty

        elif "/entries-json/":
            return instance_entries_json_empty

        else:
            return """{}"""


class WebPageDisabled(object):
    def get_contents_function(self, url, headers, timeout):
        print("Mocked Requesting page: {}".format(url))
        return TestRequestObjectMock(url, headers, timeout)

    def disable_web_pages(self):
        from ..webtools import BasePage

        BasePage.get_contents_function = self.get_contents_function

        from ..pluginentries.entryurlinterface import UrlHandler

        UrlHandler.youtube_video_handler = YouTubeVideoHandlerMock
        # UrlHandler.youtube_channel_handler = YouTubeVideoHandlerMock
        # UrlHandler.odysee_video_handler = YouTubeVideoHandlerMock
        # UrlHandler.odysee_channel_handler = YouTubeVideoHandlerMock

    def print_errors(self):
        infos = PersistentInfo.objects.all()
        for info in infos:
            print("Error: {}".format(info.info))

    def no_errors(self):
        return PersistentInfo.objects.all().count() == 0

    def create_example_data(self):
        self.create_example_sources()
        self.create_example_links()
        self.create_example_domains()
        self.create_example_exports()

    def create_example_sources(self):
        source1 = SourceDataController.objects.create(
            url="https://youtube.com",
            title="YouTube",
            category="No",
            subcategory="No",
            export_to_cms=True,
        )
        source2 = SourceDataController.objects.create(
            url="https://linkedin.com",
            title="LinkedIn",
            category="No",
            subcategory="No",
            export_to_cms=False,
        )
        return [source1, source2]

    def create_example_links(self):
        """
        All entries are outdated
        """
        entry1 = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=bookmarked",
            title="The first link",
            source_obj=source_youtube,
            bookmarked=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        entry2 = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=nonbookmarked",
            title="The second link",
            source_obj=source_youtube,
            bookmarked=False,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )
        entry3 = LinkDataController.objects.create(
            source="https://youtube.com",
            link="https://youtube.com?v=permanent",
            title="The first link",
            source_obj=source_youtube,
            permanent=True,
            date_published=DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M"),
            language="en",
        )

        return [entry1, entry2, entry3]

    def create_example_domains(self):
        DomainsController.add("https://youtube.com?v=nonbookmarked")

        DomainsController.objects.create(
            protocol="https",
            domain="youtube.com",
            category="testCategory",
            subcategory="testSubcategory",
        )
        DomainCategories.objects.all().delete()
        DomainSubCategories.objects.all().delete()

    def create_example_keywords(self):
        datetime = KeyWords.get_keywords_date_limit() - timedelta(days=1)
        keyword = KeyWords.objects.create(keyword="test")
        keyword.date_published = datetime
        keyword.save()

        return [keyword]

    def create_example_exports(self):
        export1 = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_DAILY_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        export2 = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_YEAR_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        export3 = DataExport.objects.create(
            export_type=DataExport.EXPORT_TYPE_GIT,
            export_data=DataExport.EXPORT_NOTIME_DATA,
            local_path=".",
            remote_path=".",
            export_entries=True,
            export_entries_bookmarks=True,
            export_entries_permanents=True,
            export_sources=True,
        )

        return [export1, export2, export3]

    def create_example_permanent_data(self):
        p1 = PersistentInfo.objects.create(info="info1", level=10, user="test")
        p1.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p1.save()

        p2 = PersistentInfo.objects.create(info="info2", level=10, user="test")
        p2.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p2.save()

        p3 = PersistentInfo.objects.create(info="info3", level=10, user="test")
        p3.date = DateUtils.from_string("2023-03-03;16:34", "%Y-%m-%d;%H:%M")
        p3.save()

        return [p1, p2, p3]
