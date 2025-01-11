from pathlib import Path
from flask import Flask, request, jsonify
import subprocess

from rsshistory import webtools


app = Flask(__name__)


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

    return jsonify(all_properties)


@app.route('/')
def home():
    return """
    <h1>Run Command</h1>
    <form action="/run" method="get">
        Command: <input type="text" name="url" required>
        <button type="submit">Run</button>
    </form>
    """


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
        except json.JSONDecodeError:
            pass

    return run_webtools_url(url, parsed_crawler_data)


if __name__ == '__main__':
    # Run the Flask app on port 3000
    app.run(debug=True, port=3000)

