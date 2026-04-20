from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path


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

import math

def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0   # <-- quan trọng

    values = sorted(values)
    idx = math.ceil((len(values) - 1) * p)
    return round(values[idx], 2)

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
    }) or ["no-data"]

    traffic_map = {b: 0 for b in all_buckets}
    error_map = {b: 0 for b in all_buckets}
    latency_by_bucket: dict[str, list[float]] = {b: [] for b in all_buckets}
    quality_by_bucket: dict[str, list[float]] = {b: [] for b in all_buckets}
    cost_by_bucket: dict[str, float] = {b: 0.0 for b in all_buckets}
    tokens_in_by_bucket: dict[str, int] = {b: 0 for b in all_buckets}
    tokens_out_by_bucket: dict[str, int] = {b: 0 for b in all_buckets}

    error_type_map: dict[str, int] = defaultdict(int)
    vehicle_map: dict[str, int] = defaultdict(int)
    query_type_map: dict[str, int] = defaultdict(int)

    session_request_count: dict[tuple[str, str], int] = defaultdict(int)
    user_session_stats: dict[str, list[int]] = defaultdict(list)

    total_cost = 0.0
    total_tokens_in = 0
    total_tokens_out = 0
    all_latencies: list[float] = []
    all_quality: list[float] = []

    for x in request_logs:
        b = bucket_minute(x.get("ts", ""))
        traffic_map[b] += 1

        user_id = str(x.get("user_id_hash", "unknown"))
        session_id = str(x.get("session_id", "unknown"))
        session_request_count[(user_id, session_id)] += 1

        text = extract_preview(x)
        vehicle_map[detect_vehicle(text)] += 1

        feature = str(x.get("feature", "")).strip().lower()
        feature_map = {
            "qa": "QA",
            "compare": "Compare",
            "recommend": "Recommend",
        }
        query_type_map[feature_map.get(feature, "Unknown")] += 1

    for x in error_logs:
        b = bucket_minute(x.get("ts", ""))
        error_map[b] += 1
        error_type_map[str(x.get("error_type", "UnknownError"))] += 1

    for x in response_logs:
        b = bucket_minute(x.get("ts", ""))
        latency = x.get("latency_ms")
        quality = x.get("quality_score")
        cost = x.get("cost_usd", 0)
        tin = x.get("tokens_in", 0)
        tout = x.get("tokens_out", 0)

        if isinstance(latency, (int, float)):
            latency = float(latency)
            latency_by_bucket[b].append(latency)
            all_latencies.append(latency)

        if isinstance(quality, (int, float)):
            quality = float(quality)
            quality_by_bucket[b].append(quality)
            all_quality.append(quality)

        if isinstance(cost, (int, float)):
            cost = float(cost)
            cost_by_bucket[b] += cost
            total_cost += cost

        if isinstance(tin, (int, float)):
            tin = int(tin)
            tokens_in_by_bucket[b] += tin
            total_tokens_in += tin

        if isinstance(tout, (int, float)):
            tout = int(tout)
            tokens_out_by_bucket[b] += tout
            total_tokens_out += tout

    for (user_id, _session_id), cnt in session_request_count.items():
        user_session_stats[user_id].append(cnt)

    all_session_sizes = []
    for counts in user_session_stats.values():
        all_session_sizes.extend(counts)

    labels = sorted(set(
        list(traffic_map.keys())
        + list(error_map.keys())
        + list(latency_by_bucket.keys())
        + list(quality_by_bucket.keys())
    ))

    traffic_series = [traffic_map.get(b, 0) for b in labels]
    error_count_series = [error_map.get(b, 0) for b in labels]
    error_rate_series = []
    p50_series = []
    p95_series = []
    p99_series = []
    avg_quality_series = []
    low_quality_series = []
    cost_series = []
    cumulative_cost_series = []
    tokens_in_series = []
    tokens_out_series = []

    running_cost = 0.0
    for b in labels:
        req = traffic_map.get(b, 0)
        err = error_map.get(b, 0)
        error_rate_series.append(round((err / req * 100.0), 2) if req else 0.0)

        latencies = latency_by_bucket.get(b, [])
        p50_series.append(percentile(latencies, 0.50))
        p95_series.append(percentile(latencies, 0.95))
        p99_series.append(percentile(latencies, 0.99))

        qs = quality_by_bucket.get(b, [])
        avg_quality_series.append(round(sum(qs) / len(qs), 3) if qs else 0.0)
        low_quality_series.append(
            round((sum(1 for x in qs if x < 0.6) / len(qs) * 100.0), 2) if qs else 0.0
        )

        c = round(cost_by_bucket.get(b, 0.0), 6)
        running_cost += c
        cost_series.append(c)
        cumulative_cost_series.append(round(running_cost, 6))

        tokens_in_series.append(tokens_in_by_bucket.get(b, 0))
        tokens_out_series.append(tokens_out_by_bucket.get(b, 0))

    total_requests = len(request_logs)
    total_errors = len(error_logs)
    error_rate_total = round((total_errors / total_requests * 100.0), 2) if total_requests else 0.0
    avg_latency = round(sum(all_latencies) / len(all_latencies), 2) if all_latencies else 0.0
    avg_quality = round(sum(all_quality) / len(all_quality), 3) if all_quality else 0.0
    avg_cost_per_request = round(total_cost / total_requests, 6) if total_requests else 0.0
    avg_questions_per_session = round(
        sum(all_session_sizes) / len(all_session_sizes), 2
    ) if all_session_sizes else 0.0

    sorted_vehicle_items = sorted(vehicle_map.items(), key=lambda x: x[1], reverse=True) or [("Other / Unspecified", 0)]
    sorted_query_items = sorted(query_type_map.items(), key=lambda x: x[1], reverse=True) or [("Unknown", 0)]
    sorted_error_items = sorted(error_type_map.items(), key=lambda x: x[1], reverse=True) or [("NoError", 0)]

    return {
        "summary": {
            "total_requests": total_requests,
            "total_errors": total_errors,
            "error_rate_total": error_rate_total,
            "avg_latency": avg_latency,
            "avg_cost_per_request": avg_cost_per_request,
            "avg_quality": avg_quality,
            "avg_questions_per_session": avg_questions_per_session,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "total_cost": round(total_cost, 6),
        },
        "charts": {
            "time_labels": labels,
            "traffic": traffic_series,
            "error_count": error_count_series,
            "error_rate": error_rate_series,
            "latency_p50": p50_series,
            "latency_p95": p95_series,
            "latency_p99": p99_series,
            "avg_quality": avg_quality_series,
            "low_quality": low_quality_series,
            "cost": cost_series,
            "cumulative_cost": cumulative_cost_series,
            "tokens_in": tokens_in_series,
            "tokens_out": tokens_out_series,
            "vehicle_labels": [x[0] for x in sorted_vehicle_items],
            "vehicle_values": [x[1] for x in sorted_vehicle_items],
            "query_labels": [x[0] for x in sorted_query_items],
            "query_values": [x[1] for x in sorted_query_items],
            "error_type_labels": [x[0] for x in sorted_error_items],
            "error_type_values": [x[1] for x in sorted_error_items],
        },
        "raw": {
            "requests": request_logs,
            "responses": response_logs,
            "errors": error_logs,
        }
    }


def page_shell(title: str, body: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
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
        .container {{
            padding: 18px 22px 22px 22px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 12px;
            margin-bottom: 18px;
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
        .grid-2 {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 18px;
        }}
        .grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
        }}
        .card {{
            background: white;
            border-radius: 14px;
            padding: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            min-height: 320px;
        }}
        .card h3 {{
            margin: 0 0 12px 0;
            font-size: 18px;
        }}
        canvas {{
            width: 100% !important;
            height: 250px !important;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 12px;
            overflow: hidden;
        }}
        th, td {{
            padding: 10px 12px;
            border-bottom: 1px solid #e5e7eb;
            text-align: left;
            font-size: 14px;
            vertical-align: top;
        }}
        th {{
            background: #eef2ff;
        }}
        pre {{
            white-space: pre-wrap;
            word-break: break-word;
            background: #111827;
            color: #f9fafb;
            padding: 14px;
            border-radius: 10px;
            overflow: auto;
        }}
        .filters {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-bottom: 18px;
        }}
        .filters input {{
            padding: 10px 12px;
            border: 1px solid #d1d5db;
            border-radius: 10px;
            min-width: 220px;
        }}
        @media (max-width: 1100px) {{
            .summary, .grid-2, .grid-3 {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">{title}</div>
    <div class="container">
        {body}
    </div>
</body>
</html>
"""