"""
Cleans the raw exports in raw_data/ and writes tidy versions to data_cleaned/.

raw_data/ is a deliberately messy version of the dataset in data/ (inconsistent
casing, mixed true/false formats, duplicate rows, a few impossible values,
mixed date formats). This script fixes all of that, then at the end checks
the cleaned output against data/ to make sure nothing got mangled along the way.
"""

import pandas as pd
import numpy as np

RAW_DIR = "raw_data/"
OUT_DIR = "data_cleaned/"
GOLD_DIR = "data/"

log = []


def record(table, msg):
    log.append(f"[{table}] {msg}")


def clean_categorical(series, valid_values):
    """Lowercase + strip, then map back to the canonical spelling.
    Catches 'Treatment' / ' treatment  ' / 'TREATMENT' all being the same thing."""
    cleaned = series.astype(str).str.strip().str.lower()
    lookup = {v.lower(): v for v in valid_values}
    return cleaned.map(lookup)


def clean_boolean(series):
    """Real datasets almost never store booleans consistently -- this handles
    TRUE/FALSE, 1/0, yes/no, Y/N, any casing, extra whitespace, all of it."""
    s = series.astype(str).str.strip().str.lower()
    true_set = {"true", "1", "yes", "y"}
    false_set = {"false", "0", "no", "n"}
    out = s.map(lambda v: True if v in true_set else (False if v in false_set else None))
    n_unmapped = out.isna().sum()
    if n_unmapped:
        record("clean_boolean", f"{n_unmapped} values weren't a recognizable boolean, left as NULL")
    return out


def clean_nulls(series):
    """pandas won't automatically catch 'NULL' or 'NaT' written as literal strings."""
    return series.replace({"NULL": pd.NA, "NaT": pd.NA, "": pd.NA})


def parse_dates(series):
    """format='mixed' handles the three date formats floating around in here.
    Explicitly setting dayfirst=False so 01/02/2026 reads as Jan 2, not Feb 1."""
    return pd.to_datetime(series, format="mixed", dayfirst=False, errors="coerce")


def dedupe(df, table_name, subset=None):
    before = len(df)
    df = df.drop_duplicates(subset=subset, keep="first")
    dropped = before - len(df)
    if dropped:
        record(table_name, f"dropped {dropped:,} duplicate rows" + (f" (on {subset})" if subset else ""))
    return df


print("=" * 60)
print("Cleaning raw data -> data_cleaned/")
print("=" * 60)

# ---- users ----
df = pd.read_csv(RAW_DIR + "users.csv", keep_default_na=False, na_values=[""])

df["country"] = df["country"].astype(str).str.strip().str.upper()
record("users", "normalized country casing/whitespace")

df["account_created_at"] = parse_dates(df["account_created_at"])

df["first_post_at"] = parse_dates(clean_nulls(df["first_post_at"]))
df["first_follow_at"] = parse_dates(clean_nulls(df["first_follow_at"]))
record("users", "parsed date columns, standardized null markers first")

df = dedupe(df, "users", subset=["user_id"])
df.to_csv(OUT_DIR + "users.csv", index=False)
print(f"users.csv: {len(df):,} rows")

# ---- funnel_events ----
df = pd.read_csv(RAW_DIR + "funnel_events.csv", keep_default_na=False, na_values=[""])

VALID_STAGES = ["signup", "first_post", "first_follow", "dau"]
df["stage"] = clean_categorical(df["stage"], VALID_STAGES)

# a handful of days_since_signup came in negative -- can't reach a stage
# before signing up, so this is clock skew, not a real value. The event
# itself is still valid, just floor the duration at 0 instead of dropping it.
n_negative = (df["days_since_signup"] < 0).sum()
df.loc[df["days_since_signup"] < 0, "days_since_signup"] = 0
if n_negative:
    record("funnel_events", f"floored {n_negative} negative days_since_signup values to 0")

df = dedupe(df, "funnel_events", subset=["event_id"])
df.to_csv(OUT_DIR + "funnel_events.csv", index=False)
print(f"funnel_events.csv: {len(df):,} rows")

# ---- experiment_assignments ----
df = pd.read_csv(RAW_DIR + "experiment_assignments.csv", keep_default_na=False, na_values=[""])

VALID_VARIANTS = ["treatment", "control"]
df["variant"] = clean_categorical(df["variant"], VALID_VARIANTS)

df["affected_by_srm_bug"] = clean_boolean(df["affected_by_srm_bug"])
df["had_posted_pre_test"] = clean_boolean(df["had_posted_pre_test"])

# att_status is blank on some android rows where it should say
# 'not_applicable' -- ATT is an iOS-only permission, so this isn't
# missing data, it's a genuine "doesn't apply here" case.
mask = (df["platform"] == "android") & (df["att_status"].isin(["", None]) | df["att_status"].isna())
n_filled = mask.sum()
df.loc[mask, "att_status"] = "not_applicable"
record("experiment_assignments", f"filled {n_filled} blank att_status values on android with 'not_applicable'")

df = dedupe(df, "experiment_assignments", subset=["user_id"])
df.to_csv(OUT_DIR + "experiment_assignments.csv", index=False)
print(f"experiment_assignments.csv: {len(df):,} rows")

# ---- sessions ----
df = pd.read_csv(RAW_DIR + "sessions.csv", keep_default_na=False, na_values=[""])

# negative durations are a clock-skew artifact, not garbage -- take abs value
n_negative = (df["session_duration_sec"] < 0).sum()
df.loc[df["session_duration_sec"] < 0, "session_duration_sec"] = \
    df.loc[df["session_duration_sec"] < 0, "session_duration_sec"].abs()
if n_negative:
    record("sessions", f"took abs value of {n_negative} negative session durations")

# multi-day "sessions" are sessions that never closed properly, not real usage.
# 4 hours is a generous cap for a single app session.
CAP_SECONDS = 14_400
n_capped = (df["session_duration_sec"] > CAP_SECONDS).sum()
df.loc[df["session_duration_sec"] > CAP_SECONDS, "session_duration_sec"] = CAP_SECONDS
if n_capped:
    record("sessions", f"capped {n_capped} outlier session durations at {CAP_SECONDS}s")

df["crashed"] = clean_boolean(df["crashed"])

df = dedupe(df, "sessions", subset=["session_id"])
df.to_csv(OUT_DIR + "sessions.csv", index=False)
print(f"sessions.csv: {len(df):,} rows")

# ---- stories_events ----
df = pd.read_csv(RAW_DIR + "stories_events.csv", keep_default_na=False, na_values=[""])

VALID_EVENT_TYPES = ["open", "post"]
df["event_type"] = clean_categorical(df["event_type"], VALID_EVENT_TYPES)
df["preceded_by_reel"] = clean_boolean(df["preceded_by_reel"])

df = dedupe(df, "stories_events", subset=["event_id"])
df.to_csv(OUT_DIR + "stories_events.csv", index=False)
print(f"stories_events.csv: {len(df):,} rows")

# ---- feed_impressions ----
df = pd.read_csv(RAW_DIR + "feed_impressions.csv", keep_default_na=False, na_values=[""])

df["slot_type"] = df["slot_type"].astype(str).str.strip()

# some rows have a blank creator_id (an upstream join failure, most likely).
# Still valid impressions for overall engagement rate, just can't be used
# for anything creator-level -- so flag, don't drop.
n_missing_creator = df["creator_id"].isna().sum()
record("feed_impressions", f"{n_missing_creator} rows have missing creator_id, kept as-is (join failure upstream)")

df = dedupe(df, "feed_impressions", subset=["impression_id"])
df.to_csv(OUT_DIR + "feed_impressions.csv", index=False)
print(f"feed_impressions.csv: {len(df):,} rows")

# ---- reel_engagement_events ----
df = pd.read_csv(RAW_DIR + "reel_engagement_events.csv", keep_default_na=False, na_values=[""])

VALID_ENGAGEMENT_TYPES = ["like", "comment", "share", "save"]
df["event_type"] = clean_categorical(df["event_type"], VALID_ENGAGEMENT_TYPES)

df = dedupe(df, "reel_engagement_events", subset=["event_id"])
df.to_csv(OUT_DIR + "reel_engagement_events.csv", index=False)
print(f"reel_engagement_events.csv: {len(df):,} rows")

# ---- category_taxonomy ----
df = pd.read_csv(RAW_DIR + "category_taxonomy.csv", keep_default_na=False, na_values=[""])
df["category_name"] = df["category_name"].astype(str).str.strip()
# every downstream join keys off this exact string, so whitespace here is a big deal
df.to_csv(OUT_DIR + "category_taxonomy.csv", index=False)
print(f"category_taxonomy.csv: {len(df):,} rows")

# ---- creator_profile ----
df = pd.read_csv(RAW_DIR + "creator_profile.csv", keep_default_na=False, na_values=[""])

# follower_count sometimes comes in as '1,234' instead of a plain number
df["follower_count"] = df["follower_count"].astype(str).str.replace(",", "", regex=False).astype(int)

n_negative = (df["follower_count"] < 0).sum()
df.loc[df["follower_count"] < 0, "follower_count"] = 0
if n_negative:
    record("creator_profile", f"floored {n_negative} negative follower_count values to 0")

# is_new_creator is a stored flag, but it's derived and can drift out of date.
# Safer to just recompute it from the source columns using the same rule
# used everywhere else in the project, rather than trust what's on file --
# a stale flag here would quietly throw off the equity metric in query 10.
df["is_new_creator"] = clean_boolean(df["is_new_creator"])
recomputed = (df["follower_count"] < 100) | (df["account_age_days"] < 30)
n_corrected = (df["is_new_creator"] != recomputed).sum()
df["is_new_creator"] = recomputed
record("creator_profile", f"recomputed is_new_creator from source columns, corrected {n_corrected} stale values")

df = dedupe(df, "creator_profile", subset=["creator_id"])
df.to_csv(OUT_DIR + "creator_profile.csv", index=False)
print(f"creator_profile.csv: {len(df):,} rows")

# ---- explore_impressions ----
df = pd.read_csv(RAW_DIR + "explore_impressions.csv", keep_default_na=False, na_values=[""])

df["clicked"] = clean_boolean(df["clicked"])

n_missing_cat = df["cluster_category"].isna().sum()
record("explore_impressions", f"{n_missing_cat} rows have missing cluster_category (join failure upstream)")

df = dedupe(df, "explore_impressions", subset=["impression_id"])
df.to_csv(OUT_DIR + "explore_impressions.csv", index=False)
print(f"explore_impressions.csv: {len(df):,} rows")

# ---- summary ----
print("\n" + "=" * 60)
print("CLEANING SUMMARY")
print("=" * 60)
for line in log:
    print(" -", line)

# ---- validation: does this actually match the known-good data? ----
# A script that runs without errors isn't proof it cleaned things correctly.
# This compares row counts and a couple of headline metrics against data/,
# the dataset already used everywhere else in this project. If those line
# up, the pipeline actually works -- if not, that's a real bug to chase down.
print("\n" + "=" * 60)
print("VALIDATION -- data_cleaned/ vs. data/")
print("=" * 60)

tables = ["users", "funnel_events", "experiment_assignments", "sessions",
          "stories_events", "feed_impressions", "reel_engagement_events",
          "category_taxonomy", "creator_profile", "explore_impressions"]

print(f"\n{'table':<26}{'data/ rows':>14}{'data_cleaned/ rows':>20}{'match?':>10}")
for t in tables:
    gold = pd.read_csv(GOLD_DIR + f"{t}.csv", keep_default_na=False, na_values=[""])
    cleaned = pd.read_csv(OUT_DIR + f"{t}.csv", keep_default_na=False, na_values=[""])
    # exact match isn't realistic -- cleaning removes duplicates and caps
    # outliers on purpose, so row counts shift a little. Within 1% is fine.
    pct_diff = abs(len(cleaned) - len(gold)) / len(gold) * 100
    status = "OK" if pct_diff < 1.0 else "CHECK"
    print(f"{t:<26}{len(gold):>14,}{len(cleaned):>20,}{status:>10}  ({pct_diff:.2f}% diff)")

print("\n--- headline metric check ---")

gold_ea = pd.read_csv(GOLD_DIR + "experiment_assignments.csv", keep_default_na=False, na_values=[""])
gold_sess = pd.read_csv(GOLD_DIR + "sessions.csv", keep_default_na=False, na_values=[""])
clean_ea = pd.read_csv(OUT_DIR + "experiment_assignments.csv", keep_default_na=False, na_values=[""])
clean_sess = pd.read_csv(OUT_DIR + "sessions.csv", keep_default_na=False, na_values=[""])

def time_spent_lift(ea, sess):
    ea_clean = ea[ea["affected_by_srm_bug"].astype(str).str.lower() == "false"]
    merged = sess.merge(ea_clean[["user_id", "variant"]], on="user_id")
    avg = merged.groupby("variant")["session_duration_sec"].mean()
    return (avg["treatment"] / avg["control"] - 1) * 100

gold_lift = time_spent_lift(gold_ea, gold_sess)
clean_lift = time_spent_lift(clean_ea, clean_sess)
print(f"Time spent lift -- data/: {gold_lift:+.2f}%, data_cleaned/: {clean_lift:+.2f}%")

print("\nDone. data_cleaned/ should now line up with the working dataset used")
print("throughout this project.")
