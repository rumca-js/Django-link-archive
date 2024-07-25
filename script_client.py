import socket
import json

from rsshistory.socketconnection import *


def client_program():
    host = socket.gethostname()
    port = 5007

    client_socket = socket.socket()
    client_socket.connect((host, port))
    c = SocketConnection(client_socket)

    c.send_command_string("timeout", "15")
    c.send_command_string("script", "poetry run python crawleebeautifulsoup.py")

    message = ""
    while message.lower().strip() != 'bye':
        message = input(" -> ")

        c.send_command_string("url", message)

        while True:
            command_data = c.get_command_list()
            if command_data:
                if command_data[0] == "url":
                    print("Received url:{}".format(command_data[1].decode()))
                if command_data[0] == "headers":
                    print("Received headers:{}".format(command_data[1].decode()))
                if command_data[0] == "status_code":
                    print("Received status_code:{}".format(command_data[1].decode()))
                if command_data[0] == "page_content":
                    print("Received page_content")
            else:
                break

        if c.closed:
            print("Closed")
            return

        print(command_data)

    c.close()


if __name__ == '__main__':
    client_program()
    # data = bytes.decode(errors="ignore")  # receive response
