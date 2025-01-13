"""
Starts flask server at the specified location.

Access through:
    ip:port/run?url=.... etc.

Examples:
http://127.0.0.1:3000/run?url=https://google.com&crawler_data={"crawler":"StealthRequestsCrawler","name":"StealthRequestsCrawler","settings": {"timeout_s":20}}
http://127.0.0.1:3000/run?url=https://google.com&crawler_data={"crawler":"SeleniumChromeFull","name":"SeleniumChromeFull","settings": {"timeout_s":50, "driver_executable" : "/usr/bin/chromedriver"}}
"""
from pathlib import Path
from flask import Flask, request, jsonify
import json
import subprocess
import argparse

from rsshistory import webtools


app = Flask(__name__)


url_history = []


def run_cmd_url(url):
    output_file = Path("storage") / "out.txt"

    # TODO timeout

    command = ["poetry", "run", "python", "crawleebeautifulsoup.py", "--url", url, "--output-file", output_file]
    
    try:
        # Run the command using subprocess
        result = subprocess.run(
            command,
            #shell=True,
            text=True,
            capture_output=True,
            check=True
        )

        # TODO read response

        #with open(str(output_file), "rb") as fh:
        #    bytes = fh.read()
        #    self.response = get_response_from_bytes(all_bytes)

        output = result.stdout
        error = result.stderr
        return jsonify({
            "success": True,
            "output": output,
            "error": error
        })
    except subprocess.CalledProcessError as e:
        # Handle command errors
        return jsonify({
            "success": False,
            "output": e.stdout,
            "error": e.stderr,
            "return_code": e.returncode
        })
    except Exception as e:
        # Handle general errors
        return jsonify({
            "success": False,
            "error": str(e)
        })


def run_webtools_url(url, crawler_data):
    page_url = webtools.Url(url)
    options = page_url.get_init_page_options()

    if crawler_data:
        crawler_data["crawler"] = webtools.WebConfig.get_crawler_from_string(crawler_data["crawler"])
        options.mode_mapping = [crawler_data]

    page_url = webtools.Url(url, page_options=options)
    response = page_url.get_response()
    all_properties = page_url.get_properties(full=True)

    return all_properties


@app.route('/')
def home():
    text = """
    <h1>Run Command</h1>
    <form action="/run" method="get">
        Command: <input type="text" name="url" required>
        <button type="submit">Run</button>
    </form>
    """

    text += "<h1>Url history</h1>"
    for item in url_history:
        text += "<div>{}</div>".format(item)

    return text


@app.route('/run', methods=['GET'])
def run_command():
    # Retrieve the command from the query parameters
    url = request.args.get('url')
    crawler_data = request.args.get('crawler_data')

    if not url:
        return jsonify({
            "success": False,
            "error": "No url provided"
        }), 400

    parsed_crawler_data = None
    if crawler_data:
        try:
            parsed_crawler_data = json.loads(crawler_data)
        except json.JSONDecodeError as E:
            print(str(E))

    print("Running:{}, with:{}".format(url, crawler_data))

    if len(url_history) > 0:
        url_history.pop(0)

    url_history.append(url)

    all_properties = run_webtools_url(url, parsed_crawler_data)

    return jsonify(all_properties)



class CommandLineParser(object):
    """
    Headers can only be passed by input binary file
    """

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Remote server options")
        self.parser.add_argument(
            "--port", default=3000, type=int, help="Port number to be used"
        )
        self.parser.add_argument("--host", default="0.0.0.0", help="Host")

        self.args = self.parser.parse_args()


if __name__ == '__main__':
    p = CommandLineParser()
    p.parse()

    app.run(debug=True, host=p.args.host, port=p.args.port, threaded=True)
