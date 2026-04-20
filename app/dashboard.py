from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


def bucket_minute(ts: str) -> str:
    if not ts:
        return "unknown"
    ts = ts.replace("Z", "")
    if "T" in ts:
        date_part, time_part = ts.split("T", 1)
        hhmm = time_part[:5]
        return f"{date_part} {hhmm}"
    return ts[:16]


def extract_preview(log_item: dict) -> str:
    payload = log_item.get("payload", {})
    if isinstance(payload, dict):
        return str(payload.get("message_preview", "")).lower()
    return ""


def detect_vehicle(text: str) -> str:
    t = text.lower()
    vehicle_patterns = [
        ("VF 3", ["vf3", "vf 3"]),
        ("VF 5", ["vf5", "vf 5"]),
        ("VF 6", ["vf6", "vf 6"]),
        ("VF 7", ["vf7", "vf 7"]),
        ("VF 8", ["vf8", "vf 8"]),
        ("VF 9", ["vf9", "vf 9"]),
        ("Minio Green", ["minio green"]),
        ("Herio Green", ["herio green"]),
        ("Nerio Green", ["nerio green"]),
        ("Limo Green", ["limo green"]),
    ]
    for label, patterns in vehicle_patterns:
        if any(p in t for p in patterns):
            return label
    return "Other / Unspecified"


def detect_query_type(text: str) -> str:
    t = text.lower().strip()

    compare_keywords = [
        "so sánh", "compare", "comparison", "khác nhau",
        "versus", "vs ", "vs.", "đối chiếu",
    ]

    recommend_keywords = [
        "gợi ý", "recommend", "đề xuất", "nên mua",
        "phù hợp", "tư vấn", "chọn xe", "xe nào hợp",
        "xe nào phù hợp", "nên chọn", "best car",
    ]

    if any(k in t for k in compare_keywords):
        return "Compare"

    if any(k in t for k in recommend_keywords):
        return "Recommend"

    return "QA"


def latency_histogram(values: list[float]) -> tuple[list[str], list[int]]:
    bins = [
        ("120-130", 120, 130),
        ("130-140", 130, 140),
        ("140-150", 140, 150),
        ("150-160", 150, 160),
        ("160-170", 160, 170),
        ("170-180", 170, 180),
        ("180-190", 180, 190),
    ]
    counts = []
    for _, lo, hi in bins:
        c = 0
        for v in values:
            if lo <= v < hi:
                c += 1
        counts.append(c)
    labels = [x[0] for x in bins]
    return labels, counts


def load_logs(log_file: Path) -> list[dict]:
    raw_lines = log_file.read_text(encoding="utf-8").splitlines()
    logs: list[dict] = []

    for line in raw_lines:
        line = line.strip()
        if not line:
            continue
        try:
            logs.append(json.loads(line))
        except Exception:
            continue

    return logs


def build_dashboard_data(logs: list[dict]) -> dict:
    request_logs = [x for x in logs if x.get("event") == "request_received"]
    response_logs = [x for x in logs if x.get("event") == "response_sent"]
    error_logs = [x for x in logs if x.get("event") == "request_failed"]

    all_buckets = sorted({
        bucket_minute(x.get("ts", ""))
        for x in logs
        if x.get("ts")
    })
    if not all_buckets:
        all_buckets = ["no-data"]

    traffic_map = {b: 0 for b in all_buckets}
    error_map = {b: 0 for b in all_buckets}
    latency_by_bucket = {b: [] for b in all_buckets}
    quality_by_bucket = {b: [] for b in all_buckets}
    error_type_map: dict[str, int] = {}
    vehicle_map: dict[str, int] = {}
    query_type_map: dict[str, int] = {}

    total_cost = 0.0
    total_tokens_in = 0
    total_tokens_out = 0

    for x in request_logs:
        b = bucket_minute(x.get("timestamp", ""))
        traffic_map[b] = traffic_map.get(b, 0) + 1

        text = extract_preview(x)
        vehicle = detect_vehicle(text)
        qtype = detect_query_type(text)

        vehicle_map[vehicle] = vehicle_map.get(vehicle, 0) + 1
        query_type_map[qtype] = query_type_map.get(qtype, 0) + 1

    for x in error_logs:
        b = bucket_minute(x.get("timestamp", ""))
        error_map[b] = error_map.get(b, 0) + 1
        et = x.get("error_type", "UnknownError")
        error_type_map[et] = error_type_map.get(et, 0) + 1

    all_latencies: list[float] = []

    for x in response_logs:
        b = bucket_minute(x.get("timestamp", ""))
        latency = x.get("latency_ms")
        if isinstance(latency, (int, float)):
            latency_by_bucket.setdefault(b, []).append(float(latency))
            all_latencies.append(float(latency))

        q = x.get("quality_score")
        if isinstance(q, (int, float)):
            quality_by_bucket.setdefault(b, []).append(float(q))

        cost = x.get("cost_usd", 0)
        if isinstance(cost, (int, float)):
            total_cost += float(cost)

        tin = x.get("tokens_in", 0)
        tout = x.get("tokens_out", 0)
        if isinstance(tin, (int, float)):
            total_tokens_in += int(tin)
        if isinstance(tout, (int, float)):
            total_tokens_out += int(tout)

    labels = sorted(set(
        list(traffic_map.keys())
        + list(error_map.keys())
        + list(latency_by_bucket.keys())
        + list(quality_by_bucket.keys())
    ))

    traffic_series = [traffic_map.get(b, 0) for b in labels]
    error_rate_series = []
    avg_quality_series = []
    low_quality_series = []

    for b in labels:
        req = traffic_map.get(b, 0)
        err = error_map.get(b, 0)
        error_rate_series.append(round((err / req * 100.0), 2) if req else 0.0)

        qs = quality_by_bucket.get(b, [])
        avg_quality_series.append(round(sum(qs) / len(qs), 3) if qs else 0.0)
        low_quality_series.append(
            round((sum(1 for x in qs if x < 0.6) / len(qs) * 100.0), 2) if qs else 0.0
        )

    total_requests = len(request_logs)
    total_errors = len(error_logs)
    error_rate_total = round((total_errors / total_requests * 100.0), 2) if total_requests else 0.0
    avg_latency = round(sum(all_latencies) / len(all_latencies), 2) if all_latencies else 0.0

    all_quality: list[float] = []
    for vals in quality_by_bucket.values():
        all_quality.extend(vals)
    avg_quality = round(sum(all_quality) / len(all_quality), 3) if all_quality else 0.0

    latency_hist_labels, latency_hist_counts = latency_histogram(all_latencies)

    sorted_vehicle_items = sorted(vehicle_map.items(), key=lambda x: x[1], reverse=True) or [("Other / Unspecified", 0)]
    sorted_query_items = sorted(query_type_map.items(), key=lambda x: x[1], reverse=True) or [("Unknown", 0)]
    sorted_error_items = sorted(error_type_map.items(), key=lambda x: x[1], reverse=True) or [("NoError", 0)]

    chart_data = {
        "time_labels": labels,
        "traffic": traffic_series,
        "error_rate": error_rate_series,
        "avg_quality": avg_quality_series,
        "low_quality": low_quality_series,
        "latency_hist_labels": latency_hist_labels,
        "latency_hist_counts": latency_hist_counts,
        "vehicle_labels": [x[0] for x in sorted_vehicle_items],
        "vehicle_values": [x[1] for x in sorted_vehicle_items],
        "query_labels": [x[0] for x in sorted_query_items],
        "query_values": [x[1] for x in sorted_query_items],
        "error_type_labels": [x[0] for x in sorted_error_items],
        "error_type_values": [x[1] for x in sorted_error_items],
    }

    return {
        "total_requests": total_requests,
        "error_rate_total": error_rate_total,
        "avg_latency": avg_latency,
        "total_tokens": total_tokens_in + total_tokens_out,
        "avg_quality": avg_quality,
        "chart_data": chart_data,
    }


def render_dashboard_html(data: dict) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>VinFast Query Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f3f6fb;
            color: #1f2937;
        }}
        .header {{
            background: #0f3d78;
            color: white;
            padding: 18px 28px;
            font-size: 22px;
            font-weight: 700;
        }}
        .subheader {{
            padding: 10px 28px 0 28px;
            color: #4b5563;
            font-size: 14px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
            padding: 18px 22px 0 22px;
        }}
        .summary-card {{
            background: white;
            border-radius: 12px;
            padding: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        .summary-card .label {{
            font-size: 12px;
            color: #6b7280;
            margin-bottom: 6px;
        }}
        .summary-card .value {{
            font-size: 22px;
            font-weight: 700;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
            padding: 18px 22px 22px 22px;
        }}
        .card {{
            background: white;
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            min-height: 340px;
        }}
        .card h3 {{
            margin: 0 0 12px 0;
            font-size: 18px;
        }}
        .note {{
            margin: 0 22px 22px 22px;
            background: #e8eef8;
            border-left: 6px solid #0f3d78;
            padding: 16px;
            font-size: 16px;
        }}
        canvas {{
            width: 100% !important;
            height: 250px !important;
        }}
        @media (max-width: 1100px) {{
            .grid {{
                grid-template-columns: 1fr;
            }}
            .summary {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="header">VinFast Vehicle Query Dashboard — Layer 2</div>
    <div class="subheader">
        Dashboard này tập trung vào hành vi người dùng khi hỏi về các dòng xe VinFast: mẫu xe nào được hỏi nhiều, loại câu hỏi nào phổ biến, độ trễ phân bố ra sao, và chất lượng phản hồi có ổn định không.
    </div>

    <div class="summary">
        <div class="summary-card">
            <div class="label">Total Requests</div>
            <div class="value">{data["total_requests"]}</div>
        </div>
        <div class="summary-card">
            <div class="label">Error Rate</div>
            <div class="value">{data["error_rate_total"]:.2f}%</div>
        </div>
        <div class="summary-card">
            <div class="label">Avg Latency</div>
            <div class="value">{data["avg_latency"]:.2f} ms</div>
        </div>
        <div class="summary-card">
            <div class="label">Total Tokens</div>
            <div class="value">{data["total_tokens"]}</div>
        </div>
        <div class="summary-card">
            <div class="label">Avg Quality</div>
            <div class="value">{data["avg_quality"]:.3f}</div>
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>Latency Distribution</h3>
            <canvas id="latencyHistChart"></canvas>
        </div>

        <div class="card">
            <h3>Error Rate</h3>
            <canvas id="errorRateChart"></canvas>
        </div>

        <div class="card">
            <h3>Error Types</h3>
            <canvas id="errorTypeChart"></canvas>
        </div>

        <div class="card">
            <h3>Most Asked VinFast Models</h3>
            <canvas id="vehicleChart"></canvas>
        </div>

        <div class="card">
            <h3>Query Intent Breakdown</h3>
            <canvas id="queryTypeChart"></canvas>
        </div>

        <div class="card">
            <h3>Quality Trend</h3>
            <canvas id="qualityChart"></canvas>
        </div>
    </div>

    <div class="note">
        Layer 2 chỉ nên hiển thị 6 panels quan trọng nhất cho use case VinFast. Nếu cần phân tích sâu hơn, hãy drill down xuống trace, logs, hoặc xây thêm layer 3 cho từng model xe.
    </div>

    <script>
        const data = {json.dumps(data["chart_data"])};

        new Chart(document.getElementById('latencyHistChart'), {{
            type: 'bar',
            data: {{
                labels: data.latency_hist_labels,
                datasets: [
                    {{ label: 'Count', data: data.latency_hist_counts, borderWidth: 1 }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ title: {{ display: true, text: 'Latency (ms)' }} }},
                    y: {{ title: {{ display: true, text: 'Count' }}, beginAtZero: true }}
                }}
            }}
        }});

        new Chart(document.getElementById('errorRateChart'), {{
            type: 'line',
            data: {{
                labels: data.time_labels,
                datasets: [
                    {{ label: 'Error rate %', data: data.error_rate, borderWidth: 2, fill: false }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        min: 0,
                        title: {{
                            display: true,
                            text: 'Error Rate (%)'
                        }}
                    }}
                }}
            }}
        }});

        new Chart(document.getElementById('errorTypeChart'), {{
            type: 'bar',
            data: {{
                labels: data.error_type_labels,
                datasets: [
                    {{ label: 'Error count', data: data.error_type_values, borderWidth: 1 }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('vehicleChart'), {{
            type: 'bar',
            data: {{
                labels: data.vehicle_labels,
                datasets: [
                    {{ label: 'Requests', data: data.vehicle_values, borderWidth: 1 }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y'
            }}
        }});

        new Chart(document.getElementById('queryTypeChart'), {{
            type: 'bar',
            data: {{
                labels: data.query_labels,
                datasets: [
                    {{ label: 'Count', data: data.query_values, borderWidth: 1 }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('qualityChart'), {{
            type: 'line',
            data: {{
                labels: data.time_labels,
                datasets: [
                    {{ label: 'Avg quality score', data: data.avg_quality, borderWidth: 2, fill: false }},
                    {{ label: 'Low-quality %', data: data.low_quality, borderWidth: 2, fill: false }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});
    </script>
</body>
</html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> HTMLResponse:
    log_file = Path("data/logs.jsonl")

    if not log_file.exists():
        return HTMLResponse("""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 24px;">
            <h2>No logs yet</h2>
            <p>Missing file: data/logs.jsonl</p>
        </body>
        </html>
        """)

    logs = load_logs(log_file)
    data = build_dashboard_data(logs)
    return HTMLResponse(render_dashboard_html(data))