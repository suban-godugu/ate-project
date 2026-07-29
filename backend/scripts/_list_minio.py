from app.storage.minio_client import get_client
from app.core.config import get_settings
s = get_settings()
c = get_client()
# list recent log objects
objs = list(c.list_objects(s.minio_bucket_raw, prefix="log/", recursive=True))
print("raw bucket", s.minio_bucket_raw, "count", len(objs))
for o in objs[-15:]:
    print(o.object_name, o.size)
