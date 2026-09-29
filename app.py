import plotly.express as px
import streamlit as st

from agent import answer_question, generate_executive_summary
from db import (
    get_course_completion_summary,
    get_engagement_metrics,
    get_funnel_breakdown,
    get_overall_metrics,
    get_revenue_by_plan,
    get_revenue_metrics,
    get_review_metrics,
    get_signup_trend,
    get_top_rated_specializations,
    get_users_by_country,
    get_users_by_persona,
    get_users_by_plan,
)

st.set_page_config(page_title="Аналітика курсів", layout="wide", page_icon="📊")

PLAN_UA = {"monthly": "Місячний", "annual": "Річний", "free": "Безкоштовний", "financial_aid": "Фін. допомога"}
PERSONA_UA = {
    "upskiller": "Підвищення кваліфікації",
    "career_switcher": "Зміна кар'єри",
    "student": "Студент",
    "hobbyist": "Хобі",
}
FUNNEL_UA = {"viewed": "Переглянув", "registered": "Зареєструвався", "explored": "Досліджував", "certified": "Сертифікований"}

# ---------------------------------------------------------------------------
# Design tokens — restrained enterprise palette (navy shell + blue accent).
# Applied only where Streamlit allows CSS overrides; kept minimal on purpose.
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    :root {
        --navy-950: #0E1B3D;
        --navy-900: #16224C;
        --blue-600: #2F6FED;
        --blue-50: #EEF3FE;
        --bg-app: #F5F7FB;
        --surface: #FFFFFF;
        --border: #E4E8F1;
        --text-primary: #101828;
        --text-secondary: #5B6472;
        --success: #12805C;
        --success-soft: #E6F6EE;
        --warning: #B45309;
        --warning-soft: #FEF3E2;
    }

    html, body, [class*="css"] { font-family: 'Inter', 'Segoe UI', Roboto, Arial, sans-serif; }
    .stApp { background: var(--bg-app); }

    .block-container { max-width: 1180px; padding-top: 2.2rem; padding-bottom: 3rem; }

    [data-testid="stMetricValue"] {
        font-variant-numeric: tabular-nums;
        font-feature-settings: "tnum" 1;
        color: var(--text-primary);
        font-weight: 700;
    }
    [data-testid="stMetricLabel"] { color: var(--text-secondary); font-weight: 600; font-size: 0.8rem; }

    .kpi-hero, .kpi-standard {
        background: var(--surface);
        border: 1px solid var(--border);
        border-radius: 14px;
        box-shadow: 0 1px 2px rgba(16,24,40,0.04);
        transition: border-color 120ms ease, box-shadow 120ms ease;
    }
    .kpi-hero:hover, .kpi-standard:hover {
        border-color: #C7D6FB;
        box-shadow: 0 2px 8px rgba(47,111,237,0.10);
    }
    .kpi-hero { padding: 20px 22px; min-height: 128px; display: flex; flex-direction: column; }
    .kpi-hero .icon { font-size: 18px; margin-bottom: 6px; opacity: 0.85; }
    .kpi-hero .label { color: var(--text-secondary); font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: .02em; }
    .kpi-hero .value { color: var(--navy-950); font-size: 30px; font-weight: 700; font-variant-numeric: tabular-nums; margin-top: 4px; }
    .kpi-hero .sub { color: var(--text-secondary); font-size: 12.5px; margin-top: 6px; min-height: 16px; }

    .kpi-standard { padding: 14px 16px; border-radius: 12px; }
    .kpi-standard .icon { font-size: 15px; margin-bottom: 4px; opacity: 0.8; }
    .kpi-standard .label { color: var(--text-secondary); font-size: 11.5px; font-weight: 600; text-transform: uppercase; letter-spacing: .01em; }
    .kpi-standard .value { color: var(--navy-950); font-size: 22px; font-weight: 700; font-variant-numeric: tabular-nums; margin-top: 2px; }

    .section-title { color: var(--navy-950); font-size: 19px; font-weight: 700; margin: 30px 0 2px 0; }
    .section-sub { color: var(--text-secondary); font-size: 13px; margin-bottom: 14px; }

    .chip { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
    .chip-ok { background: var(--success-soft); color: var(--success); }
    .chip-warn { background: var(--warning-soft); color: var(--warning); }

    div[data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 10px; }

    button[data-baseweb="tab"] { font-weight: 600; font-size: 14.5px; }
    div[data-baseweb="tab-highlight"] { background-color: var(--blue-600) !important; height: 2.5px !important; }
    hr { margin: 8px 0 22px 0; border-color: var(--border); }
    </style>
    """,
    unsafe_allow_html=True,
)

BRAND_PALETTE = ["#2F6FED", "#16224C", "#7FA6F5", "#0E1B3D", "#B9CCF7"]


def kpi_hero(label: str, value: str, sub: str = "", icon: str = ""):
    icon_html = f'<div class="icon">{icon}</div>' if icon else ""
    st.markdown(
        f"""<div class="kpi-hero">
                {icon_html}
                <div class="label">{label}</div>
                <div class="value">{value}</div>
                <div class="sub">{sub}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def kpi_standard(label: str, value: str, icon: str = ""):
    icon_html = f'<div class="icon">{icon}</div>' if icon else ""
    st.markdown(
        f"""<div class="kpi-standard">
                {icon_html}
                <div class="label">{label}</div>
                <div class="value">{value}</div>
            </div>""",
        unsafe_allow_html=True,
    )


def section(title: str, sub: str = ""):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if sub:
        st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def _style_fig(fig, horizontal_legend: bool = False):
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        font=dict(family="Inter, sans-serif", color="#101828", size=13),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=horizontal_legend,
        legend=dict(orientation="h", y=-0.15) if horizontal_legend else None,
    )
    fig.update_xaxes(showgrid=False, linecolor="#E4E8F1")
    fig.update_yaxes(showgrid=True, gridcolor="#EEF1F6", zeroline=False)
    return fig


def bar_chart(df, x: str, y: str):
    fig = px.bar(df, x=x, y=y, color_discrete_sequence=[BRAND_PALETTE[0]])
    fig.update_traces(marker_line_width=0)
    st.plotly_chart(_style_fig(fig), use_container_width=True)


def line_chart(df, x: str, y: str):
    fig = px.line(df, x=x, y=y, color_discrete_sequence=[BRAND_PALETTE[0]])
    fig.update_traces(line_width=2.5)
    st.plotly_chart(_style_fig(fig), use_container_width=True)


def donut_chart(df, names: str, values: str):
    fig = px.pie(df, names=names, values=values, hole=0.55, color_discrete_sequence=BRAND_PALETTE)
    fig.update_traces(textinfo="percent+label")
    st.plotly_chart(_style_fig(fig, horizontal_legend=True), use_container_width=True)


def render_ai_text(text: str):
    """Render LLM output as markdown safely — '$' would otherwise be parsed as LaTeX math."""
    st.markdown(text.replace("$", "\\$"))


st.markdown(
    '<h2 style="color:#0E1B3D; font-weight:700; margin-bottom:0;">📊 Аналітика курсів</h2>'
    '<p style="color:#5B6472; margin-top:2px;">Огляд активності, завершеності, доходу та аудиторії платформи</p>',
    unsafe_allow_html=True,
)

metrics = get_overall_metrics()
engagement = get_engagement_metrics()
revenue = get_revenue_metrics()
reviews = get_review_metrics()

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_hero("Всього зарахувань", f"{metrics['total_enrollments']:,}", icon="🎓")
with col2:
    kpi_hero("Завершено", f"{metrics['completed']:,}", f"{metrics['avg_progress']}% середній прогрес", icon="✅")
with col3:
    kpi_hero("Загальний дохід", f"${revenue['total_revenue']:,.0f}", f"{revenue['refund_rate_pct']}% повернень", icon="💰")
with col4:
    kpi_hero("Середня оцінка", f"{reviews['avg_stars']} ★", f"{reviews['total_reviews']:,} відгуків", icon="⭐")

st.markdown("<hr/>", unsafe_allow_html=True)

tab_home, tab_courses, tab_engagement, tab_revenue, tab_audience = st.tabs(
    ["🏠 Головна", "📚 Курси", "⏱ Залучення", "💰 Дохід", "🌍 Аудиторія"]
)

def _load_exec_summary():
    try:
        with st.spinner("Генерую підсумок..."):
            st.session_state["exec_summary"] = generate_executive_summary()
    except Exception as exc:  # Gemini can be transiently overloaded (503) etc.
        st.session_state["exec_summary_error"] = str(exc)


with tab_home:
    section("Підсумок від AI", "Автоматичний огляд стану платформи, згенерований Gemini")
    if "exec_summary" not in st.session_state and "exec_summary_error" not in st.session_state:
        _load_exec_summary()

    if st.session_state.get("exec_summary_error"):
        st.warning("Не вдалося згенерувати підсумок. Спробуй ще раз.")
        with st.expander("Деталі помилки (діагностика)"):
            st.code(st.session_state["exec_summary_error"])
    elif st.session_state.get("exec_summary"):
        render_ai_text(st.session_state["exec_summary"])

    if st.button("🔄 Оновити підсумок"):
        st.session_state.pop("exec_summary_error", None)
        _load_exec_summary()
        st.rerun()

with tab_courses:
    section("Відсоток завершення по курсах", "Курси з ≥20 зарахуваннями, відсортовані за завершеністю")
    summary = get_course_completion_summary()
    summary_ua = summary.rename(columns={
        "course": "Курс", "domain": "Напрям", "level": "Рівень",
        "enrollments": "Зарахування", "completed": "Завершено",
        "avg_progress": "Сер. прогрес, %", "completion_rate_pct": "Завершеність, %",
    })
    bar_chart(summary.head(15), x="course", y="completion_rate_pct")
    with st.expander("Повна таблиця курсів"):
        st.dataframe(summary_ua, width="stretch")

    section("Найкраще оцінені спеціалізації")
    top_spec = get_top_rated_specializations().rename(columns={
        "specialization_name": "Спеціалізація", "review_score": "Оцінка", "review_count": "Кількість відгуків",
    })
    st.dataframe(top_spec, width="stretch", hide_index=True)

with tab_engagement:
    section("Воронка зарахувань", "Скільки зарахувань на кожному етапі воронки")
    funnel = get_funnel_breakdown()
    funnel["funnel_state"] = funnel["funnel_state"].map(FUNNEL_UA).fillna(funnel["funnel_state"])
    bar_chart(funnel, x="funnel_state", y="enrollments")

    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_standard("Сер. хвилин/тиждень", f"{engagement['avg_minutes_per_week']}", icon="⏱")
    with c2:
        kpi_standard("Сер. бал за тести", f"{engagement['avg_quiz_score']}%", icon="📝")
    with c3:
        kpi_standard("Активні зарахування", f"{engagement['active_enrollments']:,}", icon="👥")

with tab_revenue:
    section("Дохід за планом")
    rev_plan = get_revenue_by_plan()
    rev_plan["plan"] = rev_plan["plan"].map(PLAN_UA).fillna(rev_plan["plan"])
    rev_plan_ua = rev_plan.rename(columns={
        "plan": "План", "payments": "Платежі", "revenue": "Дохід", "refund_rate_pct": "Повернення, %",
    })
    st.dataframe(rev_plan_ua, width="stretch", hide_index=True)
    bar_chart(rev_plan, x="plan", y="revenue")

with tab_audience:
    c1, c2 = st.columns(2)
    with c1:
        section("Користувачі за планом")
        plan_df = get_users_by_plan()
        plan_df["plan"] = plan_df["plan"].map(PLAN_UA).fillna(plan_df["plan"])
        donut_chart(plan_df, names="plan", values="users")
    with c2:
        section("Користувачі за типом")
        persona_df = get_users_by_persona()
        persona_df["persona"] = persona_df["persona"].map(PERSONA_UA).fillna(persona_df["persona"])
        donut_chart(persona_df, names="persona", values="users")

    section("Топ країн")
    donut_chart(get_users_by_country(), names="country", values="users")

    section("Реєстрації у часі")
    line_chart(get_signup_trend(), x="month", y="signups")

st.write("")
section("Запитати AI-агента", "Питання про курси, залучення, дохід чи аудиторію")
question = st.text_input(
    "Запитати",
    placeholder="Які курси мають найнижчу завершеність?",
    label_visibility="collapsed",
)
if st.button("Запитати") and question:
    with st.spinner("Думаю..."):
        answer = answer_question(question)
    st.markdown("**Відповідь агента:**")
    render_ai_text(answer)
