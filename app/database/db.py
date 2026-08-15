import socket
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

if _host:

    for _info in socket.getaddrinfo(
        _host,
        _port,
        socket.AF_INET,
        socket.SOCK_STREAM,
    ):

        _connect_args["hostaddr"] = _info[4][0]

        break

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