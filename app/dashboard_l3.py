from __future__ import annotations

import html
import json
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from .dashboard_shared import load_logs, build_dashboard_data, page_shell, detect_vehicle, extract_preview

router = APIRouter()


def row_status(correlation_id: str, responses: list[dict], errors: list[dict]) -> tuple[str, dict | None]:
    for e in errors:
        if e.get("correlation_id") == correlation_id:
            return "failed", e
    for r in responses:
        if r.get("correlation_id") == correlation_id:
            return "success", r
    return "pending", None


def render_l3_html(data: dict, q: str = "") -> str:
    requests = data["raw"]["requests"]
    responses = data["raw"]["responses"]
    errors = data["raw"]["errors"]

    query = q.strip().lower()
    rows = []

    for req in requests:
        preview = extract_preview(req)
        vehicle = detect_vehicle(preview)
        correlation_id = str(req.get("correlation_id", ""))
        status, matched = row_status(correlation_id, responses, errors)

        item = {
            "ts": req.get("ts", ""),
            "correlation_id": correlation_id,
            "session_id": str(req.get("session_id", "")),
            "user_id_hash": str(req.get("user_id_hash", "")),
            "feature": str(req.get("feature", "")),
            "vehicle": vehicle,
            "message_preview": req.get("payload", {}).get("message_preview", ""),
            "status": status,
            "latency_ms": matched.get("latency_ms") if matched and status == "success" else "",
            "tokens_in": matched.get("tokens_in") if matched and status == "success" else "",
            "tokens_out": matched.get("tokens_out") if matched and status == "success" else "",
            "cost_usd": matched.get("cost_usd") if matched and status == "success" else "",
            "quality_score": matched.get("quality_score") if matched and status == "success" else "",
            "answer_preview": matched.get("payload", {}).get("answer_preview", "") if matched and status == "success" else "",
            "error_type": matched.get("error_type", "") if matched and status == "failed" else "",
        }

        searchable = " ".join([
            item["correlation_id"],
            item["session_id"],
            item["user_id_hash"],
            item["feature"],
            item["vehicle"],
            item["message_preview"],
            item["status"],
            item["error_type"],
        ]).lower()

        if query and query not in searchable:
            continue

        rows.append(item)

    rows = sorted(rows, key=lambda x: x["ts"], reverse=True)

    table_rows = []
    detail_blocks = []

    for i, row in enumerate(rows[:100]):
        row_id = f"detail-{i}"

        table_rows.append(f"""
        <tr onclick="toggleDetail('{row_id}')" style="cursor:pointer;">
            <td>{html.escape(row["ts"])}</td>
            <td>{html.escape(row["correlation_id"])}</td>
            <td>{html.escape(row["feature"])}</td>
            <td>{html.escape(row["vehicle"])}</td>
            <td>{html.escape(row["status"])}</td>
            <td>{html.escape(str(row["latency_ms"]))}</td>
            <td>{html.escape(row["message_preview"][:80])}</td>
        </tr>
        """)

        detail_json = json.dumps(row, ensure_ascii=False, indent=2)
        detail_blocks.append(f"""
        <div id="{row_id}" style="display:none; margin-top:12px;">
            <div class="card">
                <h3>Request Detail — {html.escape(row["correlation_id"])}</h3>
                <pre>{html.escape(detail_json)}</pre>
            </div>
        </div>
        """)

    body = f"""
    <div class="filters">
        <form method="get" action="/dashboard/l3">
            <input
                type="text"
                name="q"
                placeholder="Search correlation_id / session_id / feature / vehicle / status"
                value="{html.escape(q)}"
            />
        </form>
    </div>

    <div class="card" style="min-height:auto;">
        <h3>Request Table</h3>
        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Correlation ID</th>
                    <th>Feature</th>
                    <th>Vehicle</th>
                    <th>Status</th>
                    <th>Latency</th>
                    <th>Message Preview</th>
                </tr>
            </thead>
            <tbody>
                {''.join(table_rows) if table_rows else '<tr><td colspan="7">No matching rows</td></tr>'}
            </tbody>
        </table>
    </div>

    {''.join(detail_blocks)}

    <script>
        function toggleDetail(id) {{
            const el = document.getElementById(id);
            if (!el) return;
            el.style.display = el.style.display === 'none' ? 'block' : 'none';
        }}
    </script>
    """
    return page_shell("VinFast Dashboard L3 — Drill Down / Debug", body)


@router.get("/dashboard/l3", response_class=HTMLResponse)
async def dashboard_l3(q: str = Query(default="")) -> HTMLResponse:
    log_file = Path("data/logs.jsonl")
    if not log_file.exists():
        return HTMLResponse("<h2 style='font-family:Arial;padding:24px;'>Missing data/logs.jsonl</h2>")

    logs = load_logs(log_file)
    data = build_dashboard_data(logs)
    return HTMLResponse(render_l3_html(data, q))