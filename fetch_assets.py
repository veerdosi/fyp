"""Fetch the published GGSD G1 model, visual meshes and two policy exports."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import urllib.request
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent / ".deps" / "ggsd"
REV = "02732d215eacbeac7403a5841996b170d3ae7c78"
SOURCE = f"https://raw.githubusercontent.com/ggsd-demo/ggsd-demo.github.io/{REV}"
SCENE = "exports/g1_boxing/g1_boxing_mesh.xml"
RUNS = ("run1_67000", "run2_70000")


def fetch(path):
    destination = ROOT / path
    if not destination.is_file():
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".part")
        urllib.request.urlretrieve(f"{SOURCE}/{path}", temporary)
        temporary.replace(destination)
    return destination


def main():
    scene = ET.parse(fetch(SCENE))
    meshes = [f"exports/g1/meshes/{mesh.attrib['file']}" for mesh in scene.findall("asset/mesh")]
    policies = [
        f"exports/g1_boxing/ckpts/{run}/{filename}"
        for run in RUNS for filename in ("policy.json", "weights.bin")
    ]
    with ThreadPoolExecutor(8) as executor:
        list(executor.map(fetch, meshes + policies))
    for path in policies[::2]:
        assert json.loads((ROOT / path).read_text())["obs_dim"] == 194


if __name__ == "__main__":
    main()
