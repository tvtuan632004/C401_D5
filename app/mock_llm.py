from __future__ import annotations

import random
import time
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

        # ===== EXTRACT CONTEXT FROM RAG =====
        # giả định prompt sẽ có dạng:
        # "Question: ... \n Context: ..."

        if "context:" in prompt_lower:
            context = prompt.split("Context:")[-1].strip()
        else:
            context = ""

        # ===== RESPONSE LOGIC =====

        # Nếu có context → ưu tiên dùng context
        if context and "vinfast" in context.lower():
            answer = f"Dựa trên thông tin tìm được: {context}"

        # So sánh xe
        elif "so sánh" in prompt_lower:
            answer = "Bạn nên so sánh dựa trên giá, tầm hoạt động và phân khúc của từng dòng xe VinFast."

        # Xe chạy xa
        elif "km" in prompt_lower or "xa" in prompt_lower:
            answer = "Bạn nên chọn xe có tầm hoạt động cao như VF8 hoặc VF9 để đi xa."

        # Xe nhỏ gọn
        elif "nhỏ gọn" in prompt_lower or "thành phố" in prompt_lower:
            answer = "VF5 là lựa chọn phù hợp vì là xe điện đô thị nhỏ gọn."

        # fallback
        else:
            answer = "VinFast có nhiều dòng xe như VF5, VF6, VF7, VF8 và VF9 phù hợp nhiều nhu cầu khác nhau."

        return FakeResponse(
            text=answer,
            usage=FakeUsage(input_tokens, output_tokens),
            model=self.model,
        )