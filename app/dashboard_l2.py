from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .dashboard_shared import load_logs, build_dashboard_data, page_shell

router = APIRouter()


def render_l2_html(data: dict) -> str:
    s = data.get("summary", {})
    c = data.get("charts", {})

    style_extra = """
    <style>
        :root {
            --vin-blue: #1b52d3;
            --vin-dark: #121212;
            --bg-light: #f8f9fa;
            --card-shadow: 0 4px 12px rgba(0,0,0,0.08);
            --accent-green: #2ecc71;
            --accent-red: #e74c3c;
        }
        body {
            background-color: var(--bg-light);
            font-family: 'Inter', -apple-system, sans-serif;
            margin: 0;
        }
        .dashboard-container {
            padding: 24px;
            max-width: 1600px;
            margin: 0 auto;
        }

        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: #fff;
            padding: 20px;
            border-radius: 12px;
            box-shadow: var(--card-shadow);
            border-bottom: 4px solid var(--vin-blue);
        }
        .label {
            color: #7f8c8d;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .value {
            color: var(--vin-dark);
            font-size: 1.6rem;
            font-weight: 800;
            margin-top: 8px;
        }

        .grid-3 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
            gap: 24px;
        }
        @media (max-width: 1024px) {
            .grid-3 {
                grid-template-columns: 1fr;
            }
        }

        .card {
            background: #fff;
            padding: 24px;
            border-radius: 16px;
            box-shadow: var(--card-shadow);
            min-height: 320px;
            display: flex;
            flex-direction: column;
        }
        .card h3 {
            margin: 0 0 20px 0;
            font-size: 1.1rem;
            color: #2c3e50;
            font-weight: 700;
            border-left: 4px solid var(--vin-blue);
            padding-left: 12px;
        }
        .chart-container {
            flex-grow: 1;
            position: relative;
            width: 100%;
        }
    </style>
    """

    body = f"""
    {style_extra}
    <div class="dashboard-container">
        <div class="summary">
            <div class="summary-card">
                <div class="label">Total Cost</div>
                <div class="value" style="color: var(--vin-blue)">${s.get("total_cost", 0):.4f}</div>
            </div>
            <div class="summary-card">
                <div class="label">Tokens In</div>
                <div class="value">{s.get("total_tokens_in", 0):,}</div>
            </div>
            <div class="summary-card">
                <div class="label">Tokens Out</div>
                <div class="value">{s.get("total_tokens_out", 0):,}</div>
            </div>
            <div class="summary-card">
                <div class="label">Avg Qns / Session</div>
                <div class="value">{s.get("avg_questions_per_session", 0):.2f}</div>
            </div>
        </div>

        <div class="grid-3">
            <div class="card">
                <h3>Latency P50 / P95 / P99 (ms)</h3>
                <div class="chart-container"><canvas id="latencyChart"></canvas></div>
            </div>

            <div class="card">
                <h3>Span Latency Breakdown (ms)</h3>
                <div class="chart-container"><canvas id="spanLatencyChart"></canvas></div>
            </div>

            <div class="card">
                <h3>Traffic & Error Performance</h3>
                <div class="chart-container"><canvas id="trafficErrorChart"></canvas></div>
            </div>

            <div class="card">
                <h3>Cost Trend (Daily & Cumulative)</h3>
                <div class="chart-container"><canvas id="costChart"></canvas></div>
            </div>

            <div class="card">
                <h3>Token Usage In/Out</h3>
                <div class="chart-container"><canvas id="tokenChart"></canvas></div>
            </div>

            <div class="card">
                <h3>Error Type Breakdown</h3>
                <div class="chart-container"><canvas id="errorTypeChart"></canvas></div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        const data = {json.dumps(c)} || {{}};

        const commonOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    position: 'bottom',
                    labels: {{
                        usePointStyle: true,
                        pointStyle: 'line',
                        padding: 15
                    }}
                }}
            }}
        }};

        // 1. Latency Chart
        new Chart(document.getElementById('latencyChart'), {{
            type: 'line',
            data: {{
                labels: data.time_labels || [],
                datasets: [
                    {{
                        label: 'P50',
                        data: data.latency_p50 || [],
                        borderColor: '#3498db',
                        tension: 0.3,
                        fill: false
                    }},
                    {{
                        label: 'P95',
                        data: data.latency_p95 || [],
                        borderColor: '#f1c40f',
                        tension: 0.3,
                        fill: false
                    }},
                    {{
                        label: 'P99',
                        data: data.latency_p99 || [],
                        borderColor: '#e74c3c',
                        tension: 0.3,
                        fill: false
                    }}
                ]
            }},
            options: commonOptions
        }});

        // 2. Span Latency Breakdown
        new Chart(document.getElementById('spanLatencyChart'), {{
            type: 'bar',
            data: {{
                labels: data.span_labels || [],
                datasets: [
                    {{
                        label: 'Avg (mean latency)',
                        data: data.span_avg || [],
                        backgroundColor: '#3498db'
                    }},
                    {{
                        label: 'P95 (tail latency)',
                        data: data.span_p95 || [],
                        backgroundColor: '#f39c12'
                    }},
                    {{
                        label: 'Max (worst case)',
                        data: data.span_max || [],
                        backgroundColor: '#e74c3c'
                    }}
                ]
            }},
            options: {{
                ...commonOptions,
                plugins: {{
                    legend: {{
                        position: 'bottom',
                        labels: {{
                            boxWidth: 12,
                            padding: 15
                        }}
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Latency (ms)'
                        }}
                    }}
                }}
            }}
        }});

        // 3. Traffic & Error Rate
        new Chart(document.getElementById('trafficErrorChart'), {{
            type: 'line',
            data: {{
                labels: data.time_labels || [],
                datasets: [
                    {{
                        label: 'Requests',
                        data: data.traffic || [],
                        borderColor: '#1b52d3',
                        backgroundColor: 'rgba(27, 82, 211, 0.1)',
                        fill: true,
                        yAxisID: 'y'
                    }},
                    {{
                        label: 'Error Rate %',
                        data: data.error_rate || [],
                        borderColor: '#e74c3c',
                        borderDash: [5, 5],
                        yAxisID: 'y1'
                    }}
                ]
            }},
            options: {{
                ...commonOptions,
                scales: {{
                    y: {{
                        position: 'left',
                        title: {{
                            display: true,
                            text: 'Requests'
                        }}
                    }},
                    y1: {{
                        position: 'right',
                        grid: {{
                            drawOnChartArea: false
                        }},
                        title: {{
                            display: true,
                            text: 'Error %'
                        }}
                    }}
                }}
            }}
        }});

        // 4. Cost Chart
        new Chart(document.getElementById('costChart'), {{
            type: 'line',
            data: {{
                labels: data.time_labels || [],
                datasets: [
                    {{
                        label: 'Cost / bucket',
                        data: data.cost || [],
                        borderColor: '#2ecc71',
                        type: 'bar',
                        backgroundColor: 'rgba(46, 204, 113, 0.5)'
                    }},
                    {{
                        label: 'Cumulative cost',
                        data: data.cumulative_cost || [],
                        borderColor: '#27ae60',
                        tension: 0.3
                    }}
                ]
            }},
            options: commonOptions
        }});

        // 5. Token Chart
        new Chart(document.getElementById('tokenChart'), {{
            type: 'bar',
            data: {{
                labels: data.time_labels || [],
                datasets: [
                    {{
                        label: 'Tokens In',
                        data: data.tokens_in || [],
                        backgroundColor: '#34495e'
                    }},
                    {{
                        label: 'Tokens Out',
                        data: data.tokens_out || [],
                        backgroundColor: '#1b52d3'
                    }}
                ]
            }},
            options: {{
                ...commonOptions,
                scales: {{
                    x: {{ stacked: true }},
                    y: {{ stacked: true }}
                }}
            }}
        }});

        // 6. Error Type Breakdown
        new Chart(document.getElementById('errorTypeChart'), {{
            type: 'bar',
            data: {{
                labels: data.error_type_labels || [],
                datasets: [
                    {{
                        label: 'Count',
                        data: data.error_type_values || [],
                        backgroundColor: '#e74c3c',
                        borderRadius: 6
                    }}
                ]
            }},
            options: {{
                ...commonOptions,
                indexAxis: 'y'
            }}
        }});
    </script>
    """
    return page_shell("VinFast Engineering L2 Dashboard", body)


@router.get("/dashboard/l2", response_class=HTMLResponse)
async def dashboard_l2() -> HTMLResponse:
    log_file = Path("data/logs.jsonl")
    if not log_file.exists():
        return HTMLResponse("<div style='padding:50px; text-align:center;'><h2>⚠️ Missing data/logs.jsonl</h2></div>")

    logs = load_logs(log_file)
    data = build_dashboard_data(logs)
    return HTMLResponse(render_l2_html(data))