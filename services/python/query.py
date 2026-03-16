# %% [markdown]
# # Langara VR ECE App — Research Queries
# 
# **Research Focus:** How does the VR app support ECE student learning?
# 
# **Connection:** Trino → MongoDB (`mongo_prod` catalog, `langara-dev-client` schema)
# 
# **SSH tunnel required:**
# ```bash
# ssh -L 8080:localhost:8080 <user>@20.151.177.201
# ```
# 
# **Tables:**
# - `levelflows` — one row per student session (includes `scene[]` JSON array + `conversations[]` nested inside)
# - `users` — student/instructor accounts
# - `levels` — level definitions
# - `trainingmodels` — NLP model accuracy records
# 
# ---
# 
# ## Sections
# 1. [Setup](#1-setup)
# 2. [Existing Dashboard Queries (Charts 01–18)](#2-existing-dashboard-queries)
# 3. [New Research Queries](#3-new-research-queries)

# %% [markdown]
# ## 1. Setup

# %%
# pip install trino pandas matplotlib seaborn
import trino
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', 80)
sns.set_theme(style='whitegrid')

TRINO_HOST = 'localhost'   # SSH tunnel: ssh -L 8080:localhost:8080 <user>@20.151.177.201
TRINO_PORT = 8080
TRINO_USER = 'admin'
CATALOG    = 'mongo_prod'
SCHEMA     = 'langara-dev-client'

conn = trino.dbapi.connect(
    host=TRINO_HOST,
    port=TRINO_PORT,
    user=TRINO_USER,
    catalog=CATALOG,
    schema=SCHEMA,
)

def query(sql):
    """Run a Trino SQL query and return a pandas DataFrame."""
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    return pd.DataFrame(rows, columns=cols)

print('Connected to Trino.')

# %% [markdown]
# ## 2. Existing Dashboard Queries
# 
# These are the queries from the Langara Superset Dashboard Guide v5.

# %% [markdown]
# ### CHART-01 — Level Completion Funnel
# **Q:** How many students complete each level vs. how many attempted it?

# %%
df_01 = query("""
SELECT
    lf.levelname                                                   AS level_name,
    COUNT(DISTINCT lf.userid)                                      AS students_attempted,
    SUM(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END)       AS students_completed,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END)
        / NULLIF(COUNT(DISTINCT lf.userid), 0), 1
    ), 0)                                                          AS completion_rate_pct
FROM levelflows lf
GROUP BY lf.levelname
ORDER BY MIN(lf."create")
""")

df_01

# %%
ax = df_01.set_index('level_name')[['students_attempted','students_completed']].plot(
    kind='barh', figsize=(10, 5), title='CHART-01: Level Completion Funnel'
)
ax.set_xlabel('Students')
plt.tight_layout()
plt.show()

# %% [markdown]
# ### CHART-02 — Scene-by-Scene Drop-Off
# **Q:** Which scene numbers have the highest failure rate across all levels?

# %%
df_02 = query("""
SELECT
    CAST(json_extract_scalar(scene_obj, '$.sceneNo') AS BIGINT)    AS scene_no,
    lf.levelname                                                   AS level_name,
    COUNT(*)                                                       AS total_attempts,
    SUM(CASE WHEN json_extract_scalar(scene_obj, '$.sceneComplete') = 'true' THEN 1 ELSE 0 END) AS scenes_completed,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN json_extract_scalar(scene_obj, '$.sceneComplete') = 'true' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    ), 0)                                                          AS scene_completion_pct
FROM levelflows lf
CROSS JOIN UNNEST(CAST(lf.scene AS ARRAY(JSON))) AS t(scene_obj)
GROUP BY json_extract_scalar(scene_obj, '$.sceneNo'), lf.levelname
ORDER BY lf.levelname, scene_no
""")

df_02

# %%
for level, grp in df_02.groupby('level_name'):
    fig, ax = plt.subplots(figsize=(10, 4))
    grp.set_index('scene_no')[['total_attempts','scenes_completed']].plot(
        kind='bar', ax=ax, title=f'CHART-02: Scene Drop-Off — {level}'
    )
    ax.set_xlabel('Scene')
    ax.set_ylabel('Count')
    plt.tight_layout()
    plt.show()

# %% [markdown]
# ### CHART-03 — Attempts Before Completion (Box Plot)
# **Q:** How many tries does it take the average student to complete a level?

# %%
df_03 = query("""
SELECT
    lf.userid                                                      AS user_id,
    lf.levelname                                                   AS level_name,
    COUNT(*)                                                       AS attempt_count,
    MAX(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END)       AS eventually_completed
FROM levelflows lf
GROUP BY lf.userid, lf.levelname
ORDER BY attempt_count DESC
""")

df_03

# %%
fig, ax = plt.subplots(figsize=(12, 5))
df_03.boxplot(column='attempt_count', by='level_name', ax=ax)
ax.set_title('CHART-03: Attempt Distribution Before Completion')
ax.set_xlabel('Level')
ax.set_ylabel('Attempts')
plt.suptitle('')
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
plt.show()

# %% [markdown]
# ### CHART-04 — Level Pass Rate by Child B Personality
# **Q:** Which Child B personality has the lowest completion rate?

# %%
df_04 = query("""
SELECT
    lf.personality_childb                                          AS personality_child_b,
    lf.levelname                                                   AS level_name,
    COUNT(*)                                                       AS total_sessions,
    SUM(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END)       AS completed_sessions,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    ), 0)                                                          AS pass_rate_pct
FROM levelflows lf
WHERE lf.personality_childb IS NOT NULL
GROUP BY lf.personality_childb, lf.levelname
ORDER BY pass_rate_pct ASC
""")

df_04

# %% [markdown]
# ### CHART-05 — Personality Combination Difficulty Matrix (Heatmap)
# **Q:** Which Child A + Child B personality combo is hardest?

# %%
df_05 = query("""
SELECT
    COALESCE(lf.personality_childa, 'Unknown')                     AS personality_child_a,
    COALESCE(lf.personality_childb, 'Unknown')                     AS personality_child_b,
    COUNT(*)                                                       AS total_sessions,
    SUM(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END)       AS completions,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    ), 0)                                                          AS pass_rate_pct
FROM levelflows lf
GROUP BY lf.personality_childa, lf.personality_childb
ORDER BY pass_rate_pct ASC
""")

# ✅ ensure numeric
df_05["pass_rate_pct"] = pd.to_numeric(df_05["pass_rate_pct"], errors="coerce")

pivot_05 = df_05.pivot_table(
    index="personality_child_a",
    columns="personality_child_b",
    values="pass_rate_pct",
    aggfunc="mean",
)

# ✅ ensure the pivot is numeric (and NaN allowed)
pivot_05 = pivot_05.apply(pd.to_numeric, errors="coerce").astype(float)

fig, ax = plt.subplots(figsize=(12, 6))
sns.heatmap(
    pivot_05,
    annot=True,
    fmt=".0f",
    cmap="RdYlGn",
    vmin=0, vmax=100,
    ax=ax
)
ax.set_title("CHART-05: Personality Combination Pass Rate (%)")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### CHART-06 — Scene Completion Rate by Personality (Heatmap)
# **Q:** For each personality, which scene do students fail the most?

# %%
df_06 = query("""
SELECT
    lf.personality_childb                                          AS personality,
    CAST(json_extract_scalar(scene_obj, '$.sceneNo') AS BIGINT)    AS scene_no,
    COUNT(*)                                                       AS attempts,
    SUM(CASE WHEN json_extract_scalar(scene_obj, '$.sceneComplete') = 'true' THEN 1 ELSE 0 END) AS completions,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN json_extract_scalar(scene_obj, '$.sceneComplete') = 'true' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    ), 0)                                                          AS completion_pct
FROM levelflows lf
CROSS JOIN UNNEST(CAST(lf.scene AS ARRAY(JSON))) AS t(scene_obj)
WHERE lf.personality_childb IS NOT NULL
GROUP BY lf.personality_childb, json_extract_scalar(scene_obj, '$.sceneNo')
ORDER BY personality, scene_no
""")

# ✅ force numeric
df_06["completion_pct"] = pd.to_numeric(df_06["completion_pct"], errors="coerce")

pivot_06 = df_06.pivot_table(
    index="personality",
    columns="scene_no",
    values="completion_pct",
    aggfunc="mean"
)

# ✅ ensure float matrix
pivot_06 = pivot_06.apply(pd.to_numeric, errors="coerce").astype(float)

fig, ax = plt.subplots(figsize=(14, 6))
sns.heatmap(
    pivot_06,
    annot=True,
    fmt=".0f",
    cmap="RdYlGn",
    vmin=0,
    vmax=100,
    ax=ax
)

ax.set_title("CHART-06: Scene Completion Rate by Personality (%)")
plt.tight_layout()
plt.show()

# %% [markdown]
# ### CHART-07 — Correct vs Incorrect Responses Per Scene
# **Q:** In which scenes do students give the most incorrect responses?

# %%
df_07 = query("""
SELECT
    lf.levelname                                                   AS level_name,
    lf.personality_childb                                          AS personality,
    CAST(json_extract_scalar(scene_obj, '$.sceneNo') AS BIGINT)    AS scene_no,
    COUNT(*)                                                       AS total_responses,
    SUM(CASE WHEN json_extract_scalar(conv_obj, '$.isCorrect') = 'true' THEN 1 ELSE 0 END)  AS correct_responses,
    SUM(CASE WHEN json_extract_scalar(conv_obj, '$.isCorrect') = 'false' THEN 1 ELSE 0 END) AS incorrect_responses,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN json_extract_scalar(conv_obj, '$.isCorrect') = 'true' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    ), 0)                                                          AS accuracy_pct
FROM levelflows lf
CROSS JOIN UNNEST(CAST(lf.scene AS ARRAY(JSON))) AS t(scene_obj)
CROSS JOIN UNNEST(CAST(json_extract(scene_obj, '$.conversations') AS ARRAY(JSON))) AS t2(conv_obj)
WHERE json_extract_scalar(conv_obj, '$.type') = 'user'
GROUP BY lf.levelname, lf.personality_childb, json_extract_scalar(scene_obj, '$.sceneNo')
ORDER BY level_name, scene_no
""")

df_07

# %% [markdown]
# ### CHART-08 — Blame Language Usage by Personality & Scene
# **Q:** In which personality + scene do students use blame language most?

# %%
df_08 = query("""
SELECT
    lf.personality_childb                                          AS personality,
    CAST(json_extract_scalar(scene_obj, '$.sceneNo') AS BIGINT)    AS scene_no,
    COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user' THEN 1 END)   AS total_user_responses,
    COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user'
               AND json_extract_scalar(conv_obj, '$.blame') = 'true' THEN 1 END)   AS blame_responses,
    COALESCE(ROUND(
        100.0 * COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user'
                           AND json_extract_scalar(conv_obj, '$.blame') = 'true' THEN 1 END)
        / NULLIF(COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user' THEN 1 END), 0), 1
    ), 0)                                                          AS blame_rate_pct
FROM levelflows lf
CROSS JOIN UNNEST(CAST(lf.scene AS ARRAY(JSON))) AS t(scene_obj)
CROSS JOIN UNNEST(CAST(json_extract(scene_obj, '$.conversations') AS ARRAY(JSON))) AS t2(conv_obj)
WHERE lf.personality_childb IS NOT NULL
GROUP BY lf.personality_childb, json_extract_scalar(scene_obj, '$.sceneNo')
ORDER BY personality, scene_no
""")

pivot_08 = df_08.pivot_table(index='personality', columns='scene_no', values='blame_rate_pct')
fig, ax = plt.subplots(figsize=(14, 6))
sns.heatmap(pivot_08, annot=True, fmt='.0f', cmap='RdYlGn_r', vmin=0, vmax=100, ax=ax)
ax.set_title('CHART-08: Blame Rate (%) by Personality & Scene')
plt.tight_layout()
plt.show()

# %% [markdown]
# ### CHART-09 — Average Responses Per Scene
# **Q:** How many attempts does a student need per scene on average?

# %%
df_09 = query("""
SELECT
    lf.levelname                                                   AS level_name,
    lf.personality_childb                                          AS personality,
    CAST(json_extract_scalar(scene_obj, '$.sceneNo') AS BIGINT)    AS scene_no,
    COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user' THEN 1 END)  AS total_user_responses,
    COUNT(DISTINCT lf._id)                                         AS unique_sessions,
    COALESCE(ROUND(
        1.0 * COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user' THEN 1 END)
        / NULLIF(COUNT(DISTINCT lf._id), 0), 2
    ), 0)                                                          AS avg_responses_per_session
FROM levelflows lf
CROSS JOIN UNNEST(CAST(lf.scene AS ARRAY(JSON))) AS t(scene_obj)
CROSS JOIN UNNEST(CAST(json_extract(scene_obj, '$.conversations') AS ARRAY(JSON))) AS t2(conv_obj)
GROUP BY lf.levelname, lf.personality_childb, json_extract_scalar(scene_obj, '$.sceneNo')
ORDER BY level_name, scene_no
""")

df_09

# %% [markdown]
# ### CHART-12 — NLP Model Accuracy by Level Over Time
# **Q:** Are NLP models improving over time for each level?

# %%
df_12 = query("""
SELECT
    json_extract_scalar(tm.level, '$.name')  AS level_name,
    tm.modellink                             AS model_link,
    tm.accuracy                              AS accuracy_score,
    tm.blame                                 AS is_blame_model,
    CAST(tm.lastmodelupdate AS DATE)         AS update_date,
    CARDINALITY(tm.originalsentences)        AS original_sentence_count,
    CARDINALITY(tm.generatedsentences)       AS generated_sentence_count
FROM trainingmodels tm
WHERE tm.accuracy IS NOT NULL
ORDER BY update_date ASC
""")

df_12

# %% [markdown]
# ### CHART-13 — Blame Model vs General Model Accuracy
# **Q:** Do blame-specific NLP models achieve higher or lower accuracy than general models?

# %%
df_13 = query("""
SELECT
    json_extract_scalar(tm.level, '$.name')             AS level_name,
    CASE WHEN tm.blame = true THEN 'Blame Model'
         ELSE 'General Model' END                       AS model_type,
    ROUND(AVG(tm.accuracy), 3)                          AS avg_accuracy,
    MAX(tm.accuracy)                                    AS max_accuracy,
    COUNT(*)                                            AS model_count
FROM trainingmodels tm
WHERE tm.accuracy IS NOT NULL
GROUP BY json_extract_scalar(tm.level, '$.name'), tm.blame
ORDER BY level_name, model_type
""")

df_13

# %% [markdown]
# ### CHART-14 — Student Activity Over Time
# **Q:** When are students most actively using the VR app?

# %%
df_14 = query("""
SELECT
    CAST(lf."create" AS DATE)    AS session_date,
    COUNT(*)                     AS sessions_started,
    COUNT(DISTINCT lf.userid)    AS unique_students,
    lf.levelname                 AS level_name
FROM levelflows lf
JOIN users u ON u._id = lf.userid
WHERE u.role = 'student'
GROUP BY CAST(lf."create" AS DATE), lf.levelname
ORDER BY session_date
""")

df_14['session_date'] = pd.to_datetime(df_14['session_date'])
daily = df_14.groupby('session_date')['sessions_started'].sum()

fig, ax = plt.subplots(figsize=(14, 4))
daily.plot(ax=ax, title='CHART-14: Student Sessions Over Time')
ax.set_ylabel('Sessions')
plt.tight_layout()
plt.show()

# %% [markdown]
# ### CHART-17 — Pass Rate by Personality & Child B Avatar
# **Q:** Does the Child B avatar body affect session pass rate within each personality type?

# %%
df_17 = query("""
SELECT
    lf.personality_childb                               AS personality,
    json_extract_scalar(lf.avatarinfo, '$.ChildB')      AS childb_avatar,
    COUNT(*)                                            AS sessions_attempted,
    SUM(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END) AS sessions_completed,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    ), 0)                                               AS pass_rate_pct
FROM levelflows lf
WHERE lf.personality_childb IS NOT NULL
  AND lf.avatarinfo IS NOT NULL
GROUP BY lf.personality_childb, json_extract_scalar(lf.avatarinfo, '$.ChildB')
ORDER BY personality, childb_avatar
""")

df_17

# %% [markdown]
# ---
# ## 3. New Research Queries
# 
# Exploratory queries not in the original guide — designed to surface deeper research insights.

# %% [markdown]
# ### NEW-01 — Student Learning Curve: Do Repeated Attempts Improve Outcomes?
# **Q:** Do students who retry a level complete it at higher rates on later attempts?  
# Ranks each attempt per student per level chronologically and measures whether completion probability increases with attempt number.

# %%
df_new01 = query("""
SELECT
    attempt_number,
    COUNT(*)                                                       AS total_sessions,
    SUM(CASE WHEN levelcomplete = true THEN 1 ELSE 0 END)          AS completed,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN levelcomplete = true THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    ), 0)                                                          AS pass_rate_pct
FROM (
    SELECT
        lf.userid,
        lf.levelname,
        lf.levelcomplete,
        ROW_NUMBER() OVER (
            PARTITION BY lf.userid, lf.levelname
            ORDER BY lf."create"
        )                                                          AS attempt_number
    FROM levelflows lf
) ranked
WHERE attempt_number <= 10
GROUP BY attempt_number
ORDER BY attempt_number
""")

fig, ax = plt.subplots(figsize=(10, 4))
ax.plot(df_new01['attempt_number'], df_new01['pass_rate_pct'], marker='o')
ax.set_title('NEW-01: Pass Rate by Attempt Number (Learning Curve)')
ax.set_xlabel('Attempt Number')
ax.set_ylabel('Pass Rate (%)')
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
ax.set_xticks(df_new01['attempt_number'])
plt.tight_layout()
plt.show()

df_new01

# %% [markdown]
# ### NEW-02 — First-Try Success Rate by Level
# **Q:** What fraction of students pass each level on their very first attempt?  
# High first-try pass rate = level is well-designed or too easy. Low = students need multiple attempts to understand.

# %%
df_new02 = query("""
SELECT
    levelname                                                      AS level_name,
    COUNT(*)                                                       AS first_attempt_students,
    SUM(CASE WHEN levelcomplete = true THEN 1 ELSE 0 END)          AS passed_first_try,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN levelcomplete = true THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    ), 0)                                                          AS first_try_pass_rate_pct
FROM (
    SELECT
        userid, levelname, levelcomplete,
        ROW_NUMBER() OVER (PARTITION BY userid, levelname ORDER BY "create") AS rn
    FROM levelflows
) t
WHERE rn = 1
GROUP BY levelname
ORDER BY first_try_pass_rate_pct ASC
""")

ax = df_new02.set_index('level_name')['first_try_pass_rate_pct'].sort_values().plot(
    kind='barh', figsize=(10, 5), title='NEW-02: First-Try Pass Rate by Level'
)
ax.set_xlabel('Pass Rate (%)')
ax.axvline(50, color='red', linestyle='--', linewidth=1, label='50%')
ax.legend()
plt.tight_layout()
plt.show()

df_new02

# %% [markdown]
# ### NEW-03 — Student Retention: Return Rate After First Session
# **Q:** How many students return to play more than once?  
# Identifies whether students are self-motivated to retry or only play when assigned.

# %%
df_new03 = query("""
SELECT
    session_count_bucket,
    COUNT(DISTINCT userid)                                        AS students
FROM (
    SELECT
        userid,
        CASE
            WHEN COUNT(*) = 1 THEN '1 session (never returned)'
            WHEN COUNT(*) BETWEEN 2 AND 5 THEN '2-5 sessions'
            WHEN COUNT(*) BETWEEN 6 AND 10 THEN '6-10 sessions'
            ELSE '11+ sessions'
        END AS session_count_bucket
    FROM levelflows lf
    JOIN users u ON u._id = lf.userid
    WHERE u.role = 'student'
    GROUP BY userid
) t
GROUP BY session_count_bucket
ORDER BY MIN(CASE session_count_bucket
    WHEN '1 session (never returned)' THEN 1
    WHEN '2-5 sessions' THEN 2
    WHEN '6-10 sessions' THEN 3
    ELSE 4 END)
""")

df_new03.set_index('session_count_bucket')['students'].plot(
    kind='pie', autopct='%1.1f%%', figsize=(7, 7),
    title='NEW-03: Student Retention (Session Count Distribution)'
)
plt.ylabel('')
plt.tight_layout()
plt.show()

df_new03

# %% [markdown]
# ### NEW-04 — Personality-Level Difficulty Index (Composite Score)
# **Q:** Which personality × level combination is objectively hardest?  
# Combines low pass rate, high blame rate, and high avg attempts into a single difficulty index.

# %%
df_new04 = query("""
SELECT
    lf.levelname                                                   AS level_name,
    lf.personality_childb                                          AS personality,
    COUNT(DISTINCT lf.userid)                                      AS unique_students,
    COUNT(*)                                                       AS total_sessions,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0), 1
    ), 0)                                                          AS pass_rate_pct,
    COALESCE(ROUND(
        1.0 * COUNT(*)
        / NULLIF(COUNT(DISTINCT lf.userid), 0), 2
    ), 0)                                                          AS avg_attempts_per_student,
    -- Difficulty index: lower pass rate + more attempts = harder
    COALESCE(ROUND(
        (100.0 - (100.0 * SUM(CASE WHEN lf.levelcomplete = true THEN 1 ELSE 0 END)
        / NULLIF(COUNT(*), 0)))
        * (1.0 * COUNT(*) / NULLIF(COUNT(DISTINCT lf.userid), 0)) / 10.0
    , 2), 0)                                                       AS difficulty_index
FROM levelflows lf
WHERE lf.personality_childb IS NOT NULL
GROUP BY lf.levelname, lf.personality_childb
HAVING COUNT(DISTINCT lf.userid) >= 3
ORDER BY difficulty_index DESC
""")

df_new04.head(15)

# %% [markdown]
# ### NEW-05 — Session Time-of-Day Analysis
# **Q:** When during the day do students play? Peaks may reveal class schedule or voluntary study patterns.

# %%
df_new05 = query("""
SELECT
    HOUR(lf."create")                AS hour_of_day,
    COUNT(*)                         AS sessions,
    COUNT(DISTINCT lf.userid)        AS unique_students
FROM levelflows lf
JOIN users u ON u._id = lf.userid
WHERE u.role = 'student'
GROUP BY HOUR(lf."create")
ORDER BY hour_of_day
""")

fig, ax = plt.subplots(figsize=(12, 4))
ax.bar(df_new05['hour_of_day'], df_new05['sessions'])
ax.set_title('NEW-05: Sessions by Hour of Day (Pacific Time)')
ax.set_xlabel('Hour of Day')
ax.set_ylabel('Sessions')
ax.set_xticks(range(0, 24))
plt.tight_layout()
plt.show()

df_new05

# %% [markdown]
# ### NEW-06 — Day-of-Week Activity Pattern
# **Q:** Are students more active on certain days? Weekday vs weekend usage reveals assignment-driven vs self-directed learning.

# %%
df_new06 = query("""
SELECT
    DAY_OF_WEEK(CAST(lf."create" AS DATE))  AS day_of_week_num,
    DATE_FORMAT(lf."create", '%W')           AS day_name,
    COUNT(*)                                 AS sessions,
    COUNT(DISTINCT lf.userid)                AS unique_students
FROM levelflows lf
JOIN users u ON u._id = lf.userid
WHERE u.role = 'student'
GROUP BY DAY_OF_WEEK(CAST(lf."create" AS DATE)), DATE_FORMAT(lf."create", '%W')
ORDER BY day_of_week_num
""")

fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(df_new06['day_name'], df_new06['sessions'])
ax.set_title('NEW-06: Sessions by Day of Week')
ax.set_ylabel('Sessions')
plt.tight_layout()
plt.show()

df_new06

# %% [markdown]
# ### NEW-07 — Level Play Order (Which Levels Do Students Play First?)
# **Q:** What is the most common order students play levels in?  
# Shows whether students follow a prescribed curriculum path or play freely.

# %%
df_new07 = query("""
SELECT
    level_order,
    levelname,
    COUNT(DISTINCT userid)   AS students_who_played_this_nth
FROM (
    SELECT
        userid,
        levelname,
        DENSE_RANK() OVER (PARTITION BY userid ORDER BY MIN("create")) AS level_order
    FROM levelflows
    GROUP BY userid, levelname
) t
WHERE level_order <= 5
GROUP BY level_order, levelname
ORDER BY level_order, students_who_played_this_nth DESC
""")

df_new07

# %% [markdown]
# ### NEW-08 — NLP Training Data Growth Over Time
# **Q:** How are training sentence counts growing as more student data is collected?  
# More data should correlate with better model accuracy.

# %%
df_new08 = query("""
SELECT
    json_extract_scalar(tm.level, '$.name')  AS level_name,
    CAST(tm.lastmodelupdate AS DATE)         AS update_date,
    CASE WHEN tm.blame = true THEN 'Blame' ELSE 'General' END AS model_type,
    CARDINALITY(tm.originalsentences)        AS original_sentences,
    CARDINALITY(tm.generatedsentences)       AS generated_sentences,
    CARDINALITY(tm.originalsentences)
    + CARDINALITY(tm.generatedsentences)     AS total_training_sentences,
    tm.accuracy                              AS accuracy_score
FROM trainingmodels tm
WHERE tm.accuracy IS NOT NULL
ORDER BY update_date ASC
""")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
for ax, col, title in zip(
    axes,
    ['total_training_sentences', 'accuracy_score'],
    ['Training Sentence Count Over Time', 'Accuracy Over Time']
):
    for (level, mtype), grp in df_new08.groupby(['level_name', 'model_type']):
        ax.plot(grp['update_date'], grp[col], marker='o', label=f'{level} ({mtype})')
    ax.set_title(f'NEW-08: {title}')
    ax.set_xlabel('Update Date')
    ax.legend(fontsize=7)
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
plt.tight_layout()
plt.show()

df_new08

# %% [markdown]
# ### NEW-09 — Scenes Where Blame Predicts Failure
# **Q:** Is blame language a leading indicator of session failure?  
# Joins session-level outcomes with per-scene blame rates to see if blaming correlates with not completing the level.

# %%
df_new09 = query("""
SELECT
    lf.levelname                                                   AS level_name,
    lf.levelcomplete,
    COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user' THEN 1 END)         AS total_responses,
    COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user'
               AND json_extract_scalar(conv_obj, '$.blame') = 'true' THEN 1 END)        AS blame_responses,
    COALESCE(ROUND(
        100.0 * COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user'
                           AND json_extract_scalar(conv_obj, '$.blame') = 'true' THEN 1 END)
        / NULLIF(COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user' THEN 1 END), 0), 1
    ), 0)                                                          AS blame_rate_pct
FROM levelflows lf
CROSS JOIN UNNEST(CAST(lf.scene AS ARRAY(JSON))) AS t(scene_obj)
CROSS JOIN UNNEST(CAST(json_extract(scene_obj, '$.conversations') AS ARRAY(JSON))) AS t2(conv_obj)
GROUP BY lf.levelname, lf.levelcomplete
ORDER BY level_name, lf.levelcomplete
""")

# Pivot: compare blame rate for completed vs not completed sessions
pivot_09 = df_new09.pivot_table(index='level_name', columns='levelcomplete', values='blame_rate_pct')
pivot_09.columns = ['Failed', 'Passed']
pivot_09.plot(kind='bar', figsize=(12, 5),
              title='NEW-09: Blame Rate (%) — Passed vs Failed Sessions by Level',
              ylabel='Blame Rate (%)')
plt.xticks(rotation=30, ha='right')
plt.tight_layout()
plt.show()

df_new09

# %% [markdown]
# ### NEW-10 — Student Progress: Scenes Reached Per Level (Never Completed)
# **Q:** For students who never completed a level, how far did they get?  
# Reveals the 'cliff' scene where students give up entirely.

# %%
df_new10 = query("""
SELECT
    lf.levelname                                                   AS level_name,
    MAX(CAST(json_extract_scalar(scene_obj, '$.sceneNo') AS BIGINT)) AS furthest_scene_reached,
    COUNT(DISTINCT lf.userid)                                      AS students
FROM levelflows lf
CROSS JOIN UNNEST(CAST(lf.scene AS ARRAY(JSON))) AS t(scene_obj)
WHERE lf.userid NOT IN (
    SELECT DISTINCT userid FROM levelflows WHERE levelcomplete = true
)
GROUP BY lf.levelname, lf.userid
-- Aggregate across students for distribution
""")

# Show distribution of furthest scene per level for students who never completed
for level, grp in df_new10.groupby('level_name'):
    print(f"\n{level}:")
    print(grp['furthest_scene_reached'].value_counts().sort_index().to_string())

# %% [markdown]
# ### NEW-11 — Response Accuracy Improvement Within a Session
# **Q:** Within a single session, do students get more accurate as they progress through scenes?  
# Tests whether learning happens within a single play session.

# %%
df_new11 = query("""
SELECT
    CAST(json_extract_scalar(scene_obj, '$.sceneNo') AS BIGINT)    AS scene_no,
    COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user' THEN 1 END)        AS responses,
    SUM(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user'
             AND json_extract_scalar(conv_obj, '$.isCorrect') = 'true' THEN 1 ELSE 0 END) AS correct,
    COALESCE(ROUND(
        100.0 * SUM(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user'
                         AND json_extract_scalar(conv_obj, '$.isCorrect') = 'true' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(CASE WHEN json_extract_scalar(conv_obj, '$.type') = 'user' THEN 1 END), 0), 1
    ), 0)                                                          AS accuracy_pct
FROM levelflows lf
CROSS JOIN UNNEST(CAST(lf.scene AS ARRAY(JSON))) AS t(scene_obj)
CROSS JOIN UNNEST(CAST(json_extract(scene_obj, '$.conversations') AS ARRAY(JSON))) AS t2(conv_obj)
GROUP BY json_extract_scalar(scene_obj, '$.sceneNo')
ORDER BY scene_no
""")

fig, ax = plt.subplots(figsize=(12, 4))
ax.plot(df_new11['scene_no'], df_new11['accuracy_pct'], marker='o', color='steelblue')
ax.set_title('NEW-11: Response Accuracy by Scene Number (Across All Levels)')
ax.set_xlabel('Scene Number')
ax.set_ylabel('Accuracy (%)')
ax.yaxis.set_major_formatter(mtick.PercentFormatter())
plt.tight_layout()
plt.show()

df_new11

# %% [markdown]
# ### NEW-12 — Student Cohort Comparison by Month of First Session
# **Q:** Do students who started in earlier cohorts (semesters) perform better?  
# Useful for measuring whether app improvements or instructor guidance improve outcomes over time.

# %%
df_new12 = query("""
SELECT
    cohort_month,
    COUNT(DISTINCT userid)                                        AS students,
    SUM(total_sessions)                                           AS total_sessions,
    ROUND(AVG(total_sessions), 1)                                 AS avg_sessions_per_student,
    ROUND(AVG(pass_rate), 1)                                      AS avg_pass_rate_pct
FROM (
    SELECT
        userid,
        DATE_FORMAT(MIN("create"), '%Y-%m')   AS cohort_month,
        COUNT(*)                              AS total_sessions,
        COALESCE(ROUND(
            100.0 * SUM(CASE WHEN levelcomplete = true THEN 1 ELSE 0 END)
            / NULLIF(COUNT(*), 0), 1
        ), 0)                                 AS pass_rate
    FROM levelflows
    GROUP BY userid
) t
GROUP BY cohort_month
ORDER BY cohort_month
""")

fig, ax1 = plt.subplots(figsize=(12, 5))
ax2 = ax1.twinx()
ax1.bar(df_new12['cohort_month'], df_new12['students'], alpha=0.6, label='Students')
ax2.plot(df_new12['cohort_month'], df_new12['avg_pass_rate_pct'], color='red', marker='o', label='Avg Pass Rate %')
ax1.set_title('NEW-12: Student Cohorts by First-Session Month')
ax1.set_ylabel('Students')
ax2.set_ylabel('Avg Pass Rate (%)')
plt.xticks(rotation=30, ha='right')
ax1.legend(loc='upper left')
ax2.legend(loc='upper right')
plt.tight_layout()
plt.show()

df_new12

# %% [markdown]
# 1. Blame as a stress response
# When a student can't resolve a scene, do they start blaming the child? The sequence matters — does blame language increase as scenes progress within a session? If yes, that's emotional fatigue showing up in language. This is a real psychological pattern — people under prolonged stress externalize responsibility.
# Within a single session: scene_no → blame_rate ordered chronologically
# Does blame_rate in scene 3 predict whether the student completes the level?
# 
# 2. Does the student actually learn within a session vs across sessions?
# Story 3 but sharper — not just "do they pass more on attempt 3" but how does their response pattern change. On attempt 1 they might give many incorrect responses before finding the right one. On attempt 3 they go straight to correct. That's the learning signal — response efficiency, not just pass/fail.
# attempt_number (ROW_NUMBER by userid+levelname+create)
# vs avg_responses_before_correct (how many wrong before right)
# 
# 3. Personality empathy fingerprint
# Each Child B personality represents a real marginalized group — PDA/Autism, War Refugee, Foster Care, Indigenous. The question is: which groups do ECE students find hardest to empathize with? Blame rate + incorrect rate + completion rate combined into one profile per personality tells you where empathy gaps are largest. That's publishable.
# Per personality: blame_rate + incorrect_rate + completion_rate + avg_attempts
# → radar/spider chart or grouped bar showing the full difficulty profile
# 
# 4. Time pressure and decision quality
# scene_create gaps between scenes — students who rush through scenes (short gaps) vs students who pause. Do the rushers blame more? Do they complete less? This could reveal whether the app needs pacing interventions — forced reflection time between scenes.
# time_gap between scenes (LEAD on scene_create by sceneNo)
# vs sceneComplete + blame_rate for that scene
# 
# 5. The recovery pattern
# After a student fails a scene (sceneComplete = false), what happens next session? Do they attempt the same scene again more carefully (fewer responses, correct faster)? Or do they repeat the same mistakes? This shows whether failure in the app triggers reflection or just repetition.
# session N: failed scene X → session N+1: same scene X
# compare response pattern before vs after failure
# 
# 6. Empathy under accumulation
# Does blame/incorrect rate in early scenes predict level completion? If a student blames in scene 1, are they 3x more likely to fail by scene 4? That would mean early warning signals are detectable — instructors could intervene before the student fully disengages.
# blame in scene 1 or 2 → levelcomplete
# early_blame flag → completion outcome
# 
# 7. Story 1: "Does struggling with a scene make you blame more?"
# Connect scene completion + blame_rate at the scene level. If blame spikes exactly where completion drops, it means students under pressure default to blame language. This is a pedagogically critical finding — it tells instructors which scenes need more pre-teaching.
# levelflows → scene[] → conversations[]
# sceneComplete + blame_rate grouped by sceneNo + personality
# 
# 8. Story 3: "The learning curve — do students actually improve across sessions?"
# Use ROW_NUMBER() OVER (PARTITION BY userid, levelname ORDER BY create) to number each student's attempts at a level. Plot pass rate by attempt number. If attempt 1 pass rate is 20% but attempt 3 is 60%, the app is working. If it stays flat, students are not learning.
# 
# 9. Story 6: "Conversation quality fingerprint by personality"
# For each personality, what is the ratio of: correct responses / incorrect responses / blame responses across all scenes? Some personalities might trigger more blame, others more incorrect guesses. This gives a "difficulty profile" per personality that's richer than just pass rate.
# 
# 10. Story 7: "Do students who take longer between scenes perform worse?"
# scene_create timestamps inside scene[] — time between scene 1 and scene 2 vs completion. Long gaps might mean confusion or distraction. Short gaps might mean rushing without absorbing. Optimal pacing vs outcome.

# %%
# Close connection when done
conn.close()
print('Connection closed.')


