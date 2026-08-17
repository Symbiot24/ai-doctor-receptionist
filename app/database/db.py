import socket
import time
from urllib.parse import urlsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

from app.core.config import DATABASE_URL

_connect_args = {}

# Neon pooler hosts resolve to IPv6 addresses first; networks without an
# IPv6 route stall on the TCP connect instead of falling back to IPv4.
# Resolve an IPv4 address once and force libpq to connect to it directly
# (the hostname is retained in the URL for display/certificate purposes).
_parsed = urlsplit(DATABASE_URL)

_host = _parsed.hostname

_port = _parsed.port or 5432


def _resolve_ipv4(host, port):

    # Transient DNS failures must not take the whole app down at import
    # time. Retry briefly, then give up and let libpq resolve at connect
    # time (which reports a proper connection error instead of crashing).
    for attempt in range(3):

        try:

            infos = socket.getaddrinfo(
                host,
                port,
                socket.AF_INET,
                socket.SOCK_STREAM,
            )

            if infos:

                return infos[0][4][0]

        except socket.gaierror:

            if attempt < 2:

                time.sleep(1)

    return None


if _host:

    ipv4 = _resolve_ipv4(_host, _port)

    if ipv4:

        _connect_args["hostaddr"] = ipv4

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()