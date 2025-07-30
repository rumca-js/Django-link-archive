"""
This is example script about how to use this project as a simple RSS reader
"""
import json
import threading
from sqlalchemy import (
    create_engine,
)
from flask import Flask, request, jsonify, Response

from rsshistory.webtools import (
   WebConfig,
   RemoteServer,
   FeedClient,
)
from utils.sqlmodel import SqlModel


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


@app.route("/entries")
def info():
    text = ""

    link = request.args.get("link")
    index = 0

    entries = client.get_entries()
    for entry in reversed(entries):
        if link and entry.link.find(link) == -1:
            continue

        index += 1

        if index > 1000:
            break

        source = client.get_source(entry.source)

        text += """
            <a href="{}" style="display: flex; align-items: center; gap: 10px; text-decoration: none; color: inherit; margin-bottom: 10px;">
                <img src="{}" width="100px" style="flex-shrink: 0;"/>
                <div>
                    <div>{}</div>
                    <div>{}</div>
                    <div>{}</div>
                    <div>{}</div>
                </div>
            </a>
            """.format(entry.link, entry.thumbnail, entry.title, entry.link, entry.date_published, source.title)

    return get_html(id=0, body=text, title="Entries")


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

    client.refresh()


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
