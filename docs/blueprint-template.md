# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
<<<<<<< HEAD
- [GROUP_NAME]: C401-D4 
- [REPO_URL]: https://github.com/tvtuan632004/C401_D4_Day13
- [MEMBERS]: Hồ Bảo Thư, Trần Văn Tuấn, Lê Đình Việt
  - Member A: [Trần Văn Tuấn] | Role: Logging & PII
  - Member B: [Lê Đình Việt] | Role: Tracing & Enrichment
  - Member B: [Lê Đình Việt] | Role: SLO & Alerts
  - Member A + C: [Hồ Bảo Thư + Trần Văn Tuấn] | Role: Load Test & Dashboard
  - Member C: [Hồ Bảo Thư] | Role: Demo & Report
=======
- [GROUP_NAME]: C401_D4
- [REPO_URL]: https://github.com/tvtuan632004/C401_D4_Day13
- [MEMBERS]:
  - Member A: Trần Văn Tuấn | Role: Logging & PII, Load Test & Dashboard
  - Member B: Lê Đình Việt | Role: Tracing & Enrichment, SLO & Alerts
  - Member C: Hồ Bảo Thư | Role: Load Test & Dashboard, Demo & Report
>>>>>>> dashboard

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
<<<<<<< HEAD
- [TOTAL_TRACES_COUNT]: 
- [PII_LEAKS_FOUND]: 
=======
- [TOTAL_TRACES_COUNT]: 74
- [PII_LEAKS_FOUND]: 0
>>>>>>> dashboard

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: ở folder screenshots  
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: ở folder screenshots     
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: ở folder screenshots    
- [TRACE_WATERFALL_EXPLANATION]: Span ghi nhận quá trình request chạm vào route `/chat`. Bên trong đó có span con là `agent-run` và `llm` thực thi logic nghiệp vụ. Khi request kết liễu, Correlation ID giúp trace nguyên vẹn toàn bộ pipeline.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: ở folder screenshots
- [SLO_TABLE]:
| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | ~150-300ms (Cập nhật từ bảng L1) |
| Error Rate | < 2% | 28d | 0% (Với dữ liệu bình thường) |
| Cost Budget | < $2.5/day | 1d | (Lấy từ số liệu Total Cost Dashboard) |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: ở folder screenshots
- [SAMPLE_RUNBOOK_LINK]: docs/alerts.md#L1

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]: Biểu đồ Latency P50/P95 trên Dashboard L1 tăng vọt (Spike) bất thường.
- [ROOT_CAUSE_PROVED_BY]: Correlation ID (Trace ID) show span `rag` tốn vài giây xử lý thay vì vài milisecond (kết quả từ kịch bản inject_incident).
- [FIX_ACTION]: Chạy script tắt incident (`--disable`) và cập nhật lại tham số timeout giới hạn hệ thống lấy RAG.
- [PREVENTIVE_MEASURE]: Thiết lập Alert Latency khi P95 vượt ngưỡng 5s. Cân nhắc bổ sung cơ chế Caching để chịu tải hoặc Fallback database.

---

## 5. Individual Contributions & Evidence

<<<<<<< HEAD
### [MEMBER_A_NAME]: 
- [TASKS_COMPLETED]: 
- [EVIDENCE_LINK]: (Link to specific commit or PR)

### [MEMBER_B_NAME]: Lê Đình Việt
- [TASKS_COMPLETED]: Tracing & Enrichment + SLO & Alerts
- [EVIDENCE_LINK]: Commit
Author: dviet04 <ledinhviet2507@gmail.com>
Date:   Mon Apr 20 17:28:24 2026 +0700

    update loging to have rag span and llm span

commit 284f2d1e89c04edfbe5c7d0a4d4ed87a90e1a8a3
Author: dviet04 <ledinhviet2507@gmail.com>
Date:   Mon Apr 20 17:07:41 2026 +0700

    update span with rag span, llm span  

commit 0a9f4f3f5e76cd13a7ef0431ae5fabc4b83d3141
Author: dviet04 <ledinhviet2507@gmail.com>
Date:   Mon Apr 20 17:06:00 2026 +0700

    update SLO & Alerts version2

commit 4a8f35bb8a9c9a825965e2a0605e1a6d9538d937
Author: dviet04 <ledinhviet2507@gmail.com>
Date:   Mon Apr 20 16:20:53 2026 +0700

    update agent.py, main.py and tracing.py to implement role: Tracing and Ẻnichment. Version2

=======
### Trần Văn Tuấn
- [TASKS_COMPLETED]: Cấu hình structlog JSON format. Phát triển chức năng filter xoá PII user data trong logs. Hỗ trợ chạy Load Test kích hoạt dữ liệu giả lập.
- [EVIDENCE_LINK]: [Điền link commit GitHub]

### Lê Đình Việt
- [TASKS_COMPLETED]: Setup hệ thống Tracing OpenTelemetry đầy đủ attribute. Viết logic Middleware nhúng Correlation ID theo request xuyên suốt Agent Pipeline. Đề xuất SLO & Docs Alerts.
- [EVIDENCE_LINK]: [Điền link commit GitHub]
>>>>>>> dashboard

### Hồ Bảo Thư
- [TASKS_COMPLETED]: Viết Logic tạo giao diện Dashboard Dashboard (L1, L2, L3) render ra UI cho việc monitor. Thực hiện quá trình Demostration báo cáo Lab, tổng hợp Blueprint Report cuối cùng.
- [EVIDENCE_LINK]: [Điền link commit GitHub]

---

## 6. Bonus Items (Optional)
- [BONUS_COST_OPTIMIZATION]: (Description + Evidence)
- [BONUS_AUDIT_LOGS]: (Description + Evidence)
- [BONUS_CUSTOM_METRIC]: (Description + Evidence)
