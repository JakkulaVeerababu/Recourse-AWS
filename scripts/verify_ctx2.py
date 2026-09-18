import boto3

INCIDENT_ID = "INC-01M2QG9R3RPKHDRC2207M56EBC"
CONTEXT_ID = "CTX-B171271D00A34F3E9EEB4CE7F8"
dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("recourse-development-incidents")
r = table.get_item(Key={"PK": "INCIDENT#" + INCIDENT_ID, "SK": "CONTEXT#" + CONTEXT_ID})
ctx = r.get("Item", {})

print("=== STEP 8: Context Item ===")
print("contextId:", ctx.get("contextId"))

# metrics
metrics = ctx.get("metrics", {})
for metric, points in metrics.items():
    count = len(points) if isinstance(points, list) else str(points)
    print(metric + " points:", count)

# logs
logs = ctx.get("logs", [])
print("log count:", len(logs))
meta = ctx.get("metadata", {})
print("logsTruncated:", meta.get("logsTruncated", False))

# configuration/environment
config = ctx.get("configuration", {})
env = config.get("environment", {})
env_vars = env.get("variables", {}) if isinstance(env, dict) else {}
print("environment values persisted?", bool(env_vars))
if env_vars:
    print("  env vars:", list(env_vars.keys()))

print("metadata:", meta)
