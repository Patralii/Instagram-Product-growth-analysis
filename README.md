# Should Instagram Expand Reels — and Is Discovery Fair to the New Creators It Creates?

*A funnel analysis, an A/B test, and a Discovery equity test, told as one investigation.*

> "Before we test anything, we needed to know where Instagram was quietly losing people."

---

## The business problem

Before deciding whether to expand Reels surface area in the feed, the team needed to understand three things, in sequence: where users were dropping off in the core engagement funnel; whether more Reels exposure would help or hurt overall engagement; and — if that test successfully turned previously-silent users into first-time creators — whether the rest of the product actually gave those new creators a fair chance to be seen.

This repo contains the full analysis: a synthetic but methodologically real dataset, the SQL behind every finding, and an interactive dashboard.

**A note on the data:** every number below comes from a real, generated, row-level dataset in `/data` — not hand-typed summary statistics. The population is synthetic (real Instagram data isn't accessible for a portfolio project), but it's scaled down from the project's real-world targets while preserving the same rates and relationships, so every query in `/queries` actually runs against it and returns numbers in the right neighborhood. The methodology transfers directly to a real dataset of any size.

**A note on exact figures:** the dashboard (`dashboard/instagram_dashboard.html`) was written first, with illustrative target numbers (e.g. "31.4 → 32.0 min," "8.2% → 9.7% weekly posting rate") describing the intended story at full scale. The dataset in `/data` was then built to reproduce those same *rates and directions* at a smaller, laptop-friendly scale — so the absolute numbers you get by querying `/data` directly (e.g. 33.34 → 34.01 min, a 4-week cumulative posting rate of 24.95% → 29.02%) won't match the dashboard's figures exactly, but the relative lifts and the underlying story do. This README's tables use the dataset's actual queried numbers, not the dashboard's illustrative ones.

---

## Part 1: The Funnel

Tracked 50,000 signups through *Signup → First Post → First Follow → Daily Active User*.

| Stage | Users | % of Signups | Drop-off |
|---|---|---|---|
| Signup | 50,000 | 100.0% | — |
| First Post | 17,979 | 36.0% | **-64.0%** |
| First Follow | 11,676 | 23.4% | -35.1% |
| DAU (Day 30) | 5,564 | 11.1% | -52.3% |

**Steepest drop-off: Signup → First Post (-64%).** This is the earliest, largest leak in the funnel — most users sign up and never create anything at all. It's also the business case for testing Reels: a passive, consumption-first format is a plausible lever on a population that never gets far enough into the product to find out if they'd like creating.

Query: [`queries/01_funnel_stage_conversion.sql`](queries/01_funnel_stage_conversion.sql), [`queries/02_funnel_time_to_convert.sql`](queries/02_funnel_time_to_convert.sql)

---

## Part 2: The Reels A/B Test

**Experiment:** Reels feed density increased from 1-in-5 to 1-in-3 feed positions. 9,000 users, 50/50 split, 28-day window, randomized at `user_id`.

**Common assumption tested:** more Reels exposure would cannibalize Stories consumption and reduce overall time spent.

**Pre-launch validity check:** A day-1 SRM check on the raw assignment data failed (control/treatment counts skewed apart) — traced to a simulated ATT-related client-side bucketing bug. Excluding the affected rows (flagged via `affected_by_srm_bug`) restores balance before any result is trusted.

**Results (from the actual generated dataset, SRM-clean):**

| Metric | Control | Treatment | Rel. Δ |
|---|---|---|---|
| Daily time spent (primary) | 33.34 min | 34.01 min | **+2.0%** |
| Stories opens/day (consumption) | 4.80 | 4.91 | +2.4% (not down) |
| **Stories posting rate (creation, 4-week cumulative)** | 24.95% | 29.02% | **+16.3%** |
| Distinct creators/session | baseline | — | -6.3% |

**The unexpected finding:** Stories consumption didn't drop — it rose slightly (+2.4%) — and Stories *posting* rose sharply (+16.3%), concentrated almost entirely in users who had never posted before the test (the segment cut in query 06 shows this directly: posting rate roughly doubles for never-posted users in treatment, vs. a small lift for users who'd already posted). Reels exposure didn't steal from Stories; it appears to have inspired creation.

> "Everyone assumed Reels was stealing from Stories. The data had other plans."

**Durability check:** Reels engagement lift decays like a classic novelty effect, week over week. Stories posting lift does the opposite — it ramps, consistent with habit formation rather than curiosity.

Queries: [`03`](queries/03_srm_bucket_check.sql) (SRM) · [`04`](queries/04_primary_metric_aggregation.sql) (primary metric) · [`05`](queries/05_stories_posting_vs_opens.sql) (the twist) · [`06`](queries/06_funnel_linked_segment_cut.sql) (funnel-linked segment) · [`07`](queries/07_weekly_novelty_ramp_trend.sql) (novelty vs. ramp) · [`08`](queries/08_mechanism_reel_then_post.sql) (mechanism check)

---

## Part 3: The Discovery Equity Test

Part 2 created a wave of brand-new, first-time creators. Part 3 asks the natural follow-up: are those creators actually getting discovered, or does Explore/Search just bury them under already-popular accounts?

**The experiment:** Explore/Search split into Group A (current flat, popularity-ranked feed) and Group B (Interest-Based Clusters — Travel, Tech, Art, etc. — with two fairness mechanisms designed in from the start: a serendipity injection of ~1-in-10 impressions outside a user's home category, and a deliberate ranking boost for new/small creators within each cluster).

**Results (10,000 users, from the actual dataset):**

| Metric | Control | Treatment | Change |
|---|---|---|---|
| Click-through rate (CTR) | 5.05% | 7.10% | **+40.6%** relative |
| % of clicks to new/small creators | 11.1% | 31.3% | **+182%** relative |
| Distinct categories seen/user/week | 6.41 | 1.96 | **-69.4%** |

> "Part 2 created thousands of new creators overnight. Part 3 asks whether anyone would ever actually see them."

**The honest read:** Both wins are real — CTR is up substantially, and the new/small-creator click share nearly tripled, direct evidence the boost mechanism is doing real work, not just relabeling popular accounts under topic headers. But the category-diversity drop is larger than the "small, monitorable" risk anticipated going in. This result does not support a clean global ship — it supports a pilot, with a higher serendipity-injection rate, before a wider rollout.

Queries: [`09`](queries/09_discovery_ctr_by_variant.sql) (CTR) · [`10`](queries/10_new_creator_engagement_share.sql) (the equity metric) · [`11`](queries/11_category_diversity_guardrail.sql) (the filter-bubble guardrail)

---

## The decision

**Ship + Pilot.** Expand Reels density to 1-in-3 globally, paired with a Stories-creation prompt targeted at the pre-First-Post segment identified in the funnel. Pilot the Discovery clustering redesign on a handful of categories with a higher serendipity rate, and re-measure the diversity guardrail before deciding on a full rollout.

The funnel found the leak. The experiment found an accidental fix. Discovery checked whether that fix actually pays off downstream — and found a real but incomplete answer, which is exactly the kind of result worth shipping carefully rather than either ignoring or over-claiming.

---

## Repo structure

```
.
├── README.md                 (this file)
├── requirements.txt           (for data/generate_data.py and data_cleaning.py)
├── schema.sql                 (10-table data model, all 3 parts)
├── data_cleaning.py            (raw_data/ -> data_cleaned/, with What/Why comments at every step)
├── queries/                   (11 SQL analyses, each with What/Why comments)
│   ├── 01_funnel_stage_conversion.sql
│   ├── 02_funnel_time_to_convert.sql
│   ├── 03_srm_bucket_check.sql
│   ├── 04_primary_metric_aggregation.sql
│   ├── 05_stories_posting_vs_opens.sql
│   ├── 06_funnel_linked_segment_cut.sql
│   ├── 07_weekly_novelty_ramp_trend.sql
│   ├── 08_mechanism_reel_then_post.sql
│   ├── 09_discovery_ctr_by_variant.sql
│   ├── 10_new_creator_engagement_share.sql
│   └── 11_category_diversity_guardrail.sql
├── data/                       (the clean, working dataset used throughout this project)
│   ├── generate_data.py       (generates everything below, with What/Why comments at every step)
│   ├── users.csv
│   ├── funnel_events.csv
│   ├── experiment_assignments.csv
│   ├── sessions.csv
│   ├── stories_events.csv
│   ├── feed_impressions.csv
│   ├── reel_engagement_events.csv
│   ├── category_taxonomy.csv
│   ├── creator_profile.csv
│   └── explore_impressions.csv
├── raw_data/                   (a realistic messy "before cleaning" version of /data)
│   ├── make_messy_data.py     (generates everything below: /data -> /raw_data)
│   └── *.csv                  (same 10 tables, with inconsistent casing, mixed booleans,
│                                3 different null styles, duplicates, and a few impossible values)
├── data_cleaned/                (output of data_cleaning.py -- reconstructs /data from /raw_data)
│   └── *.csv
└── dashboard/
    └── instagram_dashboard.html   (self-contained, no build step — open directly in a browser)
```

**Why both `/data` and `/raw_data` + `data_cleaning.py` exist:** `/data` is the clean, working dataset every query and the dashboard are built against. `/raw_data` simulates what that dataset would have looked like *before* cleaning — generated by intentionally reintroducing realistic data-quality issues into copies of `/data` (see `raw_data/make_messy_data.py`). `data_cleaning.py` then cleans `/raw_data` back into `/data_cleaned`, and validates its output against `/data` directly. This exists to demonstrate the cleaning step itself, not because `/data` was ever actually messy.

## How to use this repo

**View the dashboard:** open `dashboard/instagram_dashboard.html` directly in any browser — no server or build step needed.

**Regenerate the clean dataset from scratch:**
```bash
pip install -r requirements.txt
python3 data/generate_data.py
```
This rebuilds all 10 CSVs in `/data` from scratch with a fixed random seed (reproducible), and prints a sanity-check comparing the generated rates against this project's target numbers.

**See the cleaning pipeline in action:**
```bash
python3 raw_data/make_messy_data.py    # /data -> /raw_data (intentionally messy)
python3 data_cleaning.py               # /raw_data -> /data_cleaned (cleaned), validated against /data
```
The cleaning script prints a one-line summary of every fix applied (duplicates dropped, casing normalized, booleans standardized, a stale derived flag recomputed from source columns, etc.), then validates row counts and a headline metric (the experiment's time-spent lift) against the original `/data` to confirm the pipeline actually reconstructs usable data.

**Run the SQL:** load `schema.sql` into PostgreSQL, then load the CSVs in `/data` (or `/data_cleaned`) into their matching tables, then run any file in `/queries`. Two files (`02` and `07`) include a SQLite-compatible fallback statement for quick local testing, since PostgreSQL-specific functions (`PERCENTILE_CONT`, `DATE_TRUNC`) aren't universally supported — the primary statement in each file is the real, intended PostgreSQL version.

**Build it in Tableau Public / Looker Studio:** import the CSVs in `/data` (or connect directly to a PostgreSQL instance loaded with `schema.sql`) and recreate the dashboard's charts using the same query logic in `/queries`.
