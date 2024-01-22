from ..webtools import HtmlPage

from .fakeinternet import FakeInternetTestCase

webpage_no_lang = """<html>
</html>
"""

webpage_lang_not_default = """<html lang="it">
</html>
"""

webpage_no_title = """<html>
</html>
"""

webpage_title_lower = """<html>
 <title>This is a lower case title</title>
</html>
"""

webpage_title_upper = """<html>
 <TITLE>This is a upper case title</TITLE>
</html>
"""

webpage_title_head = """<html>
 <title>selected title</title>
</html>
"""

webpage_title_meta = """<html>
 <meta name="title" content="selected meta title" />
</html>
"""

webpage_title_meta_og = """<html>
 <TITLE>selected meta title</TITLE>
 <meta property="og:title" content="selected og:title" />
</html>
"""

webpage_description_head = """<html>
 <description>selected description</description>
</html>
"""

webpage_description_meta = """<html>
 <meta name="description" content="selected meta description"/>
</html>
"""

webpage_description_meta_og = """<html>
 <description>selected meta description</description>
 <meta property="og:description" content="selected og:description" />
</html>
"""

webpage_meta_article_date = """<html>
 <description>selected meta description</description>
 <meta property="og:description" content="selected og:description" />
 <meta property="article:published_time" content="2024-01-09T21:26:00Z" />
</html>
"""

webpage_meta_music_release_date = """<html>
 <description>selected meta description</description>
 <meta property="og:description" content="selected og:description" />
 <meta name="music:release_date" content="2024-01-09T21:26:00Z"/>
</html>
"""

webpage_meta_youtube_publish_date = """<html>
 <description>selected meta description</description>
 <meta property="og:description" content="selected og:description" />
 <meta itemprop="datePublished" content="2024-01-11T09:00:07-00:00">
 <meta itemprop="uploadDate" content="2024-01-11T09:00:07-00:00">
 <meta itemprop="genre" content="Science &amp; Technology">
</html>
"""


webpage_links = """<html>
 <TITLE>This is a upper case title</TITLE>
 <a custom-peroperty="custom-property-value" href="http://otherpage1.net" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="https://otherpage2.net" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test1" class="contentLink  hero--img -first">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test2.html" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test3.htm" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test4.js" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="/test/test5/" class="class">
   <picture></picture>
   </a>
 <a custom-peroperty="custom-property-value" href="//test6.domain.com/" class="class">
   <picture></picture>
   </a>
</html>
"""

webpage_rss_links = """<html>
 <head>
 <TITLE>This is a upper case title</TITLE>
 <link rel="alternate" type="application/rss+xml" title="9to5Google &raquo; Feed" href="http://your-site.com/your-feed1.rss" />
 <link rel="alternate" type="application/rss+xml" title="9to5Google &raquo; Feed" href="http://your-site.com/your-feed2.rss" />
 <link rel="alternate" type="application/rss+xml" title="9to5Google &raquo; Feed" href="http://your-site.com/your-feed3.rss" />

 </head>
 <body>
 page body
 </body>
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

wall_street_journal_date_full_date = """
<!DOCTYPE html>
<html lang="en-US">
	<head>
		<meta charSet="utf-8"/>
		<link rel="canonical" href="https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b"/>
		<script id="utag_data_script">if(!window.utag_data) window.utag_data = {"page_ad_zone":"","page_content_language":"en-US","page_content_region":"North_America_USA","page_content_source":"WSJ Online","page_content_type":"Article","page_content_type_detail":"immersive","page_editorial_keywords":"israel|leder|wsjworld|gfx-contrib","page_site":"Online Journal","page_site_product":"WSJ","article_author":"Marcus Walker|Anat Peled|Abeer Ayyoub","article_availability_flag":"CENTERTEXT,MVPTEST,CODES_REVIEWED","article_embedded_count":3,"article_format":"web","article_headline":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_headline_orig":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_headline_post":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_id":"WP-WSJ-0001496378","article_image_count":6,"article_inset_type":"bigtop","article_internal_link_count":23,"article_keywords":"israel|leder|wsjworld|gfx-contrib|Asia|Developing Economies|Gaza Strip|Israel|Middle East|Mediterranean Countries|Palestine|West Asia|Political/General News|National/Public Security|Society/Community|Crime/Legal Action|Armed Forces|Human Migration|Politics/International Relations|Refugees/Asylum Seekers|Risk News|Terrorism|Military Action|Content Types|Factiva Filters|C&amp;E Executive News Filter|SYND|WSJ-PRO-WSJ.com|LINK|i17-WP-WSJ-0001496378|LINK|i3-WP-WSJ-0001496378|LINK|i6-WP-WSJ-0001496378|LINK|i4-WP-WSJ-0001496378|LINK|i7-WP-WSJ-0001496378|LINK|i9-WP-WSJ-0001496378|LINK|i5-WP-WSJ-0001496378|LINK|i10-WP-WSJ-0001496378|LINK|i11-WP-WSJ-0001496378|LINK|i1-WP-WSJ-0001496378|political|general news|national|public security|society|community|crime|legal action|armed forces|human migration|politics|international relations|refugees|asylum seekers|risk news|terrorism|military action|content types|factiva filters|c&amp;e executive news filter|asia|developing economies|gaza strip|middle east|mediterranean countries|palestine|west asia","article_publish":"2024-01-11 02:00","article_publish_orig":"2024-01-17 02:00","article_type":"Middle East News","article_video_count":1,"article_word_count":1798,"cms_name":"WSJ Authoring Production","is_column":false,"listing_impression_id":"","page_access":"paid","page_section":"World","page_sponsored_name":"","page_subsection":"Middle East","page_title":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet - WSJ","previous_section":"","stack_name":"Olympia","taxonomy_applies":true,"taxonomy_array":[{"codeType":"thing","score":"0.75","value":"world|europe||"},{"codeType":"thing","score":"0.24","value":"world|middle-east||"}],"taxonomy_primary":"world|middle-east","taxonomy_primary_score":"1","taxonomy_primary_source":"manual","vix":"","user_exp":"","user_ref":"","user_tags":"","user_type":""}</script>
		<script>var aceConfig={"id":"wsj","sendLogs":false,"scripts":[{"id":"gpt","enabled":true,"forceBackend":true},{"id":"prebid","enabled":true,"forceBackend":true},{"id":"liveramp","enabled":true},{"id":"moat","enabled":true,"forceBackend":true},{"id":"uac","fileName":"uac.min.1.0.65.js","enabled":true,"params":{"enableDjcmp":true,"enablePermutive":true,"enablePublisherProvidedId":true,"permutiveSourcepointId":"5eff0d77969bfa03746427eb"},"forceBackend":true},{"id":"djcmp","fileName":"djcmp.min.1.0.52.js","params":{"enableSourcepoint":true,"gdprModalId":490347,"loadVendorScript":false,"modValue":"wsj","permutiveSourcepointId":"5eff0d77969bfa03746427eb","propertyHref":"https://www.wsj.com","propertyId":3634,"uspModalId":741479},"enabled":true,"forceBackend":true},{"id":"sourcepoint2","enabled":true,"forceBackend":true,"params":{"propertyHref":"https://www.wsj.com","propertyId":3634}},{"id":"apstag","enabled":true,"forceBackend":true},{"id":"permutive","enabled":true,"isConsented":true,"loadAfterEvent":"load","params":{"sourcepointId":"5eff0d77969bfa03746427eb"}},{"id":"adtoniq","enabled":false,"isAsync":true,"isConsented":true,"forceBackend":true,"resolver":"adtoniqProxy","url":"https://www.wsj.com/assets-proxy/intdoaq","params":{"brand":"wsj","sourcepointId":"61f2bdf7b00575078c959fee"}},{"id":"proximic","enabled":false}],"preprocessor":[{"funcName":"extendConfigByAceConfigEnv","type":"back"},{"funcName":"extendConfigByAceQueryObject","type":"back"},{"funcName":"extendConfigByAceCookieObject","type":"back"},{"funcName":"setDataAttrFromGlobasOptions","type":"back"},{"funcName":"createInlinedFunctions","type":"back"},{"funcName":"overloadOrchestratorScripts","type":"back"},{"funcName":"generateString","type":"back"},{"funcName":"appendOrchestratorScripts","type":"back"},{"funcName":"extendConfigByAceAttr","type":"front"},{"funcName":"extendConfigByAceCookie","type":"front"},{"funcName":"extendConfigByAceQuery","type":"front"},{"funcName":"overloadScripts","type":"front"},{"funcName":"setDataAttr","type":"front"},{"funcName":"classifyScripts","type":"front"},{"funcName":"addScripts","type":"front"}],"postprocessor":[],"consumerApplication":"wsj-pages-generator:prod"}</script>
		<script>!function(){var e,t,i;window.ace=window.ace||{},e={},t={},i={addToExecutionQueue(e){return t[e]||(t[e]=[]),t[e].push(arguments),t},getSubscribedElements:()=>Object.keys(e),getSubscribedFunctions:t=>Object.keys(e[t]||{}),executeQueue(e){try{t[e]&&t[e].forEach((e=>this.execute(...e))),delete t[e]}catch(e){console.error(e)}},execute(){var[t,i,r,n]=arguments,s=e[t][i],u=e=>e,c=[];return"function"!=typeof s?s:(r&&("function"==typeof r?(u=r,n&&Array.isArray(n)&&(c=n)):Array.isArray(r)&&(c=r)),u(s.apply(null,c)))},__reset(){var i=e=>Object.keys(e).forEach((t=>delete e[t]));i(e),i(t)},hasSubscription(e){return this.getSubscribedElements().indexOf(e)>-1},hasSubscribedFunction(e,t){return this.getSubscribedFunctions(e).indexOf(t)>-1},uniqueFucntionsUnderSubscription(t,i){const{__ace:r=(()=>({}))}=window;let n={};return Object.keys(i).forEach((s=>{e[t][s]?r("log","log",[{type:"warning",initiator:"page",message:"You are trying to subscribe the function "+s+" under the "+t+" namespace again. Use another name."}]):n[s]=i[s]})),n},addSubscription(t,i){if(this.hasSubscription(t)){const r=this.uniqueFucntionsUnderSubscription(t,i);e[t]={...e[t],...r}}else e[t]=i;return e},subscribe(t,i,r){if(r)return e[t]=i,e;if(!i||"object"!=typeof i)throw new Error("Missing third parameter. You must provide an object.");return this.addSubscription(t,i),this.executeQueue(t),e},globalMessaging(){var[e,t,...i]=arguments;if(!e&&!t)return this.getSubscribedElements();if(e&&"string"==typeof e&&!t)return this.getSubscribedFunctions(e);if("string"!=typeof e||"string"!=typeof t)throw new Error("First and second argument must be String types");if(this.hasSubscribedFunction(e,t))return this.execute(e,t,...i);this.addToExecutionQueue(e,t,...i)}},window.__ace=i.globalMessaging.bind(i),window.__ace.subscribe=i.subscribe.bind(i)}();var googletag=googletag||{};googletag.cmd=googletag.cmd||[];var pbjs=pbjs||{};pbjs.que=pbjs.que||[];"use strict";function _typeof(e){return(_typeof="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}!function(){var e=function(){for(var e,t,n=[],r=window,o=r;o;){try{if(o.frames.__tcfapiLocator){e=o;break}}catch(e){}if(o===r.top)break;o=o.parent}e||(function e(){var t=r.document,n=!!r.frames.__tcfapiLocator;if(!n)if(t.body){var o=t.createElement("iframe");o.style.cssText="display:none",o.name="__tcfapiLocator",t.body.appendChild(o)}else setTimeout(e,5);return!n}(),r.__tcfapi=function(){for(var e=arguments.length,r=new Array(e),o=0;o
			<e;o++)r[o]=arguments[o];if(!r.length)return n;"setGdprApplies"===r[0]?r.length>3&&2===parseInt(r[1],10)&&"boolean"==typeof r[3]&&(t=r[3],"function"==typeof r[2]&&r[2]("set",!0)):"ping"===r[0]?"function"==typeof r[2]&&r[2]({gdprApplies:t,cmpLoaded:!1,cmpStatus:"stub"}):n.push(r)},r.addEventListener("message",(function(e){var t="string"==typeof e.data,n={};if(t)try{n=JSON.parse(e.data)}catch(e){}else n=e.data;var r="object"===_typeof(n)&&null!==n?n.__tcfapiCall:null;r&&window.__tcfapi(r.command,r.version,(function(n,o){var a={__tcfapiReturn:{returnValue:n,success:o,callId:r.callId}};e&&e.source&&e.source.postMessage&&e.source.postMessage(t?JSON.stringify(a):a,"*")}),r.parameter)}),!1))};"undefined"!=typeof module?module.exports=e:e()}(),function(){var e=!1,t=window,n=document;function r(e){var n="string"==typeof e.data;try{var r=n?JSON.parse(e.data):e.data;if(r.__cmpCall){var o=r.__cmpCall;t.__uspapi(o.command,o.parameter,(function(t,r){var a={__cmpReturn:{returnValue:t,success:r,callId:o.callId}};e.source.postMessage(n?JSON.stringify(a):a,"*")}))}}catch(r){}}!function e(){if(!t.frames.__uspapiLocator)if(n.body){var r=n.body,o=n.createElement("iframe");o.style.cssText="display:none",o.name="__uspapiLocator",r.appendChild(o)}else setTimeout(e,5)}(),"function"!=typeof __uspapi&&(t.__uspapi=function(){var t=arguments;if(__uspapi.a=__uspapi.a||[],!t.length)return __uspapi.a;"ping"===t[0]?t[2]({gdprAppliesGlobally:e,cmpLoaded:!1},!0):__uspapi.a.push([].slice.apply(t))},__uspapi.msgHandler=r,t.addEventListener("message",r,!1))}(),function(e){var t={};function n(r){if(t[r])return t[r].exports;var o=t[r]={i:r,l:!1,exports:{}};return e[r].call(o.exports,o,o.exports,n),o.l=!0,o.exports}n.m=e,n.c=t,n.d=function(e,t,r){n.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:r})},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n.t=function(e,t){if(1&t&&(e=n(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var r=Object.create(null);if(n.r(r),Object.defineProperty(r,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var o in e)n.d(r,o,function(t){return e[t]}.bind(null,o));return r},n.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return n.d(t,"a",t),t},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.p="/",n(n.s=0)}([function(e,t,n){n.r(t);var r=function(e,t){var n={allRegulations:!1,cb:t,regulationType:"gdpr"};return(0,window.__ace)("djcmp","regulationApplies",[e,n])},o=function(e,t){var n={allRegulations:!1,cb:t,regulationType:"usp"};return(0,window.__ace)("djcmp","regulationApplies",[e,n])};!function(){var e=[];function t(){e.push(arguments)}window.djcmp||(t.gdprApplies=r,t.ccpaApplies=o,t.queue=e,window.djcmp=t)}()}]);
			</script>
			<script>var ace_data = JSON.parse('{}');</script>
			<script>__ace('dataLayer', 'setData', [{ abtUrl: "https://wsj-tools.sc.onservo.com/api/v2/ads/product/wsj/pageType/article?section=World&articleType=Middle%20East%20News" }])</script>
			<script>__ace('dataLayer', 'setData', [{ isUsingOrchestrator: true, abtConfig: {"node_type":"article","product":"wsj","category":"articleType","pageId":"Middle East News","adLocations":{"J":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[{"width":377,"height":50}]}},"C":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[{"width":571,"height":47}]}},"A":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[]}},"S":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":728,"height":90}],"16unit":[{"width":728,"height":90}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"Z":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"MI":{"site":"interactive.wsj.com","zone":"intromessage","active":false,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"MG":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"G":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320},{"width":2,"height":2}],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"M2":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story_m2","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"M3":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story_m3","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"L":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":728,"height":90},{"width":970,"height":90},{"width":970,"height":66},{"width":970,"height":250},{"width":1,"height":6}],"16unit":[{"width":728,"height":90},{"width":970,"height":90},{"width":970,"height":66},{"width":970,"height":250},{"width":1,"height":6}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"IMM":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"H":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story2","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":250},{"width":300,"height":600}]}},"G2":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320},{"width":1,"height":7},{"width":1,"height":6}],"8unit":[{"width":300,"height":250},{"width":320,"height":320},{"width":1,"height":6},{"width":1,"height":7}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RAIL1":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RE":{"sizes":{"4unit":["fluid",{"width":1,"height":6},{"width":1,"height":7}],"8unit":["fluid",{"width":1,"height":6},{"width":1,"height":7}],"12unit":["fluid",{"width":1,"height":6},{"width":1,"height":7},{"width":540,"height":150},{"width":728,"height":90}],"16unit":["fluid",{"width":1,"height":6},{"width":1,"height":7},{"width":700,"height":150},{"width":540,"height":150},{"width":970,"height":250},{"width":728,"height":90}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"MOBILE":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},"fluid"],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"LIVECOVERAGE":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"LOGO":{"sizes":{"4unit":[{"width":1,"height":1}],"8unit":[{"width":1,"height":1}],"12unit":[{"width":1,"height":1}],"16unit":[{"width":1,"height":1}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"WTRN":{"sizes":{"4unit":["fluid"],"8unit":["fluid"],"12unit":["fluid"],"16unit":["fluid"]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"AMP":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320},"fluid"],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"INLINEIMM":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"12unit":[{"width":728,"height":90},{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"16unit":[{"width":728,"height":90},{"width":970,"height":250},{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"G4":{"sizes":{"4unit":[{"width":1,"height":6},{"width":300,"height":250}],"8unit":[{"width":300,"height":250},{"width":1,"height":6}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"Z4":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6}],"8unit":[{"width":300,"height":250},{"width":1,"height":6}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RESHORT":{"sizes":{"4unit":["fluid"],"8unit":["fluid"],"12unit":["fluid",{"width":300,"height":250}],"16unit":["fluid",{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"}},"url":"https://wsj-tools.sc.onservo.com/api/v2/ads/product/wsj/pageType/article?section=World&articleType=Middle%20East%20News"} }])</script>
			<link as="script" href="https://www.wsj.com/asset/ace/ace.min.js" rel="preload"/>
			<link rel="preload" href="https://segment-data.zqtk.net/dowjones-d8s23j?url=https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b" as="script"/>
			<script id="proximic" async="" src="https://segment-data.zqtk.net/dowjones-d8s23j?url=https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b"></script>
			<script>try {
    document.getElementById('proximic').addEventListener('load', function () { window.__ace('page', 'setPerfMark', ['proximic-loaded']); })
  } catch(e) {
    window.__ace('page', 'log', [{
      initiator: 'page',
      type: 'error',
      message: 'Element with id proximic does not exist.'
    }]);
}</script>
</html>
"""

wall_street_journal_date_human_date = """
<!DOCTYPE html>
<html lang="en-US">
	<head>
		<meta charSet="utf-8"/>
		<link rel="canonical" href="https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b"/>
		<script id="utag_data_script">if(!window.utag_data) window.utag_data = {"page_ad_zone":"","page_content_language":"en-US","page_content_region":"North_America_USA","page_content_source":"WSJ Online","page_content_type":"Article","page_content_type_detail":"immersive","page_editorial_keywords":"israel|leder|wsjworld|gfx-contrib","page_site":"Online Journal","page_site_product":"WSJ","article_author":"Marcus Walker|Anat Peled|Abeer Ayyoub","article_availability_flag":"CENTERTEXT,MVPTEST,CODES_REVIEWED","article_embedded_count":3,"article_format":"web","article_headline":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_headline_orig":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_headline_post":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_id":"WP-WSJ-0001496378","article_image_count":6,"article_inset_type":"bigtop","article_internal_link_count":23,"article_keywords":"israel|leder|wsjworld|gfx-contrib|Asia|Developing Economies|Gaza Strip|Israel|Middle East|Mediterranean Countries|Palestine|West Asia|Political/General News|National/Public Security|Society/Community|Crime/Legal Action|Armed Forces|Human Migration|Politics/International Relations|Refugees/Asylum Seekers|Risk News|Terrorism|Military Action|Content Types|Factiva Filters|C&amp;E Executive News Filter|SYND|WSJ-PRO-WSJ.com|LINK|i17-WP-WSJ-0001496378|LINK|i3-WP-WSJ-0001496378|LINK|i6-WP-WSJ-0001496378|LINK|i4-WP-WSJ-0001496378|LINK|i7-WP-WSJ-0001496378|LINK|i9-WP-WSJ-0001496378|LINK|i5-WP-WSJ-0001496378|LINK|i10-WP-WSJ-0001496378|LINK|i11-WP-WSJ-0001496378|LINK|i1-WP-WSJ-0001496378|political|general news|national|public security|society|community|crime|legal action|armed forces|human migration|politics|international relations|refugees|asylum seekers|risk news|terrorism|military action|content types|factiva filters|c&amp;e executive news filter|asia|developing economies|gaza strip|middle east|mediterranean countries|palestine|west asia","article_publish":"Jan 10 2024 02:00","article_publish_orig":"2024-01-17 02:00","article_type":"Middle East News","article_video_count":1,"article_word_count":1798,"cms_name":"WSJ Authoring Production","is_column":false,"listing_impression_id":"","page_access":"paid","page_section":"World","page_sponsored_name":"","page_subsection":"Middle East","page_title":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet - WSJ","previous_section":"","stack_name":"Olympia","taxonomy_applies":true,"taxonomy_array":[{"codeType":"thing","score":"0.75","value":"world|europe||"},{"codeType":"thing","score":"0.24","value":"world|middle-east||"}],"taxonomy_primary":"world|middle-east","taxonomy_primary_score":"1","taxonomy_primary_source":"manual","vix":"","user_exp":"","user_ref":"","user_tags":"","user_type":""}</script>
		<script>var aceConfig={"id":"wsj","sendLogs":false,"scripts":[{"id":"gpt","enabled":true,"forceBackend":true},{"id":"prebid","enabled":true,"forceBackend":true},{"id":"liveramp","enabled":true},{"id":"moat","enabled":true,"forceBackend":true},{"id":"uac","fileName":"uac.min.1.0.65.js","enabled":true,"params":{"enableDjcmp":true,"enablePermutive":true,"enablePublisherProvidedId":true,"permutiveSourcepointId":"5eff0d77969bfa03746427eb"},"forceBackend":true},{"id":"djcmp","fileName":"djcmp.min.1.0.52.js","params":{"enableSourcepoint":true,"gdprModalId":490347,"loadVendorScript":false,"modValue":"wsj","permutiveSourcepointId":"5eff0d77969bfa03746427eb","propertyHref":"https://www.wsj.com","propertyId":3634,"uspModalId":741479},"enabled":true,"forceBackend":true},{"id":"sourcepoint2","enabled":true,"forceBackend":true,"params":{"propertyHref":"https://www.wsj.com","propertyId":3634}},{"id":"apstag","enabled":true,"forceBackend":true},{"id":"permutive","enabled":true,"isConsented":true,"loadAfterEvent":"load","params":{"sourcepointId":"5eff0d77969bfa03746427eb"}},{"id":"adtoniq","enabled":false,"isAsync":true,"isConsented":true,"forceBackend":true,"resolver":"adtoniqProxy","url":"https://www.wsj.com/assets-proxy/intdoaq","params":{"brand":"wsj","sourcepointId":"61f2bdf7b00575078c959fee"}},{"id":"proximic","enabled":false}],"preprocessor":[{"funcName":"extendConfigByAceConfigEnv","type":"back"},{"funcName":"extendConfigByAceQueryObject","type":"back"},{"funcName":"extendConfigByAceCookieObject","type":"back"},{"funcName":"setDataAttrFromGlobasOptions","type":"back"},{"funcName":"createInlinedFunctions","type":"back"},{"funcName":"overloadOrchestratorScripts","type":"back"},{"funcName":"generateString","type":"back"},{"funcName":"appendOrchestratorScripts","type":"back"},{"funcName":"extendConfigByAceAttr","type":"front"},{"funcName":"extendConfigByAceCookie","type":"front"},{"funcName":"extendConfigByAceQuery","type":"front"},{"funcName":"overloadScripts","type":"front"},{"funcName":"setDataAttr","type":"front"},{"funcName":"classifyScripts","type":"front"},{"funcName":"addScripts","type":"front"}],"postprocessor":[],"consumerApplication":"wsj-pages-generator:prod"}</script>
		<script>!function(){var e,t,i;window.ace=window.ace||{},e={},t={},i={addToExecutionQueue(e){return t[e]||(t[e]=[]),t[e].push(arguments),t},getSubscribedElements:()=>Object.keys(e),getSubscribedFunctions:t=>Object.keys(e[t]||{}),executeQueue(e){try{t[e]&&t[e].forEach((e=>this.execute(...e))),delete t[e]}catch(e){console.error(e)}},execute(){var[t,i,r,n]=arguments,s=e[t][i],u=e=>e,c=[];return"function"!=typeof s?s:(r&&("function"==typeof r?(u=r,n&&Array.isArray(n)&&(c=n)):Array.isArray(r)&&(c=r)),u(s.apply(null,c)))},__reset(){var i=e=>Object.keys(e).forEach((t=>delete e[t]));i(e),i(t)},hasSubscription(e){return this.getSubscribedElements().indexOf(e)>-1},hasSubscribedFunction(e,t){return this.getSubscribedFunctions(e).indexOf(t)>-1},uniqueFucntionsUnderSubscription(t,i){const{__ace:r=(()=>({}))}=window;let n={};return Object.keys(i).forEach((s=>{e[t][s]?r("log","log",[{type:"warning",initiator:"page",message:"You are trying to subscribe the function "+s+" under the "+t+" namespace again. Use another name."}]):n[s]=i[s]})),n},addSubscription(t,i){if(this.hasSubscription(t)){const r=this.uniqueFucntionsUnderSubscription(t,i);e[t]={...e[t],...r}}else e[t]=i;return e},subscribe(t,i,r){if(r)return e[t]=i,e;if(!i||"object"!=typeof i)throw new Error("Missing third parameter. You must provide an object.");return this.addSubscription(t,i),this.executeQueue(t),e},globalMessaging(){var[e,t,...i]=arguments;if(!e&&!t)return this.getSubscribedElements();if(e&&"string"==typeof e&&!t)return this.getSubscribedFunctions(e);if("string"!=typeof e||"string"!=typeof t)throw new Error("First and second argument must be String types");if(this.hasSubscribedFunction(e,t))return this.execute(e,t,...i);this.addToExecutionQueue(e,t,...i)}},window.__ace=i.globalMessaging.bind(i),window.__ace.subscribe=i.subscribe.bind(i)}();var googletag=googletag||{};googletag.cmd=googletag.cmd||[];var pbjs=pbjs||{};pbjs.que=pbjs.que||[];"use strict";function _typeof(e){return(_typeof="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}!function(){var e=function(){for(var e,t,n=[],r=window,o=r;o;){try{if(o.frames.__tcfapiLocator){e=o;break}}catch(e){}if(o===r.top)break;o=o.parent}e||(function e(){var t=r.document,n=!!r.frames.__tcfapiLocator;if(!n)if(t.body){var o=t.createElement("iframe");o.style.cssText="display:none",o.name="__tcfapiLocator",t.body.appendChild(o)}else setTimeout(e,5);return!n}(),r.__tcfapi=function(){for(var e=arguments.length,r=new Array(e),o=0;o
			<e;o++)r[o]=arguments[o];if(!r.length)return n;"setGdprApplies"===r[0]?r.length>3&&2===parseInt(r[1],10)&&"boolean"==typeof r[3]&&(t=r[3],"function"==typeof r[2]&&r[2]("set",!0)):"ping"===r[0]?"function"==typeof r[2]&&r[2]({gdprApplies:t,cmpLoaded:!1,cmpStatus:"stub"}):n.push(r)},r.addEventListener("message",(function(e){var t="string"==typeof e.data,n={};if(t)try{n=JSON.parse(e.data)}catch(e){}else n=e.data;var r="object"===_typeof(n)&&null!==n?n.__tcfapiCall:null;r&&window.__tcfapi(r.command,r.version,(function(n,o){var a={__tcfapiReturn:{returnValue:n,success:o,callId:r.callId}};e&&e.source&&e.source.postMessage&&e.source.postMessage(t?JSON.stringify(a):a,"*")}),r.parameter)}),!1))};"undefined"!=typeof module?module.exports=e:e()}(),function(){var e=!1,t=window,n=document;function r(e){var n="string"==typeof e.data;try{var r=n?JSON.parse(e.data):e.data;if(r.__cmpCall){var o=r.__cmpCall;t.__uspapi(o.command,o.parameter,(function(t,r){var a={__cmpReturn:{returnValue:t,success:r,callId:o.callId}};e.source.postMessage(n?JSON.stringify(a):a,"*")}))}}catch(r){}}!function e(){if(!t.frames.__uspapiLocator)if(n.body){var r=n.body,o=n.createElement("iframe");o.style.cssText="display:none",o.name="__uspapiLocator",r.appendChild(o)}else setTimeout(e,5)}(),"function"!=typeof __uspapi&&(t.__uspapi=function(){var t=arguments;if(__uspapi.a=__uspapi.a||[],!t.length)return __uspapi.a;"ping"===t[0]?t[2]({gdprAppliesGlobally:e,cmpLoaded:!1},!0):__uspapi.a.push([].slice.apply(t))},__uspapi.msgHandler=r,t.addEventListener("message",r,!1))}(),function(e){var t={};function n(r){if(t[r])return t[r].exports;var o=t[r]={i:r,l:!1,exports:{}};return e[r].call(o.exports,o,o.exports,n),o.l=!0,o.exports}n.m=e,n.c=t,n.d=function(e,t,r){n.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:r})},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n.t=function(e,t){if(1&t&&(e=n(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var r=Object.create(null);if(n.r(r),Object.defineProperty(r,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var o in e)n.d(r,o,function(t){return e[t]}.bind(null,o));return r},n.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return n.d(t,"a",t),t},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.p="/",n(n.s=0)}([function(e,t,n){n.r(t);var r=function(e,t){var n={allRegulations:!1,cb:t,regulationType:"gdpr"};return(0,window.__ace)("djcmp","regulationApplies",[e,n])},o=function(e,t){var n={allRegulations:!1,cb:t,regulationType:"usp"};return(0,window.__ace)("djcmp","regulationApplies",[e,n])};!function(){var e=[];function t(){e.push(arguments)}window.djcmp||(t.gdprApplies=r,t.ccpaApplies=o,t.queue=e,window.djcmp=t)}()}]);
			</script>
			<script>var ace_data = JSON.parse('{}');</script>
			<script>__ace('dataLayer', 'setData', [{ abtUrl: "https://wsj-tools.sc.onservo.com/api/v2/ads/product/wsj/pageType/article?section=World&articleType=Middle%20East%20News" }])</script>
			<script>__ace('dataLayer', 'setData', [{ isUsingOrchestrator: true, abtConfig: {"node_type":"article","product":"wsj","category":"articleType","pageId":"Middle East News","adLocations":{"J":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[{"width":377,"height":50}]}},"C":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[{"width":571,"height":47}]}},"A":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[]}},"S":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":728,"height":90}],"16unit":[{"width":728,"height":90}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"Z":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"MI":{"site":"interactive.wsj.com","zone":"intromessage","active":false,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"MG":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"G":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320},{"width":2,"height":2}],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"M2":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story_m2","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"M3":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story_m3","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"L":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":728,"height":90},{"width":970,"height":90},{"width":970,"height":66},{"width":970,"height":250},{"width":1,"height":6}],"16unit":[{"width":728,"height":90},{"width":970,"height":90},{"width":970,"height":66},{"width":970,"height":250},{"width":1,"height":6}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"IMM":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"H":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story2","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":250},{"width":300,"height":600}]}},"G2":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320},{"width":1,"height":7},{"width":1,"height":6}],"8unit":[{"width":300,"height":250},{"width":320,"height":320},{"width":1,"height":6},{"width":1,"height":7}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RAIL1":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RE":{"sizes":{"4unit":["fluid",{"width":1,"height":6},{"width":1,"height":7}],"8unit":["fluid",{"width":1,"height":6},{"width":1,"height":7}],"12unit":["fluid",{"width":1,"height":6},{"width":1,"height":7},{"width":540,"height":150},{"width":728,"height":90}],"16unit":["fluid",{"width":1,"height":6},{"width":1,"height":7},{"width":700,"height":150},{"width":540,"height":150},{"width":970,"height":250},{"width":728,"height":90}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"MOBILE":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},"fluid"],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"LIVECOVERAGE":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"LOGO":{"sizes":{"4unit":[{"width":1,"height":1}],"8unit":[{"width":1,"height":1}],"12unit":[{"width":1,"height":1}],"16unit":[{"width":1,"height":1}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"WTRN":{"sizes":{"4unit":["fluid"],"8unit":["fluid"],"12unit":["fluid"],"16unit":["fluid"]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"AMP":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320},"fluid"],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"INLINEIMM":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"12unit":[{"width":728,"height":90},{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"16unit":[{"width":728,"height":90},{"width":970,"height":250},{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"G4":{"sizes":{"4unit":[{"width":1,"height":6},{"width":300,"height":250}],"8unit":[{"width":300,"height":250},{"width":1,"height":6}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"Z4":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6}],"8unit":[{"width":300,"height":250},{"width":1,"height":6}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RESHORT":{"sizes":{"4unit":["fluid"],"8unit":["fluid"],"12unit":["fluid",{"width":300,"height":250}],"16unit":["fluid",{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"}},"url":"https://wsj-tools.sc.onservo.com/api/v2/ads/product/wsj/pageType/article?section=World&articleType=Middle%20East%20News"} }])</script>
			<link as="script" href="https://www.wsj.com/asset/ace/ace.min.js" rel="preload"/>
			<link rel="preload" href="https://segment-data.zqtk.net/dowjones-d8s23j?url=https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b" as="script"/>
			<script id="proximic" async="" src="https://segment-data.zqtk.net/dowjones-d8s23j?url=https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b"></script>
			<script>try {
    document.getElementById('proximic').addEventListener('load', function () { window.__ace('page', 'setPerfMark', ['proximic-loaded']); })
  } catch(e) {
    window.__ace('page', 'log', [{
      initiator: 'page',
      type: 'error',
      message: 'Element with id proximic does not exist.'
    }]);
}</script>
</html>
"""

wall_street_journal_date_human_date_dot = """
<!DOCTYPE html>
<html lang="en-US">
	<head>
		<meta charSet="utf-8"/>
		<link rel="canonical" href="https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b"/>
		<script id="utag_data_script">if(!window.utag_data) window.utag_data = {"page_ad_zone":"","page_content_language":"en-US","page_content_region":"North_America_USA","page_content_source":"WSJ Online","page_content_type":"Article","page_content_type_detail":"immersive","page_editorial_keywords":"israel|leder|wsjworld|gfx-contrib","page_site":"Online Journal","page_site_product":"WSJ","article_author":"Marcus Walker|Anat Peled|Abeer Ayyoub","article_availability_flag":"CENTERTEXT,MVPTEST,CODES_REVIEWED","article_embedded_count":3,"article_format":"web","article_headline":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_headline_orig":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_headline_post":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_id":"WP-WSJ-0001496378","article_image_count":6,"article_inset_type":"bigtop","article_internal_link_count":23,"article_keywords":"israel|leder|wsjworld|gfx-contrib|Asia|Developing Economies|Gaza Strip|Israel|Middle East|Mediterranean Countries|Palestine|West Asia|Political/General News|National/Public Security|Society/Community|Crime/Legal Action|Armed Forces|Human Migration|Politics/International Relations|Refugees/Asylum Seekers|Risk News|Terrorism|Military Action|Content Types|Factiva Filters|C&amp;E Executive News Filter|SYND|WSJ-PRO-WSJ.com|LINK|i17-WP-WSJ-0001496378|LINK|i3-WP-WSJ-0001496378|LINK|i6-WP-WSJ-0001496378|LINK|i4-WP-WSJ-0001496378|LINK|i7-WP-WSJ-0001496378|LINK|i9-WP-WSJ-0001496378|LINK|i5-WP-WSJ-0001496378|LINK|i10-WP-WSJ-0001496378|LINK|i11-WP-WSJ-0001496378|LINK|i1-WP-WSJ-0001496378|political|general news|national|public security|society|community|crime|legal action|armed forces|human migration|politics|international relations|refugees|asylum seekers|risk news|terrorism|military action|content types|factiva filters|c&amp;e executive news filter|asia|developing economies|gaza strip|middle east|mediterranean countries|palestine|west asia","article_publish":"Jan. 09 2024 02:00","article_publish_orig":"2024-01-17 02:00","article_type":"Middle East News","article_video_count":1,"article_word_count":1798,"cms_name":"WSJ Authoring Production","is_column":false,"listing_impression_id":"","page_access":"paid","page_section":"World","page_sponsored_name":"","page_subsection":"Middle East","page_title":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet - WSJ","previous_section":"","stack_name":"Olympia","taxonomy_applies":true,"taxonomy_array":[{"codeType":"thing","score":"0.75","value":"world|europe||"},{"codeType":"thing","score":"0.24","value":"world|middle-east||"}],"taxonomy_primary":"world|middle-east","taxonomy_primary_score":"1","taxonomy_primary_source":"manual","vix":"","user_exp":"","user_ref":"","user_tags":"","user_type":""}</script>
		<script>var aceConfig={"id":"wsj","sendLogs":false,"scripts":[{"id":"gpt","enabled":true,"forceBackend":true},{"id":"prebid","enabled":true,"forceBackend":true},{"id":"liveramp","enabled":true},{"id":"moat","enabled":true,"forceBackend":true},{"id":"uac","fileName":"uac.min.1.0.65.js","enabled":true,"params":{"enableDjcmp":true,"enablePermutive":true,"enablePublisherProvidedId":true,"permutiveSourcepointId":"5eff0d77969bfa03746427eb"},"forceBackend":true},{"id":"djcmp","fileName":"djcmp.min.1.0.52.js","params":{"enableSourcepoint":true,"gdprModalId":490347,"loadVendorScript":false,"modValue":"wsj","permutiveSourcepointId":"5eff0d77969bfa03746427eb","propertyHref":"https://www.wsj.com","propertyId":3634,"uspModalId":741479},"enabled":true,"forceBackend":true},{"id":"sourcepoint2","enabled":true,"forceBackend":true,"params":{"propertyHref":"https://www.wsj.com","propertyId":3634}},{"id":"apstag","enabled":true,"forceBackend":true},{"id":"permutive","enabled":true,"isConsented":true,"loadAfterEvent":"load","params":{"sourcepointId":"5eff0d77969bfa03746427eb"}},{"id":"adtoniq","enabled":false,"isAsync":true,"isConsented":true,"forceBackend":true,"resolver":"adtoniqProxy","url":"https://www.wsj.com/assets-proxy/intdoaq","params":{"brand":"wsj","sourcepointId":"61f2bdf7b00575078c959fee"}},{"id":"proximic","enabled":false}],"preprocessor":[{"funcName":"extendConfigByAceConfigEnv","type":"back"},{"funcName":"extendConfigByAceQueryObject","type":"back"},{"funcName":"extendConfigByAceCookieObject","type":"back"},{"funcName":"setDataAttrFromGlobasOptions","type":"back"},{"funcName":"createInlinedFunctions","type":"back"},{"funcName":"overloadOrchestratorScripts","type":"back"},{"funcName":"generateString","type":"back"},{"funcName":"appendOrchestratorScripts","type":"back"},{"funcName":"extendConfigByAceAttr","type":"front"},{"funcName":"extendConfigByAceCookie","type":"front"},{"funcName":"extendConfigByAceQuery","type":"front"},{"funcName":"overloadScripts","type":"front"},{"funcName":"setDataAttr","type":"front"},{"funcName":"classifyScripts","type":"front"},{"funcName":"addScripts","type":"front"}],"postprocessor":[],"consumerApplication":"wsj-pages-generator:prod"}</script>
		<script>!function(){var e,t,i;window.ace=window.ace||{},e={},t={},i={addToExecutionQueue(e){return t[e]||(t[e]=[]),t[e].push(arguments),t},getSubscribedElements:()=>Object.keys(e),getSubscribedFunctions:t=>Object.keys(e[t]||{}),executeQueue(e){try{t[e]&&t[e].forEach((e=>this.execute(...e))),delete t[e]}catch(e){console.error(e)}},execute(){var[t,i,r,n]=arguments,s=e[t][i],u=e=>e,c=[];return"function"!=typeof s?s:(r&&("function"==typeof r?(u=r,n&&Array.isArray(n)&&(c=n)):Array.isArray(r)&&(c=r)),u(s.apply(null,c)))},__reset(){var i=e=>Object.keys(e).forEach((t=>delete e[t]));i(e),i(t)},hasSubscription(e){return this.getSubscribedElements().indexOf(e)>-1},hasSubscribedFunction(e,t){return this.getSubscribedFunctions(e).indexOf(t)>-1},uniqueFucntionsUnderSubscription(t,i){const{__ace:r=(()=>({}))}=window;let n={};return Object.keys(i).forEach((s=>{e[t][s]?r("log","log",[{type:"warning",initiator:"page",message:"You are trying to subscribe the function "+s+" under the "+t+" namespace again. Use another name."}]):n[s]=i[s]})),n},addSubscription(t,i){if(this.hasSubscription(t)){const r=this.uniqueFucntionsUnderSubscription(t,i);e[t]={...e[t],...r}}else e[t]=i;return e},subscribe(t,i,r){if(r)return e[t]=i,e;if(!i||"object"!=typeof i)throw new Error("Missing third parameter. You must provide an object.");return this.addSubscription(t,i),this.executeQueue(t),e},globalMessaging(){var[e,t,...i]=arguments;if(!e&&!t)return this.getSubscribedElements();if(e&&"string"==typeof e&&!t)return this.getSubscribedFunctions(e);if("string"!=typeof e||"string"!=typeof t)throw new Error("First and second argument must be String types");if(this.hasSubscribedFunction(e,t))return this.execute(e,t,...i);this.addToExecutionQueue(e,t,...i)}},window.__ace=i.globalMessaging.bind(i),window.__ace.subscribe=i.subscribe.bind(i)}();var googletag=googletag||{};googletag.cmd=googletag.cmd||[];var pbjs=pbjs||{};pbjs.que=pbjs.que||[];"use strict";function _typeof(e){return(_typeof="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}!function(){var e=function(){for(var e,t,n=[],r=window,o=r;o;){try{if(o.frames.__tcfapiLocator){e=o;break}}catch(e){}if(o===r.top)break;o=o.parent}e||(function e(){var t=r.document,n=!!r.frames.__tcfapiLocator;if(!n)if(t.body){var o=t.createElement("iframe");o.style.cssText="display:none",o.name="__tcfapiLocator",t.body.appendChild(o)}else setTimeout(e,5);return!n}(),r.__tcfapi=function(){for(var e=arguments.length,r=new Array(e),o=0;o
			<e;o++)r[o]=arguments[o];if(!r.length)return n;"setGdprApplies"===r[0]?r.length>3&&2===parseInt(r[1],10)&&"boolean"==typeof r[3]&&(t=r[3],"function"==typeof r[2]&&r[2]("set",!0)):"ping"===r[0]?"function"==typeof r[2]&&r[2]({gdprApplies:t,cmpLoaded:!1,cmpStatus:"stub"}):n.push(r)},r.addEventListener("message",(function(e){var t="string"==typeof e.data,n={};if(t)try{n=JSON.parse(e.data)}catch(e){}else n=e.data;var r="object"===_typeof(n)&&null!==n?n.__tcfapiCall:null;r&&window.__tcfapi(r.command,r.version,(function(n,o){var a={__tcfapiReturn:{returnValue:n,success:o,callId:r.callId}};e&&e.source&&e.source.postMessage&&e.source.postMessage(t?JSON.stringify(a):a,"*")}),r.parameter)}),!1))};"undefined"!=typeof module?module.exports=e:e()}(),function(){var e=!1,t=window,n=document;function r(e){var n="string"==typeof e.data;try{var r=n?JSON.parse(e.data):e.data;if(r.__cmpCall){var o=r.__cmpCall;t.__uspapi(o.command,o.parameter,(function(t,r){var a={__cmpReturn:{returnValue:t,success:r,callId:o.callId}};e.source.postMessage(n?JSON.stringify(a):a,"*")}))}}catch(r){}}!function e(){if(!t.frames.__uspapiLocator)if(n.body){var r=n.body,o=n.createElement("iframe");o.style.cssText="display:none",o.name="__uspapiLocator",r.appendChild(o)}else setTimeout(e,5)}(),"function"!=typeof __uspapi&&(t.__uspapi=function(){var t=arguments;if(__uspapi.a=__uspapi.a||[],!t.length)return __uspapi.a;"ping"===t[0]?t[2]({gdprAppliesGlobally:e,cmpLoaded:!1},!0):__uspapi.a.push([].slice.apply(t))},__uspapi.msgHandler=r,t.addEventListener("message",r,!1))}(),function(e){var t={};function n(r){if(t[r])return t[r].exports;var o=t[r]={i:r,l:!1,exports:{}};return e[r].call(o.exports,o,o.exports,n),o.l=!0,o.exports}n.m=e,n.c=t,n.d=function(e,t,r){n.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:r})},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n.t=function(e,t){if(1&t&&(e=n(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var r=Object.create(null);if(n.r(r),Object.defineProperty(r,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var o in e)n.d(r,o,function(t){return e[t]}.bind(null,o));return r},n.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return n.d(t,"a",t),t},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.p="/",n(n.s=0)}([function(e,t,n){n.r(t);var r=function(e,t){var n={allRegulations:!1,cb:t,regulationType:"gdpr"};return(0,window.__ace)("djcmp","regulationApplies",[e,n])},o=function(e,t){var n={allRegulations:!1,cb:t,regulationType:"usp"};return(0,window.__ace)("djcmp","regulationApplies",[e,n])};!function(){var e=[];function t(){e.push(arguments)}window.djcmp||(t.gdprApplies=r,t.ccpaApplies=o,t.queue=e,window.djcmp=t)}()}]);
			</script>
			<script>var ace_data = JSON.parse('{}');</script>
			<script>__ace('dataLayer', 'setData', [{ abtUrl: "https://wsj-tools.sc.onservo.com/api/v2/ads/product/wsj/pageType/article?section=World&articleType=Middle%20East%20News" }])</script>
			<script>__ace('dataLayer', 'setData', [{ isUsingOrchestrator: true, abtConfig: {"node_type":"article","product":"wsj","category":"articleType","pageId":"Middle East News","adLocations":{"J":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[{"width":377,"height":50}]}},"C":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[{"width":571,"height":47}]}},"A":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[]}},"S":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":728,"height":90}],"16unit":[{"width":728,"height":90}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"Z":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"MI":{"site":"interactive.wsj.com","zone":"intromessage","active":false,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"MG":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"G":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320},{"width":2,"height":2}],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"M2":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story_m2","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"M3":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story_m3","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"L":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":728,"height":90},{"width":970,"height":90},{"width":970,"height":66},{"width":970,"height":250},{"width":1,"height":6}],"16unit":[{"width":728,"height":90},{"width":970,"height":90},{"width":970,"height":66},{"width":970,"height":250},{"width":1,"height":6}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"IMM":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"H":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story2","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":250},{"width":300,"height":600}]}},"G2":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320},{"width":1,"height":7},{"width":1,"height":6}],"8unit":[{"width":300,"height":250},{"width":320,"height":320},{"width":1,"height":6},{"width":1,"height":7}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RAIL1":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RE":{"sizes":{"4unit":["fluid",{"width":1,"height":6},{"width":1,"height":7}],"8unit":["fluid",{"width":1,"height":6},{"width":1,"height":7}],"12unit":["fluid",{"width":1,"height":6},{"width":1,"height":7},{"width":540,"height":150},{"width":728,"height":90}],"16unit":["fluid",{"width":1,"height":6},{"width":1,"height":7},{"width":700,"height":150},{"width":540,"height":150},{"width":970,"height":250},{"width":728,"height":90}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"MOBILE":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},"fluid"],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"LIVECOVERAGE":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"LOGO":{"sizes":{"4unit":[{"width":1,"height":1}],"8unit":[{"width":1,"height":1}],"12unit":[{"width":1,"height":1}],"16unit":[{"width":1,"height":1}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"WTRN":{"sizes":{"4unit":["fluid"],"8unit":["fluid"],"12unit":["fluid"],"16unit":["fluid"]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"AMP":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320},"fluid"],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"INLINEIMM":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"12unit":[{"width":728,"height":90},{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"16unit":[{"width":728,"height":90},{"width":970,"height":250},{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"G4":{"sizes":{"4unit":[{"width":1,"height":6},{"width":300,"height":250}],"8unit":[{"width":300,"height":250},{"width":1,"height":6}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"Z4":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6}],"8unit":[{"width":300,"height":250},{"width":1,"height":6}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RESHORT":{"sizes":{"4unit":["fluid"],"8unit":["fluid"],"12unit":["fluid",{"width":300,"height":250}],"16unit":["fluid",{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"}},"url":"https://wsj-tools.sc.onservo.com/api/v2/ads/product/wsj/pageType/article?section=World&articleType=Middle%20East%20News"} }])</script>
			<link as="script" href="https://www.wsj.com/asset/ace/ace.min.js" rel="preload"/>
			<link rel="preload" href="https://segment-data.zqtk.net/dowjones-d8s23j?url=https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b" as="script"/>
			<script id="proximic" async="" src="https://segment-data.zqtk.net/dowjones-d8s23j?url=https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b"></script>
			<script>try {
    document.getElementById('proximic').addEventListener('load', function () { window.__ace('page', 'setPerfMark', ['proximic-loaded']); })
  } catch(e) {
    window.__ace('page', 'log', [{
      initiator: 'page',
      type: 'error',
      message: 'Element with id proximic does not exist.'
    }]);
}</script>
</html>
"""

wall_street_journal_date_human_date_one_digit = """
<!DOCTYPE html>
<html lang="en-US">
	<head>
		<meta charSet="utf-8"/>
		<link rel="canonical" href="https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b"/>
		<script id="utag_data_script">if(!window.utag_data) window.utag_data = {"page_ad_zone":"","page_content_language":"en-US","page_content_region":"North_America_USA","page_content_source":"WSJ Online","page_content_type":"Article","page_content_type_detail":"immersive","page_editorial_keywords":"israel|leder|wsjworld|gfx-contrib","page_site":"Online Journal","page_site_product":"WSJ","article_author":"Marcus Walker|Anat Peled|Abeer Ayyoub","article_availability_flag":"CENTERTEXT,MVPTEST,CODES_REVIEWED","article_embedded_count":3,"article_format":"web","article_headline":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_headline_orig":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_headline_post":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet","article_id":"WP-WSJ-0001496378","article_image_count":6,"article_inset_type":"bigtop","article_internal_link_count":23,"article_keywords":"israel|leder|wsjworld|gfx-contrib|Asia|Developing Economies|Gaza Strip|Israel|Middle East|Mediterranean Countries|Palestine|West Asia|Political/General News|National/Public Security|Society/Community|Crime/Legal Action|Armed Forces|Human Migration|Politics/International Relations|Refugees/Asylum Seekers|Risk News|Terrorism|Military Action|Content Types|Factiva Filters|C&amp;E Executive News Filter|SYND|WSJ-PRO-WSJ.com|LINK|i17-WP-WSJ-0001496378|LINK|i3-WP-WSJ-0001496378|LINK|i6-WP-WSJ-0001496378|LINK|i4-WP-WSJ-0001496378|LINK|i7-WP-WSJ-0001496378|LINK|i9-WP-WSJ-0001496378|LINK|i5-WP-WSJ-0001496378|LINK|i10-WP-WSJ-0001496378|LINK|i11-WP-WSJ-0001496378|LINK|i1-WP-WSJ-0001496378|political|general news|national|public security|society|community|crime|legal action|armed forces|human migration|politics|international relations|refugees|asylum seekers|risk news|terrorism|military action|content types|factiva filters|c&amp;e executive news filter|asia|developing economies|gaza strip|middle east|mediterranean countries|palestine|west asia","article_publish":"Jan. 9 2024 02:00","article_publish_orig":"2024-01-17 02:00","article_type":"Middle East News","article_video_count":1,"article_word_count":1798,"cms_name":"WSJ Authoring Production","is_column":false,"listing_impression_id":"","page_access":"paid","page_section":"World","page_sponsored_name":"","page_subsection":"Middle East","page_title":"Israel’s War in Gaza Enters Its Most Perilous Phase Yet - WSJ","previous_section":"","stack_name":"Olympia","taxonomy_applies":true,"taxonomy_array":[{"codeType":"thing","score":"0.75","value":"world|europe||"},{"codeType":"thing","score":"0.24","value":"world|middle-east||"}],"taxonomy_primary":"world|middle-east","taxonomy_primary_score":"1","taxonomy_primary_source":"manual","vix":"","user_exp":"","user_ref":"","user_tags":"","user_type":""}</script>
		<script>var aceConfig={"id":"wsj","sendLogs":false,"scripts":[{"id":"gpt","enabled":true,"forceBackend":true},{"id":"prebid","enabled":true,"forceBackend":true},{"id":"liveramp","enabled":true},{"id":"moat","enabled":true,"forceBackend":true},{"id":"uac","fileName":"uac.min.1.0.65.js","enabled":true,"params":{"enableDjcmp":true,"enablePermutive":true,"enablePublisherProvidedId":true,"permutiveSourcepointId":"5eff0d77969bfa03746427eb"},"forceBackend":true},{"id":"djcmp","fileName":"djcmp.min.1.0.52.js","params":{"enableSourcepoint":true,"gdprModalId":490347,"loadVendorScript":false,"modValue":"wsj","permutiveSourcepointId":"5eff0d77969bfa03746427eb","propertyHref":"https://www.wsj.com","propertyId":3634,"uspModalId":741479},"enabled":true,"forceBackend":true},{"id":"sourcepoint2","enabled":true,"forceBackend":true,"params":{"propertyHref":"https://www.wsj.com","propertyId":3634}},{"id":"apstag","enabled":true,"forceBackend":true},{"id":"permutive","enabled":true,"isConsented":true,"loadAfterEvent":"load","params":{"sourcepointId":"5eff0d77969bfa03746427eb"}},{"id":"adtoniq","enabled":false,"isAsync":true,"isConsented":true,"forceBackend":true,"resolver":"adtoniqProxy","url":"https://www.wsj.com/assets-proxy/intdoaq","params":{"brand":"wsj","sourcepointId":"61f2bdf7b00575078c959fee"}},{"id":"proximic","enabled":false}],"preprocessor":[{"funcName":"extendConfigByAceConfigEnv","type":"back"},{"funcName":"extendConfigByAceQueryObject","type":"back"},{"funcName":"extendConfigByAceCookieObject","type":"back"},{"funcName":"setDataAttrFromGlobasOptions","type":"back"},{"funcName":"createInlinedFunctions","type":"back"},{"funcName":"overloadOrchestratorScripts","type":"back"},{"funcName":"generateString","type":"back"},{"funcName":"appendOrchestratorScripts","type":"back"},{"funcName":"extendConfigByAceAttr","type":"front"},{"funcName":"extendConfigByAceCookie","type":"front"},{"funcName":"extendConfigByAceQuery","type":"front"},{"funcName":"overloadScripts","type":"front"},{"funcName":"setDataAttr","type":"front"},{"funcName":"classifyScripts","type":"front"},{"funcName":"addScripts","type":"front"}],"postprocessor":[],"consumerApplication":"wsj-pages-generator:prod"}</script>
		<script>!function(){var e,t,i;window.ace=window.ace||{},e={},t={},i={addToExecutionQueue(e){return t[e]||(t[e]=[]),t[e].push(arguments),t},getSubscribedElements:()=>Object.keys(e),getSubscribedFunctions:t=>Object.keys(e[t]||{}),executeQueue(e){try{t[e]&&t[e].forEach((e=>this.execute(...e))),delete t[e]}catch(e){console.error(e)}},execute(){var[t,i,r,n]=arguments,s=e[t][i],u=e=>e,c=[];return"function"!=typeof s?s:(r&&("function"==typeof r?(u=r,n&&Array.isArray(n)&&(c=n)):Array.isArray(r)&&(c=r)),u(s.apply(null,c)))},__reset(){var i=e=>Object.keys(e).forEach((t=>delete e[t]));i(e),i(t)},hasSubscription(e){return this.getSubscribedElements().indexOf(e)>-1},hasSubscribedFunction(e,t){return this.getSubscribedFunctions(e).indexOf(t)>-1},uniqueFucntionsUnderSubscription(t,i){const{__ace:r=(()=>({}))}=window;let n={};return Object.keys(i).forEach((s=>{e[t][s]?r("log","log",[{type:"warning",initiator:"page",message:"You are trying to subscribe the function "+s+" under the "+t+" namespace again. Use another name."}]):n[s]=i[s]})),n},addSubscription(t,i){if(this.hasSubscription(t)){const r=this.uniqueFucntionsUnderSubscription(t,i);e[t]={...e[t],...r}}else e[t]=i;return e},subscribe(t,i,r){if(r)return e[t]=i,e;if(!i||"object"!=typeof i)throw new Error("Missing third parameter. You must provide an object.");return this.addSubscription(t,i),this.executeQueue(t),e},globalMessaging(){var[e,t,...i]=arguments;if(!e&&!t)return this.getSubscribedElements();if(e&&"string"==typeof e&&!t)return this.getSubscribedFunctions(e);if("string"!=typeof e||"string"!=typeof t)throw new Error("First and second argument must be String types");if(this.hasSubscribedFunction(e,t))return this.execute(e,t,...i);this.addToExecutionQueue(e,t,...i)}},window.__ace=i.globalMessaging.bind(i),window.__ace.subscribe=i.subscribe.bind(i)}();var googletag=googletag||{};googletag.cmd=googletag.cmd||[];var pbjs=pbjs||{};pbjs.que=pbjs.que||[];"use strict";function _typeof(e){return(_typeof="function"==typeof Symbol&&"symbol"==typeof Symbol.iterator?function(e){return typeof e}:function(e){return e&&"function"==typeof Symbol&&e.constructor===Symbol&&e!==Symbol.prototype?"symbol":typeof e})(e)}!function(){var e=function(){for(var e,t,n=[],r=window,o=r;o;){try{if(o.frames.__tcfapiLocator){e=o;break}}catch(e){}if(o===r.top)break;o=o.parent}e||(function e(){var t=r.document,n=!!r.frames.__tcfapiLocator;if(!n)if(t.body){var o=t.createElement("iframe");o.style.cssText="display:none",o.name="__tcfapiLocator",t.body.appendChild(o)}else setTimeout(e,5);return!n}(),r.__tcfapi=function(){for(var e=arguments.length,r=new Array(e),o=0;o
			<e;o++)r[o]=arguments[o];if(!r.length)return n;"setGdprApplies"===r[0]?r.length>3&&2===parseInt(r[1],10)&&"boolean"==typeof r[3]&&(t=r[3],"function"==typeof r[2]&&r[2]("set",!0)):"ping"===r[0]?"function"==typeof r[2]&&r[2]({gdprApplies:t,cmpLoaded:!1,cmpStatus:"stub"}):n.push(r)},r.addEventListener("message",(function(e){var t="string"==typeof e.data,n={};if(t)try{n=JSON.parse(e.data)}catch(e){}else n=e.data;var r="object"===_typeof(n)&&null!==n?n.__tcfapiCall:null;r&&window.__tcfapi(r.command,r.version,(function(n,o){var a={__tcfapiReturn:{returnValue:n,success:o,callId:r.callId}};e&&e.source&&e.source.postMessage&&e.source.postMessage(t?JSON.stringify(a):a,"*")}),r.parameter)}),!1))};"undefined"!=typeof module?module.exports=e:e()}(),function(){var e=!1,t=window,n=document;function r(e){var n="string"==typeof e.data;try{var r=n?JSON.parse(e.data):e.data;if(r.__cmpCall){var o=r.__cmpCall;t.__uspapi(o.command,o.parameter,(function(t,r){var a={__cmpReturn:{returnValue:t,success:r,callId:o.callId}};e.source.postMessage(n?JSON.stringify(a):a,"*")}))}}catch(r){}}!function e(){if(!t.frames.__uspapiLocator)if(n.body){var r=n.body,o=n.createElement("iframe");o.style.cssText="display:none",o.name="__uspapiLocator",r.appendChild(o)}else setTimeout(e,5)}(),"function"!=typeof __uspapi&&(t.__uspapi=function(){var t=arguments;if(__uspapi.a=__uspapi.a||[],!t.length)return __uspapi.a;"ping"===t[0]?t[2]({gdprAppliesGlobally:e,cmpLoaded:!1},!0):__uspapi.a.push([].slice.apply(t))},__uspapi.msgHandler=r,t.addEventListener("message",r,!1))}(),function(e){var t={};function n(r){if(t[r])return t[r].exports;var o=t[r]={i:r,l:!1,exports:{}};return e[r].call(o.exports,o,o.exports,n),o.l=!0,o.exports}n.m=e,n.c=t,n.d=function(e,t,r){n.o(e,t)||Object.defineProperty(e,t,{enumerable:!0,get:r})},n.r=function(e){"undefined"!=typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(e,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(e,"__esModule",{value:!0})},n.t=function(e,t){if(1&t&&(e=n(e)),8&t)return e;if(4&t&&"object"==typeof e&&e&&e.__esModule)return e;var r=Object.create(null);if(n.r(r),Object.defineProperty(r,"default",{enumerable:!0,value:e}),2&t&&"string"!=typeof e)for(var o in e)n.d(r,o,function(t){return e[t]}.bind(null,o));return r},n.n=function(e){var t=e&&e.__esModule?function(){return e.default}:function(){return e};return n.d(t,"a",t),t},n.o=function(e,t){return Object.prototype.hasOwnProperty.call(e,t)},n.p="/",n(n.s=0)}([function(e,t,n){n.r(t);var r=function(e,t){var n={allRegulations:!1,cb:t,regulationType:"gdpr"};return(0,window.__ace)("djcmp","regulationApplies",[e,n])},o=function(e,t){var n={allRegulations:!1,cb:t,regulationType:"usp"};return(0,window.__ace)("djcmp","regulationApplies",[e,n])};!function(){var e=[];function t(){e.push(arguments)}window.djcmp||(t.gdprApplies=r,t.ccpaApplies=o,t.queue=e,window.djcmp=t)}()}]);
			</script>
			<script>var ace_data = JSON.parse('{}');</script>
			<script>__ace('dataLayer', 'setData', [{ abtUrl: "https://wsj-tools.sc.onservo.com/api/v2/ads/product/wsj/pageType/article?section=World&articleType=Middle%20East%20News" }])</script>
			<script>__ace('dataLayer', 'setData', [{ isUsingOrchestrator: true, abtConfig: {"node_type":"article","product":"wsj","category":"articleType","pageId":"Middle East News","adLocations":{"J":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[{"width":377,"height":50}]}},"C":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[{"width":571,"height":47}]}},"A":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[],"16unit":[]}},"S":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":728,"height":90}],"16unit":[{"width":728,"height":90}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"Z":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"MI":{"site":"interactive.wsj.com","zone":"intromessage","active":false,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"MG":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"G":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320},{"width":2,"height":2}],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"M2":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story_m2","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"M3":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story_m3","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]}},"L":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":728,"height":90},{"width":970,"height":90},{"width":970,"height":66},{"width":970,"height":250},{"width":1,"height":6}],"16unit":[{"width":728,"height":90},{"width":970,"height":90},{"width":970,"height":66},{"width":970,"height":250},{"width":1,"height":6}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"IMM":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"H":{"site":"interactive.wsj.com","zone":"worldnews_middleeast_story2","active":true,"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320}],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":250},{"width":300,"height":600}]}},"G2":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320},{"width":1,"height":7},{"width":1,"height":6}],"8unit":[{"width":300,"height":250},{"width":320,"height":320},{"width":1,"height":6},{"width":1,"height":7}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RAIL1":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":600},{"width":300,"height":250}],"16unit":[{"width":300,"height":1050},{"width":300,"height":600},{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RE":{"sizes":{"4unit":["fluid",{"width":1,"height":6},{"width":1,"height":7}],"8unit":["fluid",{"width":1,"height":6},{"width":1,"height":7}],"12unit":["fluid",{"width":1,"height":6},{"width":1,"height":7},{"width":540,"height":150},{"width":728,"height":90}],"16unit":["fluid",{"width":1,"height":6},{"width":1,"height":7},{"width":700,"height":150},{"width":540,"height":150},{"width":970,"height":250},{"width":728,"height":90}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"MOBILE":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},"fluid"],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7},{"width":320,"height":320}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"LIVECOVERAGE":{"sizes":{"4unit":[{"width":300,"height":250}],"8unit":[{"width":300,"height":250}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"LOGO":{"sizes":{"4unit":[{"width":1,"height":1}],"8unit":[{"width":1,"height":1}],"12unit":[{"width":1,"height":1}],"16unit":[{"width":1,"height":1}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"WTRN":{"sizes":{"4unit":["fluid"],"8unit":["fluid"],"12unit":["fluid"],"16unit":["fluid"]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"AMP":{"sizes":{"4unit":[{"width":300,"height":250},{"width":320,"height":320},"fluid"],"8unit":[{"width":300,"height":250},{"width":320,"height":320}],"12unit":[{"width":300,"height":250}],"16unit":[{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"INLINEIMM":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"8unit":[{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"12unit":[{"width":728,"height":90},{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}],"16unit":[{"width":728,"height":90},{"width":970,"height":250},{"width":300,"height":250},{"width":1,"height":6},{"width":1,"height":7}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"G4":{"sizes":{"4unit":[{"width":1,"height":6},{"width":300,"height":250}],"8unit":[{"width":300,"height":250},{"width":1,"height":6}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"Z4":{"sizes":{"4unit":[{"width":300,"height":250},{"width":1,"height":6}],"8unit":[{"width":300,"height":250},{"width":1,"height":6}],"12unit":[],"16unit":[]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"},"RESHORT":{"sizes":{"4unit":["fluid"],"8unit":["fluid"],"12unit":["fluid",{"width":300,"height":250}],"16unit":["fluid",{"width":300,"height":250}]},"customParams":{},"active":true,"site":"interactive.wsj.com","zone":"worldnews_middleeast_story"}},"url":"https://wsj-tools.sc.onservo.com/api/v2/ads/product/wsj/pageType/article?section=World&articleType=Middle%20East%20News"} }])</script>
			<link as="script" href="https://www.wsj.com/asset/ace/ace.min.js" rel="preload"/>
			<link rel="preload" href="https://segment-data.zqtk.net/dowjones-d8s23j?url=https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b" as="script"/>
			<script id="proximic" async="" src="https://segment-data.zqtk.net/dowjones-d8s23j?url=https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b"></script>
			<script>try {
    document.getElementById('proximic').addEventListener('load', function () { window.__ace('page', 'setPerfMark', ['proximic-loaded']); })
  } catch(e) {
    window.__ace('page', 'log', [{
      initiator: 'page',
      type: 'error',
      message: 'Element with id proximic does not exist.'
    }]);
}</script>
</html>
"""


class HtmlPageTest(FakeInternetTestCase):
    def test_default_language(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_no_lang)
        self.assertEqual(p.get_language(), "")
        self.assertTrue(p.is_html())

    def test_language_it(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_lang_not_default)
        self.assertEqual(p.get_language(), "it")

    def test_no_title(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_no_title)

        # when page has no title, URL is chosen for the title
        self.assertEqual(p.get_title(), "http://test.com/my-site-test")

    def test_title_lowercase(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_title_lower)
        self.assertEqual(p.get_title(), "This is a lower case title")

    def test_title_uppercase(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_title_upper)
        self.assertEqual(p.get_title(), "This is a upper case title")

    def test_title_head(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_title_head)
        self.assertEqual(p.get_title(), "selected title")

    def test_title_meta(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_title_meta)
        self.assertEqual(p.get_title(), "selected meta title")

    def test_title_meta_og(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_title_meta_og)
        self.assertEqual(p.get_title(), "selected og:title")

    def test_description_head(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_description_head)
        self.assertEqual(p.get_description(), "selected description")

    def test_description_meta(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_description_meta)
        self.assertEqual(p.get_description(), "selected meta description")

    def test_description_meta_og(self):
        # default language
        p = HtmlPage("http://test.com/my-site-test", webpage_description_meta_og)
        self.assertEqual(p.get_description(), "selected og:description")

    def test_is_youtube(self):
        # default language
        p = HtmlPage("http://youtube.com/?v=1234", webpage_title_upper)
        self.assertTrue(p.is_youtube())

        p = HtmlPage("http://youtu.be/djjdj", webpage_title_upper)
        self.assertTrue(p.is_youtube())

        p = HtmlPage("http://www.m.youtube/?v=1235", webpage_title_upper)
        self.assertTrue(p.is_youtube())

        p = HtmlPage("http://twitter.com/test", webpage_title_upper)
        self.assertFalse(p.is_youtube())

    def test_is_mainstream(self):
        # default language
        p = HtmlPage("http://youtube.com/?v=1234", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://youtu.be/djjdj", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://www.m.youtube/?v=1235", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://twitter.com/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://www.facebook.com/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://www.rumble.com/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

        p = HtmlPage("http://wikipedia.org/test", webpage_title_upper)
        self.assertTrue(p.is_mainstream())

    def test_get_links(self):
        p = HtmlPage("http://mytestpage.com/?argument=value", webpage_links)

        links = p.get_links()

        self.assertTrue("http://otherpage1.net" in links)
        self.assertTrue("https://otherpage2.net" in links)

        self.assertTrue("http://mytestpage.com/test/test1" in links)
        self.assertTrue("http://mytestpage.com/test/test2.html" in links)
        self.assertTrue("http://mytestpage.com/test/test3.htm" in links)
        # java script is not accepted by default
        self.assertTrue("http://mytestpage.com/test/test4.js" not in links)
        self.assertTrue("http://mytestpage.com/test/test5/" in links)
        self.assertTrue("https://test6.domain.com/" in links)

    def test_get_links_nodomain(self):
        p = HtmlPage("http://mytestpage.com/nodomain/", webpage_links)

        links = p.get_links()

        self.assertTrue("http://otherpage1.net" in links)
        self.assertTrue("https://otherpage2.net" in links)

        self.assertTrue("http://mytestpage.com/test/test1" in links)
        self.assertTrue("http://mytestpage.com/test/test2.html" in links)
        self.assertTrue("http://mytestpage.com/test/test3.htm" in links)
        # java script is not accepted by default
        self.assertTrue("http://mytestpage.com/test/test4.js" not in links)
        self.assertTrue("http://mytestpage.com/test/test5/" in links)
        self.assertTrue("https://test6.domain.com/" in links)

    def test_get_rss_url(self):
        p = HtmlPage("http://mytestpage.com/nodomain/", webpage_rss_links)

        rss_url = p.get_rss_url()

        self.assertEqual("http://your-site.com/your-feed1.rss", rss_url)

    def test_get_rss_urls(self):
        p = HtmlPage("http://mytestpage.com/nodomain/", webpage_rss_links)

        all_rss = p.get_rss_urls()

        self.assertTrue("http://your-site.com/your-feed1.rss" in all_rss)
        self.assertTrue("http://your-site.com/your-feed2.rss" in all_rss)
        self.assertTrue("http://your-site.com/your-feed3.rss" in all_rss)

    def test_get_favicons(self):
        p = HtmlPage("http://mytestpage.com/nodomain/", webpage_html_favicon)

        all_favicons = p.get_favicons()

        self.assertEqual(
            all_favicons[0][0],
            "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon.ico",
        )
        self.assertEqual(
            all_favicons[1][0],
            "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_32x32.png",
        )
        self.assertEqual(
            all_favicons[2][0],
            "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_48x48.png",
        )
        self.assertEqual(
            all_favicons[3][0],
            "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_96x96.png",
        )
        self.assertEqual(
            all_favicons[4][0],
            "https://www.youtube.com/s/desktop/e4d15d2c/img/favicon_144x144.png",
        )

    def test_get_date_published_article_date(self):
        p = HtmlPage(
            "https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b?mod=hp_lead_pos7",
            webpage_meta_article_date,
        )

        date = p.get_date_published()
        self.assertTrue(date)
        self.assertEqual(date.isoformat(), "2024-01-09T21:26:00+00:00")

    def test_get_date_published_music_date(self):
        p = HtmlPage(
            "https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b?mod=hp_lead_pos7",
            webpage_meta_music_release_date,
        )

        date = p.get_date_published()
        self.assertTrue(date)
        self.assertEqual(date.isoformat(), "2024-01-09T21:26:00+00:00")

    def test_get_date_published_youtube(self):
        p = HtmlPage(
            "https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b?mod=hp_lead_pos7",
            webpage_meta_youtube_publish_date,
        )

        date = p.get_date_published()
        self.assertTrue(date)
        self.assertEqual(date.isoformat(), "2024-01-11T09:00:07+00:00")

    def test_guess_date_for_full_date(self):
        p = HtmlPage(
            "https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b?mod=hp_lead_pos7",
            wall_street_journal_date_full_date,
        )

        date = p.guess_date()
        self.assertTrue(date)
        self.assertEqual(date.isoformat(), "2024-01-11T00:00:00+00:00")

    def test_guess_date_for_human_date(self):
        p = HtmlPage(
            "https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b?mod=hp_lead_pos7",
            wall_street_journal_date_human_date,
        )

        date = p.guess_date()
        self.assertTrue(date)
        self.assertEqual(date.isoformat(), "2024-01-10T00:00:00+00:00")

    def test_guess_date_for_human_date_dot(self):
        p = HtmlPage(
            "https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b?mod=hp_lead_pos7",
            wall_street_journal_date_human_date_dot,
        )

        date = p.guess_date()
        self.assertTrue(date)
        self.assertEqual(date.isoformat(), "2024-01-09T00:00:00+00:00")

    def test_guess_date_for_human_date_one_digit(self):
        p = HtmlPage(
            "https://www.wsj.com/world/middle-east/israel-war-gaza-hamas-perilous-phase-1ed3ea9b?mod=hp_lead_pos7",
            wall_street_journal_date_human_date_one_digit,
        )

        date = p.guess_date()
        self.assertTrue(date)
        self.assertEqual(date.isoformat(), "2024-01-09T00:00:00+00:00")
