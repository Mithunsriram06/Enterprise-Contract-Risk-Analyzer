"""
Enterprise Contract Risk Analyzer & Compliance Auditor
=======================================================
A production-ready Streamlit application that authenticates users via Supabase,
ingests PDF/TXT contracts, runs structured AI risk analysis via Google Gemini,
and persists audit history per user.

Environment variables required (see .env.example):
  SUPABASE_URL, SUPABASE_ANON_KEY, GEMINI_API_KEY
"""

import os
import json
import re
import time
import streamlit as st
import pandas as pd

# ── Load .env file for local development ──────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Third-party imports ────────────────────────────────────────────────────────
try:
    from supabase import create_client, Client
except ImportError:
    st.error("Missing dependency: `supabase`. Run `pip install supabase`.")
    st.stop()

try:
    import google.generativeai as genai
except ImportError:
    st.error("Missing dependency: `google-generativeai`. Run `pip install google-generativeai`.")
    st.stop()

try:
    from pypdf import PdfReader
except ImportError:
    st.error("Missing dependency: `pypdf`. Run `pip install pypdf`.")
    st.stop()


# ── Page configuration ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Contract Risk Analyzer",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject Google Font via <link> ─────────────────────────────────────────────
st.markdown(
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">',
    unsafe_allow_html=True,
)

# ── Full UI theme ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Global ── */
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .stApp {
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 40%, #0a1628 70%, #0f0a1e 100%);
        background-attachment: fixed;
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        background:
            radial-gradient(ellipse at 20% 20%, rgba(99,102,241,0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 80% 80%, rgba(139,92,246,0.06) 0%, transparent 50%),
            radial-gradient(ellipse at 60% 10%, rgba(59,130,246,0.05) 0%, transparent 40%);
        pointer-events: none;
        z-index: 0;
    }

    .main .block-container { position: relative; z-index: 1; padding-top: 2rem; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d1117 0%, #0a0e1a 100%) !important;
        border-right: 1px solid rgba(99,102,241,0.2) !important;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div { color: #c9d1d9 !important; }

    [data-testid="stSidebar"] input {
        background: #161b27 !important;
        border: 1px solid rgba(99,102,241,0.35) !important;
        border-radius: 6px !important;
        color: #f0f6fc !important;
        padding: 0.5rem 0.75rem !important;
    }
    [data-testid="stSidebar"] input::placeholder { color: #8b949e !important; opacity: 1 !important; }
    [data-testid="stSidebar"] input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99,102,241,0.15) !important;
    }

    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: opacity 0.2s, transform 0.1s !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        opacity: 0.88 !important;
        transform: translateY(-1px) !important;
    }

    [data-testid="stSidebar"] .stButton:last-of-type > button {
        background: transparent !important;
        border: 1px solid rgba(99,102,241,0.4) !important;
        color: #8b9cf4 !important;
    }

    /* ── Main content text ── */
    h1, h2, h3 { color: #f0f6fc !important; }
    p, li, span { color: #c9d1d9; }

    /* ── Metric cards ── */
    [data-testid="stMetric"] {
        background: rgba(22,27,42,0.85) !important;
        border: 1px solid rgba(99,102,241,0.25) !important;
        border-radius: 12px !important;
        padding: 1.25rem 1.5rem !important;
        backdrop-filter: blur(10px);
    }
    [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.78rem !important; text-transform: uppercase; }
    [data-testid="stMetricValue"] { color: #f0f6fc !important; font-size: 2.2rem !important; font-weight: 700 !important; }

    /* ── Main action button ── */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(99,102,241,0.3) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 6px 20px rgba(99,102,241,0.45) !important;
        transform: translateY(-2px) !important;
    }

    /* ── File uploader ── */
    [data-testid="stFileUploader"] {
        background: rgba(22,27,42,0.6) !important;
        border: 2px dashed rgba(99,102,241,0.35) !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
    }
    [data-testid="stFileUploader"]:hover { border-color: #6366f1 !important; }
    [data-testid="stFileUploader"] * { color: #c9d1d9 !important; }

    /* ── Dataframe / table ── */
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(99,102,241,0.2) !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }

    /* ── Expanders ── */
    [data-testid="stExpander"] {
        background: rgba(22,27,42,0.7) !important;
        border: 1px solid rgba(99,102,241,0.2) !important;
        border-radius: 10px !important;
        backdrop-filter: blur(8px) !important;
        margin-bottom: 0.5rem !important;
    }
    [data-testid="stExpander"] summary { color: #c9d1d9 !important; font-weight: 500 !important; }

    /* ── Section header label ── */
    .section-header {
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #6366f1;
        margin: 1.5rem 0 0.5rem 0;
    }

    /* ── Risk badges ── */
    .badge-high   { background:rgba(239,68,68,0.15);  color:#f87171; border:1px solid rgba(239,68,68,0.4);
                    padding:3px 12px; border-radius:20px; font-size:0.75rem; font-weight:700; }
    .badge-medium { background:rgba(245,158,11,0.15); color:#fbbf24; border:1px solid rgba(245,158,11,0.4);
                    padding:3px 12px; border-radius:20px; font-size:0.75rem; font-weight:700; }
    .badge-low    { background:rgba(34,197,94,0.15);  color:#4ade80; border:1px solid rgba(34,197,94,0.4);
                    padding:3px 12px; border-radius:20px; font-size:0.75rem; font-weight:700; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  CONFIGURATION & CONNECTIONS
# ══════════════════════════════════════════════════════════════════════════════

def _get_secret(key: str) -> str:
    value = os.getenv(key)
    if not value:
        st.error(f"Configuration error: environment variable `{key}` is not set.")
        st.stop()
    return value

@st.cache_resource(show_spinner=False)
def get_supabase_client() -> Client:
    url = _get_secret("SUPABASE_URL")
    key = _get_secret("SUPABASE_ANON_KEY")
    return create_client(url, key)

@st.cache_resource(show_spinner=False)
def configure_gemini() -> genai.GenerativeModel:
    genai.configure(api_key=_get_secret("GEMINI_API_KEY"))
    return genai.GenerativeModel("gemini-2.5-flash")


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

def init_session():
    defaults = {
        "user": None,
        "session": None,
        "analysis": None,
        "doc_name": None,
        "auth_mode": "Login",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ══════════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION LAYER
# ══════════════════════════════════════════════════════════════════════════════

def auth_sidebar(sb: Client):
    st.sidebar.markdown("## Contract Risk Analyzer")
    st.sidebar.markdown('<p class="section-header">Account Access</p>', unsafe_allow_html=True)

    mode = st.sidebar.radio(
        "Action",
        ["Login", "Sign Up"],
        index=0 if st.session_state.auth_mode == "Login" else 1,
        horizontal=True,
        label_visibility="collapsed",
    )
    st.session_state.auth_mode = mode

    email = st.sidebar.text_input("Email address", key="auth_email")
    password = st.sidebar.text_input("Password", type="password", key="auth_password")

    if st.sidebar.button(mode, use_container_width=True):
        if not email or not password:
            st.sidebar.warning("Enter both email and password.")
            return

        try:
            if mode == "Login":
                resp = sb.auth.sign_in_with_password({"email": email, "password": password})
            else:
                resp = sb.auth.sign_up({"email": email, "password": password})

            if resp.user:
                st.session_state.user = resp.user
                st.session_state.session = resp.session
                st.rerun()
            else:
                st.sidebar.error("Authentication failed. Check your credentials.")

        except Exception as exc:
            st.sidebar.error(f"Authentication error: {exc}")

def sidebar_user_info(sb: Client):
    user = st.session_state.user
    st.sidebar.markdown("## Contract Risk Analyzer")
    st.sidebar.markdown('<p class="section-header">Signed In As</p>', unsafe_allow_html=True)
    st.sidebar.code(user.email, language=None)

    if st.sidebar.button("Sign Out", use_container_width=True):
        try:
            sb.auth.sign_out()
        except Exception:
            pass
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
#  DOCUMENT INGESTION
# ══════════════════════════════════════════════════════════════════════════════

MAX_CHARS = 50_000

def extract_text(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    if name.endswith(".txt"):
        raw = uploaded_file.read()
        try:
            text = raw.decode("utf-8").strip()
        except UnicodeDecodeError:
            text = raw.decode("latin-1", errors="replace").strip()
        
        if not text:
            raise ValueError("The uploaded TXT file is empty.")
        return text[:MAX_CHARS]

    if name.endswith(".pdf"):
        try:
            reader = PdfReader(uploaded_file)
            pages = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                pages.append(page_text)
                if sum(len(p) for p in pages) >= MAX_CHARS:
                    break
            combined = "\n".join(pages).strip()
            
            if not combined:
                raise ValueError("No readable text could be extracted. The PDF might be a scanned image.")
            return combined[:MAX_CHARS]
        except Exception as exc:
            raise ValueError(f"PDF extraction failed: {exc}") from exc

    raise ValueError("Unsupported file type. Upload a PDF or TXT file.")


# ══════════════════════════════════════════════════════════════════════════════
#  AI ANALYSIS ENGINE
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """
You are a Senior Commercial Legal Analyst AI specialising in contract risk assessment.
Your task is to audit the provided contract text for commercial vulnerabilities.
Return ONLY a valid JSON object. Do not include any markdown fences or explanations.

{
  "overall_risk_score": <integer 0-100, where 100 is extreme risk>,
  "summary": "<3-5 sentence executive summary of the document's risk exposure>",
  "risks": [
    {
      "clause_name": "<Short name identifying the clause>",
      "severity": "<High | Medium | Low>",
      "extracted_text": "<Exact verbatim text from the contract that creates the risk>",
      "risk_explanation": "<Why this clause leaves the business exposed>",
      "revised_text": "<Recommended legally safer alternative phrasing>"
    }
  ]
}
"""

def run_analysis(model: genai.GenerativeModel, contract_text: str) -> dict:
    if not contract_text.strip():
        raise ValueError("The extracted contract text is empty. Please ensure the file contains readable text.")

    prompt = f"{SYSTEM_PROMPT}\n\n---CONTRACT TEXT START---\n{contract_text}\n---CONTRACT TEXT END---"
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.1,
                max_output_tokens=8192,
                response_mime_type="application/json", # <--- Forces strict JSON response at the API level
            ),
        )
    except Exception as exc:
        raise ValueError(f"Gemini API call failed: {exc}") from exc

    try:
        raw_text = response.text.strip()
    except ValueError as exc:
        raise ValueError("Gemini API blocked the response (likely due to safety filters) or returned empty content.") from exc

    # Isolate the JSON block in case Gemini prepends conversational legal disclaimers
    start_idx = raw_text.find('{')
    end_idx = raw_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1 and end_idx >= start_idx:
        raw_text = raw_text[start_idx:end_idx+1]
    else:
        raise ValueError(f"Gemini did not return a valid JSON structure. Raw output: {raw_text[:200]}")

    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        # If it still fails, print the actual bad output to the UI so we can see exactly what broke it
        raise ValueError(f"Gemini returned non-JSON output. Parse error: {exc}\n\nRaw output was: {raw_text[:200]}...") from exc

    return data


# ══════════════════════════════════════════════════════════════════════════════
#  DATABASE LAYER (Supabase)
# ══════════════════════════════════════════════════════════════════════════════

def save_audit(sb: Client, user_id: str, doc_name: str, risk_score: int, payload: dict):
    try:
        sb.table("contract_logs").insert({
            "user_id": user_id,
            "document_name": doc_name,
            "risk_score": risk_score,
            "analysis_payload": payload,
        }).execute()
    except Exception as exc:
        st.warning(f"Audit log could not be saved: {exc}")

@st.cache_data(ttl=60, show_spinner=False)
def fetch_past_audits(_sb: Client, user_id: str) -> list[dict]:
    try:
        resp = (
            _sb.table("contract_logs")
            .select("id, document_name, risk_score, analysis_payload, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return resp.data or []
    except Exception as exc:
        st.warning(f"Could not retrieve audit history: {exc}")
        return []


# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD RENDERING
# ══════════════════════════════════════════════════════════════════════════════

def severity_badge(level: str) -> str:
    level_lower = level.lower()
    css_class = f"badge-{level_lower}"
    return f'<span class="{css_class}">{level.upper()}</span>'

def score_colour(score: int) -> str:
    if score >= 70: return "#ff4b4b"
    if score >= 40: return "#ffa700"
    return "#21c55d"

def render_dashboard(analysis: dict, doc_name: str):
    score = analysis.get("overall_risk_score", 0)
    summary = analysis.get("summary", "")
    risks = analysis.get("risks", [])

    col_score, col_high, col_med, col_low = st.columns([2, 1, 1, 1])
    high_count = sum(1 for r in risks if r.get("severity", "").lower() == "high")
    medium_count = sum(1 for r in risks if r.get("severity", "").lower() == "medium")
    low_count = sum(1 for r in risks if r.get("severity", "").lower() == "low")

    with col_score:
        st.metric("Overall Risk Score", f"{score} / 100")
        colour = score_colour(score)
        st.markdown(
            f"""
            <div style="background:#1e2130;border-radius:6px;height:10px;margin-top:4px;">
              <div style="background:{colour};width:{score}%;height:10px;border-radius:6px;transition:width 0.6s ease;"></div>
            </div>
            """, unsafe_allow_html=True
        )
    with col_high:
        st.metric("High Severity", high_count)
    with col_med:
        st.metric("Medium Severity", medium_count)
    with col_low:
        st.metric("Low Severity", low_count)

    st.markdown("---")
    st.markdown('<p class="section-header">Executive Summary</p>', unsafe_allow_html=True)
    st.info(summary)

    if not risks:
        st.success("No significant risk clauses were identified in this document.")
        return

    st.markdown('<p class="section-header">Identified Risk Clauses</p>', unsafe_allow_html=True)

    table_rows = []
    for r in risks:
        table_rows.append({
            "Clause": r.get("clause_name", "—"),
            "Severity": r.get("severity", "—"),
            "Exposure": r.get("risk_explanation", "—")[:120] + "…" if len(r.get("risk_explanation", "")) > 120 else r.get("risk_explanation", "—"),
        })

    df = pd.DataFrame(table_rows)

    def style_severity(val):
        colours = {"High": "color:#ff4b4b", "Medium": "color:#ffa700", "Low": "color:#21c55d"}
        return colours.get(val, "")

    styler = df.style
    if hasattr(styler, 'map'):
        styled_df = styler.map(style_severity, subset=["Severity"])
    else:
        styled_df = styler.applymap(style_severity, subset=["Severity"])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    st.markdown('<p class="section-header">Clause Detail & Recommended Revisions</p>', unsafe_allow_html=True)

    for idx, risk in enumerate(risks):
        severity = risk.get("severity", "Unknown")
        clause_name = risk.get("clause_name", f"Clause {idx + 1}")

        with st.expander(f"{clause_name}   —   {severity.upper()}"):
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Extracted Contract Language**")
                st.markdown(
                    f"""
                    <div style="background:#1e1a1a;border-left:3px solid #ff4b4b;padding:1rem;border-radius:4px;font-size:0.88rem;color:#e0e0e0;line-height:1.6;font-style:italic;">
                        {risk.get("extracted_text", "Not available.")}
                    </div>
                    """, unsafe_allow_html=True
                )
                st.markdown("")
                st.markdown("**Risk Explanation**")
                st.markdown(risk.get("risk_explanation", "—"))
            with col_b:
                st.markdown("**Recommended Revision**")
                st.markdown(
                    f"""
                    <div style="background:#0d1f12;border-left:3px solid #21c55d;padding:1rem;border-radius:4px;font-size:0.88rem;color:#e0e0e0;line-height:1.6;">
                        {risk.get("revised_text", "No revision suggested.")}
                    </div>
                    """, unsafe_allow_html=True
                )


def render_past_audits(sb: Client, user_id: str):
    st.markdown('<p class="section-header">Audit History</p>', unsafe_allow_html=True)

    if st.button("Refresh History"):
        fetch_past_audits.clear()
        st.rerun()

    audits = fetch_past_audits(sb, user_id)

    if not audits:
        st.info("No past audits found for your account.")
        return

    for audit in audits:
        created = audit.get("created_at", "")[:19].replace("T", " ")
        score = audit.get("risk_score", "—")
        name = audit.get("document_name", "Unknown document")

        with st.expander(f"{name}   |   Score: {score}   |   {created}"):
            payload = audit.get("analysis_payload")
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    st.error("Stored payload is corrupted.")
                    continue

            if payload:
                if st.button("Load into Dashboard", key=f"load_{audit['id']}"):
                    st.session_state.analysis = payload
                    st.session_state.doc_name = name
                    st.rerun()
                render_dashboard(payload, name)
            else:
                st.warning("No analysis payload found for this audit record.")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN LOOP
# ══════════════════════════════════════════════════════════════════════════════

def main():
    init_session()
    sb = get_supabase_client()
    model = configure_gemini()

    if not st.session_state.user:
        auth_sidebar(sb)
        
        st.markdown("""
        <div style="min-height: 88vh; display: flex; flex-direction: column; justify-content: center; padding: 3rem 1rem 2rem 1rem;">
            <div style="text-align:center; margin-bottom: 3.5rem;">
                <div style="display: inline-block; background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.1)); border: 1px solid rgba(99,102,241,0.3); border-radius: 50px; padding: 6px 20px; margin-bottom: 1.5rem; font-size: 0.75rem; font-weight: 600; color: #a78bfa; letter-spacing: 0.1em; text-transform: uppercase;">AI-Powered Legal Intelligence</div>
                <h1 style="font-size: clamp(2.2rem, 5vw, 3.8rem); font-weight: 800; background: linear-gradient(135deg, #f0f6fc 0%, #a78bfa 50%, #60a5fa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; line-height: 1.15; margin-bottom: 1.2rem; letter-spacing: -0.02em;">Enterprise Contract<br>Risk Analyzer</h1>
                <p style="font-size: 1.1rem; color: #8b949e; max-width: 560px; margin: 0 auto 2rem auto; line-height: 1.7;">Upload any contract and receive a structured commercial risk audit powered by Google Gemini — in seconds, not hours.</p>
                <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(99,102,241,0.1); border: 1px solid rgba(99,102,241,0.25); border-radius: 8px; padding: 10px 20px; font-size: 0.85rem; color: #a78bfa;">Sign in or create a free account in the sidebar to get started</div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem; max-width: 900px; margin: 0 auto 3rem auto; width: 100%;">
                <div style="background: rgba(22,27,42,0.8); border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 1.75rem; backdrop-filter: blur(12px);">
                    <div style="width: 44px; height: 44px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; margin-bottom: 1rem;">&#9878;</div>
                    <div style="font-weight: 700; color: #f0f6fc; margin-bottom: 0.5rem; font-size: 1rem;">AI Risk Analysis</div>
                    <div style="color: #8b949e; font-size: 0.88rem; line-height: 1.6;">Gemini audits every clause for indemnification traps, uncapped liability, and unfair termination terms.</div>
                </div>
                <div style="background: rgba(22,27,42,0.8); border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 1.75rem; backdrop-filter: blur(12px);">
                    <div style="width: 44px; height: 44px; background: linear-gradient(135deg, #f59e0b, #ef4444); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; margin-bottom: 1rem;">&#9888;</div>
                    <div style="font-weight: 700; color: #f0f6fc; margin-bottom: 0.5rem; font-size: 1rem;">Severity Scoring</div>
                    <div style="color: #8b949e; font-size: 0.88rem; line-height: 1.6;">Clauses are ranked High, Medium, and Low severity with revised safe-harbour language generated automatically.</div>
                </div>
                <div style="background: rgba(22,27,42,0.8); border: 1px solid rgba(99,102,241,0.2); border-radius: 16px; padding: 1.75rem; backdrop-filter: blur(12px);">
                    <div style="width: 44px; height: 44px; background: linear-gradient(135deg, #10b981, #0ea5e9); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.3rem; margin-bottom: 1rem;">&#128196;</div>
                    <div style="font-weight: 700; color: #f0f6fc; margin-bottom: 0.5rem; font-size: 1rem;">Persistent Archive</div>
                    <div style="color: #8b949e; font-size: 0.88rem; line-height: 1.6;">Every audit is saved to your account. Reload any past analysis instantly — no extra AI tokens consumed.</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    sidebar_user_info(sb)
    st.sidebar.markdown("---")
    st.sidebar.markdown('<p class="section-header">Navigation</p>', unsafe_allow_html=True)
    page = st.sidebar.radio("Page", ["New Analysis", "Past Audits"], label_visibility="collapsed")
    user_id = st.session_state.user.id

    if page == "New Analysis":
        st.markdown("# New Contract Analysis")
        st.markdown("Upload a PDF or plain-text contract file. The document will be parsed and analysed for commercial risk.")
        st.markdown("---")

        uploaded = st.file_uploader("Select contract file", type=["pdf", "txt"], label_visibility="collapsed")

        if uploaded:
            st.markdown(f"**File:** `{uploaded.name}`")
            if st.button("Run Risk Analysis", type="primary"):
                with st.spinner("Extracting document text…"):
                    try:
                        text = extract_text(uploaded)
                    except ValueError as exc:
                        st.error(str(exc))
                        return
                
                with st.spinner("Running AI compliance audit — this may take 15-30 seconds…"):
                    try:
                        analysis = run_analysis(model, text)
                    except ValueError as exc:
                        st.error(str(exc))
                        return

                st.session_state.analysis = analysis
                st.session_state.doc_name = uploaded.name

                with st.spinner("Saving audit record…"):
                    save_audit(sb, user_id, uploaded.name, analysis.get("overall_risk_score", 0), analysis)
                    fetch_past_audits.clear()

                st.success("Analysis complete. Results saved to your audit archive.")

        if st.session_state.analysis:
            st.markdown("---")
            st.markdown(f"### Audit Results — `{st.session_state.doc_name}`")
            render_dashboard(st.session_state.analysis, st.session_state.doc_name)

    elif page == "Past Audits":
        st.markdown("# Audit Archive")
        st.markdown("All previous contract analyses are listed below. Expand any entry to review the full report or reload it into the dashboard.")
        st.markdown("---")
        render_past_audits(sb, user_id)

if __name__ == "__main__":
    main()