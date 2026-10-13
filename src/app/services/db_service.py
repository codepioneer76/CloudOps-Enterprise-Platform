"""Database service interface and implementations (Mock and PostgreSQL)."""

import json
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.database import (
    AuditRecordDetail,
    DatabaseBackendInfo,
)


class DatabaseError(Exception):
    """Base database exception."""
    pass


class DatabaseService(ABC):
    """Abstract interface for relational database backends."""

    @abstractmethod
    def get_backend_info(self) -> DatabaseBackendInfo:
        """Return provider and connectivity metadata."""
        pass

    @abstractmethod
    def check_health(self) -> Tuple[bool, str]:
        """Verify database connectivity and query execution."""
        pass

    @abstractmethod
    def create_record(self, event_type: str, actor: str, payload: Dict[str, Any]) -> AuditRecordDetail:
        """Insert an operational audit record."""
        pass

    @abstractmethod
    def list_records(self, limit: int = 50) -> List[AuditRecordDetail]:
        """Retrieve recent audit records."""
        pass


class MockDatabaseService(DatabaseService):
    """
    In-memory mock database for testing and offline development.
    Explicitly identifies that PostgreSQL is detached.
    """

    def __init__(self) -> None:
        self._records: List[AuditRecordDetail] = []
        self._counter: int = 1

    def get_backend_info(self) -> DatabaseBackendInfo:
        return DatabaseBackendInfo(
            provider="mock_in_memory",
            is_connected=False,
            database_name="local_mock",
            status="active_mock",
            description="In-memory database mock. PostgreSQL integration enabled when DB_BACKEND=postgres.",
        )

    def check_health(self) -> Tuple[bool, str]:
        return True, "In-memory database mock operational (PostgreSQL detached)"

    def create_record(self, event_type: str, actor: str, payload: Dict[str, Any]) -> AuditRecordDetail:
        now_iso = datetime.now(timezone.utc).isoformat()
        record = AuditRecordDetail(
            id=self._counter,
            event_type=event_type,
            actor=actor,
            payload=payload,
            created_at=now_iso,
        )
        self._counter += 1
        self._records.append(record)
        return record

    def list_records(self, limit: int = 50) -> List[AuditRecordDetail]:
        return list(reversed(self._records))[:limit]


class PostgresDatabaseService(DatabaseService):
    """
    Production-ready PostgreSQL database service using psycopg 3.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "cloudops_db",
        user: str = "cloudops_user",
        password: str = "cloudops_secure_pass_local",
        conn_url: Optional[str] = None,
    ) -> None:
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.conn_url = conn_url
        self._initialized = False

    def _get_connection_string(self) -> str:
        if self.conn_url:
            return self.conn_url
        return f"host={self.host} port={self.port} dbname={self.dbname} user={self.user} password={self.password} connect_timeout=3"

    def _get_connection(self):
        import psycopg
        return psycopg.connect(self._get_connection_string())

    def _init_tables(self) -> None:
        if self._initialized:
            return
        create_sql = """
        CREATE TABLE IF NOT EXISTS cloudops_audit_log (
            id SERIAL PRIMARY KEY,
            event_type VARCHAR(64) NOT NULL,
            actor VARCHAR(64) NOT NULL,
            payload TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(create_sql)
                conn.commit()
            self._initialized = True
        except Exception as e:
            raise DatabaseError(f"Failed to initialize PostgreSQL schema: {e}")

    def get_backend_info(self) -> DatabaseBackendInfo:
        ok, msg = self.check_health()
        return DatabaseBackendInfo(
            provider="postgresql",
            is_connected=ok,
            database_name=self.dbname,
            status="connected" if ok else "unreachable",
            description=f"PostgreSQL persistent database ({msg}).",
        )

    def check_health(self) -> Tuple[bool, str]:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    cur.fetchone()
            return True, "PostgreSQL database operational and queryable"
        except Exception as e:
            return False, f"PostgreSQL connection failed: {e}"

    def create_record(self, event_type: str, actor: str, payload: Dict[str, Any]) -> AuditRecordDetail:
        self._init_tables()
        payload_str = json.dumps(payload)
        insert_sql = """
        INSERT INTO cloudops_audit_log (event_type, actor, payload)
        VALUES (%s, %s, %s)
        RETURNING id, created_at;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(insert_sql, (event_type, actor, payload_str))
                    row = cur.fetchone()
                    conn.commit()
                    if not row:
                        raise DatabaseError("Failed to retrieve inserted row ID")
                    record_id, created_at = row[0], row[1]
                    return AuditRecordDetail(
                        id=record_id,
                        event_type=event_type,
                        actor=actor,
                        payload=payload,
                        created_at=created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
                    )
        except Exception as e:
            raise DatabaseError(f"Database insert error: {e}")

    def list_records(self, limit: int = 50) -> List[AuditRecordDetail]:
        self._init_tables()
        select_sql = """
        SELECT id, event_type, actor, payload, created_at
        FROM cloudops_audit_log
        ORDER BY id DESC
        LIMIT %s;
        """
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(select_sql, (limit,))
                    rows = cur.fetchall()
            results = []
            for row in rows:
                rec_id, evt_type, rec_actor, p_text, created_at = row
                try:
                    payload_data = json.loads(p_text)
                except Exception:
                    payload_data = {"raw": p_text}
                results.append(
                    AuditRecordDetail(
                        id=rec_id,
                        event_type=evt_type,
                        actor=rec_actor,
                        payload=payload_data,
                        created_at=created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
                    )
                )
            return results
        except Exception as e:
            raise DatabaseError(f"Database query error: {e}")


_db_instance: Optional[DatabaseService] = None


def get_db_service() -> DatabaseService:
    """Singleton getter for database service dependency injection."""
    global _db_instance
    if _db_instance is None:
        from app.config import get_settings
        settings = get_settings()
        if settings.db_backend == "postgres":
            _db_instance = PostgresDatabaseService(
                host=settings.db_host,
                port=settings.db_port,
                dbname=settings.db_name,
                user=settings.db_user,
                password=settings.db_password,
                conn_url=settings.db_url,
            )
        else:
            _db_instance = MockDatabaseService()
    return _db_instance
