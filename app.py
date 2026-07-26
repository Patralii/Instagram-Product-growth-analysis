import streamlit as st
import plotly.graph_objects as go
import pandas as pd

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Instagram: Funnel, Reels A/B & Discovery Equity",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# PALETTE
# ─────────────────────────────────────────────
C = {
    "accent": "#c8b5ff", "green": "#5ae4a0", "blue": "#5bc0f8",
    "amber": "#ffb347", "red": "#ff6b6b", "teal": "#4dd9c4",
    "coral": "#ff8a65", "bg3": "#1a1a20", "text2": "#9995a0",
}

BASE_LAYOUT = dict(
    paper_bgcolor=C["bg3"], plot_bgcolor=C["bg3"],
    font=dict(color=C["text2"], family="Arial, sans-serif", size=12),
    margin=dict(l=12, r=12, t=12, b=12),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                font=dict(size=10), bgcolor="rgba(0,0,0,0)"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.12)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.07)", zerolinecolor="rgba(255,255,255,0.12)"),
)


def styled(f, height=300):
    f.update_layout(**BASE_LAYOUT, height=height)
    return f


def header(title, desc, hook=None):
    st.subheader(title)
    st.caption(desc)
    if hook:
        st.markdown(f"> *{hook}*")
    st.divider()


def kpis(items):
    cols = st.columns(len(items))
    for col, it in zip(cols, items):
        with col:
            st.metric(it["label"], it["value"], it.get("delta"), it.get("dc", "normal"), help=it.get("help"))


def insight(text, kind="info"):
    {"info": st.info, "warning": st.warning, "success": st.success, "error": st.error}[kind](text)


# ─────────────────────────────────────────────
# SIDEBAR NAVIGATION (Excluding recommendation through last pages)
# ─────────────────────────────────────────────
NAV = {
    "Overview": ["Executive Summary"],
    "Part 1 — Funnel": ["The Engagement Funnel"],
    "Part 2 — Experiment": [
        "Experiment Design", "Pre-Launch Checks (SRM)", "Primary Metrics",
        "The Stories Effect", "Durability Check",
    ],
    "Part 3 — Discovery": ["Discovery Test Design", "Results & Creator Equity"],
    "Synthesis": ["Funnel-Linked Segments"],
}

ICONS = {
    "Executive Summary": "📊", "The Engagement Funnel": "🔽", "Experiment Design": "🧪",
    "Pre-Launch Checks (SRM)": "✅", "Primary Metrics": "📈", "The Stories Effect": "🌀",
    "Durability Check": "🌊", "Discovery Test Design": "🔍", "Results & Creator Equity": "⚖️",
    "Funnel-Linked Segments": "🧩",
}

ALL_PAGES = [p for group in NAV.values() for p in group]
PAGE_GROUP = {p: g for g, pages in NAV.items() for p in pages}

with st.sidebar:
    st.markdown("### 📊 Instagram Analytics")
    st.caption("Funnel · Reels A/B · Discovery Equity")
    st.write("")
    page = st.radio("Navigate", ALL_PAGES, format_func=lambda p: f"{ICONS[p]}  {p}", label_visibility="collapsed")
    st.write("")
    st.divider()
    m1, m2 = st.columns(2)
    m1.metric("Test Window", "28 days", help="Apr 1–28, 2026")
    m2.metric("Dataset", "50K / 9K / 10K", help="Funnel / Experiment / Discovery users")

tl, tr = st.columns([4, 1])
tl.caption(f"Instagram Portfolio · {page}")
tr.caption("🟢 Ship + Pilot · Apr 2026")

# ══════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ══════════════════════════════════════════════════════════════
if page == "Executive Summary":
    header(
        "Should Instagram Expand Reels — and Is Discovery Fair to the New Creators It Creates?",
        "Funnel (50,000 signups) · Reels A/B test (9,000 users, 28 days) · Discovery equity test (10,000 users)",
        hook="Before we test anything, we needed to know where Instagram was quietly losing people.",
    )
    st.warning(
        "**🟢 Ship + Pilot** — The funnel shows a **-64.3% drop-off** before a user ever posts. "
        "The Reels experiment found an accidental fix: exposure pulled non-posters into creating "
        "(+16.2% Stories posting lift). A third test found real equity gains for new creators — "
        "alongside a bigger-than-expected filter-bubble cost. "
        "**Ship Reels + targeted prompt now. Pilot Discovery before global rollout.**"
    )
    kpis([
        {"label": "Steepest Funnel Drop-off", "value": "-64.3%", "delta": "Signup → First Post", "dc": "inverse"},
        {"label": "Daily Time Spent (Primary)", "value": "+1.9%", "delta": "33.42 → 34.07 min", "dc": "normal"},
        {"label": "Stories Posting Rate", "value": "+16.2%", "delta": "25.48% → 29.60%", "dc": "normal"},
        {"label": "Discovery Equity Lift", "value": "+241%", "delta": "9.0% → 30.7% of clicks", "dc": "normal"},
    ])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Funnel — where users drop off**")
        f = go.Figure(go.Bar(
            x=[-64.3, -35.3, -52.1], y=["Signup → First Post", "First Post → First Follow", "First Follow → DAU"],
            orientation="h", marker_color=[C["red"], C["amber"], C["amber"]],
            text=["-64.3%", "-35.3%", "-52.1%"], textposition="outside",
        ))
        f.update_xaxes(title="Drop-off %")
        st.plotly_chart(styled(f), use_container_width=True)
    with c2:
        st.markdown("**The assumption vs. the result**")
        f = go.Figure(go.Bar(
            x=["Assumed: Stories ↓", "Actual: Stories posting"], y=[-15, 16.2],
            marker_color=[C["red"], C["teal"]], text=["-15% (assumed)", "+16.2% (actual)"], textposition="outside",
        ))
        f.update_yaxes(title="%")
        st.plotly_chart(styled(f), use_container_width=True)
    insight(
        "**Why all three parts matter together:** the funnel found the leak (-64.3% at First Post). "
        "The Reels experiment, run to test a different question, accidentally found a fix for that "
        "exact stage. The Discovery test then asked whether the new creators that fix produced are "
        "actually being seen — and found a real but incomplete yes.",
    )

# ══════════════════════════════════════════════════════════════
# THE ENGAGEMENT FUNNEL
# ══════════════════════════════════════════════════════════════
elif page == "The Engagement Funnel":
    header(
        "The Engagement Funnel",
        "Part 1 — Signup → First Post → First Follow → DAU · 50,000 users, 90-day lookback",
    )
    st.dataframe(pd.DataFrame({
        "Stage": ["Signup", "First Post", "First Follow", "DAU (Day 30)"],
        "Users": ["50,000", "17,844", "11,550", "5,531"],
        "% of Signups": ["100.0%", "35.7%", "23.1%", "11.1%"],
        "Drop-off": ["—", "-64.3%", "-35.3%", "-52.1%"],
    }), hide_index=True, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Stage-over-stage drop-off**")
        f = go.Figure(go.Bar(
            y=["Signup → First Post", "First Post → First Follow", "First Follow → DAU"],
            x=[-64.3, -35.3, -52.1], orientation="h",
            marker_color=[C["red"], C["amber"], C["amber"]], text=["-64.3%", "-35.3%", "-52.1%"], textposition="outside",
        ))
        st.plotly_chart(styled(f, 280), use_container_width=True)
    with c2:
        st.markdown("**Median days to convert (among converters)**")
        f = go.Figure(go.Bar(
            x=["First Post", "First Follow", "DAU (Day 30)"], y=[2.3, 1.1, 6.8],
            marker_color=[C["accent"], C["teal"], C["blue"]], text=["2.3 days", "1.1 days", "6.8 days"], textposition="outside",
        ))
        st.plotly_chart(styled(f, 280), use_container_width=True)
    insight(
        "**Steepest stage: Signup → First Post (-64.3%)** — the earliest, largest leak in the "
        "funnel. Of users who never post within 7 days, 73% churn within 5 days of signing up. "
        "This is the business case for testing Reels: a passive, consumption-first format is a "
        "plausible lever on a population that never gets far enough into the product to create.",
        kind="warning",
    )

# ══════════════════════════════════════════════════════════════
# EXPERIMENT DESIGN
# ══════════════════════════════════════════════════════════════
elif page == "Experiment Design":
    header("Experiment Design", "Part 2 — Hypothesis, randomization, metric tiers, power")
    with st.container(border=True):
        st.markdown("**Hypothesis**")
        st.write(
            "Increasing Reels feed density from **1-in-5** to **1-in-3** positions will increase "
            "daily time spent. Common assumption: denser Reels will cannibalize Stories. The funnel "
            "adds a second hypothesis: could Reels exposure also pull never-posted users toward "
            "creating content for the first time?"
        )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Design parameters**")
        st.dataframe(pd.DataFrame({
            "Parameter": ["Randomization unit", "Allocation", "Sample", "Duration", "Alpha / Power"],
            "Value": ["user_id", "50 / 50", "9,000 users", "28 days", "0.05 / 0.80"],
        }), hide_index=True, use_container_width=True)
    with c2:
        st.markdown("**Metric tiers**")
        st.dataframe(pd.DataFrame({
            "Tier": ["Primary", "Secondary", "Guardrail", "Exploratory"],
            "Metric": ["Daily time spent", "Reels engagement rate", "Stories opens/day", "Stories posting rate"],
            "Why": ["North star", "Confirms mechanism", "Cannibalization risk", "Added after funnel review"],
        }), hide_index=True, use_container_width=True)
    st.markdown("**MDE vs. required sample size per arm** (σ = 18.2 min, α = 0.05, power = 0.80)")
    f = go.Figure(go.Scatter(
        x=[0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0], y=[210712, 52678, 23412, 13170, 5853, 3293, 2107],
        mode="lines+markers", line=dict(color=C["accent"], width=2),
        marker=dict(size=7, color=C["accent"]), fill="tozeroy", fillcolor="rgba(200,181,255,0.10)",
    ))
    f.update_xaxes(title="Relative MDE (%)")
    f.update_yaxes(title="Required N per arm (log)", type="log")
    st.plotly_chart(styled(f, 280), use_container_width=True)
    insight("At 1% MDE the formula requires ~52,700 users/arm. The test ran with ~4,500/arm "
            "(SRM-clean) — smaller than ideal, but every direction and relative-lift finding "
            "reproduces correctly, and the same methodology scales to the full 1.2M-per-arm design.")

# ══════════════════════════════════════════════════════════════
# PRE-LAUNCH CHECKS (SRM)
# ══════════════════════════════════════════════════════════════
elif page == "Pre-Launch Checks (SRM)":
    header("Pre-Launch Checks — Sample Ratio Mismatch (SRM)", "Validating randomization before trusting any result")
    kpis([
        {"label": "Expected Split", "value": "50.0%", "help": "Pre-registered 50/50"},
        {"label": "Observed (Day 1, raw)", "value": "Skewed", "delta": "~4.2% of traffic affected", "dc": "off"},
        {"label": "Status", "value": "SRM → Fixed", "delta": "Excluded, re-validated", "dc": "off"},
    ])
    st.error(
        "**Root cause:** the client-side bucketing service fell back to a session-scoped hash for "
        "ATT-denied iOS users, re-randomizing them on every session, disproportionately routing "
        "them into control. Fixed with a server-side stable hash; affected rows excluded via "
        "`affected_by_srm_bug` before any result is trusted."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Bucket counts — raw (before exclusion)**")
        f = go.Figure()
        f.add_trace(go.Bar(x=["Treatment", "Control"], y=[4457, 4543], name="Observed", marker_color=C["red"]))
        f.add_trace(go.Bar(x=["Treatment", "Control"], y=[4500, 4500], name="Expected", marker_color="rgba(255,255,255,0.15)"))
        f.update_layout(barmode="group")
        st.plotly_chart(styled(f, 260), use_container_width=True)
    with c2:
        st.markdown("**Bucket counts — after excluding SRM rows**")
        f = go.Figure()
        f.add_trace(go.Bar(x=["Treatment", "Control"], y=[4356, 4284], name="Observed", marker_color=C["green"]))
        f.add_trace(go.Bar(x=["Treatment", "Control"], y=[4320, 4320], name="Expected", marker_color="rgba(255,255,255,0.15)"))
        f.update_layout(barmode="group")
        st.plotly_chart(styled(f, 260), use_container_width=True)

# ══════════════════════════════════════════════════════════════
# PRIMARY METRICS
# ══════════════════════════════════════════════════════════════
elif page == "Primary Metrics":
    header("Primary & Secondary Metric Results", "Post-fix results · full 28-day window · SRM-clean sample only")
    kpis([
        {"label": "Daily Time Spent", "value": "+1.9%", "delta": "33.42 → 34.07 min", "dc": "normal"},
        {"label": "Stories Opens (consump.)", "value": "+2.4%", "delta": "not down — expected was a drop", "dc": "normal"},
        {"label": "Stories Posting (creation)", "value": "+16.2%", "delta": "25.48% → 29.60%", "dc": "normal"},
    ])
    st.markdown("**Full results table**")
    st.dataframe(pd.DataFrame({
        "Metric": ["Primary: Daily time spent", "Guardrail: Stories opens/day", "Exploratory: Stories posting rate"],
        "Control": ["33.42 min", "4.80/day", "25.48%"],
        "Treatment": ["34.07 min", "4.91/day", "29.60%"],
        "Rel. Δ": ["+1.9%", "+2.4%", "+16.2%"],
    }), hide_index=True, use_container_width=True)
    insight(
        "The assumed risk (Stories cannibalization) didn't materialize — consumption (+2.4%) and "
        "creation (+16.2%) both went up.",
        kind="success",
    )

# ══════════════════════════════════════════════════════════════
# THE STORIES EFFECT
# ══════════════════════════════════════════════════════════════
elif page == "The Stories Effect":
    header(
        "The Stories Effect — The Unexpected Finding",
        "The metric nobody expected to be the headline",
        hook="Everyone assumed Reels was stealing from Stories. The data had other plans.",
    )
    kpis([
        {"label": "Assumption Going In", "value": "Stories ↓", "help": "Cannibalization expected"},
        {"label": "Actual Posting Lift", "value": "+16.2%", "delta": "25.48% → 29.60%", "dc": "normal"},
        {"label": "Opens (consumption)", "value": "+2.4%", "delta": "also up, not down", "dc": "normal"},
    ])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Stories posting rate — control vs. treatment**")
        f = go.Figure(go.Bar(x=["Control", "Treatment"], y=[25.48, 29.60], marker_color=[C["blue"], C["teal"]],
                              text=["25.48%", "29.60%"], textposition="outside"))
        st.plotly_chart(styled(f), use_container_width=True)
    with c2:
        st.markdown("**Mechanism: more Reels watched → higher first-post conversion**")
        st.caption("Never-posted users only, by Reels exposure level")
        f = go.Figure(go.Bar(x=["Low exposure", "Medium exposure", "High exposure"], y=[9.8, 15.2, 23.6],
                              marker_color=[C["blue"], C["amber"], C["teal"]], text=["9.8%", "15.2%", "23.6%"], textposition="outside"))
        st.plotly_chart(styled(f), use_container_width=True)
    insight(
        "**Why this isn't just a lucky number:** Stories opens also rose (+2.4%) — if Reels were "
        "simply substituting for Stories, consumption should have dropped. The lift concentrates in "
        "users who hadn't posted before (see Funnel-Linked Segments), and watching a Reel measurably "
        "precedes a Stories post within the same session in the event-level data.",
        kind="success",
    )

# ══════════════════════════════════════════════════════════════
# DURABILITY CHECK
# ══════════════════════════════════════════════════════════════
elif page == "Durability Check":
    header("Durability Check", "Novelty effect or real behavior change?")
    weeks = ["Week 1", "Week 2", "Week 3", "Week 4"]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Reels engagement lift — classic novelty decay**")
        f = go.Figure(go.Scatter(x=weeks, y=[14.2, 9.1, 5.8, 4.6], mode="lines+markers",
                                  line=dict(color=C["coral"], width=2), marker=dict(size=8, color=C["coral"]),
                                  fill="tozeroy", fillcolor="rgba(255,138,101,0.1)"))
        st.plotly_chart(styled(f), use_container_width=True)
    with c2:
        st.markdown("**Stories posting lift — ramping, not decaying**")
        f = go.Figure(go.Scatter(x=weeks, y=[9.4, 14.1, 17.8, 18.3], mode="lines+markers",
                                  line=dict(color=C["teal"], width=2), marker=dict(size=8, color=C["teal"]),
                                  fill="tozeroy", fillcolor="rgba(77,217,196,0.1)"))
        st.plotly_chart(styled(f), use_container_width=True)
    insight(
        "A pure novelty effect decays toward zero. Reels engagement fits that pattern. Stories "
        "posting does the opposite — it builds every week, consistent with a habit forming. "
        "**Recommendation: extend measurement to 8 weeks** before using the posting-lift number in "
        "retention forecasting.",
        kind="success",
    )

# ══════════════════════════════════════════════════════════════
# DISCOVERY TEST DESIGN
# ══════════════════════════════════════════════════════════════
elif page == "Discovery Test Design":
    header(
        "Discovery Test Design",
        "Part 3 — Does Explore/Search give Part 2's new creators a fair chance to be seen?",
        hook="Part 2 created thousands of new creators overnight. Part 3 asks whether anyone would ever actually see them.",
    )
    with st.container(border=True):
        st.markdown("**Why this test, why now**")
        st.write(
            "Part 2 converted never-posted users into first-time creators with zero followers and "
            "no track record. The current Explore/Search tab ranks largely by popularity — a "
            "brand-new creator's first post is competing directly against established accounts, and "
            "probably losing. This test asks whether organizing Explore by topic cluster, with a "
            "deliberate visibility boost for new/small creators built in from the start, changes that."
        )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**The experiment**")
        st.dataframe(pd.DataFrame({
            "Parameter": ["Group A (Control)", "Group B (Treatment)", "Mitigation", "Sample"],
            "Value": ["Flat, popularity-ranked feed", "Interest-Based Clusters + new-creator boost",
                      "~1-in-10 impressions outside home category", "10,000 users, 50/50"],
        }), hide_index=True, use_container_width=True)
    with c2:
        st.markdown("**Metric tiers**")
        st.dataframe(pd.DataFrame({
            "Tier": ["Primary", "Equity (key)", "Guardrail"],
            "Metric": ["Click-through rate (CTR)", "% of clicks to new/small creators", "Distinct categories/user/week"],
            "Why": ["Did clustering help discovery", "Are Part 2's new creators actually found", "Filter-bubble risk"],
        }), hide_index=True, use_container_width=True)
    insight(
        "**Why this design, not a simpler one:** a clustering test without the new-creator boost "
        "risks raising CTR while still burying small creators under big accounts within each "
        "category. Building both mechanisms in from the start — and pre-registering the equity "
        "metric alongside CTR — is what makes the result defensible to a skeptical stakeholder."
    )

# ══════════════════════════════════════════════════════════════
# RESULTS & CREATOR EQUITY
# ══════════════════════════════════════════════════════════════
elif page == "Results & Creator Equity":
    header("Discovery Results & Creator Equity", "CTR and equity moved right. The guardrail needs an honest look.")
    kpis([
        {"label": "Click-Through Rate", "value": "+38.0%", "delta": "5.16% → 7.12%", "dc": "normal"},
        {"label": "New-Creator Click Share", "value": "+241%", "delta": "9.0% → 30.7%", "dc": "normal"},
        {"label": "Category Diversity", "value": "-68.8%", "delta": "6.35 → 1.98 categories/user", "dc": "inverse"},
    ])
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**CTR — control vs. treatment**")
        f = go.Figure(go.Bar(x=["Control (flat)", "Treatment (clusters)"], y=[5.16, 7.12], marker_color=[C["blue"], C["green"]],
                              text=["5.16%", "7.12%"], textposition="outside"))
        st.plotly_chart(styled(f), use_container_width=True)
    with c2:
        st.markdown("**% clicks to new/small creators**")
        f = go.Figure(go.Bar(x=["Control (flat)", "Treatment (clusters + boost)"], y=[9.0, 30.7], marker_color=[C["blue"], C["teal"]],
                              text=["9.0%", "30.7%"], textposition="outside"))
        st.plotly_chart(styled(f), use_container_width=True)
    st.markdown("**Category diversity guardrail — the filter-bubble check**")
    f = go.Figure(go.Bar(x=["Control (flat)", "Treatment (clusters)"], y=[6.35, 1.98], marker_color=[C["blue"], C["red"]],
                          text=["6.35 categories", "1.98 categories"], textposition="outside"))
    st.plotly_chart(styled(f, 250), use_container_width=True)
    insight(
        "**The honest read:** both wins are real — CTR up 38.0% and new-creator click share up "
        "241%. But category diversity dropped 68.8%, larger than the 'small, monitorable' "
        "expectation going in. **This does not support a clean global ship.** Pilot first, raise "
        "the serendipity injection rate, re-measure before wider rollout.",
        kind="warning",
    )

# ══════════════════════════════════════════════════════════════
# FUNNEL-LINKED SEGMENTS
# ══════════════════════════════════════════════════════════════
elif page == "Funnel-Linked Segments":
    header("Funnel-Linked Segments", "Connecting Part 1 and Part 2")
    st.markdown("**Segment summary**")
    st.dataframe(pd.DataFrame({
        "Segment": ["Never posted before", "Had posted before"],
        "Posting Rate — Control": ["18.93%", "29.17%"],
        "Treatment": ["28.08%", "30.43%"],
        "Lift": ["+48.3%", "+4.3%"],
    }), hide_index=True, use_container_width=True)
    f = go.Figure(go.Bar(x=["Never posted before", "Had posted before"], y=[48.3, 4.3],
                          marker_color=[C["teal"], C["blue"]], text=["+48.3%", "+4.3%"], textposition="outside"))
    st.plotly_chart(styled(f), use_container_width=True)
    insight(
        "The population-level +16.2% lift is driven mostly by users who hadn't posted before the "
        "test — the exact group stuck at the funnel's steepest stage. The funnel told us where to "
        "look; the experiment found something that moves the needle specifically there.",
        kind="success",
    )
