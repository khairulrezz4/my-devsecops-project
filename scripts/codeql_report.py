"""Create interactive HTML and readable PDF reports from CodeQL SARIF output."""

from __future__ import annotations

import argparse
import html
import json
import textwrap
from pathlib import Path
from typing import Any


def load_results(source: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for sarif_path in sorted(source.rglob("*.sarif")):
        document = json.loads(sarif_path.read_text(encoding="utf-8"))
        for run in document.get("runs", []):
            tool = run.get("tool", {}).get("driver", {}).get("name", "CodeQL")
            rules = {
                rule.get("id"): rule
                for rule in run.get("tool", {}).get("driver", {}).get("rules", [])
            }
            for result in run.get("results", []):
                rule_id = result.get("ruleId", "unknown")
                location = (result.get("locations") or [{}])[0].get("physicalLocation", {})
                artifact = location.get("artifactLocation", {}).get("uri", "unknown")
                line = location.get("region", {}).get("startLine", "?")
                rule = rules.get(rule_id, {})
                results.append(
                    {
                        "tool": tool,
                        "rule": rule_id,
                        "level": result.get("level", "warning"),
                        "message": result.get("message", {}).get("text", "No message"),
                        "location": f"{artifact}:{line}",
                        "help": result.get("helpUri") or rule.get("helpUri", ""),
                    }
                )
    return results


def write_html(results: list[dict[str, Any]], destination: Path) -> None:
    rows = []
    for item in results:
        rows.append(
            "<tr data-search='{search}'><td>{level}</td><td>{rule}</td>"
            "<td>{location}</td><td>{message}</td><td>{link}</td></tr>".format(
                search=html.escape(
                    " ".join(str(item[key]) for key in ("level", "rule", "location", "message")),
                    quote=True,
                ),
                level=html.escape(item["level"]),
                rule=html.escape(item["rule"]),
                location=html.escape(item["location"]),
                message=html.escape(item["message"]),
                link=(
                    f'<a href="{html.escape(item["help"], quote=True)}">Guidance</a>'
                    if item["help"]
                    else "-"
                ),
            )
        )
    body = "\n".join(rows) or (
        '<tr><td colspan="5">No CodeQL findings were reported.</td></tr>'
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>CodeQL report</title>
<style>
body{{font:14px system-ui,sans-serif;margin:2rem;color:#17202a}}
input{{padding:.6rem;width:min(50rem,100%);margin-bottom:1rem}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #d0d7de;padding:.6rem;text-align:left;vertical-align:top}}
th{{background:#f6f8fa}}tr[data-search=""]{{display:table-row}}
</style></head><body><h1>CodeQL security report</h1>
<p>Findings: <strong>{len(results)}</strong>. Filter by severity, rule, file, or message:</p>
<input id="filter" placeholder="Filter findings..." aria-label="Filter findings">
<table><thead><tr><th>Level</th><th>Rule</th><th>Location</th><th>Message</th><th>Help</th></tr></thead>
<tbody>{body}</tbody></table>
<script>
const input=document.getElementById('filter');
input.addEventListener('input',()=>{{const q=input.value.toLowerCase();
document.querySelectorAll('tbody tr').forEach(r=>r.hidden=q&&!r.dataset.search.toLowerCase().includes(q));}});
</script></body></html>"""
    destination.write_text(document, encoding="utf-8")


def pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_pdf(results: list[dict[str, Any]], destination: Path) -> None:
    lines = ["CodeQL security report", f"Findings: {len(results)}", ""]
    for index, item in enumerate(results, 1):
        lines.extend(
            textwrap.wrap(
                f"{index}. [{item['level']}] {item['rule']} - {item['location']}",
                105,
            )
        )
        lines.extend(textwrap.wrap(f"   {item['message']}", 105) or ["   "])
        if item["help"]:
            lines.extend(textwrap.wrap(f"   Guidance: {item['help']}", 105))
        lines.append("")
    pages = [lines[i : i + 48] for i in range(0, len(lines), 48)] or [[]]
    objects: list[bytes] = []

    def add(value: str) -> int:
        objects.append(value.encode("latin-1", errors="replace"))
        return len(objects)

    catalog = add("")
    pages_object = add("")
    font = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_ids = []
    for page_lines in pages:
        content = ["BT", "/F1 10 Tf", "50 750 Td", "13 TL"]
        for line in page_lines:
            content.append(f"({pdf_escape(line)}) Tj T*")
        content.append("ET")
        stream = "\n".join(content).encode("latin-1", errors="replace")
        stream_id = add(f"<< /Length {len(stream)} >>\nstream\n") 
        objects[stream_id - 1] += stream + b"\nendstream"
        page_ids.append(add(""))
        objects[page_ids[-1] - 1] = (
            f"<< /Type /Page /Parent {pages_object} 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {font} 0 R >> >> /Contents {stream_id} 0 R >>"
        ).encode()
    objects[pages_object - 1] = (
        f"<< /Type /Pages /Kids [{' '.join(f'{i} 0 R' for i in page_ids)}] "
        f"/Count {len(page_ids)} >>"
    ).encode()
    objects[catalog - 1] = f"<< /Type /Catalog /Pages {pages_object} 0 R >>".encode()

    output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for number, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode())
        output.extend(obj)
        output.extend(b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    output.extend(
        b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    )
    output.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog} 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode()
    )
    destination.write_bytes(output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sarif_directory", type=Path)
    parser.add_argument("report_directory", type=Path)
    args = parser.parse_args()
    args.report_directory.mkdir(parents=True, exist_ok=True)
    results = load_results(args.sarif_directory)
    write_html(results, args.report_directory / "codeql-report.html")
    write_pdf(results, args.report_directory / "codeql-report.pdf")


if __name__ == "__main__":
    main()
