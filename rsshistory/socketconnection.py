import json


class SocketConnection(object):
    def __init__(self, conn):
        self.conn = conn
        self.read_message = None
        self.closed = False

    def send(self, bytes):
        self.conn.send(bytes)

    def send_command_bytes(self, command_string, bytes):
        command_string = command_string + ":"

        self.conn.send(command_string.encode())
        self.conn.send(bytes)
        self.conn.send( (0).to_bytes(1, byteorder='big'))

    def send_command_string(self, command_string, string):
        self.send_command_bytes(command_string, string.encode())

    def send_results(self, results):
        # send first known data. terminated by 0 byte
        # url | status_code | headers | contents |

        # TODO this cannot be send as json, as there are many things that can be in page contents
        self.send_command_string("url", results["url"])
        self.send_command_string("status_code", str(results["status_code"]))

        headers = json.dumps(results["headers"])

        self.send_command_string("headers", headers)

        self.send_command_string("page_content", results['page_content'])

    def get_command_bytes(self):
        while True:
            try:
                bytes = self.conn.recv(1024)
            except Exception as E:
                self.closed = True
                return

            if not bytes:
                self.closed = True
                return

            if self.read_message is None:
                self.read_message = bytearray(bytes)
            else:
                self.read_message.extend(bytearray(bytes))

            wh = self.read_message.find(b'\x00')

            if wh >= 0:
                command = self.read_message[:wh]
                self.read_message = self.read_message[wh+1:]

                return command

    def get_command_list(self):
        command = self.get_command_bytes()

        if not command:
            return

        wh = command.find(b'\x3A')
        if not wh:
            print("Cannot find ':' in response")
            return

        else:
            command_string = command[:wh].decode()
            data = command[wh+1:]
            return [command_string, data]

    def close(self):
        self.conn.close()
