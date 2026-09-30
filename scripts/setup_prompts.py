#!/usr/bin/env python
from __future__ import annotations

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

load_dotenv()

from app.cli import configure_utf8_stdio
from app.tracing import get_langfuse_client, tracing_enabled

configure_utf8_stdio()

PROMPT_NAME = os.getenv("LANGFUSE_PROMPT_NAME", "day13-chat")

V1_TEMPLATE = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}"
V2_TEMPLATE = "Feature={{feature}}\nDocs={{docs}}\nQuestion={{message}}\nInstruction: Provide an accurate, concise answer under 3 sentences."


def setup_prompts() -> None:
    if not tracing_enabled():
        print("[!] LANGFUSE_PUBLIC_KEY hoặc LANGFUSE_SECRET_KEY chưa được đặt trong .env.")
        print("    Vui lòng tạo project day13-k4-l3a-<MSSV> trên cloud.langfuse.com và điền key vào .env.")
        return

    client = get_langfuse_client()
    print(f"[*] Đang kết nối Langfuse Cloud: {os.getenv('LANGFUSE_BASE_URL')}...")

    # 1. Tạo hoặc cập nhật Version 1
    print(f"[*] Tạo Version 1 cho prompt '{PROMPT_NAME}'...")
    try:
        p1 = client.create_prompt(
            name=PROMPT_NAME,
            prompt=V1_TEMPLATE,
            type="text",
            labels=["baseline", "production"],
        )
        print(f"    [OK] Tạo Version 1 thành công (version={getattr(p1, 'version', 1)}, labels=['baseline', 'production'])")
    except Exception as e:
        print(f"    [INFO] {e}")

    # 2. Tạo Version 2 với label 'candidate'
    print(f"[*] Tạo Version 2 cho prompt '{PROMPT_NAME}'...")
    try:
        p2 = client.create_prompt(
            name=PROMPT_NAME,
            prompt=V2_TEMPLATE,
            type="text",
            labels=["candidate"],
        )
        print(f"    [OK] Tạo Version 2 thành công (version={getattr(p2, 'version', 2)}, labels=['candidate'])")
    except Exception as e:
        print(f"    [INFO] {e}")

    print("\n[OK] Đã cấu hình xong Prompts trên Langfuse!")
    print(f"     - v1 (baseline, production)")
    print(f"     - v2 (candidate)")
    print("     Bạn có thể xem trực tiếp tại mục 'Prompts' trên dashboard Langfuse.")


if __name__ == "__main__":
    setup_prompts()
