"""
This server accepts web scraping commands.

We communicate through binary interface:
 - PageRequestObject
 - PageResponseObject

Communication through port should be used, communication through single file is a potential bottleneck

Communication is only for request - response pairs.

Communication breakdown:
    [server] Server starts, listens for incoming clients
    [client A] client connects
    [server] Accepts client. Handles connection in in task 1
    [client A] client sends request
    [server] Start crawling script in task 1
    [server] we end processing in task 1
    [crawling script] starts, fetches internet data produces response, connects to server
    [server] Accepts crawling script client. Handles connection in in task 2
    [crawling script] crawling script sends response
    [crawling script] terminates
    [server] Handles response in task 2
    [server] Closes all client sockets for that request
    [server] Closes socket for crawling script
    [server] we end processing in task 2
    [client A] terminates
"""

import argparse
import socket
import threading
import json

from pathlib import Path
from rsshistory import webtools
from rsshistory.webtools import ipc
import subprocess
import traceback
from datetime import datetime, timedelta


mutex = threading.Lock()
max_transaction_timeout_s = 40


# TODO request mapping [connection] => url
# TODO send responses using it
# request[url] -> list of connections
#


requests = []  # date, connection, request


def run_script(script, request, parser):
    if script is None:
        print("Client has not set script to execute")
        return

    # run response through file, only if requested
    if "output_file" in parser.args and parser.args.output_file:
        return run_script_with_file(script, request, parser)
    else:
        run_script_with_port(script, request, parser)


def run_script_with_port(script, request, parser):
    if script is None:
        print("Client has not set script to execute")
        return

    if "port" in parser.args:
        script = '{} --url "{}" --port "{}" --timeout {} --ssl-verify {}'.format(
            script, request.url, ipc.DEFAULT_PORT, request.timeout_s, request.ssl_verify
        )

    print("Running {} with timeout:{}".format(script, request.timeout_s))

    try:
        p = subprocess.run(script, shell=True, timeout=request.timeout_s + 3)
    except Exception as E:
        print(str(E))
        print("Could not finish command")
        return


def run_script_with_file(script, request, parser):
    if script is None:
        print("Client has not set script to execute")
        return

    output_file = Path("output.txt")

    if "output_file" in parser.args:
        script = '{} --url "{}" --output-file "{}" --timeout {} --ssl-verify {}'.format(
            script, request.url, str(output_file), request.timeout_s, request.ssl_verify
        )

    print("Running {} with timeout:{}".format(script, request.timeout_s))

    with mutex:
        try:
            p = subprocess.run(script, shell=True, timeout=request.timeout_s + 3)
        except Exception as E:
            print(str(E))
            print("Could not finish command")
            return

    # response comes from socket connection

    all_bytes = None

    if output_file.exists():
        print("File exists")
        with open(str(output_file), "rb") as fh:
            all_bytes = fh.read()

        output_file.unlink()
    else:
        print("Error! File does not exist!")

    return all_bytes


def delete_connection(c):
    for index, request_data in enumerate(requests):
        connection = request_data['connection']

        if c == connection:
            del requests[index]
            c.close()
            break


def delete_request_connection(url):
    for index, request_data in enumerate(requests):
        request = request_data['request']
        connection = request_data['connection']

        if request.url == url:
            del requests[index]


def permanent_error(string_error):
    error_text = traceback.format_exc()

    with open("server_errors.txt", "w") as fh:
        fh.write("Error:{}\n{}".format(string_error, error_text))


def handle_connection_inner(c, address, parser):
    script = None
    request = None
    response = None

    time_start_s = datetime.now()

    while True:
        command = c.get_command_and_data()

        if not command and c.is_closed():
            print("No more commands. Closing")
            delete_connection(c)
            return

        diff = datetime.now() - time_start_s
        if diff.total_seconds() > max_transaction_timeout_s:
            permanent_error("Timeout - closing")
            delete_connection(c)
            return

        if not command:
            continue

        # Request handling

        if command[0] == "PageRequestObject.__init__":
            print("Received request init")

        elif command[0] == "PageRequestObject.url":
            print("Received request url")
            url = command[1].decode()
            request = webtools.PageRequestObject(url=url)

        elif command[0] == "PageRequestObject.timeout":
            timeout_s = int(command[1].decode())
            print("Set timeout:{}".format(timeout_s))
            request.timeout_s = timeout_s

        elif command[0] == "PageRequestObject.script":
            script = command[1].decode()
            print("Set script:{}".format(script))

        elif command[0] == "PageRequestObject.headers":
            print("{} is not yet supported".format(command[0]))
            request.headers = json.loads(command[1].decode())

        elif command[0] == "PageRequestObject.user_agent":
            print("{} is not yet supported".format(command[0]))
            request.user_agent = command[1].decode()

        elif command[0] == "PageRequestObject.ssl_verify":
            ssl_verify = command[1].decode() == "True"
            print("SSL verify:{}".format(ssl_verify))
            request.ssl_verify = ssl_verify

        elif command[0] == "PageRequestObject.__del__":
            print("Received request complete")

            # two clients might ask for the same URL
            # do not run browser again in that case
            should_run_script = True
            for request_data in requests:
                one = request_data["request"]

                if one.url == request.url:
                    should_run_script = False

            request_data = {}
            request_data['request'] = request
            request_data['connection'] = c
            request_data['datetime'] = datetime.now()
            requests.append(request_data)

            if should_run_script:
                data = run_script(script, request, parser)
                if data:
                    c.send(data)

            print("Processed request successfully")

        # Response handling

        elif command[0] == "PageResponseObject.__init__":
            print("Received response init")

        elif command[0] == "PageResponseObject.url":
            response = webtools.PageResponseObject(command[1].decode())
            print("Received response url")

        elif command[0] == "PageResponseObject.status_code":
            response.status_code = int(command[1].decode())
            print("Received response status_code")

        elif command[0] == "PageResponseObject.text":
            response.text = command[1].decode()
            print("Received response text")

        elif command[0] == "PageResponseObject.headers":
            response.headers = json.loads(command[1].decode())
            print("Received response headers")

        elif command[0] == "PageResponseObject.request_url":
            response.request_url = command[1].decode()
            print("Received response request_url")

        elif command[0] == "PageResponseObject.__del__":
            print("Received response complete")

            all_bytes = webtools.get_response_to_bytes(response)

            to_delete = []
            for index, request_data in enumerate(requests):
                connection = request_data["connection"]
                request = request_data["request"]

                if request.url == response.request_url:
                    print("Sending response to connection:{} bytes:{}".format(connection, len(all_bytes)))
                    connection.send(all_bytes)

            delete_request_connection(response.request_url)

            response = None
            c.close()

            print("Response handling complete")
            break

        # Other commands handling
        elif command[0] == "commands.debug":
            print("Requests:{}".format(len(requests)))
            c.send_command_string("debug.requests", str(len(requests)))

        elif command[0] == "debug.requests":
            pass

        elif comand[0] == "commands.close":
            delete_connection(c)

        else:
            permanent_error("Unknown command request:{}".format(command[0]))


def remove_stale_connections():
    to_delete = []
    for index, request_data in enumerate(requests):
        connection = request_data["connection"]
        request = request_data["request"]
        dt = request_data["datetime"]

        diff = datetime.now() - dt

        if diff.total_seconds() > 40:
            to_delete.append(connection)

    for connection in to_delete:
        permanent_error("Removed stale connection")
        delete_connection(connection)


def handle_connection(conn, address, parser):
    now = datetime.now()
    print("[{}] Handling connection from:{}. Requests len:{}".format(now, str(address), len(requests)))

    c = ipc.SocketConnection(conn)
    try:
        handle_connection_inner(c, address, parser)
    except Exception as E:
        error_text = "Exception during handling command:{}".format(str(E))
        permanent_error(error_text)

        delete_connection(c)

    c.close()

    now = datetime.now()
    print("[{}] Handling connection from:{} DONE. Requests len:{}.".format(now, str(address), len(requests)))


def server_program(parser):
    # get the hostname
    host = socket.gethostname()

    if "port" in parser.args and parser.args.port:
        port = parser.args.port
    else:
        port = ipc.DEFAULT_PORT

    server_socket = socket.socket()
    server_socket.settimeout(1.0)  # to be able to make ctrl-c on server

    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind((host, port))

        print("Listening on port {}".format(port))

        server_socket.listen(1)

        started = False

        print("Accepting new connections")

        while True:
            try:
                remove_stale_connections()

                conn, address = server_socket.accept()

                if len(requests) > 10:
                    print("Problem with remaining sockets")
                    index = 0
                    for connection in requests:
                        if index > 6:
                            break

                        del requests[connection]
                        connection.close()

                        index += 1

                client_thread = threading.Thread(
                    target=handle_connection,
                    args=(conn, address, parser),
                )
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                # print("Timeout")
                pass

    except Exception as E:
        print(str(E))
        error_text = traceback.format_exc()
        print(error_text)

    print("Closing")
    server_socket.close()


class Parser(object):
    """
    Headers can only be passed by input binary file
    """

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Script server")
        self.parser.add_argument("--port", type=int, help="Port")
        self.parser.add_argument("-o", "--output-file", help="Response binary file")

        self.args = self.parser.parse_args()

    def is_valid(self):
        return True


if __name__ == "__main__":
    p = Parser()
    p.parse()

    server_program(p)
