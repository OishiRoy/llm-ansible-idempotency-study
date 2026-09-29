import json
from pathlib import Path

with open("tasks/tasks.json", "r", encoding="utf-8") as f:
    data = json.load(f)

output_dir = Path("prompts/default")
output_dir.mkdir(parents=True, exist_ok=True)

for task in data["tasks"]:
    task_id = task["id"]
    task_text = task["task"]

    prompt = f"""Generate a complete Ansible playbook for Ubuntu 22.04 that performs the following task:

{task_text}

Requirements:
- Target localhost using a local connection.
- Use become: true where necessary.
- Return only the complete YAML playbook.
"""

    output_file = output_dir / f"{task_id}.txt"
    output_file.write_text(prompt, encoding="utf-8")

print(f"Created {len(data['tasks'])} prompts.")