import os
import re

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "src"))

# LiveTopology.tsx
lt_path = os.path.join(root, "components", "topology", "LiveTopology.tsx")
if os.path.exists(lt_path):
    with open(lt_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r'\(d\) =>', '(d: any) =>', content)
    content = re.sub(r'\(_, d\) =>', '(_, d: any) =>', content)
    content = re.sub(r'\(event, d\) =>', '(event: any, d: any) =>', content)
    with open(lt_path, "w", encoding="utf-8") as f:
        f.write(content)

# AIAssistantPanel.tsx
aia_path = os.path.join(root, "components", "dashboard", "AIAssistantPanel.tsx")
if os.path.exists(aia_path):
    with open(aia_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("nplEvents.forEach((event) =>", "nplEvents.forEach((event: any) =>")
    with open(aia_path, "w", encoding="utf-8") as f:
        f.write(content)

# Dashboard.tsx
db_path = os.path.join(root, "pages", "Dashboard.tsx")
if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        content = f.read()
    content = content.replace("insights={insights}", "insights={insights as any}")
    with open(db_path, "w", encoding="utf-8") as f:
        f.write(content)

print("TS fixes applied")
