import tomllib
import re
from importlib.metadata import distributions, PackageNotFoundError
from pathlib import Path

project = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
requirements = project["project"].get("dependencies", [])
installed = {
    d.metadata["Name"].lower().replace("_", "-"): d.version
    for d in distributions()
    if d.metadata.get("Name")
}

print("\n=== CUREGENIX DEPENDENCY AUDIT ===")
missing = []

for req in requirements:
    name = re.split(r"[<>=!~;\[]", req, maxsplit=1)[0].strip()
    key = name.lower().replace("_", "-")
    version = installed.get(key)
    if version:
        print(f"[INSTALLED] {req}  -> {version}")
    else:
        print(f"[MISSING]   {req}")
        missing.append(req)

print(f"\nDeclared dependencies: {len(requirements)}")
print(f"Missing distributions: {len(missing)}")

Path("dependency-audit-missing.txt").write_text(
    "\n".join(missing) + ("\n" if missing else ""),
    encoding="utf-8"
)
print("Missing-package list saved to dependency-audit-missing.txt")
