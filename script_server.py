"""
We could use 
https://realpython.com/python-sockets/   "Sending an Application Message"

TODO - solve race condition, where 2 clients at the same time might perform a query, and write an
output file.

use mutex for running. cleanup files after reading.
this will slow down our operations, but who cares?
"""

import socket
import threading
from pathlib import Path
from rsshistory.socketconnection import *
import subprocess


mutex = threading.Lock()


def handle_connection_inner(conn, address):
    c = SocketConnection(conn)

    timeout = 10
    script = None

    while True:
        command = c.get_command_list()

        if not command:
            c.close()
            return

        if command[0] == "url":
            print("Trying to obtain URL contents")

            url = command[1].decode()

            if script is None:
                print("Client has not set script to execute")
                return

            output_file = Path("output.txt")

            # TODO pass through socket
            script = '{} --url "{}" -o "{}" --timeout {}'.format(script, url, str(output_file), timeout)

            print("Running {} with timeout:{}".format(script, timeout))
            with mutex:
                try:
                    p = subprocess.run(script, shell=True, timeout = timeout+3)
                except Exception as E:
                    print(str(E))
                    print("Could not finish command")
                    c.close()
                    return

            if output_file.exists():
                with open(str(output_file), "rb") as fh:
                    all_bytes = fh.read()
                    c.send(all_bytes)

                output_file.unlink()

            c.close()

            print("Sent everything successfully")

        elif command[0] == "timeout":
            timeout = int(command[1].decode())
            print("Applying timeout:{}".format(timeout))

        elif command[0] == "script":
            script = command[1].decode()
            print("Applying script:{}".format(script))

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
    port = 5007

    server_socket = socket.socket()

    try:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_socket.bind((host, port))

        print("Listening on port {}".format(port))

        server_socket.listen()

        started = False

        while True:
            conn, address = server_socket.accept()

            client_thread = threading.Thread(target=handle_connection,
                    args=(conn,address),
                )
            client_thread.daemon = True
            client_thread.start()
    except Exception as E:
        print(str(E))

    server_socket.close()


if __name__ == '__main__':
    server_program()
