"""Write site/boxes/index.json: the list of Eddy boxes for the static site.

Run by the Pages workflow at deploy time (a static host cannot list a folder);
read by site/eddy-boxes.js. Mirrors Eddy's reading (nopekit server/eddy.py
view_boxes): each site/boxes/<id>/box.json, defaults view "both", aspect "4/3".
A box whose src or thumbnail is missing is skipped and named on stderr.
"""
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "site") / "boxes"
boxes = []
for manifest in sorted(root.glob("*/box.json")):
    folder = manifest.parent
    try:
        doc = json.loads(manifest.read_text(encoding="utf-8"))
    except ValueError as err:
        print(f"skip {manifest}: {err}", file=sys.stderr)
        continue
    missing = [k for k in ("src", "thumbnail") if not (folder / str(doc.get(k, ""))).is_file()]
    if doc.get("kind") not in ("image", "video", "custom") or "section" not in doc or missing:
        print(f"skip {manifest}: kind/section/files ({missing})", file=sys.stderr)
        continue
    boxes.append({"id": folder.name, "kind": doc["kind"], "title": doc.get("title", ""),
                  "caption": doc.get("caption", ""), "view": doc.get("view", "both"),
                  "section": doc["section"], "about": doc.get("about", ""),
                  "aspect": doc.get("aspect", "4/3"), "src": doc["src"],
                  "thumbnail": doc["thumbnail"]})
(root / "index.json").write_text(json.dumps({"boxes": boxes}, indent=1) + "\n", encoding="utf-8")
print(f"wrote {root / 'index.json'}: {len(boxes)} box(es)")
