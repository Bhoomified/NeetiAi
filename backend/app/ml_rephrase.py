"""
Optional response variety layer — rephrases an ALREADY-FACTUAL template
response for tone variety. Never trusted to generate numbers; if the
rephrase alters any figure, it's discarded and the safe template is used.
"""
import os
import re
from huggingface_hub import InferenceClient

HF_TOKEN = os.getenv("HF_TOKEN")
_client = InferenceClient(token=HF_TOKEN) if HF_TOKEN else None


def safe_rephrase(template_output: str) -> str:
    if _client is None:
        return template_output

    prompt = (
        f"Rephrase this casually in GenZ slang. Keep ALL numbers EXACTLY as written. "
        f"Don't add new facts. One sentence only:\n\n\"{template_output}\""
    )
    try:
        completion = _client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            model="Qwen/Qwen2.5-7B-Instruct",
            max_tokens=40,
            temperature=0.8,
        )
        rephrased = completion.choices[0].message.content.strip()
    except Exception as e:
        print(f"HF rephrase unavailable, using template: {e}")
        return template_output

    original_numbers = set(re.findall(r"\d+", template_output))
    rephrased_numbers = set(re.findall(r"\d+", rephrased))
    if original_numbers != rephrased_numbers:
        return template_output

    return rephrased