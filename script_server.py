"""
This is server that accepts scraping commands, scrapes web page, and produces results.

We communicate through binary interface:
 - PageRequestObject
 - PageResponseObject

Since scraping can be done through celery, and web server, it is convinient to limit the amount
of running browsers. We require only 1 browser at a time.

We are not nasty, we are not in a hurry. We are good scrapers.
"""

import socket
import threading
from pathlib import Path
from rsshistory import ipc, webtools
import subprocess
import traceback


mutex = threading.Lock()


def handle_connection_inner(conn, address):
    def run_script(script, request):
        if script is None:
            print("Client has not set script to execute")
            return

        output_file = Path("output.txt")

        # TODO pass through socket
        script = '{} --url "{}" -o "{}" --timeout {} --ssl-verify {}'.format(script, request.url, str(output_file), request.timeout_s, request.ssl_verify)

        print("Running {} with timeout:{}".format(script, request.timeout_s))
        with mutex:
            try:
                p = subprocess.run(script, shell=True, timeout = request.timeout_s+3)
            except Exception as E:
                print(str(E))
                print("Could not finish command")
                return

        all_bytes = None

        if output_file.exists():
            print("File exists")
            with open(str(output_file), "rb") as fh:
                all_bytes = fh.read()

            output_file.unlink()
        else:
            print("Error! File does not exist!")

        return all_bytes

    c = ipc.SocketConnection(conn)

    timeout_s = 10
    script = None
    ssl_verify = True

    while True:
        command = c.get_command_and_data()

        if not command:
            print("No more commands. Closing")
            c.close()
            return

        if command[0] == "PageRequestObject.__init__":
            pass

        elif command[0] == "PageRequestObject.url":

            url = command[1].decode()

            request = webtools.PageRequestObject(url=url, timeout_s = timeout_s, ssl_verify=ssl_verify)
            data = run_script(script, request)
            if data:
                c.send(data)

            c.close()

            print("Sent everything successfully")

        elif command[0] == "PageRequestObject.timeout":
            timeout_s = int(command[1].decode())
            print("Set timeout:{}".format(timeout_s))

        elif command[0] == "PageRequestObject.script":
            script = command[1].decode()
            print("Set script:{}".format(script))

        elif command[0] == "PageRequestObject.headers":
            print("{} is not yet supported".format(command[0]))

        elif command[0] == "PageRequestObject.user_agent":
            print("{} is not yet supported".format(command[0]))

        elif command[0] == "PageRequestObject.ssl_verify":
            ssl_verify = (command[1].decode() == "True")
            print("SSL verify:{}".format(ssl_verify))

        elif command[0] == "PageRequestObject.__del__":
            pass

        else:
            print("Unknown command request:{}".format(command[0]))


def handle_connection(conn, address):
    print("Handling connection from: " + str(address))
    handle_connection_inner(conn, address)
    conn.close()
    print("Handling connection from:{} DONE".format(str(address)))


def server_program():
    # get the hostname
    host = socket.gethostname()
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

                client_thread = threading.Thread(target=handle_connection,
                        args=(conn,address),
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


if __name__ == '__main__':
    server_program()
