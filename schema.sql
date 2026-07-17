-- ============================================================================
-- schema.sql
-- ============================================================================
-- WHAT: Full data model for the Instagram three-part project --
--       Part 1 (Funnel), Part 2 (Reels A/B Test), Part 3 (Discovery Equity).
-- WHY:  One schema, ten tables, shared across all three analyses -- this is
--       what makes Part 3's "funnel-linked segment" and "did the experiment's
--       new creators actually get discovered" questions answerable with a
--       JOIN instead of a separate disconnected dataset per part.
-- LOAD ORDER: tables are listed in dependency order -- run top to bottom so
--       foreign keys resolve (e.g. users before funnel_events).
-- ============================================================================

-- ----------------------------------------------------------------------------
-- PART 1: FUNNEL TABLES
-- ----------------------------------------------------------------------------

-- WHAT: One row per signed-up user.
-- WHY:  The root of the funnel -- every other funnel/experiment table joins
--       back to this for cohort definition.
CREATE TABLE users (
    user_id             VARCHAR(20)   PRIMARY KEY,
    account_created_at  TIMESTAMP     NOT NULL,
    first_post_at       TIMESTAMP,                  -- NULL if user never posted
    first_follow_at     TIMESTAMP,                  -- NULL if user never followed anyone
    country             VARCHAR(2)    NOT NULL       -- US / CA
);

-- WHAT: One row per user, per funnel stage reached (signup / first_post /
--       first_follow / dau). A user who never reaches a stage simply has
--       no row for it -- this is what makes drop-off computable via COUNT.
-- WHY:  Tidy/long event format mirrors how real warehouse event tables are
--       shaped (e.g. Snowflake/BigQuery), and is what the funnel SQL
--       analyses (01, 02) are written against.
CREATE TABLE funnel_events (
    event_id            VARCHAR(20)   PRIMARY KEY,
    user_id             VARCHAR(20)   NOT NULL REFERENCES users(user_id),
    stage               VARCHAR(20)   NOT NULL,      -- signup / first_post / first_follow / dau
    reached_at           TIMESTAMP     NOT NULL,
    days_since_signup    NUMERIC(6,1)  NOT NULL
);

-- ----------------------------------------------------------------------------
-- PART 2: REELS A/B TEST TABLES
-- ----------------------------------------------------------------------------

-- WHAT: One row per user enrolled in the Reels density experiment.
-- WHY:  The anchor table for every Part 2 (and Part 3 cross-reference)
--       query -- variant, SRM-bug flag, and the funnel-linked segment flag
--       (had_posted_pre_test) all live here.
CREATE TABLE experiment_assignments (
    user_id              VARCHAR(20)   PRIMARY KEY,   -- not a FK to users -- separate experiment cohort
    experiment_id        VARCHAR(30)   NOT NULL,       -- 'reels_density_q2_2026'
    variant              VARCHAR(10)   NOT NULL,       -- 'treatment' / 'control'
    assigned_at           TIMESTAMP     NOT NULL,
    bucketing_method      VARCHAR(30)   NOT NULL,       -- 'server_hash' or 'session_hash_fallback' (buggy)
    affected_by_srm_bug   BOOLEAN       NOT NULL,        -- TRUE = exclude from all analysis
    had_posted_pre_test   BOOLEAN       NOT NULL,        -- the funnel-linked segment flag
    platform              VARCHAR(10)   NOT NULL,        -- ios / android
    att_status             VARCHAR(20)   NOT NULL         -- granted / denied / not_applicable
);

-- WHAT: One row per user per day of the test, with time spent and the
--       content-diversity guardrail metric.
-- WHY:  Backs the primary metric (daily time spent) and the diversity
--       guardrail.
CREATE TABLE sessions (
    session_id              VARCHAR(20)   PRIMARY KEY,
    user_id                  VARCHAR(20)   NOT NULL REFERENCES experiment_assignments(user_id),
    session_start             TIMESTAMP     NOT NULL,
    session_duration_sec      INT           NOT NULL,
    distinct_creators_seen    INT           NOT NULL,
    crashed                    BOOLEAN       NOT NULL,
    p50_feed_latency_ms        INT           NOT NULL
);

-- WHAT: One row per Stories interaction -- either an 'open' (consumption)
--       or a 'post' (creation). preceded_by_reel flags whether the same
--       session included a Reel watch right before a post.
-- WHY:  This is the single most important table in the project -- it's
--       what separates the "Stories went down" assumption from the
--       "Stories posting went up" finding, and the mechanism check.
CREATE TABLE stories_events (
    event_id              VARCHAR(20)   PRIMARY KEY,
    user_id                VARCHAR(20)   NOT NULL REFERENCES experiment_assignments(user_id),
    event_type             VARCHAR(10)   NOT NULL,     -- 'open' / 'post'
    event_at                TIMESTAMP     NOT NULL,
    preceded_by_reel        BOOLEAN       NOT NULL      -- mechanism check (Analysis 8)
);

-- WHAT: One row per Reels slot served to a user.
-- WHY:  Denominator for the Reels engagement rate metric.
CREATE TABLE feed_impressions (
    impression_id          VARCHAR(20)   PRIMARY KEY,
    user_id                  VARCHAR(20)   NOT NULL REFERENCES experiment_assignments(user_id),
    served_at                 TIMESTAMP     NOT NULL,
    slot_type                  VARCHAR(15)   NOT NULL,   -- 'reel' (only type generated in this dataset)
    creator_id                  VARCHAR(20)   NOT NULL
);

-- WHAT: One row per engagement action (like/comment/share/save) on a Reel.
-- WHY:  Numerator for the Reels engagement rate metric; joins back to
--       feed_impressions for the rate calculation.
CREATE TABLE reel_engagement_events (
    event_id               VARCHAR(20)   PRIMARY KEY,
    impression_id            VARCHAR(20)   NOT NULL REFERENCES feed_impressions(impression_id),
    event_type                VARCHAR(15)   NOT NULL,    -- like / comment / share / save
    event_at                   TIMESTAMP     NOT NULL
);

-- ----------------------------------------------------------------------------
-- PART 3: DISCOVERY EQUITY TABLES
-- ----------------------------------------------------------------------------

-- WHAT: The cluster definitions used in the Explore/Search treatment arm.
-- WHY:  Lookup table -- keeps category names consistent and queryable
--       rather than hardcoded strings scattered across other tables.
CREATE TABLE category_taxonomy (
    category_id            VARCHAR(10)   PRIMARY KEY,
    category_name            VARCHAR(30)   NOT NULL,
    description                VARCHAR(100)
);

-- WHAT: One row per creator, with follower count and account age -- the
--       fields needed to define "new/small creator" (the equity question).
-- WHY:  Without follower_count and account_age_days, there's no way to
--       check whether Discovery is actually surfacing new creators or just
--       relabeling the same popular accounts under category headers.
CREATE TABLE creator_profile (
    creator_id              VARCHAR(20)   PRIMARY KEY,
    follower_count            INT           NOT NULL,
    account_age_days          INT           NOT NULL,
    category                   VARCHAR(30)   NOT NULL,
    is_new_creator             BOOLEAN       NOT NULL    -- follower_count < 100 OR account_age_days < 30
);

-- WHAT: One row per Explore/Search impression -- which variant, which
--       cluster, which creator was shown, and whether the user clicked.
-- WHY:  This is the table every Part 3 analysis runs against: CTR by
--       variant, % of clicks to new creators (the equity metric), and
--       category diversity (the filter-bubble guardrail).
CREATE TABLE explore_impressions (
    impression_id            VARCHAR(20)   PRIMARY KEY,
    user_id                    VARCHAR(20)   NOT NULL,    -- separate Discovery-test cohort, not a FK to users
    variant                      VARCHAR(15)   NOT NULL,    -- 'A_control' / 'B_treatment'
    cluster_category             VARCHAR(30)   NOT NULL,    -- see note below on category_taxonomy join
    creator_id                    VARCHAR(20)   NOT NULL REFERENCES creator_profile(creator_id),
    shown_at                       TIMESTAMP     NOT NULL,
    clicked                         BOOLEAN       NOT NULL
);

-- NOTE: cluster_category stores the category name directly rather than a
-- formal FK to category_taxonomy (which is keyed on category_id) -- this
-- keeps the table queryable without an extra join for the common case.
-- A production schema would add a UNIQUE constraint on category_name and
-- a proper FK here instead.
