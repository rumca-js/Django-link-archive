import socket
import json

from rsshistory import ipc


def client_program():
    host = socket.gethostname()
    port = 5007

    client_socket = socket.socket()
    client_socket.connect((host, port))
    c = ipc.SocketConnection(client_socket)

    c.send_command_string("PageRequestObject.timeout", "15")
    c.send_command_string("PageRequestObject.script", "poetry run python crawleebeautifulsoup.py")

    message = ""
    while message.lower().strip() != 'bye':
        message = input(" -> ")

        c.send_command_string("PageRequestObject.url", message)

        while True:
            command_data = c.get_command_and_data()
            if command_data:
                if command_data[0] == "PageResponseObject.__init__":
                    pass
                elif command_data[0] == "PageResponseObject.url":
                    print("Received url:{}".format(command_data[1].decode()))
                elif command_data[0] == "PageResponseObject.headers":
                    print("Received headers:{}".format(command_data[1].decode()))
                elif command_data[0] == "PageResponseObject.status_code":
                    print("Received status_code:{}".format(command_data[1].decode()))
                elif command_data[0] == "PageResponseObject.text":
                    print("Received page_content")
                elif command_data[0] == "PageResponseObject.__del__":
                    pass
                else:
                    print("Unknown command")

            else:
                print("No data")
                break

        if c.closed:
            print("Closed")
            return

    c.close()


if __name__ == '__main__':
    client_program()
    # data = bytes.decode(errors="ignore")  # receive response
