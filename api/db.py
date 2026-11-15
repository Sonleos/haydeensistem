from __future__ import annotations

import queue
import threading
from contextlib import contextmanager
from typing import Any, Iterator

import pymysql
from pymysql.cursors import DictCursor

from config import settings


class MySQLPool:
    """Pool de conexiones mínimo y thread-safe sobre PyMySQL."""

    def __init__(self, size: int = 5, timeout: int = 10) -> None:
        self._size = max(1, size)
        self._timeout = max(1, timeout)
        self._pool: queue.LifoQueue = queue.LifoQueue(maxsize=self._size)
        self._created = 0
        self._lock = threading.Lock()

    def _connect(self):
        return pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
            connect_timeout=5,
            read_timeout=30,
            write_timeout=30,
        )

    def acquire(self):
        while True:
            try:
                connection = self._pool.get_nowait()
            except queue.Empty:
                with self._lock:
                    can_create = self._created < self._size
                    if can_create:
                        self._created += 1

                if can_create:
                    try:
                        return self._connect()
                    except Exception:
                        with self._lock:
                            self._created = max(0, self._created - 1)
                        raise

                try:
                    connection = self._pool.get(timeout=self._timeout)
                except queue.Empty as exc:
                    raise RuntimeError(
                        "No hay conexiones MySQL disponibles en el pool."
                    ) from exc

            try:
                connection.ping(reconnect=True)
                return connection
            except Exception:
                self._discard(connection)

    def release(self, connection) -> None:
        if connection is None:
            return

        try:
            connection.rollback()
        except Exception:
            self._discard(connection)
            return

        try:
            self._pool.put_nowait(connection)
        except queue.Full:
            self._discard(connection)

    def _discard(self, connection) -> None:
        try:
            connection.close()
        except Exception:
            pass

        with self._lock:
            self._created = max(0, self._created - 1)

    @contextmanager
    def cursor(self, commit: bool = False) -> Iterator[DictCursor]:
        connection = self.acquire()
        try:
            with connection.cursor() as cursor:
                yield cursor
            if commit:
                connection.commit()
            else:
                connection.rollback()
        except Exception:
            try:
                connection.rollback()
            except Exception:
                pass
            raise
        finally:
            self.release(connection)

    def fetch_one(self, sql: str, params: tuple | None = None) -> dict[str, Any] | None:
        with self.cursor() as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchone()

    def fetch_all(self, sql: str, params: tuple | None = None) -> list[dict[str, Any]]:
        with self.cursor() as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return list(cursor.fetchall())

    def execute(self, sql: str, params: tuple | None = None) -> tuple[int, int]:
        with self.cursor(commit=True) as cursor:
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.lastrowid, cursor.rowcount

    def ping(self) -> dict[str, Any]:
        with self.cursor() as cursor:
            cursor.execute("SELECT 1 AS ok")
            return cursor.fetchone()

    @property
    def status(self) -> dict[str, int]:
        with self._lock:
            return {
                "tamano": self._size,
                "creadas": self._created,
                "libres": self._pool.qsize(),
            }

    def close_all(self) -> None:
        with self._lock:
            while True:
                try:
                    connection = self._pool.get_nowait()
                except queue.Empty:
                    break
                try:
                    connection.close()
                except Exception:
                    pass
                self._created = max(0, self._created - 1)


db = MySQLPool(size=settings.DB_POOL_SIZE, timeout=settings.DB_POOL_TIMEOUT)
