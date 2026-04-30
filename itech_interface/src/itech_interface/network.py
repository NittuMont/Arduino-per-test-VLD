"""Networking layer to communicate with the ITECH power supply."""

import socket
import logging
import time
from typing import Optional

LOGGER = logging.getLogger(__name__)

# Number of automatic reconnection attempts before giving up
_MAX_RECONNECT_ATTEMPTS = 3
_RECONNECT_DELAY_S = 0.2  # seconds between attempts


class ITechConnection:
    """TCP client for SCPI commands to the ITECH device.

    Includes automatic reconnection: if a send/query fails because the
    underlying socket is broken (e.g. after PC hibernation), the class
    transparently attempts to re-establish the connection before
    re-raising the error.
    """

    def __init__(self, host: str, port: int = 5025, timeout: float = 0.5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._sock: Optional[socket.socket] = None

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    @property
    def is_connected(self) -> bool:
        """Return *True* if the socket appears to be open."""
        return self._sock is not None

    def connect(self) -> None:
        """Open (or re-open) the TCP connection."""
        # Close any stale socket first
        self._close_socket()
        LOGGER.debug("Connecting to %s:%s", self.host, self.port)
        self._sock = socket.create_connection(
            (self.host, self.port), self.timeout
        )
        self._sock.settimeout(self.timeout)
        # Enable TCP keep-alive so the OS detects dead peers sooner
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

    def disconnect(self) -> None:
        LOGGER.debug("Disconnecting from device")
        self._close_socket()

    def reconnect(self) -> None:
        """Try to re-establish the connection up to *_MAX_RECONNECT_ATTEMPTS* times."""
        LOGGER.warning("Attempting reconnection to %s:%s", self.host, self.port)
        last_err: Optional[Exception] = None
        for attempt in range(1, _MAX_RECONNECT_ATTEMPTS + 1):
            try:
                self.connect()
                LOGGER.info("Reconnected on attempt %d", attempt)
                return
            except Exception as exc:
                last_err = exc
                LOGGER.warning(
                    "Reconnect attempt %d/%d failed: %s",
                    attempt, _MAX_RECONNECT_ATTEMPTS, exc,
                )
                time.sleep(_RECONNECT_DELAY_S)
        raise ConnectionError(
            f"Impossibile riconnettersi dopo {_MAX_RECONNECT_ATTEMPTS} tentativi"
        ) from last_err

    def ping(self) -> bool:
        """Send a lightweight SCPI identity query to check liveness.

        Returns *True* if the device responds, *False* otherwise.
        """
        try:
            resp = self.query("*IDN?")
            return bool(resp)
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Data exchange (with auto-reconnect)
    # ------------------------------------------------------------------

    def send(self, command: str) -> None:
        self._ensure_connected()
        try:
            LOGGER.debug("Sending command: %s", command)
            self._sock.sendall(command.encode("ascii") + b"\n")
        except (OSError, socket.error, BrokenPipeError) as exc:
            LOGGER.warning("Send failed (%s), attempting reconnect…", exc)
            self.reconnect()
            # Retry once after reconnection
            LOGGER.debug("Retrying command: %s", command)
            self._sock.sendall(command.encode("ascii") + b"\n")

    def query(self, command: str) -> str:
        self._ensure_connected()
        try:
            LOGGER.debug("Sending query: %s", command)
            self._sock.sendall(command.encode("ascii") + b"\n")
            data = self._sock.recv(4096)
        except (OSError, socket.error, BrokenPipeError) as exc:
            LOGGER.warning("Query failed (%s), attempting reconnect…", exc)
            self.reconnect()
            # Retry once after reconnection
            LOGGER.debug("Retrying query: %s", command)
            self._sock.sendall(command.encode("ascii") + b"\n")
            data = self._sock.recv(4096)
        result = data.decode("ascii").strip()
        LOGGER.debug("Received: %s", result)
        return result

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_connected(self) -> None:
        if not self._sock:
            LOGGER.info("Socket is None — reconnecting automatically")
            self.reconnect()
            return
        # Fast check: detect dead sockets left over after standby/hibernate.
        # Temporarily set a very short timeout, peek at the socket, then
        # restore the original timeout.  A dead peer returns b'' (EOF) or
        # raises immediately — no 5-second wait.
        try:
            orig_timeout = self._sock.gettimeout()
            self._sock.settimeout(0.05)  # 50 ms — just enough to detect EOF
            try:
                data = self._sock.recv(1, socket.MSG_PEEK)
                if not data:
                    raise OSError("Peer closed connection (EOF)")
            except BlockingIOError:
                pass  # no data available — socket is alive
            except socket.timeout:
                pass  # no data available — socket is alive
            finally:
                self._sock.settimeout(orig_timeout)
        except (OSError, socket.error) as exc:
            LOGGER.warning("Dead socket detected (%s) — reconnecting", exc)
            self._close_socket()
            self.reconnect()

    def _close_socket(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
