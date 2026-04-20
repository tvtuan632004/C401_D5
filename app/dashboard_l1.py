from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .dashboard_shared import load_logs, build_dashboard_data, page_shell

router = APIRouter()


def render_l1_html(data: dict) -> str:
    s = data["summary"]
    c = data["charts"]

    body = f"""
    <div class="summary">
        <div class="summary-card">
            <div class="label">Total Requests</div>
            <div class="value">{s["total_requests"]}</div>
        </div>
        <div class="summary-card">
            <div class="label">Error Rate</div>
            <div class="value">{s["error_rate_total"]:.2f}%</div>
        </div>

        <div class="summary-card">
            <div class="label">Avg Quality</div>
            <div class="value">{s["avg_quality"]:.3f}</div>
        </div>
    </div>

    <div class="grid-2">
        <div class="card">
            <h3>Traffic vs Error Rate</h3>
            <canvas id="trafficErrorChart"></canvas>
        </div>

        <div class="card">
            <h3>Query Intent Breakdown</h3>
            <canvas id="queryTypeChart"></canvas>
        </div>

        <div class="card">
            <h3>Top Asked VinFast Models</h3>
            <canvas id="vehicleChart"></canvas>
        </div>

        <div class="card">
            <h3>Quality Snapshot</h3>
            <canvas id="qualityOverviewChart"></canvas>
        </div>
    </div>

    <script>
        const data = {json.dumps(c)};

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
                        title: {{ display: true, text: 'Requests' }}
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

        new Chart(document.getElementById('queryTypeChart'), {{
            type: 'bar',
            data: {{
                labels: data.query_labels,
                datasets: [
                    {{
                        label: 'Count',
                        data: data.query_values
                    }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        new Chart(document.getElementById('vehicleChart'), {{
            type: 'bar',
            data: {{
                labels: data.vehicle_labels,
                datasets: [
                    {{
                        label: 'Requests',
                        data: data.vehicle_values
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y'
            }}
        }});

        new Chart(document.getElementById('qualityOverviewChart'), {{
            type: 'line',
            data: {{
                labels: data.time_labels,
                datasets: [
                    {{
                        label: 'Avg quality',
                        data: data.avg_quality
                    }},
                    {{
                        label: 'Low-quality %',
                        data: data.low_quality
                    }}
                ]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});
    </script>
    """
    return page_shell("VinFast Dashboard L1 — Overview", body)


@router.get("/dashboard/l1", response_class=HTMLResponse)
async def dashboard_l1() -> HTMLResponse:
    log_file = Path("data/logs.jsonl")
    if not log_file.exists():
        return HTMLResponse("<h2 style='font-family:Arial;padding:24px;'>Missing data/logs.jsonl</h2>")

    logs = load_logs(log_file)
    data = build_dashboard_data(logs)
    return HTMLResponse(render_l1_html(data))