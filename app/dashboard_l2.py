from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .dashboard_shared import load_logs, build_dashboard_data, page_shell

router = APIRouter()


def render_l2_html(data: dict) -> str:
    s = data["summary"]
    c = data["charts"]

    body = f"""
    <div class="summary">
        <div class="summary-card">
            <div class="label">Total Cost</div>
            <div class="value">${s["total_cost"]}</div>
        </div>
        <div class="summary-card">
            <div class="label">Tokens In</div>
            <div class="value">{s["total_tokens_in"]}</div>
        </div>
        <div class="summary-card">
            <div class="label">Tokens Out</div>
            <div class="value">{s["total_tokens_out"]}</div>
        </div>
        <div class="summary-card">
            <div class="label">Avg Questions / Session</div>
            <div class="value">{s["avg_questions_per_session"]}</div>
        </div>

    </div>

    <div class="grid-3">
        <div class="card">
            <h3>Latency P50 / P95 / P99</h3>
            <canvas id="latencyChart"></canvas>
        </div>

        <div class="card">
            <h3>Traffic / Errors / Error Rate</h3>
            <canvas id="trafficErrorChart"></canvas>
        </div>

        <div class="card">
            <h3>Cost Trend</h3>
            <canvas id="costChart"></canvas>
        </div>

        <div class="card">
            <h3>Tokens In / Out</h3>
            <canvas id="tokenChart"></canvas>
        </div>


        <div class="card">
            <h3>Error Type Breakdown</h3>
            <canvas id="errorTypeChart"></canvas>
        </div>
    </div>

    <script>
        const data = {json.dumps(c)};

        new Chart(document.getElementById('latencyChart'), {{
            type: 'line',
            data: {{
                labels: data.time_labels,
                datasets: [
                    {{ label: 'P50', data: data.latency_p50 }},
                    {{ label: 'P95', data: data.latency_p95 }},
                    {{ label: 'P99', data: data.latency_p99 }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('trafficErrorChart'), {{
            type: 'line',
            data: {{
                labels: data.time_labels,
                datasets: [
                    {{
                        label: 'Requests',
                        data: data.traffic,
                        yAxisID: 'y'
                    }},
                    {{
                        label: 'Error rate %',
                        data: data.error_rate,
                        yAxisID: 'y1'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        position: 'left',
                        title: {{ display: true, text: 'Count' }}
                    }},
                    y1: {{
                        beginAtZero: true,
                        position: 'right',
                        grid: {{ drawOnChartArea: false }},
                        title: {{ display: true, text: 'Error %' }}
                    }}
                }}
            }}
        }});

        new Chart(document.getElementById('costChart'), {{
            type: 'line',
            data: {{
                labels: data.time_labels,
                datasets: [
                    {{ label: 'Cost / bucket', data: data.cost }},
                    {{ label: 'Cumulative cost', data: data.cumulative_cost }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('tokenChart'), {{
            type: 'bar',
            data: {{
                labels: data.time_labels,
                datasets: [
                    {{ label: 'Tokens in', data: data.tokens_in }},
                    {{ label: 'Tokens out', data: data.tokens_out }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false
            }}
        }});

        new Chart(document.getElementById('qualityChart'), {{
            type: 'line',
            data: {{
                labels: data.time_labels,
                datasets: [
                    {{ label: 'Avg quality', data: data.avg_quality }},
                    {{ label: 'Low-quality %', data: data.low_quality }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('errorTypeChart'), {{
            type: 'bar',
            data: {{
                labels: data.error_type_labels,
                datasets: [
                    {{ label: 'Count', data: data.error_type_values }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('queryChart'), {{
            type: 'bar',
            data: {{
                labels: data.query_labels,
                datasets: [
                    {{ label: 'Count', data: data.query_values }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('vehicleChart'), {{
            type: 'bar',
            data: {{
                labels: data.vehicle_labels,
                datasets: [
                    {{ label: 'Requests', data: data.vehicle_values }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y'
            }}
        }});
    </script>
    """
    return page_shell("VinFast Dashboard L2 — Engineering Detail", body)


@router.get("/dashboard/l2", response_class=HTMLResponse)
async def dashboard_l2() -> HTMLResponse:
    log_file = Path("data/logs.jsonl")
    if not log_file.exists():
        return HTMLResponse("<h2 style='font-family:Arial;padding:24px;'>Missing data/logs.jsonl</h2>")

    logs = load_logs(log_file)
    data = build_dashboard_data(logs)
    return HTMLResponse(render_l2_html(data))