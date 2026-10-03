import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import requests
from src.config import LLM_PROVIDER, LLM_API_KEY, LLM_MODEL

logger = logging.getLogger("llm_client")

REPORT_TIMEOUT = 30
CHAT_TIMEOUT = 25

GENERIC_IMMEDIATE = [
    "Isolate or closely monitor the affected plants and avoid handling healthy plants right after touching sick ones.",
    "Remove and bag heavily affected leaves; do not compost them.",
    "Keep foliage dry: water at the base, early in the day, and avoid overhead irrigation.",
]
GENERIC_PREVENTION = [
    "Rotate crops and avoid planting the same family in the same spot in consecutive seasons.",
    "Use certified, disease-free seed or transplants and resistant varieties where available.",
    "Space plants for airflow and clean tools between plants.",
]
GENERIC_IPM = [
    "Scout fields or plants at least twice a week and note any change with dated photos.",
    "Combine cultural, biological and (only if needed) chemical measures, starting with the least harmful.",
]


def _bullets(items: List[str], limit: int = 6) -> str:
    return "\n".join(f"- {str(i).strip()}" for i in (items or [])[:limit] if str(i).strip())


class LLMClient:
    """
    Configurable LLM Client with strict grounding and fallback capabilities.
    Instances are stateless (safe to share between sessions).
    """
    def __init__(self, provider: str = LLM_PROVIDER, api_key: Optional[str] = LLM_API_KEY, model: str = LLM_MODEL):
        self.provider = (provider or "fallback").lower()
        self.api_key = api_key
        self.model = model

    # ------------------------------------------------------------------ status
    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 5 and self.provider in ("gemini", "openai"))

    def describe(self) -> Dict[str, Any]:
        """Non-secret summary for the Settings page."""
        return {
            "provider": self.provider if self.is_configured() else "built-in",
            "model": self.model if self.is_configured() else "Grounded knowledge assistant",
            "configured": self.is_configured(),
            "key_present": bool(self.api_key and self.api_key.strip()),
        }

    # ------------------------------------------------------------------ report
    def generate_report(self, workflow_state: Dict[str, Any]) -> str:
        """Generates a structured crop health analysis report."""
        if self.is_configured():
            try:
                if self.provider == "gemini":
                    return self._call_gemini_api(workflow_state)
                if self.provider == "openai":
                    return self._call_openai_api(workflow_state)
            except Exception as e:
                logger.error("%s report call failed, using grounded template engine: %s", self.provider, e)
        return self._generate_grounded_fallback_report(workflow_state)

    # ------------------------------------------------------------------ chat
    def generate_chat_response(self, prompt: str, session_context: Dict[str, Any], history: List[Dict[str, str]]) -> str:
        """Backward compatible wrapper returning only the answer text."""
        return self.chat(prompt, session_context, history)[0]

    def chat(self, prompt: str, session_context: Dict[str, Any], history: List[Dict[str, str]]) -> Tuple[str, str]:
        """Return (answer, source) where source is 'gemini', 'openai' or 'built-in'."""
        ctx = session_context or {}
        system_instruction = self._chat_system_prompt(ctx)
        if self.is_configured():
            try:
                if self.provider == "gemini":
                    return self._call_gemini_chat(system_instruction, prompt, history), "gemini"
                if self.provider == "openai":
                    return self._call_openai_chat(system_instruction, prompt, history), "openai"
            except Exception as e:
                logger.error("LLM chat API call failed (%s): %s", self.provider, e)
        return self._generate_grounded_chat_fallback(prompt, ctx), "built-in"

    @staticmethod
    def _chat_system_prompt(ctx: Dict[str, Any]) -> str:
        crop = ctx.get("crop") or "the crop"
        evidence = ctx.get("retrieved_evidence") or []
        sources = "\n".join(
            f"- {ev.get('title', '')}: {((ev.get('raw_record') or {}).get('content') or ev.get('content') or ev.get('text') or '')[:300]}"
            for ev in evidence[:2]
        )
        return (
            f"You are the Crop Health Analyzer assistant helping a farmer or gardener with {crop}.\n"
            "Current assessment context:\n"
            f"- Crop: {crop}\n"
            f"- Possible condition: {ctx.get('result_condition') or 'none yet'}\n"
            f"- Evidence level: {ctx.get('evidence_level') or 'unknown'}\n"
            f"- Severity: {ctx.get('severity') or 'unknown'}\n"
            f"- Reported symptoms: {ctx.get('symptoms') or 'none provided'}\n"
            f"Grounded knowledge sources:\n{sources or '- none retrieved'}\n\n"
            "Rules:\n"
            "1. Be helpful, clear and concise (under 200 words unless asked for more).\n"
            "2. Prefer Integrated Pest Management (IPM): cultural, biological, then chemical measures.\n"
            "3. Do NOT invent pesticide products, doses or application rates; tell the user to follow the registered label.\n"
            "4. Say when you are unsure, and recommend a local agricultural extension officer for severe or unclear cases.\n"
            "5. This is decision support, not a laboratory diagnosis."
        )

    # ------------------------------------------------------------------ prompt payloads
    @staticmethod
    def _compact_state(state: Dict[str, Any]) -> Dict[str, Any]:
        """Small, JSON-safe view of the workflow state (no image bytes, no duplicated chunk text)."""
        vision = state.get("vision_result") or {}
        evidence = []
        for ev in (state.get("retrieved_evidence") or [])[:4]:
            rec = ev.get("raw_record") or {}
            evidence.append({
                "title": ev.get("title"), "source": ev.get("source"), "condition": ev.get("condition"),
                "url": ev.get("url"), "summary": str(rec.get("content") or ev.get("text") or "")[:500],
            })
        return {
            "crop": state.get("crop"),
            "input_mode": state.get("input_mode"),
            "reported_symptoms": state.get("symptoms"),
            "symptom_analysis": state.get("symptom_result"),
            "vision": {
                "available": vision.get("available"), "mode": vision.get("mode"),
                "top_prediction": vision.get("top_prediction"), "predictions": (vision.get("predictions") or [])[:3],
            },
            "evidence_fusion": state.get("evidence_fusion"),
            "risk_assessment": state.get("risk_assessment"),
            "management_guidance": state.get("management_guidance"),
            "safety_notes": (state.get("safety_result") or {}).get("safety_notes"),
            "retrieved_evidence": evidence,
        }

    def _report_prompt(self, state: Dict[str, Any]) -> str:
        return (
            "Generate a professional, structured agricultural crop health report based STRICTLY on the following JSON.\n"
            "Do not invent diseases, products, doses or sources that are not in the JSON. "
            "Where evidence is limited, say so plainly.\n\n"
            f"{json.dumps(self._compact_state(state), indent=2, default=str)}\n\n"
            "Use markdown headers for: Possible Condition, Observed Symptoms, Evidence Level & Uncertainty, Severity, "
            "Evidence & Sources, Immediate Actions, IPM & Prevention, Treatment Information, and Safety Precautions. "
            "Start with a level-1 header containing the words 'Crop Health Analyzer'."
        )

    # ------------------------------------------------------------------ providers
    def _call_gemini_api(self, state: Dict[str, Any]) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        payload = {"contents": [{"role": "user", "parts": [{"text": self._report_prompt(state)}]}]}
        res = requests.post(url, headers=headers, json=payload, timeout=REPORT_TIMEOUT)
        if res.status_code == 200:
            return self._extract_gemini_text(res.json())
        raise RuntimeError(f"Gemini API returned status {res.status_code}")

    def _call_openai_api(self, state: Dict[str, Any]) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        payload = {
            "model": self.model or "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You are an agricultural specialist who grounds every recommendation in the provided evidence."},
                {"role": "user", "content": self._report_prompt(state)},
            ],
        }
        res = requests.post(url, headers=headers, json=payload, timeout=REPORT_TIMEOUT)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        raise RuntimeError(f"OpenAI API status {res.status_code}")

    @staticmethod
    def _extract_gemini_text(data: Dict[str, Any]) -> str:
        parts = data["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
        if not text:
            raise RuntimeError("Gemini returned an empty response")
        return text

    @staticmethod
    def _clean_history(history: List[Dict[str, str]], prompt: str) -> List[Dict[str, str]]:
        """Last 10 turns, without the current prompt if the caller already appended it."""
        msgs = [m for m in (history or []) if m.get("role") in ("user", "assistant") and str(m.get("content", "")).strip()]
        if msgs and msgs[-1].get("role") == "user" and str(msgs[-1].get("content")).strip() == prompt.strip():
            msgs = msgs[:-1]
        return msgs[-10:]

    def _call_gemini_chat(self, system: str, prompt: str, history: List[Dict[str, str]]) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        headers = {"Content-Type": "application/json", "x-goog-api-key": self.api_key}
        contents: List[Dict[str, Any]] = []
        for m in self._clean_history(history, prompt):
            role = "model" if m["role"] == "assistant" else "user"
            text = str(m["content"]).strip()
            if contents and contents[-1]["role"] == role:
                contents[-1]["parts"][0]["text"] += "\n" + text
            elif contents or role == "user":      # Gemini requires the first turn to be from the user
                contents.append({"role": role, "parts": [{"text": text}]})
        if contents and contents[-1]["role"] == "user":
            contents[-1]["parts"][0]["text"] += "\n" + prompt
        else:
            contents.append({"role": "user", "parts": [{"text": prompt}]})
        payload = {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents}
        res = requests.post(url, headers=headers, json=payload, timeout=CHAT_TIMEOUT)
        if res.status_code == 200:
            return self._extract_gemini_text(res.json())
        raise RuntimeError(f"Gemini chat error {res.status_code}")

    def _call_openai_chat(self, system: str, prompt: str, history: List[Dict[str, str]]) -> str:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {self.api_key}"}
        messages = [{"role": "system", "content": system}]
        messages += [{"role": m["role"], "content": str(m["content"])} for m in self._clean_history(history, prompt)]
        messages.append({"role": "user", "content": prompt})
        res = requests.post(url, headers=headers, json={"model": self.model or "gpt-4o-mini", "messages": messages}, timeout=CHAT_TIMEOUT)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        raise RuntimeError(f"OpenAI chat error {res.status_code}")

    # ------------------------------------------------------------------ grounded fallbacks
    def _generate_grounded_fallback_report(self, state: Dict[str, Any]) -> str:
        crop = state.get("crop", "Crop")
        fusion = state.get("evidence_fusion", {})
        condition = fusion.get("top_condition", "Condition Analysis Pending")
        severity = state.get("risk_assessment", {}).get("severity", "Moderate")
        level = fusion.get("evidence_level") or fusion.get("uncertainty") or "Insufficient evidence"
        symptoms = state.get("symptom_result", {}).get("observed_symptoms", [])
        evidence = state.get("retrieved_evidence", [])
        management = state.get("management_guidance", {})
        safety_notes = state.get("safety_result", {}).get("safety_notes", [])

        symptoms_str = _bullets(symptoms) or "- Symptoms specified in input analysis."

        sources_str = ""
        for ev in evidence[:3]:
            sources_str += f"\n- **{ev.get('title', 'Agricultural Record')}** ({ev.get('source', 'Extension Service')})"
            if ev.get("url"):
                sources_str += f" — {ev['url']}"

        immediate = _bullets(management.get("immediate_actions", []))
        ipm = _bullets(management.get("ipm", []))
        prevention = _bullets(management.get("prevention", []))
        biological = _bullets(management.get("biological_controls", []))
        treatments = _bullets(management.get("treatment_information", []))
        safety_str = _bullets(safety_notes, limit=10)

        return f"""# 🌾 Crop Health Analyzer — Crop Health Assessment

**Crop:** {crop}  
**Possible condition:** {condition}  
**Assessed severity:** {severity}  
**Evidence level:** {level}

---

### 🔍 Observed Symptoms
{symptoms_str}

---

### 🛡️ Immediate Actions
{immediate or "- Inspect the plant canopy closely and isolate suspicious foliage."}

---

### 🌿 Integrated Pest Management (IPM) & Prevention
{ipm or "- Practice regular crop rotation and soil sanitation."}

**Long-term prevention**
{prevention or "- Ensure proper spacing and avoid overhead irrigation."}

---

### 🧪 Biological Options & Treatment Information
{biological or "- Biological products such as *Bacillus subtilis* may help where registered locally."}

**Treatment information**
{treatments or "- No chemical treatment information was retrieved. Verify any product locally before use."}

---

### 📚 Evidence & Sources
{sources_str or "Grounding from FAO and agricultural extension knowledge records."}

---

### ⚠️ Safety Precautions & Limitations
{safety_str}

- **Professional escalation:** if symptoms persist or worsen rapidly, consult a local agricultural extension officer.
"""

    # --- offline assistant -------------------------------------------------------------------
    _INTENTS: List[Tuple[str, str]] = [
        ("greeting", r"^\s*(hi|hello|hey|salam|assalam|good (morning|afternoon|evening))\b"),
        ("thanks", r"\b(thanks|thank you|thx|shukriya)\b"),
        ("treatment", r"\b(chemical|fungicide|pesticide|insecticide|spray|treatment|medicine|dose|dosage|how much|product|copper)\b"),
        ("organic", r"\b(organic|natural|bio\w*|non[- ]chemical|home remed\w*|eco)\b"),
        ("prevent", r"\b(prevent\w*|avoid|future|next (season|year|time)|rotation|stop it|recur\w*|come back)\b"),
        ("spread", r"\b(spread\w*|contagious|infect\w*|other plants|neighbou?r\w*|nearby|catching)\b"),
        ("why", r"\b(why|reason|sure|certain|confiden\w*|accura\w*|trust|how do you know|evidence|basis)\b"),
        ("severity", r"\b(serious|severe|severity|dangerous|how bad|worried|die|dying|save|urgent|emergency)\b"),
        ("expert", r"\b(expert|professional|extension|lab|laborator\w*|agronomist|specialist|officer)\b"),
        ("photo", r"\b(photo|picture|image|camera|retake)\b"),
        ("water", r"\b(water\w*|irrigat\w*|rain|humid\w*)\b"),
        ("nutrition", r"\b(fertili[sz]\w*|nitrogen|nutrient\w*|manure|compost)\b"),
        ("harvest", r"\b(eat|edible|harvest\w*|consume|safe to|wash)\b"),
        ("first", r"\b(first|immediately|right now|what (should|can|do) i|next step|action|do now|start)\b"),
        ("describe", r"\b(what is|tell me about|explain|cause\w*|symptom\w*|signs?|look like|identify)\b"),
    ]

    def _detect_intent(self, prompt: str) -> str:
        for name, rx in self._INTENTS:
            if re.search(rx, prompt, re.I):
                return name
        return "general"

    def _generate_grounded_chat_fallback(self, prompt: str, ctx: Dict[str, Any]) -> str:
        crop = ctx.get("crop") or ""
        condition = ctx.get("result_condition") or ""
        has_analysis = bool(ctx.get("has_analysis") or (condition and condition.lower() not in ("unknown", "")))
        mg = ctx.get("management_guidance") or {}
        severity = ctx.get("severity") or "Unknown"
        level = ctx.get("evidence_level") or "Insufficient evidence"
        evidence = ctx.get("retrieved_evidence") or []
        record = (evidence[0].get("raw_record") if evidence and isinstance(evidence[0], dict) else None) or {}
        label = f"**{condition}** in {crop}" if has_analysis and crop else "your crop"
        intent = self._detect_intent(prompt)

        immediate = mg.get("immediate_actions") or record.get("immediate_actions") or GENERIC_IMMEDIATE
        prevention = mg.get("prevention") or record.get("prevention") or GENERIC_PREVENTION
        ipm = mg.get("ipm") or record.get("ipm") or GENERIC_IPM
        bio = mg.get("biological_controls") or record.get("biological_controls") or []
        treatments = mg.get("treatment_information") or record.get("verified_treatments") or []

        verify = "\n\n*Always follow the product label, check that it is registered for your crop locally, and respect PHI/REI intervals.*"
        no_analysis_hint = "" if has_analysis else "\n\n*Tip: run an assessment on the Analyze page so I can tailor this to your crop's symptoms and photos.*"

        if intent == "greeting":
            if has_analysis:
                return f"Hello! I'm looking at your latest assessment: {label} (evidence: {level.lower()}). Ask me what to do first, how to prevent it, organic options, or how serious it is."
            return "Hello! I'm your crop health assistant. Run an assessment on the **Analyze** page, or ask me a general question about plant diseases, prevention or IPM."
        if intent == "thanks":
            return "You're welcome! Keep scouting regularly and take dated photos so you can track whether things improve. Ask me anything else."
        if intent == "first":
            return f"For {label}, start here:\n\n{_bullets(immediate, 5)}{no_analysis_hint}"
        if intent == "spread":
            extra = ["Most leaf diseases travel on water splash, wind, tools and hands — disinfect tools and wash hands after handling affected plants.",
                     "Keep a few metres between affected and healthy plants if you can, and check neighbours every 2–3 days."]
            return f"Whether {label} spreads depends on weather (warm, wet and humid conditions speed it up).\n\n{_bullets(extra)}\n\nAlso:\n{_bullets(immediate, 3)}{no_analysis_hint}"
        if intent == "prevent":
            return f"To prevent {label} from coming back:\n\n{_bullets(list(prevention) + list(ipm), 7)}{no_analysis_hint}"
        if intent == "organic":
            options = list(bio) or ["Cultural controls come first: remove infected tissue, improve airflow, water at the base."]
            return f"Lower-impact options for {label}:\n\n{_bullets(options + list(ipm), 6)}\n\n*Biological and organic products also need to be registered for your crop and used per the label.*{no_analysis_hint}"
        if intent == "treatment":
            if treatments:
                return f"Treatment information on record for {label}:\n\n{_bullets(treatments, 6)}\n\nTry the IPM steps first where possible. I can't give doses — they depend on the product and local rules.{verify}"
            return f"I don't have verified chemical treatment information on record for {label}, so I won't guess a product or dose. Focus on the IPM steps (sanitation, airflow, dry foliage) and ask your local agricultural extension office which registered products suit your situation.{verify}"
        if intent == "why":
            if not has_analysis:
                return "I don't have an assessment yet, so there is nothing to explain. Run one on the **Analyze** page — I will then show the evidence behind the result."
            symptoms = ctx.get("symptoms") or "the information you provided"
            return (f"The assessment of {label} has **{level.lower()}**. It is based on matching your reported symptoms ({symptoms[:200]}) "
                    "and any photo features against the agricultural knowledge records, not on laboratory testing. "
                    "Similar diseases can look alike, so adding clearer close-up photos or more symptom details can improve it.")
        if intent == "severity":
            note = {"High": "This looks **high priority**: act soon and consider professional advice.",
                    "Moderate": "This looks **moderate**: act in the next few days and keep monitoring.",
                    "Low": "This looks **low risk** right now: keep monitoring.",
                    }.get(severity, "I can't judge severity reliably from the information available.")
            return f"For {label}: {note}\n\nFirst steps:\n{_bullets(immediate, 3)}\n\n*Severity here means urgency, not a laboratory result.*{no_analysis_hint}"
        if intent == "expert":
            return ("Contact a local agricultural extension officer or plant clinic if: symptoms spread quickly, many plants are affected, "
                    "the result here shows limited evidence, you grow for sale, or you are considering a chemical spray. "
                    "Bring dated photos of leaves, stems and the whole plant." + no_analysis_hint)
        if intent == "photo":
            return ("For a useful photo: use natural daylight, keep the leaf in sharp focus about 20–30 cm away, include both affected and healthy tissue, "
                    "and add one whole-plant shot. Avoid flash glare and shadows. Up to 4 photos can be added on the Analyze page.")
        if intent == "water":
            return "Water at the base of the plant, early in the day so foliage dries quickly, and avoid overhead sprinklers. Drip or furrow irrigation lowers leaf wetness, which many fungal and bacterial diseases need." + no_analysis_hint
        if intent == "nutrition":
            return "Balanced nutrition helps plants tolerate disease. Avoid excess nitrogen (it produces soft, susceptible growth) and don't apply extra fertiliser to a plant that is stressed by disease or waterlogging. A soil test is the best guide." + no_analysis_hint
        if intent == "harvest":
            return ("Remove and discard diseased fruit or leaves, harvest healthy produce and wash it. If you have sprayed anything, wait for the pre-harvest interval (PHI) on the label before harvesting. "
                    "Some conditions only affect leaves while others can affect fruit — check the specific condition with your local extension service." + no_analysis_hint)
        if intent == "describe":
            if record:
                content = str(record.get("content", ""))[:600]
                syms = ", ".join(record.get("symptoms") or [])
                return f"**{record.get('title', condition)}**\n\n{content}\n\n**Typical signs:** {syms or 'see the assessment details.'}"
            found = self._lookup_kb(prompt, crop)
            if found:
                return found

        # general / unknown intent
        if has_analysis:
            return (f"Here's where things stand for {label}: evidence level **{level.lower()}**, severity **{severity.lower()}**.\n\n"
                    f"Good next steps:\n{_bullets(immediate, 3)}\n\nYou can ask me about prevention, organic options, treatment information, spread, or when to call an expert.")
        found = self._lookup_kb(prompt, crop)
        if found:
            return found
        return ("I can help with crop diseases, prevention and IPM. Try asking things like *“How do I prevent early blight?”*, *“What are organic options for powdery mildew?”* "
                "or run an assessment on the **Analyze** page for guidance tailored to your plant.")

    @staticmethod
    def _lookup_kb(prompt: str, crop: str = "") -> str:
        """Answer from the local knowledge base when no assessment is available."""
        try:
            from src.rag.retriever import retrieve_agricultural_evidence
            results = retrieve_agricultural_evidence(crop=crop or "", symptoms=prompt, top_k=1)
        except Exception as exc:                       # retrieval must never break the chat
            logger.warning("Knowledge lookup failed: %s", exc)
            return ""
        if not results or results[0].get("score", 0) < 0.12:
            return ""
        rec = results[0].get("raw_record") or {}
        syms = ", ".join(rec.get("symptoms") or [])
        ipm = _bullets(rec.get("ipm") or [], 3)
        return (f"From the knowledge base — **{rec.get('title', 'Related condition')}**\n\n{str(rec.get('content', ''))[:500]}\n\n"
                f"**Typical signs:** {syms or '—'}\n\n**IPM steps:**\n{ipm or '- See Learn → Disease library.'}\n\n*Source: {rec.get('source', 'Agricultural extension knowledge base')}.*")
