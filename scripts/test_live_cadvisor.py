import urllib.request
import urllib.parse
import json

def query(promql):
    q = urllib.parse.quote(promql)
    url = f"http://127.0.0.1:9090/api/v1/query?query={q}"
    res = urllib.request.urlopen(url)
    return json.loads(res.read())["data"]["result"]

print("--- Memory Working Set Bytes ---")
for r in query('container_memory_working_set_bytes{namespace="sentinelops-e2e"}')[:6]:
    print("  Pod:", r["metric"].get("pod"), "Container:", r["metric"].get("container"), "Bytes:", r["value"][1])

print("--- CPU Usage Seconds Rate ---")
for r in query('rate(container_cpu_usage_seconds_total{namespace="sentinelops-e2e"}[1m])')[:6]:
    print("  Pod:", r["metric"].get("pod"), "Rate:", r["value"][1])
