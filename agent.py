import os
import json
import google.generativeai as genai
from retriever import get_retriever

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

SYSTEM_PROMPT = """You are an SHL Assessment Recommender. Only recommend SHL assessments from the catalog given to you.
Rules:
1) CLARIFY if query is vague - ask what role they are hiring for. Ask MAX 1 question per turn.
2) RECOMMEND 1-10 assessments when you have enough context. Commit by turn 3-4.
3) REFINE when user changes constraints - update shortlist, do not restart.
4) COMPARE using catalog data only - never make up features.
5) REFUSE off-topic questions politely.
Always return ONLY valid JSON: {"reply": "...", "recommendations": [{"name": "...", "url": "...", "test_type": "..."}], "end_of_conversation": false}
Empty recommendations array when clarifying or refusing. Never invent URLs or assessment names."""

def get_agent_reply(messages):
    retriever = get_retriever()
    query = " ".join([m["content"] for m in messages if m["role"] == "user"][-3:])
    relevant = retriever.retrieve(query, top_k=15)
    catalog_ctx = "AVAILABLE ASSESSMENTS (use ONLY these):\n"
    for a in relevant:
        catalog_ctx += f"- {a['name']} | URL: {a['url']} | Type: {a['test_type']}\n"
    conv = SYSTEM_PROMPT + "\n\n" + catalog_ctx + "\n\nCONVERSATION:\n"
    for m in messages:
        role = "User" if m["role"] == "user" else "Assistant"
        conv += f"{role}: {m['content']}\n"
    conv += "\nAssistant (return JSON only):"
    try:
        resp = model.generate_content(conv)
        raw = resp.text.strip()
        if "```" in raw:
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            raw = raw[start:end]
        result = json.loads(raw)
        if "reply" not in result:
            result["reply"] = "What role are you hiring for?"
        if "recommendations" not in result:
            result["recommendations"] = []
        if "end_of_conversation" not in result:
            result["end_of_conversation"] = False
        valid_urls = {a["url"] for a in retriever.catalog}
        result["recommendations"] = [r for r in result["recommendations"] if r.get("url") in valid_urls][:10]
        return result
    except Exception as e:
        print(f"Agent error: {e}")
        return {"reply": "What role are you hiring for?", "recommendations": [], "end_of_conversation": False}