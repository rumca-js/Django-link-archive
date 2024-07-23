"""
This file should not include any other or django related files.
"""

import json


class PageResponseObject(object):
    STATUS_CODE_OK = 200
    STATUS_CODE_ERROR = 500
    STATUS_CODE_UNDEF = 0

    def __init__(
        self, url, contents=None, status_code=STATUS_CODE_OK, encoding=None, headers=None, binary=None
    ):
        """
        @param contents Text

        TODO this should be cleaned up. We should pass binary, and encoding
        """
        self.errors = []
        self.url = url
        self.status_code = status_code

        self.content = contents
        # decoded contents
        self.text = contents
        self.binary = binary

        # I read selenium always assume utf8 encoding

        # encoding = chardet.detect(contents)['encoding']
        # self.apparent_encoding = encoding
        # self.encoding = encoding

        if not headers:
            self.headers = {}
        else:
            self.headers = headers

        if not self.is_headers_empty():
            charset = self.get_content_type_charset()
            if charset:
                self.encoding = charset
                self.apparent_encoding = charset
            elif encoding:
                self.encoding = encoding
                self.apparent_encoding = encoding
            else:
                self.encoding = "utf-8"
                self.apparent_encoding = "utf-8"
        else:
            self.encoding = encoding
            self.apparent_encoding = encoding

    def is_headers_empty(self):
        return len(self.headers) == 0

    def get_content_type(self):
        if "Content-Type" in self.headers:
            return self.headers["Content-Type"]
        if "content-type" in self.headers:
            return self.headers["content-type"]

    def get_headers(self):
        return self.headers

    def get_last_modified(self):
        date = None
        if "Last-Modified" in self.headers:
            date = self.headers["Last-Modified"]
        if "last-modified" in self.headers:
            date = self.headers["last-modified"]

    def get_content_type_charset(self):
        content = self.get_content_type()
        if not content:
            return

        elements = content.split(";")
        for element in elements:
            wh = element.lower().find("charset")
            if wh >= 0:
                charset_elements = element.split("=")
                if len(charset_elements) > 1:
                    charset = charset_elements[1]

                    if charset.startswith('"') or charset.startswith("'"):
                        return charset[1:-1]
                    else:
                        return charset

    def is_content_html(self):
        content = self.get_content_type()
        if not content:
            return False

        if content.lower().find("html") >= 0:
            return True

    def is_content_image(self):
        content = self.get_content_type()
        if not content:
            return False

        if content.lower().find("image") >= 0:
            return True

    def is_content_rss(self):
        content = self.get_content_type()
        if not content:
            return False

        if content.lower().find("rss") >= 0:
            return True
        if content.lower().find("xml") >= 0:
            return True

    def get_content_length(self):
        if "content-length" in self.headers:
            return int(self.headers["content-length"])
        if "Content-Length" in self.headers:
            return int(self.headers["Content-Length"])

        return 100

    def is_content_type_supported(self):
        """
        You can preview on a browser headers. Ctr-shift-i on ff
        """
        content_type = self.get_content_type()
        if content_type.find("text") >= 0:
            return True
        if content_type.find("application") >= 0:
            return True
        if content_type.find("xml") >= 0:
            return True

        return False

    def get_redirect_url(self):
        if (
            self.is_this_status_redirect()
            and "Location" in self.headers
            and self.headers["Location"]
        ):
            return self.headers["Location"]

    def is_this_status_ok(self):
        if self.status_code == 0:
            return False

        return self.status_code >= 200 and self.status_code < 300

    def is_this_status_redirect(self):
        """
        HTML code 403 - some pages block you because of your user agent. This code says exactly that.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
        """
        return (
            self.status_code > 300 and self.status_code < 400
        ) or self.status_code == 403

    def is_this_status_nok(self):
        """
        This function informs that status code is so bad, that further communication does not make any sense
        """
        if self.is_this_status_redirect():
            return False

        return self.status_code < 200 or self.status_code >= 400

    def is_valid(self):
        if self.is_this_status_nok():
            return False

        return True

    def get_status_code(self):
        return self.status_code

    def get_contents(self):
        return self.content

    def get_binary(self):
        return self.binary

    def add_error(self, error_text):
        self.errors.append(error_text)

    def to_bytes(self):
        # send first known data. terminated by 0 byte
        # url | status_code | headers | contents |

        # TODO this cannot be send as json, as there are many things that can be in page contents
        b1 = self.string_to_bytes("url", self.url)
        b2 = self.string_to_bytes("status_code", str(self.status_code))

        headers = json.dumps(self.headers)

        b3 = self.string_to_bytes("headers", headers)
        b4 = self.string_to_bytes("page_content", self.content)

        b1.extend(b2)
        b1.extend(b3)
        b1.extend(b4)
        return b1

    def command_to_bytes(self, command_string, bytes):
        command_string = command_string + ":"

        total = bytearray(command_string.encode())
        total.extend(bytearray(bytes))
        total.extend(bytearray( (0).to_bytes(1, byteorder='big')))
        return total

    def string_to_bytes(self, command_string, string):
        if string is None:
            return self.command_to_bytes(command_string, "None".encode())
        else:
            return self.command_to_bytes(command_string, string.encode())

    def from_bytes(self, read_message):
        read_message = bytearray(read_message)

        index = 0
        while True:
            command, data, read_message = self.get_command_list(read_message)
            if not command:
                break

            if command == "url":
                self.url = data.decode()

            if command == "status_code":
                try:
                    self.status_code = int(data.decode())
                except Exception as E:
                    print("Error {}".format(E))

            if command == "headers":
                try:
                    self.headers = json.loads(data.decode())
                except Exception as E:
                    print("Error {}".format(E))

            if command == "page_content":
                self.content = data.decode()

    def get_command_bytes(self, read_message):
        wh = read_message.find(b'\x00')

        if wh >= 0:
            command = read_message[:wh]
            read_message = read_message[wh+1:]

            return [command, read_message]

        return [None, None]

    def get_command_list(self, read_message):
        command, remaining = self.get_command_bytes(read_message)

        if not command:
            return [None, None, None]

        wh = command.find(b'\x3A')
        if not wh:
            print("Cannot find ':' in response")
            return [None, None, None]

        else:
            command_string = command[:wh].decode()
            data = command[wh+1:]
            return [command_string, data, remaining]
