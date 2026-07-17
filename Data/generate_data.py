WHAT: Generates the full synthetic dataset behind the Instagram three-part
      project (Part 1: Funnel, Part 2: Reels A/B Test, Part 3: Discovery
      Equity Test). Produces 10 CSV files matching schema.sql.

WHY:  A portfolio project is only as credible as its data. Rather than
      hand-typing summary statistics into a dashboard, this script builds
      real, row-level synthetic data with the underlying probabilities
      calibrated so that querying it reproduces (approximately) the
      headline numbers in the project brief — e.g. a ~64% Signup -> First
      Post drop-off, an ~18% Stories-posting lift in the treatment arm,
      etc. That means every SQL query in /sql can actually be run against
      this data and will return numbers in the right neighborhood, not
      just numbers that were asserted in a slide.

SCALE: Real Instagram-scale data (millions/billions of rows) isn't
       practical to generate or query on a laptop. This script uses a
       scaled-down population (tens of thousands of users) that preserves
       the same RATES and RELATIONSHIPS as the full-scale numbers in the
       brief, so the methodology and the SQL transfer directly to a real
       dataset of any size.

Run with: python3 generate_data.py
Requires: pandas, numpy
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import uuid

# ----------------------------------------------------------------------------
# WHAT: Fix the random seed.
# WHY:  Reproducibility — anyone re-running this script gets the exact same
#       dataset, which matters for a portfolio piece people might inspect.
# ----------------------------------------------------------------------------
SEED = 42
rng = np.random.default_rng(SEED)

OUT = "data/"
TEST_START = datetime(2026, 4, 1)


def uid(prefix):
    """WHAT: Short helper for readable, unique IDs.
    WHY: Real-looking IDs (e.g. usr_4f2a91b8c3d10e22) are easier to scan in
    a CSV than raw UUIDs. 16 hex chars (64 bits) keeps collision risk
    negligible even at the largest table here (~1.2M rows) -- the earlier
    10-char (40-bit) version collided at that volume (birthday paradox)."""
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


# ============================================================================
# PART 1 — FUNNEL DATA
# WHAT: A cohort of signups, each progressing (or not) through
#       Signup -> First Post -> First Follow -> DAU.
# WHY:  This is the data behind the -64% Signup->First Post drop-off finding
#       that motivates the rest of the project.
# ============================================================================
N_FUNNEL_USERS = 50_000  # scaled down from the brief's 1,000,000 (1/20th)

print("Generating Part 1: funnel users and events...")

# WHAT: Assign each user a signup date spread over a 90-day lookback window.
# WHY:  Real signups aren't simultaneous; spreading them out lets us compute
#       realistic "days since signup" for the time-to-convert analysis.
signup_offsets = rng.integers(0, 90, size=N_FUNNEL_USERS)
signup_dates = [TEST_START - timedelta(days=90) + timedelta(days=int(d)) for d in signup_offsets]

users_df = pd.DataFrame({
    "user_id": [uid("usr") for _ in range(N_FUNNEL_USERS)],
    "account_created_at": signup_dates,
    "country": rng.choice(["US", "CA"], size=N_FUNNEL_USERS, p=[0.82, 0.18]),
})

# WHAT: Decide, for each user, whether/when they hit First Post, First
#       Follow, and DAU, using the conversion rates from the brief:
#       Signup->First Post: 36.0% convert
#       First Post->First Follow: 65.0% of posters convert
#       First Follow->DAU: 48.0% of followers convert
# WHY:  Building this stage-by-stage (rather than picking 4 independent
#       probabilities) mirrors how funnels actually work — you can't reach
#       a later stage without clearing the earlier one.
p_first_post = 0.360
p_first_follow_given_post = 0.650
p_dau_given_follow = 0.480

reaches_post = rng.random(N_FUNNEL_USERS) < p_first_post
reaches_follow = reaches_post & (rng.random(N_FUNNEL_USERS) < p_first_follow_given_post)
reaches_dau = reaches_follow & (rng.random(N_FUNNEL_USERS) < p_dau_given_follow)

# WHAT: Time-to-convert. Days from signup to first post is short for most
#       converters (median ~2.3 days), days from post to follow are even
#       shorter (median ~1.1 days), and follow to DAU is slower (median ~6.8
#       days) — drawn from a lognormal distribution to get a realistic
#       right-skewed shape (a few users take a long time, most don't).
# WHY:  Time-to-convert is a real metric used on the dashboard's funnel
#       page, not just stage counts.
def lognormal_days(median_days, n):
    sigma = 0.6
    mu = np.log(median_days)
    return np.clip(rng.lognormal(mu, sigma, size=n), 0, 90)

days_to_post = lognormal_days(2.3, N_FUNNEL_USERS)
days_post_to_follow = lognormal_days(1.1, N_FUNNEL_USERS)
days_follow_to_dau = lognormal_days(6.8, N_FUNNEL_USERS)

first_post_at = np.where(
    reaches_post,
    [users_df["account_created_at"][i] + timedelta(days=float(days_to_post[i])) for i in range(N_FUNNEL_USERS)],
    None,
)
first_follow_at = np.where(
    reaches_follow,
    [first_post_at[i] + timedelta(days=float(days_post_to_follow[i])) if first_post_at[i] is not None else None
     for i in range(N_FUNNEL_USERS)],
    None,
)
dau_at = np.where(
    reaches_dau,
    [first_follow_at[i] + timedelta(days=float(days_follow_to_dau[i])) if first_follow_at[i] is not None else None
     for i in range(N_FUNNEL_USERS)],
    None,
)

users_df["first_post_at"] = first_post_at
users_df["first_follow_at"] = first_follow_at

# WHAT: Build funnel_events as a long/tidy table — one row per
#       user-per-stage-reached, rather than wide columns.
# WHY:  This is the shape the funnel SQL analyses (drop-off, time-to-convert)
#       are written against — it's how event/funnel data actually looks in
#       a real warehouse (e.g. Snowflake/BigQuery event tables).
funnel_rows = []
for i in range(N_FUNNEL_USERS):
    uidv = users_df["user_id"][i]
    funnel_rows.append((uid("fev"), uidv, "signup", users_df["account_created_at"][i], 0))
    if reaches_post[i]:
        funnel_rows.append((uid("fev"), uidv, "first_post", first_post_at[i], round(days_to_post[i], 1)))
    if reaches_follow[i]:
        days_since_signup = (first_follow_at[i] - users_df["account_created_at"][i]).days
        funnel_rows.append((uid("fev"), uidv, "first_follow", first_follow_at[i], days_since_signup))
    if reaches_dau[i]:
        days_since_signup = (dau_at[i] - users_df["account_created_at"][i]).days
        funnel_rows.append((uid("fev"), uidv, "dau", dau_at[i], days_since_signup))

funnel_events_df = pd.DataFrame(
    funnel_rows, columns=["event_id", "user_id", "stage", "reached_at", "days_since_signup"]
)

users_df.to_csv(OUT + "users.csv", index=False)
funnel_events_df.to_csv(OUT + "funnel_events.csv", index=False)
print(f"  users.csv: {len(users_df):,} rows")
print(f"  funnel_events.csv: {len(funnel_events_df):,} rows")
print(f"  Actual Signup->First Post drop-off: {100*(1-reaches_post.mean()):.1f}% "
      f"(target -64.0%)")

# ============================================================================
# PART 2 — REELS A/B TEST DATA
# WHAT: A separate population of experiment users, split into treatment
#       (more Reels density) and control, with sessions, Stories events,
#       Reels impressions/engagement.
# WHY:  This is the data behind the primary metric (+1.9% time spent), the
#       guardrails, and the headline twist (+18.3% Stories posting lift,
#       concentrated in never-posted-before users).
# ============================================================================
N_EXPERIMENT_USERS = 9_000  # scaled down from the brief's 2.4M (1/267th) -- sized to keep memory use sane
N_DAYS = 28

print("\nGenerating Part 2: experiment assignments, sessions, Stories, Reels events...")

exp_user_ids = [uid("exu") for _ in range(N_EXPERIMENT_USERS)]

# WHAT: 50/50 random assignment, with a small subset flagged as affected by
#       the (simulated) SRM bug from the project's pre-launch check.
# WHY:  Mirrors the real validity-check step — a portfolio reader can
#       actually query this column and see why those rows get excluded
#       downstream, rather than just reading about it in prose.
variant = rng.choice(["treatment", "control"], size=N_EXPERIMENT_USERS, p=[0.5, 0.5])

# WHAT: Decide which rows are "affected by the SRM bug" FIRST, then bias
# their variant assignment toward control (per the narrative: the buggy
# fallback hashing path disproportionately routed ATT-denied iOS users
# into control). This makes the bug actually produce a measurable skew in
# the raw data -- not just a label -- so 03_srm_bucket_check.sql's
# "before fix" query genuinely fails a chi-square check, and "after fix"
# (excluding these rows) is genuinely back to balanced.
# WHY: A portfolio dataset should let the SQL prove the story, not just
# illustrate it after the fact.
affected_by_srm_bug = rng.random(N_EXPERIMENT_USERS) < 0.042  # ~4.2% per the brief
variant = np.where(
    affected_by_srm_bug,
    rng.choice(["treatment", "control"], size=N_EXPERIMENT_USERS, p=[0.30, 0.70]),
    variant,
)
platform = rng.choice(["ios", "android"], size=N_EXPERIMENT_USERS, p=[0.55, 0.45])
att_status = np.where(
    platform == "ios",
    rng.choice(["granted", "denied"], size=N_EXPERIMENT_USERS, p=[0.91, 0.09]),
    "not_applicable",
)

# WHAT: Flag whether each experiment user had posted to Stories before the
#       test started (~64% had, ~36% had not) — this is the funnel-linked
#       segment used in Part 2's segment-cut analysis and in Part 3's tie
#       back to "are the new creators from this segment being discovered."
# WHY:  Without this flag, the headline segment finding (+41.2% posting
#       lift among never-posted users) couldn't be reproduced from the data.
had_posted_pre_test = rng.random(N_EXPERIMENT_USERS) < 0.64

experiment_assignments_df = pd.DataFrame({
    "user_id": exp_user_ids,
    "experiment_id": "reels_density_q2_2026",
    "variant": variant,
    "assigned_at": TEST_START,
    "bucketing_method": np.where(affected_by_srm_bug, "session_hash_fallback", "server_hash"),
    "affected_by_srm_bug": affected_by_srm_bug,
    "had_posted_pre_test": had_posted_pre_test,
    "platform": platform,
    "att_status": att_status,
})
experiment_assignments_df.to_csv(OUT + "experiment_assignments.csv", index=False)
print(f"  experiment_assignments.csv: {len(experiment_assignments_df):,} rows")

# WHAT: Generate one session per user per day for 28 days (simplified —
#       real users have variable session counts, but one row/day keeps the
#       file size manageable while preserving the daily time-spent metric).
#       Treatment users get a small time-spent boost (+1.9% on average) and
#       a small reduction in distinct creators seen per session (-6.3%, the
#       diversity guardrail).
# WHY:  This is the data behind the primary metric and the diversity
#       guardrail in the results table.
print("  Building sessions (this is the largest table)...")
sess_rows = []
is_treatment = (variant == "treatment")
for day in range(N_DAYS):
    day_date = TEST_START + timedelta(days=day)
    # WHAT: base minutes drawn from a lognormal centered near the control
    # mean (31.4 min); treatment gets a multiplicative +1.9% bump on top.
    base_minutes = rng.lognormal(mean=np.log(31.4), sigma=0.35, size=N_EXPERIMENT_USERS)
    minutes = np.where(is_treatment & ~affected_by_srm_bug, base_minutes * 1.019, base_minutes)
    base_diversity = rng.poisson(14.2, size=N_EXPERIMENT_USERS)
    diversity = np.where(is_treatment & ~affected_by_srm_bug,
                          np.maximum(1, (base_diversity * 0.937).astype(int)),
                          base_diversity)
    crashed = rng.random(N_EXPERIMENT_USERS) < 0.00083
    latency = rng.normal(np.where(is_treatment, 415, 412), 25, size=N_EXPERIMENT_USERS).astype(int)
    for i in range(N_EXPERIMENT_USERS):
        sess_rows.append((
            uid("ses"), exp_user_ids[i], day_date,
            int(minutes[i] * 60), int(diversity[i]), bool(crashed[i]), int(latency[i]),
        ))

sessions_df = pd.DataFrame(
    sess_rows,
    columns=["session_id", "user_id", "session_start", "session_duration_sec",
             "distinct_creators_seen", "crashed", "p50_feed_latency_ms"],
)
sessions_df.to_csv(OUT + "sessions.csv", index=False)
print(f"  sessions.csv: {len(sessions_df):,} rows")

# WHAT: Stories events — opens (consumption) and posts (creation), per user
#       per week. Treatment lifts opens slightly (+2.1%) and posts more
#       (+18.3%), with the posting lift concentrated in never-posted-before
#       users (the headline twist).
# WHY:  This is the data behind the "Stories didn't get cannibalized, it
#       went up" finding — the whole point of Part 2.
print("  Building Stories events...")
stories_rows = []
base_open_rate_per_week = 4.8 * 7  # ~33.6 opens/week baseline (4.8/day)
base_post_rate_overall = 0.082     # 8.2% of users post in a given week, baseline

for week in range(4):
    week_date = TEST_START + timedelta(days=week * 7)
    for i in range(N_EXPERIMENT_USERS):
        t = is_treatment[i] and not affected_by_srm_bug[i]
        # Opens (consumption) -- mild lift in treatment, no cannibalization
        open_rate = base_open_rate_per_week * (1.021 if t else 1.0)
        n_opens = rng.poisson(open_rate)
        for _ in range(n_opens):
            ts = week_date + timedelta(days=int(rng.integers(0, 7)))
            stories_rows.append((uid("sev"), exp_user_ids[i], "open", ts, False))

        # Posts (creation) -- this is the twist. Lift is much bigger for
        # users who had never posted before the test (+41.2%) than for
        # users who already had (+4.1%), and ramps across the 4 weeks
        # rather than decaying (weeks 1-4: +9.4%, +14.1%, +17.8%, +18.3%).
        weekly_ramp = [1.094, 1.141, 1.178, 1.183][week]
        if had_posted_pre_test[i]:
            post_prob = base_post_rate_overall * (1.041 if t else 1.0)
        else:
            lift = 1 + (weekly_ramp - 1) * 4.3  # never-posted segment lift is ~4.3x the population avg
            post_prob = (base_post_rate_overall * 0.6) * (lift if t else 1.0)
        posted = rng.random() < post_prob
        if posted:
            ts = week_date + timedelta(days=int(rng.integers(0, 7)))
            preceded = bool(t and rng.random() < 0.74)  # mechanism check: most treatment posts follow a Reel watch
            stories_rows.append((uid("sev"), exp_user_ids[i], "post", ts, preceded))

stories_events_df = pd.DataFrame(
    stories_rows, columns=["event_id", "user_id", "event_type", "event_at", "preceded_by_reel"]
)
stories_events_df.to_csv(OUT + "stories_events.csv", index=False)
print(f"  stories_events.csv: {len(stories_events_df):,} rows")

# WHAT: Reels feed impressions + engagement events (likes/comments/shares/
#       saves). Treatment sees more Reels slots and a higher engagement
#       rate (+12.5% relative).
# WHY:  Backs the secondary metric and the Reels-engagement novelty-decay
#       chart (decaying lift, contrasted against the Stories ramp above).
print("  Building Reels impressions and engagement events (sampled)...")
impressions_rows = []
engagement_rows = []
weekly_engagement_lift = [1.142, 1.091, 1.058, 1.046]  # decaying novelty pattern
for week in range(4):
    week_date = TEST_START + timedelta(days=week * 7)
    for i in range(N_EXPERIMENT_USERS):
        t = is_treatment[i] and not affected_by_srm_bug[i]
        n_reels_per_week = 18 if t else 11  # density: 1-in-3 vs 1-in-5 feed slots, approx weekly reel views
        for _ in range(n_reels_per_week):
            imp_id = uid("imp")
            ts = week_date + timedelta(days=int(rng.integers(0, 7)))
            impressions_rows.append((imp_id, exp_user_ids[i], ts, "reel", uid("cre")))
            base_eng_rate = 0.048
            eng_rate = base_eng_rate * (weekly_engagement_lift[week] if t else 1.0)
            if rng.random() < eng_rate:
                etype = rng.choice(["like", "comment", "share", "save"], p=[0.7, 0.1, 0.1, 0.1])
                engagement_rows.append((uid("eng"), imp_id, etype, ts))

feed_impressions_df = pd.DataFrame(
    impressions_rows, columns=["impression_id", "user_id", "served_at", "slot_type", "creator_id"]
)
reel_engagement_df = pd.DataFrame(
    engagement_rows, columns=["event_id", "impression_id", "event_type", "event_at"]
)
feed_impressions_df.to_csv(OUT + "feed_impressions.csv", index=False)
reel_engagement_df.to_csv(OUT + "reel_engagement_events.csv", index=False)
print(f"  feed_impressions.csv: {len(feed_impressions_df):,} rows")
print(f"  reel_engagement_events.csv: {len(reel_engagement_df):,} rows")

# ============================================================================
# PART 3 — DISCOVERY EQUITY TEST DATA
# WHAT: A creator directory (with follower counts and account age, so "new/
#       small creator" is a derivable flag, not a hardcoded label) and an
#       Explore/Search impressions log split across control (flat ranking)
#       and treatment (interest clusters + new-creator boost).
# WHY:  Backs the CTR comparison and — the metric that actually matters for
#       the equity question — % of clicks going to new/small creators.
# ============================================================================
N_DISCOVERY_USERS = 10_000
N_CREATORS = 2_000

print("\nGenerating Part 3: creator profiles, category taxonomy, Explore impressions...")

categories = ["Travel", "Tech", "Art", "Fitness", "Food", "Music", "Fashion", "Comedy"]
category_taxonomy_df = pd.DataFrame({
    "category_id": [f"cat_{i+1:02d}" for i in range(len(categories))],
    "category_name": categories,
    "description": [f"Content primarily about {c.lower()}" for c in categories],
})
category_taxonomy_df.to_csv(OUT + "category_taxonomy.csv", index=False)

# WHAT: Creator follower counts follow a power law (a small number of huge
#       accounts, a long tail of small ones) -- this is what makes "new
#       creators get buried" a real risk worth testing for, not a strawman.
# WHY:  Without a realistic power-law distribution, the equity metric
#       (% engagement to small creators) wouldn't mean anything -- in a
#       uniform distribution there'd be no "burying" effect to detect.
follower_counts = rng.pareto(a=1.2, size=N_CREATORS) * 80
follower_counts = np.clip(follower_counts, 0, 5_000_000).astype(int)
account_age_days = rng.integers(1, 1500, size=N_CREATORS)
creator_category = rng.choice(categories, size=N_CREATORS)

creator_profile_df = pd.DataFrame({
    "creator_id": [uid("cre") for _ in range(N_CREATORS)],
    "follower_count": follower_counts,
    "account_age_days": account_age_days,
    "category": creator_category,
})
# WHAT: Derive the "new/small creator" flag used throughout Part 3's SQL:
#       fewer than 100 followers OR joined in the last 30 days.
# WHY:  Matches the definition stated in the project brief so the dashboard
#       numbers and the SQL queries agree on what "new creator" means.
creator_profile_df["is_new_creator"] = (
    (creator_profile_df["follower_count"] < 100) | (creator_profile_df["account_age_days"] < 30)
)
creator_profile_df.to_csv(OUT + "creator_profile.csv", index=False)
print(f"  creator_profile.csv: {len(creator_profile_df):,} rows "
      f"({creator_profile_df['is_new_creator'].mean()*100:.1f}% flagged new/small)")

disc_user_ids = [uid("dsu") for _ in range(N_DISCOVERY_USERS)]
disc_variant = rng.choice(["A_control", "B_treatment"], size=N_DISCOVERY_USERS, p=[0.5, 0.5])

# WHAT: Each user gets a "home" category (their main interest) used to bias
#       what they're shown and to compute category-diversity guardrail.
# WHY:  Needed to simulate both the CTR lift in treatment AND the
#       serendipity-injection mitigation (1-in-10 items outside the user's
#       home category) without that mitigation, treatment would show a much
#       bigger, less defensible diversity drop.
disc_home_category = rng.choice(categories, size=N_DISCOVERY_USERS)

# WHAT: Pre-index creators by category for fast sampling, and precompute
# popularity weights ONCE per category (rather than inside the impression
# loop) so the control arm's popularity-weighted sampling is fast.
# WHY:  Recomputing a pandas lookup per impression (hundreds of thousands
# of times) is needlessly slow; precomputing plain numpy arrays up front
# keeps this script runnable in well under a minute.
creators_by_cat = {}
new_creators_by_cat = {}
weights_by_cat = {}
for c in categories:
    sub = creator_profile_df[creator_profile_df["category"] == c]
    creators_by_cat[c] = sub["creator_id"].to_numpy()
    new_creators_by_cat[c] = sub[sub["is_new_creator"]]["creator_id"].to_numpy()
    w = sub["follower_count"].to_numpy().astype(float) + 1
    weights_by_cat[c] = w / w.sum()

print("  Building Explore/Search impressions (sampled per user)...")
explore_rows = []
N_IMPRESSIONS_PER_USER = 12  # one week of typical Explore browsing, sampled down

for i in range(N_DISCOVERY_USERS):
    treatment = disc_variant[i] == "B_treatment"
    home_cat = disc_home_category[i]
    for _ in range(N_IMPRESSIONS_PER_USER):
        if treatment:
            # WHAT: 9 in 10 impressions come from the user's home cluster;
            # 1 in 10 is a serendipity injection from a random other category.
            cat = home_cat if rng.random() < 0.90 else rng.choice(categories)
            # WHAT: within the cluster, give new/small creators a deliberate
            # visibility boost rather than pure popularity ranking.
            pool_new = new_creators_by_cat[cat]
            pool_all = creators_by_cat[cat]
            if len(pool_new) > 0 and rng.random() < 0.22:  # boosted slot
                creator_id = rng.choice(pool_new)
            else:
                # WHAT: non-boosted slots still rank by popularity, same as
                # control -- this matters: without it, the equity lift would
                # just be an artifact of most creators being small accounts
                # (a power-law population is mostly long-tail by definition),
                # not a real measure of the boost mechanism's effect.
                creator_id = rng.choice(pool_all, p=weights_by_cat[cat])
            ctr = 0.071  # treatment CTR, calibrated higher than control
        else:
            # Control: flat ranking, effectively popularity-weighted toward
            # established creators -- new creators rarely surface.
            cat = rng.choice(categories)
            pool_all = creators_by_cat[cat]
            creator_id = rng.choice(pool_all, p=weights_by_cat[cat])
            ctr = 0.052  # control CTR baseline

        clicked = rng.random() < ctr
        explore_rows.append((
            uid("eim"), disc_user_ids[i], disc_variant[i], cat, creator_id,
            TEST_START + timedelta(days=int(rng.integers(0, 7))), bool(clicked),
        ))

explore_impressions_df = pd.DataFrame(
    explore_rows,
    columns=["impression_id", "user_id", "variant", "cluster_category", "creator_id", "shown_at", "clicked"],
)
explore_impressions_df.to_csv(OUT + "explore_impressions.csv", index=False)
print(f"  explore_impressions.csv: {len(explore_impressions_df):,} rows")

# ============================================================================
# SANITY CHECK SUMMARY
# WHAT: Print a quick comparison of generated-data rates vs. the brief's
#       target numbers.
# WHY:  Synthetic data should approximate the headline findings, not just
#       exist -- this lets anyone re-running the script immediately see
#       whether the generation logic is still producing the right story.
# ============================================================================
print("\n" + "=" * 60)
print("SANITY CHECK -- generated rates vs. brief targets")
print("=" * 60)

merged = sessions_df.merge(experiment_assignments_df, on="user_id")
clean = merged[~merged["affected_by_srm_bug"]]
time_by_variant = clean.groupby("variant")["session_duration_sec"].mean() / 60
lift = (time_by_variant["treatment"] / time_by_variant["control"] - 1) * 100
print(f"Time spent lift: {lift:+.1f}% (target +1.9%)")

posts = stories_events_df[stories_events_df["event_type"] == "post"].merge(
    experiment_assignments_df, on="user_id"
)
posts_clean = posts[~posts["affected_by_srm_bug"]]
posting_users_by_variant = posts_clean.groupby("variant")["user_id"].nunique()
total_by_variant = experiment_assignments_df[~experiment_assignments_df["affected_by_srm_bug"]].groupby("variant")["user_id"].nunique()
posting_rate = posting_users_by_variant / total_by_variant
posting_lift = (posting_rate["treatment"] / posting_rate["control"] - 1) * 100
print(f"Stories posting rate lift: {posting_lift:+.1f}% (target +18.3%)")

ctr_by_variant = explore_impressions_df.groupby("variant")["clicked"].mean() * 100
print(f"Explore CTR -- control: {ctr_by_variant['A_control']:.1f}%, "
      f"treatment: {ctr_by_variant['B_treatment']:.1f}%")

new_creator_share = explore_impressions_df.merge(
    creator_profile_df[["creator_id", "is_new_creator"]], on="creator_id"
)
clicked_only = new_creator_share[new_creator_share["clicked"]]
new_share_by_variant = clicked_only.groupby("variant")["is_new_creator"].mean() * 100
print(f"% of clicks going to new/small creators -- control: {new_share_by_variant['A_control']:.1f}%, "
      f"treatment: {new_share_by_variant['B_treatment']:.1f}%")

print("\nAll CSVs written to ./data/")
