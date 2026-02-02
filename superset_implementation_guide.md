# Superset Implementation Guide for Langara VR Analytics

## Table of Contents
1. [Quick Start](#quick-start)
2. [Creating Datasets](#creating-datasets)
3. [Recommended Visualizations](#recommended-visualizations)
4. [Dashboard Ideas](#dashboard-ideas)
5. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Step 1: Test Basic Connectivity
```sql
-- Test that joins work with _id
SELECT u._id, u.username, lf.levelname 
FROM "langara-dev".users u 
LEFT JOIN "langara-dev".levelflows lf ON u._id = lf.userid 
LIMIT 10;
```

### Step 2: Choose Your Approach

**Option A: Create Views in Trino** (Recommended for complex queries)
- Run the `CREATE OR REPLACE VIEW` statements in Superset SQL Lab
- Then add the views as datasets in Superset

**Option B: Use SQL Directly in Datasets** (Simpler, no view creation needed)
- In Superset, go to Data → Datasets → + Dataset
- Choose "SQL" tab
- Paste the query from the SQL file
- Name your dataset

---

## Creating Datasets

### Priority Datasets to Create First

#### 1. User Activity Summary
```sql
-- Dataset: user_activity_summary
SELECT 
    u._id as user_id,
    u.username,
    u.role,
    u.created as registration_date,
    COUNT(DISTINCT lf._id) as total_level_flows,
    COUNT(DISTINCT lf.levelname) as unique_levels_played,
    MAX(lf.create) as last_activity_date,
    DATE_DIFF('day', u.created, MAX(lf.create)) as days_active
FROM "langara-dev".users u
LEFT JOIN "langara-dev".levelflows lf ON u._id = lf.userid
GROUP BY u._id, u.username, u.role, u.created;
```

**Metrics to create:**
- Count of user_id (Total Users)
- Sum of total_level_flows
- Sum of unique_levels_played
- Average of days_active

**Useful Charts:**
- Table (all columns)
- Big Number (Total Users)
- Bar Chart (users by role)
- Time Series (registrations over time)

---

#### 2. Level Completion Statistics
```sql
-- Dataset: level_completion_stats
SELECT 
    levelname,
    levelno,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN levelcomplete = true THEN 1 END) as completed_count,
    COUNT(CASE WHEN levelcomplete = false THEN 1 END) as incomplete_count,
    ROUND(COUNT(CASE WHEN levelcomplete = true THEN 1 END) * 100.0 / COUNT(*), 2) as completion_rate,
    COUNT(DISTINCT userid) as unique_users
FROM "langara-dev".levelflows
GROUP BY levelname, levelno;
```

**Useful Charts:**
- Bar Chart (completion_rate by levelname)
- Table (showing all stats)
- Pie Chart (completed vs incomplete)
- Heatmap (levelname x levelno, colored by completion_rate)

---

#### 3. Scene Analytics
```sql
-- Dataset: scenes_with_user_info
SELECT 
    u.username,
    u.role,
    lf.levelname,
    lf.levelno,
    t.sceneNo,
    t.purpose,
    t.userPhysicalInteraction,
    t.sceneComplete,
    t.scene_id,
    t.created_at as scene_created,
    t.turn_index,
    lf.create as level_started
FROM "langara-dev".users u
JOIN "langara-dev".levelflows lf ON u._id = lf.userid
CROSS JOIN UNNEST(lf.scene) WITH ORDINALITY AS t(
    sceneNo,
    purpose,
    userPhysicalInteraction,
    conversations,
    sceneComplete,
    scene_id,
    created_at,
    turn_index
);
```

**Useful Charts:**
- Funnel Chart (scene progression)
- Sankey Diagram (user flow through scenes)
- Bar Chart (scene completion by level)
- Line Chart (user interactions over time)

---

#### 4. Daily Activity
```sql
-- Dataset: daily_activity
SELECT 
    DATE(lf.create) as activity_date,
    COUNT(DISTINCT lf.userid) as active_users,
    COUNT(*) as total_level_attempts,
    COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) as completed_levels
FROM "langara-dev".levelflows lf
GROUP BY DATE(lf.create)
ORDER BY activity_date DESC;
```

**Useful Charts:**
- Time Series (active_users over time)
- Area Chart (level attempts over time)
- Combined Chart (multiple metrics on same timeline)

---

#### 5. User Journey
```sql
-- Dataset: user_journey
SELECT 
    u._id as user_id,
    u.username,
    u.role,
    u.created as user_registered,
    lf.levelname,
    lf.levelno,
    lf.levelcomplete,
    lf.create as level_started,
    lf.update as level_updated,
    CARDINALITY(lf.scene) as scenes_count,
    ROW_NUMBER() OVER (PARTITION BY u._id ORDER BY lf.create) as level_sequence
FROM "langara-dev".users u
LEFT JOIN "langara-dev".levelflows lf ON u._id = lf.userid;
```

**Useful Charts:**
- Sankey (user progression through levels)
- Table with filters
- Bar Chart (distribution of level sequences)

---

## Recommended Visualizations

### Dashboard 1: Executive Overview
**Purpose:** High-level KPIs for stakeholders

**Charts:**
1. **Big Number with Trendline** - Total Users
2. **Big Number with Trendline** - Active Users (Last 7 Days)
3. **Big Number** - Total Level Completions
4. **Line Chart** - Daily Active Users (30 days)
5. **Bar Chart** - Level Completion Rates
6. **Pie Chart** - Users by Role

**Filters:**
- Date Range
- User Role

---

### Dashboard 2: Level Performance
**Purpose:** Analyze which levels are performing well

**Charts:**
1. **Table** - Level Statistics (attempts, completions, rate, unique users)
2. **Bar Chart** - Completion Rate by Level (sorted)
3. **Heatmap** - Level x Scene Completion Matrix
4. **Box Plot** - Duration Distribution by Level
5. **Funnel Chart** - Level Progression Drop-off

**Filters:**
- Level Name
- Date Range
- Completion Status

---

### Dashboard 3: User Engagement
**Purpose:** Track user behavior and retention

**Charts:**
1. **Cohort Table** - User Retention by Registration Week
2. **Line Chart** - User Registrations Over Time
3. **Bar Chart** - Average Levels per User by Role
4. **Scatter Plot** - Days Active vs Levels Completed
5. **Table** - Top Users by Activity

**Filters:**
- Registration Date Range
- User Role
- Activity Threshold

---

### Dashboard 4: Scene Deep Dive
**Purpose:** Analyze scene-level interactions

**Charts:**
1. **Sankey Diagram** - User Flow Through Scenes
2. **Bar Chart** - Physical Interactions by Scene
3. **Heatmap** - Scene Completion by Purpose
4. **Line Chart** - Scene Completion Rate Over Time
5. **Table** - Scene Statistics with Drill-down

**Filters:**
- Level Name
- Scene Number
- Date Range

---

### Dashboard 5: Quiz Performance
**Purpose:** Track assessment results

**Charts:**
1. **Histogram** - Distribution of Quiz Scores
2. **Bar Chart** - Average Score by Level
3. **Line Chart** - Quiz Performance Over Time
4. **Table** - User Quiz History
5. **Box Plot** - Score Distribution by Attempt Number

**Filters:**
- Level Name
- Date Range
- User

---

## Specific Chart Recommendations

### 1. User Retention Funnel
```sql
SELECT 
    'Registered' as stage, COUNT(*) as users, 1 as stage_order
FROM "langara-dev".users
UNION ALL
SELECT 
    'Started Level' as stage, COUNT(DISTINCT userid) as users, 2 as stage_order
FROM "langara-dev".levelflows
UNION ALL
SELECT 
    'Completed Level' as stage, COUNT(DISTINCT userid) as users, 3 as stage_order
FROM "langara-dev".levelflows
WHERE levelcomplete = true
UNION ALL
SELECT 
    'Attempted Quiz' as stage, COUNT(DISTINCT userid) as users, 4 as stage_order
FROM "langara-dev".attemptquizzes
ORDER BY stage_order;
```
**Chart Type:** Funnel Chart

---

### 2. Level Difficulty Heatmap
```sql
SELECT 
    levelname,
    CONCAT('Level ', CAST(levelno AS VARCHAR)) as level_number,
    ROUND(AVG(CASE WHEN levelcomplete = true THEN 1.0 ELSE 0.0 END) * 100, 1) as completion_rate
FROM "langara-dev".levelflows
GROUP BY levelname, levelno;
```
**Chart Type:** Heatmap
**X-axis:** level_number
**Y-axis:** levelname
**Metric:** completion_rate

---

### 3. User Activity Timeline
```sql
SELECT 
    username,
    levelname,
    levelno,
    create as activity_time,
    levelcomplete
FROM "langara-dev".levelflows lf
JOIN "langara-dev".users u ON lf.userid = u._id
WHERE u.username IN (
    SELECT username FROM "langara-dev".users LIMIT 10
)
ORDER BY username, create;
```
**Chart Type:** Gantt Chart or Timeline
**Filters:** Add username filter for drill-down

---

### 4. Scene Purpose Distribution
```sql
SELECT 
    t.purpose,
    COUNT(*) as count,
    COUNT(CASE WHEN t.sceneComplete = true THEN 1 END) as completed,
    ROUND(AVG(CASE WHEN t.userPhysicalInteraction = true THEN 1.0 ELSE 0.0 END) * 100, 1) as interaction_rate
FROM "langara-dev".levelflows lf
CROSS JOIN UNNEST(lf.scene) AS t(
    sceneNo, purpose, userPhysicalInteraction, conversations, 
    sceneComplete, scene_id, created_at, turn_index
)
GROUP BY t.purpose;
```
**Chart Type:** Treemap or Pie Chart

---

## Advanced Analytics Queries

### Cohort Analysis
```sql
WITH user_cohorts AS (
    SELECT 
        _id as user_id,
        DATE_TRUNC('week', created) as cohort_week
    FROM "langara-dev".users
),
user_activity AS (
    SELECT 
        userid,
        DATE_TRUNC('week', create) as activity_week
    FROM "langara-dev".levelflows
)
SELECT 
    uc.cohort_week,
    ua.activity_week,
    COUNT(DISTINCT uc.user_id) as cohort_size,
    COUNT(DISTINCT ua.userid) as active_users,
    ROUND(COUNT(DISTINCT ua.userid) * 100.0 / COUNT(DISTINCT uc.user_id), 2) as retention_rate
FROM user_cohorts uc
LEFT JOIN user_activity ua ON uc.user_id = ua.userid
GROUP BY uc.cohort_week, ua.activity_week
ORDER BY uc.cohort_week, ua.activity_week;
```

---

### Level Progression Path Analysis
```sql
WITH level_sequences AS (
    SELECT 
        userid,
        levelname,
        levelno,
        create,
        ROW_NUMBER() OVER (PARTITION BY userid ORDER BY create) as sequence_num
    FROM "langara-dev".levelflows
)
SELECT 
    CONCAT(l1.levelname, ' → ', l2.levelname) as progression_path,
    COUNT(*) as frequency
FROM level_sequences l1
JOIN level_sequences l2 ON l1.userid = l2.userid AND l1.sequence_num + 1 = l2.sequence_num
GROUP BY l1.levelname, l2.levelname
ORDER BY frequency DESC
LIMIT 20;
```

---

## Troubleshooting

### Issue: Views not creating
**Solution:** Trino might not support `CREATE OR REPLACE VIEW`. Try:
```sql
CREATE VIEW v_my_view AS
SELECT ...
```

If view exists:
```sql
DROP VIEW v_my_view;
CREATE VIEW v_my_view AS
SELECT ...
```

---

### Issue: UNNEST not working as expected
**Problem:** Array fields showing as nested objects

**Solution:** Make sure to specify all fields in the UNNEST:
```sql
CROSS JOIN UNNEST(array_column) AS t(field1, field2, field3)
```

Check your MongoDB schema to confirm field names.

---

### Issue: _id not showing in joins
**Solution:** Always explicitly select `_id`:
```sql
SELECT u._id, u.username, lf.*
FROM users u
JOIN levelflows lf ON u._id = lf.userid
```

---

### Issue: Slow query performance
**Solutions:**
1. Add `LIMIT` clauses for testing
2. Use date filters to reduce data volume
3. Create materialized views if supported
4. Index userid and frequently queried fields in MongoDB

---

### Issue: Date/Time formatting
**Trino date functions:**
```sql
DATE(timestamp_field)                          -- Extract date
DATE_TRUNC('day', timestamp_field)            -- Truncate to day
DATE_TRUNC('week', timestamp_field)           -- Truncate to week
DATE_DIFF('day', start_date, end_date)        -- Difference in days
CURRENT_DATE                                   -- Current date
CURRENT_TIMESTAMP                              -- Current timestamp
```

---

## Best Practices

### 1. Dataset Naming Convention
- `v_` prefix for views
- Use descriptive names: `v_user_activity_summary`, not `v_data1`
- Include time grain if relevant: `v_daily_user_activity`

### 2. Performance Optimization
- Always use `LIMIT` during development
- Add WHERE clauses to filter data early
- Use date filters: `WHERE create >= CURRENT_DATE - INTERVAL '90' DAY`
- Avoid `SELECT *` in production views

### 3. Documentation
- Add comments to complex queries
- Document metric calculations in Superset
- Keep a changelog of dataset modifications

### 4. Testing
1. Test each query in SQL Lab first
2. Verify row counts make sense
3. Check for NULL values
4. Validate calculations manually on sample data

---

## Quick Reference: Common Patterns

### Pattern 1: Counting Distinct Users
```sql
COUNT(DISTINCT userid) as unique_users
```

### Pattern 2: Completion Rate
```sql
ROUND(
    COUNT(CASE WHEN complete_flag = true THEN 1 END) * 100.0 / COUNT(*), 
    2
) as completion_rate
```

### Pattern 3: Time-based Aggregation
```sql
DATE_TRUNC('day', timestamp_field) as date,
COUNT(*) as daily_count
GROUP BY DATE_TRUNC('day', timestamp_field)
```

### Pattern 4: Array Unnesting with Filters
```sql
FROM table_name t
CROSS JOIN UNNEST(t.array_field) AS a(col1, col2, col3)
WHERE a.col1 = 'some_value'
```

### Pattern 5: Window Functions for Rankings
```sql
ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY create_date) as sequence_num
```

---

## Next Steps

1. **Start Small:** Create 3-5 basic datasets first
2. **Build Incrementally:** Add one dashboard at a time
3. **Get Feedback:** Share with stakeholders early
4. **Iterate:** Refine based on actual usage patterns
5. **Document:** Keep notes on what works and what doesn't

---

## Additional Resources

- Superset Documentation: https://superset.apache.org/docs/intro
- Trino SQL Reference: https://trino.io/docs/current/sql.html
- Trino MongoDB Connector: https://trino.io/docs/current/connector/mongodb.html

---

**Questions or Issues?** Check the Troubleshooting section or test queries in SQL Lab first!
