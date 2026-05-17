import os
import re

root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "src", "components", "topology", "LiveTopology.tsx"))

with open(root, "r", encoding="utf-8") as f:
    content = f.read()

# Remove type arguments from forceSimulation and forceLink
content = re.sub(r'forceSimulation<TopologyNode>', 'forceSimulation', content)
content = re.sub(r'forceLink<TopologyNode, TopologyEdge>', 'forceLink', content)
content = content.replace("as TopologyNode).x", "as any).x")
content = content.replace("as TopologyNode).y", "as any).y")
content = content.replace("<SVGCircleElement, TopologyNode>", "<SVGCircleElement, any>")

with open(root, "w", encoding="utf-8") as f:
    f.write(content)

print("Fixed LiveTopology")
