from datetime import timedelta
from io import BytesIO

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

settings = get_settings()
_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_use_ssl,
        )
    return _client


def get_presigned_put_url(bucket: str, object_key: str, expires: int = 3600) -> str:
    client = get_minio_client()
    return client.presigned_put_object(bucket, object_key, expires=timedelta(seconds=expires))


def get_presigned_get_url(bucket: str, object_key: str, expires: int = 3600) -> str:
    client = get_minio_client()
    return client.presigned_get_object(bucket, object_key, expires=timedelta(seconds=expires))


def put_object_bytes(bucket: str, object_key: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    client = get_minio_client()
    client.put_object(bucket, object_key, BytesIO(data), length=len(data), content_type=content_type)


def get_object_bytes(bucket: str, object_key: str) -> bytes:
    client = get_minio_client()
    try:
        response = client.get_object(bucket, object_key)
        return response.read()
    finally:
        if "response" in locals():
            response.close()
            response.release_conn()


def build_raw_upload_key(kind: str, job_id: str, filename: str, year: int, month: int) -> str:
    return f"{kind}/{year:04d}/{month:02d}/{job_id}/{filename}"


def build_export_key(user_id: str, export_id: str, year: int, month: int) -> str:
    return f"{user_id}/{year:04d}/{month:02d}/{export_id}/report.pdf"


def build_parsed_summary_key(upload_job_id: str) -> str:
    return f"{upload_job_id}/summary.json"


def build_parsed_scan_chains_key(upload_job_id: str) -> str:
    return f"{upload_job_id}/scan-chains.json"


def build_parsed_metadata_key(upload_job_id: str) -> str:
    return f"{upload_job_id}/metadata.json"


def build_parsed_waveform_key(upload_job_id: str) -> str:
    return f"{upload_job_id}/waveforms.json"


def build_unified_dataset_key(upload_job_id: str) -> str:
    return f"{upload_job_id}/unified_dataset.json"


def build_pattern_artifact_key(upload_job_id: str) -> str:
    return f"{upload_job_id}/pattern_report.json"


def build_failure_artifact_key(upload_job_id: str) -> str:
    return f"{upload_job_id}/failure_report.json"


def build_diagnosis_artifact_key(upload_job_id: str) -> str:
    return f"{upload_job_id}/diagnosis_report.json"


def build_scan_chain_result_key(upload_job_id: str) -> str:
    return f"{upload_job_id}/scan_chain_result.json"


def delete_object(bucket: str, object_key: str) -> None:
    client = get_minio_client()
    client.remove_object(bucket, object_key)
