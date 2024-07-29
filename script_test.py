
from rsshistory import ipc

c = ipc.SocketConnection("whatever")

class Test(object):
    def __init__(self):
        self.test_string_to_command()
        self.test_object_to_command()

    def assertEqual(self, one, two):
        if one == two:
            print("OK")
        else:
            print("ERROR. One:{} Two:{}".format(one, two))

    def assertTrue(self, one):
        if one:
            print("OK")
        else:
            print("ERROR")

    def test_string_to_command(self):
        google_bytes = ipc.string_to_command("url", "https://google.com")
        timeout_bytes = ipc.string_to_command("timeout", "20")

        total_bytes = bytearray()
        total_bytes.extend(google_bytes)
        total_bytes.extend(timeout_bytes)

        commands = ipc.commands_from_bytes(total_bytes)
        self.assertEqual(len(commands), 2)

        self.assertEqual(commands[0][0], "url")
        self.assertEqual(commands[0][1].decode(), "https://google.com")

        self.assertEqual(commands[1][0], "timeout")
        self.assertEqual(commands[1][1].decode(), "20")

    def test_object_to_command(self):
        object_bytes = ipc.object_to_command("test", self)

        self.assertTrue(len(object_bytes) > 0)

Test()
