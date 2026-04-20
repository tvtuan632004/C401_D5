from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .dashboard_shared import load_logs, build_dashboard_data, page_shell

router = APIRouter()


def render_l1_html(data: dict) -> str:
    s = data.get("summary", {})
    c = data.get("charts", {})

    # Các giá trị mặc định để tránh lỗi NoneType khi render
    total_req = s.get("total_requests", 0)
    err_rate = s.get("error_rate_total", 0)
    avg_qual = s.get("avg_quality", 0)

    # CSS tinh chỉnh hiện đại
    style_extra = """
    <style>
        :root {
            --vin-blue: #1b52d3;
            --vin-dark: #121212;
            --bg-light: #f8f9fa;
            --card-shadow: 0 4px 12px rgba(0,0,0,0.08);
        }
        body { background-color: var(--bg-light); font-family: 'Inter', -apple-system, sans-serif; margin: 0; }
        .dashboard-container { padding: 30px; max-width: 1440px; margin: 0 auto; }
        
        .summary {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: #fff;
            padding: 24px;
            border-radius: 16px;
            box-shadow: var(--card-shadow);
            border-bottom: 4px solid var(--vin-blue);
        }
        .label { color: #7f8c8d; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
        .value { color: var(--vin-dark); font-size: 2rem; font-weight: 800; margin-top: 10px; }

        .grid-2 {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 25px;
        }
        @media (max-width: 1024px) { .grid-2 { grid-template-columns: 1fr; } }

        .card {
            background: #fff;
            padding: 24px;
            border-radius: 16px;
            box-shadow: var(--card-shadow);
            min-height: 20px;
            display: flex;
            flex-direction: column;
        }
        .card h3 {
            margin: 0 0 20px 0;
            font-size: 1.15rem;
            color: #2c3e50;
            font-weight: 700;
        }
        .chart-container { flex-grow: 1; position: relative; width: 100%; }
    </style>
    """

    body = f"""
    {style_extra}
    <div class="dashboard-container">
        <div class="summary">
            <div class="summary-card">
                <div class="label">Total Requests</div>
                <div class="value">{total_req:,}</div>
            </div>
            <div class="summary-card">
                <div class="label">Error Rate</div>
                <div class="value" style="color: {'#e74c3c' if err_rate > 5 else '#27ae60'}">{err_rate:.2f}%</div>
            </div>
            <div class="summary-card">
                <div class="label">Avg Quality Score</div>
                <div class="value">{avg_qual:.3f}</div>
            </div>
        </div>

        <div class="grid-2">
            <div class="card">
                <h3>Traffic vs Error Rate</h3>
                <div class="chart-container"><canvas id="trafficErrorChart"></canvas></div>
            </div>
            <div class="card">
                <h3>Query Intent Breakdown</h3>
                <div class="chart-container"><canvas id="queryTypeChart"></canvas></div>
            </div>
            <div class="card">
                <h3>Top Asked VinFast Models</h3>
                <div class="chart-container"><canvas id="vehicleChart"></canvas></div>
            </div>
            <div class="card">
                <h3>Quality Snapshot</h3>
                <div class="chart-container"><canvas id="qualityOverviewChart"></canvas></div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        // Bảo vệ script nếu data charts bị thiếu
        const data = {json.dumps(c)} || {{}};
        
        const setupChart = (id, config) => {{
            const ctx = document.getElementById(id);
            if (ctx) new Chart(ctx, config);
        }};

        // 1. Traffic vs Error
        setupChart('trafficErrorChart', {{
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
                    tension: 0.4,
                    yAxisID: 'y'
                }},
                {{
                    label: 'Error %',
                    data: data.error_rate || [],
                    borderColor: '#e74c3c',
                    borderDash: [5, 5],
                    tension: 0.4,
                    yAxisID: 'y1'
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    labels: {{
                        usePointStyle: true,
                        pointStyle: 'line'
                    }}
                }}
            }},
            scales: {{
                y: {{ position: 'left' }},
                y1: {{ position: 'right', grid: {{ drawOnChartArea: false }} }}
            }}
        }}
    }});

        // 2. Query Intent
        setupChart('queryTypeChart', {{
            type: 'bar',
            data: {{
                labels: data.query_labels || [],
                datasets: [{{ label: 'Count', data: data.query_values || [], backgroundColor: '#34495e', borderRadius: 8 }}]
            }},
            options: {{ responsive: true, maintainAspectRatio: false }}
        }});

        // 3. Vehicle Models (Xử lý lỗi lấy model xe ở đây)
        setupChart('vehicleChart', {{
            type: 'bar',
            data: {{
                labels: data.vehicle_labels || [],
                datasets: [{{ 
                    label: 'Requests', 
                    data: data.vehicle_values || [], 
                    backgroundColor: '#1b52d3',
                    borderRadius: 8
                }}]
            }},
            options: {{ 
                responsive: true, 
                maintainAspectRatio: false, 
                indexAxis: 'y',
                plugins: {{ legend: {{ display: false }} }}
            }}
        }});

        // 4. Quality
        setupChart('qualityOverviewChart', {{
        type: 'line',
        data: {{
            labels: data.time_labels || [],
            datasets: [
                {{
                    label: 'Avg Quality',
                    data: data.avg_quality || [],
                    borderColor: '#2ecc71',
                    tension: 0.4
                }},
                {{
                    label: 'Low Quality %',
                    data: data.low_quality || [],
                    borderColor: '#f1c40f',
                    tension: 0.4
                }}
            ]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    labels: {{
                        usePointStyle: true,
                        pointStyle: 'line'
                    }}
                }}
            }}
        }}
    }});
    </script>
    """
    return page_shell("VinFast Dashboard L1", body)


@router.get("/dashboard/l1", response_class=HTMLResponse)
async def dashboard_l1() -> HTMLResponse:
    log_file = Path("data/logs.jsonl")
    if not log_file.exists():
        return HTMLResponse("<div style='padding:50px; text-align:center;'><h2>⚠️ Data missing: data/logs.jsonl</h2></div>")

    try:
        logs = load_logs(log_file)
        data = build_dashboard_data(logs)
        # Kiểm tra nếu data['charts'] không có key vehicle_labels
        if "charts" in data and "vehicle_labels" not in data["charts"]:
            data["charts"]["vehicle_labels"] = []
            data["charts"]["vehicle_values"] = []
            
        return HTMLResponse(render_l1_html(data))
    except Exception as e:
        return HTMLResponse(f"<div style='padding:50px;'><h2>❌ Error Processing Data</h2><p>{str(e)}</p></div>")