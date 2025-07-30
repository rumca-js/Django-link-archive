"""
This is example script about how to use this project as a simple RSS reader
"""
import json
import time
import threading

from sqlalchemy import (
    create_engine,
)

from flask import Flask, request, jsonify, Response

from utils.sqlmodel import SqlModel
from rsshistory.webtools import (
   WebConfig,
   RemoteServer,
   FeedClient,
   Url,
)


engine = create_engine("sqlite:///feedclient.db")
#model = SqlModel(engine=engine)
client = FeedClient(engine=engine)

app = Flask(__name__)


def get_html(id, body, title="", index=False):
    if not index:
        if not id:
            id = ""
        body = '<a href="/?id={}">Back</a>'.format(id) + body

    html = """<!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{}</title>
    </head>
    <body>
    {}
    </body>
    </html>
    """.format(
        title, body
    )

    return html


@app.route("/")
def index():
    id = 0

    # fmt: off

    command_links = []
    command_links.append({"link" : "/entries", "name":"entries", "description":"Shows entries"})
    command_links.append({"link" : "/sources", "name":"sources", "description":"Shows sources"})

    # fmt: on

    text = """<h1>Commands</h1>"""

    for link_data in command_links:
        text += """<div><a href="{}?id={}">{}</a> - {}</div>""".format(
            link_data["link"], id, link_data["name"], link_data["description"]
        )

    return get_html(id=id, body=text, title="Yafr server", index=True)


@app.route("/entries")
def entries():
    text = ""

    link = request.args.get("link")
    source_id = request.args.get("source")

    index = 0

    entries = client.get_entries()
    for entry in reversed(entries):
        if link and entry.link.find(link) == -1:
            continue

        if source_id and entry.source != int(source_id):
            continue

        index += 1

        if index > 1000:
            break

        source = client.get_source(entry.source)

        text += """
            <a href="/entry?id={}" style="display: flex; align-items: center; gap: 10px; text-decoration: none; color: inherit; margin-bottom: 10px;">
                <img src="{}" width="100px" style="flex-shrink: 0;"/>
                <div>
                    <div>{}</div>
                    <div>{}</div>
                    <div>{}</div>
                    <div>{}</div>
                </div>
            </a>
            """.format(entry.id, entry.thumbnail, entry.title, entry.link, entry.date_published, source.title)

    return get_html(id=0, body=text, title="Entries")


@app.route("/entry")
def entry():
    text = ""

    link = request.args.get("link")
    id = request.args.get("id")
    index = 0

    entry = client.get_entry(id = id)

    if entry:
        source = client.get_source(entry.source)

        handler = Url.get_type(entry.link)
        if handler.get_link_embed():
            embed = handler.get_link_embed()

            text += """
            <div width=50% height=50%>
            <iframe src="{0}" frameborder="0" allowfullscreen class="youtube_player_frame" referrerpolicy="no-referrer-when-downgrade"></iframe>
            </div>
            """.format(embed)

            text += """
                <a href="{}" style="display: flex; align-items: center; gap: 10px; text-decoration: none; color: inherit; margin-bottom: 10px;">
                    <div>
                        <div>{}</div>
                        <div>{}</div>
                        <div>{}</div>
                        <div>{}</div>
                        <pre>{}</pre>
                    </div>
                </a>
                """.format(entry.link, entry.thumbnail, entry.title, entry.link, entry.date_published, source.title, entry.description)

        else:
            text += """
                <a href="{}" style="display: flex; align-items: center; gap: 10px; text-decoration: none; color: inherit; margin-bottom: 10px;">
                    <div>
                        <img src="{}" width="200px" style="flex-shrink: 0;"/>
                        <div>{}</div>
                        <div>{}</div>
                        <div>{}</div>
                        <div>{}</div>
                        <pre>{}</pre>
                    </div>
                </a>
                """.format(entry.link, entry.thumbnail, entry.title, entry.link, entry.date_published, source.title, entry.description)

    else:
        text = "not found"

    return get_html(id=0, body=text, title="Entries")


@app.route("/sources")
def sources():
    text = ""

    link = request.args.get("link")
    index = 0

    sources = client.get_sources()
    for source in sources:
        if link and source.url.find(link) == -1:
            continue

        index += 1

        if index > 1000:
            break

        text += """
            <a href="/source?id={}" style="display: flex; align-items: center; gap: 10px; text-decoration: none; color: inherit; margin-bottom: 10px;">
                <img src="{}" width="100px" style="flex-shrink: 0;"/>
                <div>
                    <div>{}</div>
                    <div>{}</div>
                </div>
            </a>
            """.format(source.id, source.favicon, source.url, source.title)

    return get_html(id=0, body=text, title="Sources")


@app.route("/source")
def source():
    text = ""

    link = request.args.get("link")
    id = request.args.get("id")
    index = 0

    source = client.get_source(id=id)

    if source:
        text += """
                <img src="{}" width="100px" style="flex-shrink: 0;"/>
                <div>
                    <div>{}</div>
                    <div>{}</div>
                    <div>{}</div>
                    <a href="/entries?source={}">Entries</a>
                </div>
            """.format(source.favicon, source.id, source.title, source.url, source.id)
    else:
        text = "Not found"

    return get_html(id=0, body=text, title="Source")


def fetch(url):
    request_server = RemoteServer("http://127.0.0.1:3000")

    all_properties = request_server.get_getj(url, name="RequestsCrawler")
    return all_properties


def read_sources(file):
    with open(file, "r") as fh:
        contents = fh.read()
        return json.loads(contents)


def background_refresh():
    news_sources = read_sources("init_sources_news.json")
    for source in news_sources:
        url = source["url"]
        #print(url)
        client.follow_url(url)

    while True:
        client.refresh()
        time.sleep(60*10) # every 10 minutes


def start_server():
    host = "127.0.0.1"
    port=8000

    context = None
    app.run(debug=True, host=host, port=port, threaded=True)


def main():
    WebConfig.init()

    # Start refresh in a daemon thread
    refresh_thread = threading.Thread(target=background_refresh, daemon=True)
    refresh_thread.start()

    start_server()


if __name__ == "__main__":
    main()
