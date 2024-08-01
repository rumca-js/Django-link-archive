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
from rsshistory import ipc, webtools
import subprocess
import traceback


mutex = threading.Lock()


# TODO request mapping [connection] => url
# TODO send responses using it
# request[url] -> list of connections
# 


requests = {} # connection is key


def run_script(script, request, parser):
    if script is None:
        print("Client has not set script to execute")
        return

    # run response through file, only if requested
    if 'output_file' in parser.args and parser.args.output_file:
        return run_script_with_file(script, request, parser)
    else:
        run_script_with_port(script, request, parser)


def run_script_with_port(script, request, parser):
    if script is None:
        print("Client has not set script to execute")
        return

    if 'port' in parser.args:
        script = '{} --url "{}" --port "{}" --timeout {} --ssl-verify {}'.format(script, request.url, ipc.DEFAULT_PORT, request.timeout_s, request.ssl_verify)

    print("Running {} with timeout:{}".format(script, request.timeout_s))

    try:
        p = subprocess.run(script, shell=True, timeout = request.timeout_s+3)
    except Exception as E:
        print(str(E))
        print("Could not finish command")
        return


def run_script_with_file(script, request, parser):
    if script is None:
        print("Client has not set script to execute")
        return

    output_file = Path("output.txt")

    if 'output_file' in parser.args:
        script = '{} --url "{}" --output-file "{}" --timeout {} --ssl-verify {}'.format(script, request.url, str(output_file), request.timeout_s, request.ssl_verify)

    print("Running {} with timeout:{}".format(script, request.timeout_s))

    with mutex:
        try:
            p = subprocess.run(script, shell=True, timeout = request.timeout_s+3)
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


def handle_connection_inner(conn, address, parser):

    c = ipc.SocketConnection(conn)

    script = None
    request = None
    response = None

    while True:
        command = c.get_command_and_data()

        if not command and c.closed:
            print("No more commands. Closing")
            c.close()
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
            ssl_verify = (command[1].decode() == "True")
            print("SSL verify:{}".format(ssl_verify))
            request.ssl_verify = ssl_verify

        elif command[0] == "PageRequestObject.__del__":
            print("Received request complete")

            # two clients might ask for the same URL
            # do not run browser again in that case
            should_run_script = True
            for one in requests:
                if one.url == request.url:
                    should_run_script = False

            requests[c] = request

            if should_run_script:
                data = run_script(script, request, parser)
                if data:
                    c.send(data)

            print("Processed request successfully")
            break

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
            for connection in requests:
                request = requests[connection]

                if request.url == response.request_url:
                    connection.send(all_bytes)
                    to_delete.append(connection)

            for connection in to_delete:
                print("Closing connection")
                connection.close()
                del requests[connection]

            response = None
            c.close()

            print("Response handling complete")
            break

        else:
            print("Unknown command request:{}".format(command[0]))


def handle_connection(conn, address, parser):
    print("Handling connection from: " + str(address))
    handle_connection_inner(conn, address, parser)
    conn.close()
    print("Handling connection from:{} DONE".format(str(address)))


def server_program(parser):
    # get the hostname
    host = socket.gethostname()

    if "port" in parser.args and parser.args.port:
        port = parser.args.port
    else:
        port = ipc.DEFAULT_PORT

    server_socket = socket.socket()
    server_socket.settimeout(1.0) # to be able to make ctrl-c on server

    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind((host, port))

        print("Listening on port {}".format(port))

        server_socket.listen(1)

        started = False

        print("Accepting new connections")

        while True:
            try:
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

                client_thread = threading.Thread(target=handle_connection,
                        args=(conn, address, parser),
                    )
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                #print("Timeout")
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


if __name__ == '__main__':
    p = Parser()
    p.parse()

    server_program(p)
