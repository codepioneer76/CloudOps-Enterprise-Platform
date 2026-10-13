"""Storage service interface and implementations (In-Memory and S3/MinIO)."""

import hashlib
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.schemas.storage import (
    BucketInfo,
    StorageBackendInfo,
    StorageObjectDetail,
    StorageObjectMeta,
)


class StorageError(Exception):
    """Base storage exception."""
    pass


class ObjectNotFoundError(StorageError):
    """Raised when requested object does not exist."""
    pass


class StorageService(ABC):
    """Abstract interface for CloudOps object storage backends."""

    @abstractmethod
    def get_backend_info(self) -> StorageBackendInfo:
        """Return provider and connectivity metadata."""
        pass

    @abstractmethod
    def list_buckets(self) -> List[BucketInfo]:
        """List available storage buckets."""
        pass

    @abstractmethod
    def put_object(
        self,
        bucket: str,
        key: str,
        content_text: str,
        content_type: str = "text/plain",
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageObjectMeta:
        """Store or overwrite an object."""
        pass

    @abstractmethod
    def get_object(self, bucket: str, key: str) -> StorageObjectDetail:
        """Retrieve an object's content and metadata."""
        pass

    @abstractmethod
    def list_objects(self, bucket: str) -> List[StorageObjectMeta]:
        """List all objects in a bucket."""
        pass

    @abstractmethod
    def delete_object(self, bucket: str, key: str) -> bool:
        """Delete an object from storage."""
        pass

    @abstractmethod
    def check_health(self) -> Tuple[bool, str]:
        """Verify storage subsystem health status."""
        pass


class InMemoryStorageService(StorageService):
    """
    Local in-memory storage implementation for development and testing.
    Explicitly informs callers that AWS S3 is not connected yet.
    """

    def __init__(self, default_bucket: str = "cloudops-artifacts") -> None:
        self.default_bucket = default_bucket
        # Map: bucket -> {key: StorageObjectDetail}
        self._store: Dict[str, Dict[str, StorageObjectDetail]] = {
            self.default_bucket: {}
        }

    def get_backend_info(self) -> StorageBackendInfo:
        return StorageBackendInfo(
            provider="in_memory_local_mock",
            is_cloud_connected=False,
            status="active_local",
            description="Local in-memory storage provider (AWS S3 integration will be enabled in Module 2/5).",
        )

    def list_buckets(self) -> List[BucketInfo]:
        now_iso = datetime.now(timezone.utc).isoformat()
        buckets = []
        for name, items in self._store.items():
            buckets.append(
                BucketInfo(
                    name=name,
                    provider="in_memory_local_mock",
                    created_at=now_iso,
                    object_count=len(items),
                    lifecycle_policy="None (local in-memory)",
                )
            )
        return buckets

    def put_object(
        self,
        bucket: str,
        key: str,
        content_text: str,
        content_type: str = "text/plain",
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageObjectMeta:
        target_bucket = bucket or self.default_bucket
        if target_bucket not in self._store:
            self._store[target_bucket] = {}

        now_iso = datetime.now(timezone.utc).isoformat()
        raw_bytes = content_text.encode("utf-8")
        etag = hashlib.md5(raw_bytes).hexdigest()

        obj_detail = StorageObjectDetail(
            key=key,
            bucket=target_bucket,
            size_bytes=len(raw_bytes),
            content_type=content_type,
            created_at=now_iso,
            etag=etag,
            metadata=metadata or {},
            content_text=content_text,
        )

        self._store[target_bucket][key] = obj_detail
        return StorageObjectMeta(
            key=obj_detail.key,
            bucket=obj_detail.bucket,
            size_bytes=obj_detail.size_bytes,
            content_type=obj_detail.content_type,
            created_at=obj_detail.created_at,
            etag=obj_detail.etag,
            metadata=obj_detail.metadata,
        )

    def get_object(self, bucket: str, key: str) -> StorageObjectDetail:
        target_bucket = bucket or self.default_bucket
        bucket_dict = self._store.get(target_bucket)
        if bucket_dict is None or key not in bucket_dict:
            raise ObjectNotFoundError(f"Object '{key}' not found in bucket '{target_bucket}'")
        return bucket_dict[key]

    def list_objects(self, bucket: str) -> List[StorageObjectMeta]:
        target_bucket = bucket or self.default_bucket
        bucket_dict = self._store.get(target_bucket, {})
        return [
            StorageObjectMeta(
                key=item.key,
                bucket=item.bucket,
                size_bytes=item.size_bytes,
                content_type=item.content_type,
                created_at=item.created_at,
                etag=item.etag,
                metadata=item.metadata,
            )
            for item in bucket_dict.values()
        ]

    def delete_object(self, bucket: str, key: str) -> bool:
        target_bucket = bucket or self.default_bucket
        bucket_dict = self._store.get(target_bucket)
        if bucket_dict is None or key not in bucket_dict:
            raise ObjectNotFoundError(f"Object '{key}' not found in bucket '{target_bucket}'")
        del bucket_dict[key]
        return True

    def check_health(self) -> Tuple[bool, str]:
        return True, "In-memory storage provider operational (AWS S3 detached)"


class S3StorageService(StorageService):
    """
    S3-compatible object storage provider (MinIO / AWS S3) via boto3.
    """

    def __init__(
        self,
        endpoint_url: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        default_bucket: str = "cloudops-artifacts",
    ) -> None:
        import boto3
        from botocore.config import Config

        self.endpoint_url = endpoint_url
        self.default_bucket = default_bucket
        self.region_name = region_name

        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=region_name,
            config=Config(signature_version="s3v4", connect_timeout=3, retries={"max_attempts": 2}),
        )
        self._ensure_bucket(self.default_bucket)

    def _ensure_bucket(self, bucket: str) -> None:
        try:
            self.client.head_bucket(Bucket=bucket)
        except Exception:
            try:
                self.client.create_bucket(Bucket=bucket)
            except Exception:
                pass

    def get_backend_info(self) -> StorageBackendInfo:
        ok, msg = self.check_health()
        return StorageBackendInfo(
            provider="s3_minio_compatible",
            is_cloud_connected=ok,
            status="connected" if ok else "unreachable",
            description=f"S3/MinIO compatible object storage provider ({msg}).",
        )

    def list_buckets(self) -> List[BucketInfo]:
        try:
            resp = self.client.list_buckets()
            now_iso = datetime.now(timezone.utc).isoformat()
            results = []
            for b in resp.get("Buckets", []):
                b_name = b["Name"]
                results.append(
                    BucketInfo(
                        name=b_name,
                        provider="s3_minio_compatible",
                        created_at=b["CreationDate"].isoformat() if hasattr(b.get("CreationDate"), "isoformat") else now_iso,
                        object_count=len(self.list_objects(bucket=b_name)),
                        lifecycle_policy="Standard-IA / MinIO lifecycle",
                    )
                )
            return results
        except Exception as e:
            raise StorageError(f"Error listing S3 buckets: {e}")

    def put_object(
        self,
        bucket: str,
        key: str,
        content_text: str,
        content_type: str = "text/plain",
        metadata: Optional[Dict[str, str]] = None,
    ) -> StorageObjectMeta:
        target_bucket = bucket or self.default_bucket
        self._ensure_bucket(target_bucket)
        raw_bytes = content_text.encode("utf-8")
        clean_meta = metadata or {}
        try:
            resp = self.client.put_object(
                Bucket=target_bucket,
                Key=key,
                Body=raw_bytes,
                ContentType=content_type,
                Metadata=clean_meta,
            )
            etag = resp.get("ETag", "").strip('"')
            now_iso = datetime.now(timezone.utc).isoformat()
            return StorageObjectMeta(
                key=key,
                bucket=target_bucket,
                size_bytes=len(raw_bytes),
                content_type=content_type,
                created_at=now_iso,
                etag=etag,
                metadata=clean_meta,
            )
        except Exception as e:
            raise StorageError(f"Error putting object to S3: {e}")

    def get_object(self, bucket: str, key: str) -> StorageObjectDetail:
        target_bucket = bucket or self.default_bucket
        try:
            resp = self.client.get_object(Bucket=target_bucket, Key=key)
            content_bytes = resp["Body"].read()
            content_text = content_bytes.decode("utf-8")
            etag = resp.get("ETag", "").strip('"')
            content_type = resp.get("ContentType", "text/plain")
            last_modified = resp.get("LastModified")
            created_at = last_modified.isoformat() if hasattr(last_modified, "isoformat") else datetime.now(timezone.utc).isoformat()
            meta = resp.get("Metadata", {})
            return StorageObjectDetail(
                key=key,
                bucket=target_bucket,
                size_bytes=len(content_bytes),
                content_type=content_type,
                created_at=created_at,
                etag=etag,
                metadata=meta,
                content_text=content_text,
            )
        except self.client.exceptions.NoSuchKey:
            raise ObjectNotFoundError(f"Object '{key}' not found in bucket '{target_bucket}'")
        except Exception as e:
            if "NoSuchKey" in str(e) or "404" in str(e):
                raise ObjectNotFoundError(f"Object '{key}' not found in bucket '{target_bucket}'")
            raise StorageError(f"Error getting object from S3: {e}")

    def list_objects(self, bucket: str) -> List[StorageObjectMeta]:
        target_bucket = bucket or self.default_bucket
        try:
            resp = self.client.list_objects_v2(Bucket=target_bucket)
            items = []
            for obj in resp.get("Contents", []):
                etag = obj.get("ETag", "").strip('"')
                last_mod = obj.get("LastModified")
                created_at = last_mod.isoformat() if hasattr(last_mod, "isoformat") else datetime.now(timezone.utc).isoformat()
                items.append(
                    StorageObjectMeta(
                        key=obj["Key"],
                        bucket=target_bucket,
                        size_bytes=obj["Size"],
                        content_type="text/plain",
                        created_at=created_at,
                        etag=etag,
                        metadata={},
                    )
                )
            return items
        except Exception as e:
            raise StorageError(f"Error listing S3 objects: {e}")

    def delete_object(self, bucket: str, key: str) -> bool:
        target_bucket = bucket or self.default_bucket
        # Verify existence first so 404 is properly returned
        self.get_object(bucket=target_bucket, key=key)
        try:
            self.client.delete_object(Bucket=target_bucket, Key=key)
            return True
        except Exception as e:
            raise StorageError(f"Error deleting object from S3: {e}")

    def check_health(self) -> Tuple[bool, str]:
        try:
            self.client.list_buckets()
            return True, "S3/MinIO object storage operational"
        except Exception as e:
            return False, f"S3 connection failed: {e}"


_storage_instance: Optional[StorageService] = None


def get_storage_service(default_bucket: str = "cloudops-artifacts") -> StorageService:
    """Singleton getter for storage service dependency injection."""
    global _storage_instance
    if _storage_instance is None:
        from app.config import get_settings
        settings = get_settings()
        if settings.storage_backend in ("s3", "minio"):
            _storage_instance = S3StorageService(
                endpoint_url=settings.s3_endpoint_url,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                region_name=settings.aws_region,
                default_bucket=settings.storage_bucket_default or default_bucket,
            )
        else:
            _storage_instance = InMemoryStorageService(default_bucket=default_bucket)
    return _storage_instance
