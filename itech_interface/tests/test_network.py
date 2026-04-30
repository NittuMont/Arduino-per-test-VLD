import pytest
from itech_interface.network import ITechConnection
import socket

class DummySocket:
    def __init__(self):
        self.data = b""
        self._timeout = None
    def settimeout(self, t):
        self._timeout = t
    def gettimeout(self):
        return self._timeout
    def setsockopt(self, *args):
        pass
    def sendall(self, data):
        self.data += data
    def recv(self, bufsize, flags=0):
        if flags & socket.MSG_PEEK:
            raise BlockingIOError
        return b"OK\n"
    def close(self):
        pass

@pytest.fixture(autouse=True)
def patch_socket(monkeypatch):
    def create_connection(addr, timeout):
        return DummySocket()
    monkeypatch.setattr(socket, "create_connection", create_connection)


def test_send_and_query():
    conn = ITechConnection("127.0.0.1")
    conn.connect()
    conn.send("TEST")
    assert b"TEST" in conn._sock.data
    resp = conn.query("MEAS:VOLT?")
    assert resp == "OK"
    conn.disconnect()
