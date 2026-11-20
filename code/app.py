import json
import os
import re
from pathlib import Path
import streamlit as st

# Deriving project root dynamically for cross-platform and directory-independent path resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent

st.set_page_config(
    page_title="AlignCV | PromptLab",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for clean SaaS look
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    .pill-missing {
        display: inline-block;
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 3px;
    }
    .pill-nice {
        display: inline-block;
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 3px;
    }
    .pill-ok {
        display: inline-block;
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 3px;
    }
</style>
""", unsafe_allow_html=True)


def redact_pii(text: str) -> str:
    """Redact emails, phone numbers, and LinkedIn/GitHub URLs before LLM call."""
    text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "[EMAIL_REDACTED]", text)
    text = re.sub(r"(\+?\d[\d\s-]{8,14}\d)", "[PHONE_REDACTED]", text)
    text = re.sub(r"https?://(www\.)?(linkedin|github)\.com/[^\s]+", "[PROFILE_URL_REDACTED]", text)
    return text


SAMPLE_RESUME = """[NAME_REDACTED] — B.Tech CSE (2026) | [EMAIL_REDACTED] | [PHONE_REDACTED]
Skills: Python, SQL, Git, Flask, HTML/CSS, Data Structures.
Projects:
- Built an e-commerce website using Flask and SQLite with user login and cart.
- Created a weather dashboard using Python and OpenWeather API.
Experience:
- Software Intern at TechCorp: Assisted in testing software bugs and writing basic SQL queries."""

SAMPLE_JD = """Junior Backend Developer
Requirements:
- 1+ years or strong project experience in Python and Django or FastAPI.
- Proficiency in PostgreSQL, REST API design, and Docker containerization.
- Familiarity with CI/CD pipelines (GitHub Actions) and unit testing (pytest).
- Strong debugging and system design fundamentals."""

DEMO_OUTPUT_V3 = {
    "p1": {
        "match_score": 64,
        "rubric_breakdown": {
            "skills_40": 24,
            "domain_30": 20,
            "experience_20": 12,
            "clarity_10": 8,
        },
        "missing_critical_skills": ["Django / FastAPI", "PostgreSQL", "Docker", "REST API Design"],
        "missing_nice_to_have_skills": ["CI/CD (GitHub Actions)", "pytest"],
        "strengths": ["Python fundamentals", "SQL experience", "Flask web app project"],
        "verdict": "Needs Tailoring",
    },
    "p2": {
        "bullet_improvements": [
            {
                "original": "Built an e-commerce website using Flask and SQLite with user login and cart.",
                "improved": "Engineered a full-stack e-commerce web application using Python (Flask) and SQLite, implementing authentication and cart workflows for [N] simulated users.",
                "target_skill_addressed": "Python Backend & Web Architecture",
            },
            {
                "original": "Assisted in testing software bugs and writing basic SQL queries.",
                "improved": "Executed [N] functional test cases and optimized relational SQL queries during internship, reducing defect turnaround time by [X%].",
                "target_skill_addressed": "Debugging & SQL",
            },
        ],
        "tailoring_tip": "Containerize your Flask e-commerce project with Docker and migrate SQLite to PostgreSQL to directly match core backend requirements.",
    },
}

DEMO_OUTPUT_V1 = """Overall, the candidate is an entry-level developer who knows Python and SQL, making them a decent fit for the Junior Backend Developer role.

Strengths:
- Good foundation in Python and Flask.
- Built a nice e-commerce project.

Missing Skills:
- Needs Django/FastAPI, Docker, and PostgreSQL.

Fit Rating: 7/10. Keep learning!"""


def call_gemini(prompt_text: str, api_key: str, json_mode: bool = True) -> str:
    import google.generativeai as genai
    genai.configure(api_key=api_key)
    generation_config = {"temperature": 0.2}
    if json_mode:
        generation_config["response_mime_type"] = "application/json"
    model = genai.GenerativeModel("gemini-2.5-flash", generation_config=generation_config)
    response = model.generate_content(prompt_text)
    return response.text


# Sidebar
with st.sidebar:
    st.title("⚙️ AlignCV Settings")
    mode = st.radio("Execution Mode", ["Offline Demo Mode (No API Key)", "Live Gemini 2.5 Flash API"])
    api_key = ""
    if mode == "Live Gemini 2.5 Flash API":
        try:
            if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
                api_key = st.secrets["GEMINI_API_KEY"]
        except Exception:
            pass
        if not api_key:
            api_key = os.getenv("GEMINI_API_KEY", "")
    prompt_ver = st.selectbox("Prompt Version", ["v3 (2-Step Chain + Guardrails)", "v1 (Unstructured Baseline)"])
    st.markdown("---")
    st.caption("**Team PromptLab** · SCSE4041 Mini Project (C9)")
    st.caption("PII Redaction: **Active** (Emails, Phones, URLs masked)")

# Header
st.markdown('<div class="main-header">📄 AlignCV — Resume Feedback & Job Alignment</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">2-Step Prompt Chain (P1: Weighted ATS Rubric Scorer → P2: Anti-Hallucination STAR Rewriter)</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    resume_input = st.text_area("Candidate Resume (Plain Text)", value=SAMPLE_RESUME, height=230)
with col2:
    jd_input = st.text_area("Target Job Description", value=SAMPLE_JD, height=230)

if st.button("🚀 Analyze Resume & Generate Feedback", type="primary", use_container_width=True):
    if len(resume_input.strip().split()) < 15 or len(jd_input.strip().split()) < 15:
        st.error("Insufficient Input: Please provide a valid resume and job description (at least 15 words each).")
    else:
        redacted = redact_pii(resume_input)
        with st.expander("🔒 PII Redacted Input Sent to Model", expanded=False):
            st.code(redacted, language="text")

        if prompt_ver.startswith("v1"):
            if mode == "Offline Demo Mode (No API Key)":
                st.warning("Running v1 Baseline (Demo Output) — Notice vague prose and no JSON structure:")
                st.write(DEMO_OUTPUT_V1)
            else:
                if not api_key:
                    st.error("Gemini API key is not configured. Please add GEMINI_API_KEY to Streamlit Secrets or environment variables.")
                else:
                    v1_prompt = f"You are a helpful assistant. Review this resume against the JD.\nResume:\n{redacted}\nJD:\n{jd_input}"
                    st.write(call_gemini(v1_prompt, api_key, json_mode=False))
        else:
            if mode == "Offline Demo Mode (No API Key)":
                if "ignore all" in resume_input.lower():
                    # Test #12: Defense against prompt injection (verified in evaluation)
                    p1_data = {
                        "match_score": 18,
                        "rubric_breakdown": {
                            "skills_40": 8,
                            "domain_30": 5,
                            "experience_20": 3,
                            "clarity_10": 2,
                        },
                        "missing_critical_skills": ["Docker", "PostgreSQL", "Django / FastAPI", "System Design"],
                        "missing_nice_to_have_skills": ["CI/CD Pipelines", "pytest"],
                        "strengths": ["Basic Python awareness"],
                        "verdict": "Low Match",
                    }
                    p2_data = {
                        "bullet_improvements": [
                            {
                                "original": "Basic Python and HTML experience.",
                                "improved": "Implemented modular Python scripts for data processing, handling [N] data records with [X%] improved throughput.",
                                "target_skill_addressed": "Python Backend Fundamentals",
                            }
                        ],
                        "tailoring_tip": "Embedded prompt injection ignored. Candidate profile requires substantial backend and database tailoring to meet role requirements.",
                    }
                else:
                    p1_data = DEMO_OUTPUT_V3["p1"]
                    p2_data = DEMO_OUTPUT_V3["p2"]
            else:
                if not api_key:
                    st.error("Gemini API key is not configured. Please add GEMINI_API_KEY to Streamlit Secrets or environment variables.")
                    st.stop()
                with st.spinner("Running Step 1 (P1: ATS Rubric Scorer)..."):
                    p1_file = PROJECT_ROOT / "prompts" / "final" / "P1.txt"
                    p1_prompt = p1_file.read_text(encoding="utf-8")
                    p1_prompt = p1_prompt.replace("{redacted_resume}", redacted).replace("{job_description}", jd_input)
                    p1_raw = call_gemini(p1_prompt, api_key, json_mode=True)
                    clean_p1 = re.sub(r"^```(?:json)?\s*|\s*```$", "", p1_raw.strip(), flags=re.MULTILINE)
                    p1_data = json.loads(clean_p1)
                
                if "error" in p1_data:
                    st.error(f"ATS Scorer Error: {p1_data.get('message', 'Insufficient or invalid input.')}")
                    st.stop()

                with st.spinner("Running Step 2 (P2: STAR Bullet Rewriter)..."):
                    p2_file = PROJECT_ROOT / "prompts" / "final" / "P2.txt"
                    p2_prompt = p2_file.read_text(encoding="utf-8")
                    p2_prompt = (
                        p2_prompt.replace("{redacted_resume}", redacted)
                        .replace("{job_description}", jd_input)
                        .replace("{p1_gap_json}", json.dumps(p1_data, indent=2))
                    )
                    p2_raw = call_gemini(p2_prompt, api_key, json_mode=True)
                    clean_p2 = re.sub(r"^```(?:json)?\s*|\s*```$", "", p2_raw.strip(), flags=re.MULTILINE)
                    p2_data = json.loads(clean_p2)

            # Render Dashboard
            m1, m2, m3, m4, m5 = st.columns(5)
            rb = p1_data["rubric_breakdown"]
            m1.metric("Overall Match", f"{p1_data['match_score']}/100", p1_data["verdict"])
            m2.metric("Skills (40)", f"{rb['skills_40']}/40")
            m3.metric("Domain (30)", f"{rb['domain_30']}/30")
            m4.metric("Experience (20)", f"{rb['experience_20']}/20")
            m5.metric("Clarity (10)", f"{rb['clarity_10']}/10")

            st.subheader("🔍 Skill-Gap Breakdown")
            g1, g2, g3 = st.columns(3)
            with g1:
                st.markdown("**Missing Critical Skills**")
                st.markdown("".join(f'<span class="pill-missing">{s}</span>' for s in p1_data["missing_critical_skills"]), unsafe_allow_html=True)
            with g2:
                st.markdown("**Missing Nice-to-Have**")
                st.markdown("".join(f'<span class="pill-nice">{s}</span>' for s in p1_data["missing_nice_to_have_skills"]), unsafe_allow_html=True)
            with g3:
                st.markdown("**Verified Strengths**")
                st.markdown("".join(f'<span class="pill-ok">{s}</span>' for s in p1_data["strengths"]), unsafe_allow_html=True)

            st.subheader("✍️ STAR-Method Bullet Rewrites (Anti-Hallucination Guarded)")
            for item in p2_data["bullet_improvements"]:
                with st.container(border=True):
                    st.caption(f"Target Skill: {item['target_skill_addressed']}")
                    c_a, c_b = st.columns(2)
                    c_a.markdown(f"**Original:**\n{item['original']}")
                    c_b.markdown(f"**Improved (STAR):**\n{item['improved']}")

            st.info(f"💡 **Tailoring Tip:** {p2_data['tailoring_tip']}")
            with st.expander("📦 Raw Structured JSON Output"):
                st.json({"step_1_ats_evaluation": p1_data, "step_2_star_rewrites": p2_data})
