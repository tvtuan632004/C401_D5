from __future__ import annotations

import random
import time
import re
from dataclasses import dataclass

from .incidents import STATE


@dataclass
class FakeUsage:
    input_tokens: int
    output_tokens: int


@dataclass
class FakeResponse:
    text: str
    usage: FakeUsage
    model: str


class FakeLLM:
    def __init__(self, model: str = "vinfast-assistant-v1") -> None:
        self.model = model

    def generate(self, prompt: str) -> FakeResponse:
        time.sleep(0.15)

        input_tokens = max(20, len(prompt) // 4)
        output_tokens = random.randint(80, 150)

        if STATE["cost_spike"]:
            output_tokens *= 4

        prompt_lower = prompt.lower()

        # ===== EXTRACT CONTEXT =====
        if "context:" in prompt_lower:
            context = prompt.split("Context:")[-1].strip()
        else:
            context = ""

        # ===== DETECT MODELS =====
        matches = re.findall(r"vf\s?\d+", prompt_lower)
        models = list(set([m.replace(" ", "") for m in matches]))

        # ===== DETECT INTENT =====
        if "so sánh" in prompt_lower or "khác nhau" in prompt_lower:
            intent = "compare"
        elif any(x in prompt_lower for x in ["nên chọn", "tư vấn", "phù hợp", "xe nào", "gợi ý"]):
            intent = "recommend"
        else:
            intent = "qa"

        # ===== LOGIC =====

        # -------- COMPARE --------
        if intent == "compare" and len(models) >= 2:
            if context:
                parts = context.split("\n")
                answer = "So sánh các xe VinFast:\n"
                for p in parts:
                    answer += f"- {p}\n"
            else:
                answer = "Bạn có thể so sánh các xe dựa trên giá, tầm hoạt động và phân khúc."

        # -------- QA --------
        elif intent == "qa" and len(models) == 1:
            if context:
                answer = f"Thông tin chi tiết:\n{context}"
            else:
                answer = f"Chưa có dữ liệu chi tiết cho {models[0].upper()}."

        # -------- RECOMMEND --------
        elif intent == "recommend":
            if "nhỏ gọn" in prompt_lower or "thành phố" in prompt_lower:
                answer = "Bạn nên chọn VinFast VF5 vì đây là xe điện nhỏ gọn, phù hợp di chuyển trong thành phố."
            elif "gia đình" in prompt_lower:
                answer = "Bạn có thể chọn VF6 hoặc VF8 vì phù hợp cho gia đình với không gian rộng rãi."
            elif "chạy xa" in prompt_lower or "km" in prompt_lower:
                answer = "VF9 là lựa chọn tốt nhất vì có tầm hoạt động lên đến 594 km."
            elif "giá rẻ" in prompt_lower:
                answer = "VF5 là mẫu xe có giá thấp nhất trong các dòng SUV VinFast hiện tại."
            elif "700" in prompt_lower:
                answer = "VF6 là lựa chọn phù hợp trong tầm giá khoảng 675 triệu."
            else:
                answer = "Bạn có thể cân nhắc VF5, VF6 hoặc VF7 tùy theo nhu cầu sử dụng."

        # -------- FALLBACK --------
        else:
            answer = "Hiện tại tôi chưa hỗ trợ câu hỏi này. Vui lòng hỏi về các dòng xe VinFast như VF5, VF6, VF7."

        return FakeResponse(
            text=answer,
            usage=FakeUsage(input_tokens, output_tokens),
            model=self.model,
        )