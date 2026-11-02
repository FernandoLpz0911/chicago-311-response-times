import psycopg


def connect(url: str) -> psycopg.Connection:
    """Open an autocommit connection; callers group writes with conn.transaction()."""
    return psycopg.connect(url, autocommit=True)
