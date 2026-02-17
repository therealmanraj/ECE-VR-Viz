# Teacher Dashboard Guide - Langara VR Analytics

## Overview
This dashboard helps teachers monitor student performance, engagement, and progress through VR learning modules.

---

## IMPORTANT: Reserved Keyword Fix
**The column `create` is a SQL reserved keyword in Trino/Superset.**
- Always use double quotes: `"create"` in all queries
- Similarly for `"update"` if needed

---

## SQL Lab Queries for Teacher Dashboard

### Query 1: Student Performance Overview
**Purpose:** Main dataset showing each student's overall performance

```sql
-- Dataset Name: teacher_student_performance
SELECT 
    u._id as student_id,
    u.username as student_name,
    u.role,
    u.created as registration_date,
    COUNT(DISTINCT lf._id) as total_attempts,
    COUNT(DISTINCT lf.levelname) as unique_levels_attempted,
    COUNT(DISTINCT CASE WHEN lf.levelcomplete = true THEN lf.levelname END) as unique_levels_completed,
    COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) as completed_attempts,
    COUNT(CASE WHEN lf.levelcomplete = false THEN 1 END) as incomplete_attempts,
    ROUND(
        COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 
        1
    ) as completion_rate,
    MAX(lf."create") as last_activity_date,
    DATE_DIFF('day', u.created, COALESCE(MAX(lf."create"), CURRENT_TIMESTAMP)) as days_since_registration,
    DATE_DIFF('day', MAX(lf."create"), CURRENT_TIMESTAMP) as days_since_last_activity
FROM "langara-dev".users u
LEFT JOIN "langara-dev".levelflows lf ON u._id = lf.userid
WHERE u.role = 'student'  -- Only show students
GROUP BY u._id, u.username, u.role, u.created
ORDER BY last_activity_date DESC NULLS LAST;
```

**How to Create in Superset:**
1. Go to **SQL Lab** → **SQL Editor**
2. Select database: `trino`
3. Select schema: `langara-dev-client` (or your schema from screenshot)
4. Paste the query above
5. Click **RUN** to test
6. Click **SAVE** → **Save dataset**
7. Name it: `teacher_student_performance`

---

### Query 2: Level-by-Level Student Progress
**Purpose:** See which students completed which levels

```sql
-- Dataset Name: teacher_level_progress
SELECT 
    u.username as student_name,
    lf.levelname,
    lf.levelno,
    lf.levelcomplete,
    lf."create" as level_started,
    lf."update" as level_last_updated,
    DATE_DIFF('minute', lf."create", lf."update") as time_spent_minutes,
    CARDINALITY(lf.scene) as total_scenes,
    ROW_NUMBER() OVER (PARTITION BY u._id ORDER BY lf."create") as attempt_sequence
FROM "langara-dev".users u
JOIN "langara-dev".levelflows lf ON u._id = lf.userid
WHERE u.role = 'student'
ORDER BY u.username, lf."create";
```

**How to Create:**
1. Same steps as Query 1
2. Name it: `teacher_level_progress`

---

### Query 3: Student Activity Timeline
**Purpose:** Track when students are active

```sql
-- Dataset Name: teacher_student_activity_timeline
SELECT 
    DATE(lf."create") as activity_date,
    u.username as student_name,
    COUNT(*) as level_attempts,
    COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) as completions,
    COUNT(DISTINCT lf.levelname) as unique_levels
FROM "langara-dev".users u
JOIN "langara-dev".levelflows lf ON u._id = lf.userid
WHERE u.role = 'student'
GROUP BY DATE(lf."create"), u.username
ORDER BY activity_date DESC, student_name;
```

---

### Query 4: Level Difficulty Analysis
**Purpose:** Identify which levels students struggle with

```sql
-- Dataset Name: teacher_level_difficulty
SELECT 
    lf.levelname,
    lf.levelno,
    COUNT(*) as total_attempts,
    COUNT(DISTINCT lf.userid) as unique_students,
    COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) as completions,
    ROUND(
        COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 
        1
    ) as completion_rate,
    ROUND(AVG(DATE_DIFF('minute', lf."create", lf."update")), 1) as avg_time_minutes,
    ROUND(AVG(CARDINALITY(lf.scene)), 1) as avg_scenes_per_attempt
FROM "langara-dev".levelflows lf
JOIN "langara-dev".users u ON lf.userid = u._id
WHERE u.role = 'student'
GROUP BY lf.levelname, lf.levelno
ORDER BY completion_rate ASC, total_attempts DESC;
```

---

### Query 5: Student Engagement Score
**Purpose:** Calculate engagement metrics for each student

```sql
-- Dataset Name: teacher_student_engagement
SELECT 
    u.username as student_name,
    COUNT(DISTINCT DATE(lf."create")) as active_days,
    COUNT(*) as total_interactions,
    COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) as successful_completions,
    ROUND(AVG(DATE_DIFF('minute', lf."create", lf."update")), 1) as avg_session_minutes,
    MAX(lf."create") as last_active,
    DATE_DIFF('day', MAX(lf."create"), CURRENT_TIMESTAMP) as days_inactive,
    CASE 
        WHEN DATE_DIFF('day', MAX(lf."create"), CURRENT_TIMESTAMP) <= 7 THEN 'Active'
        WHEN DATE_DIFF('day', MAX(lf."create"), CURRENT_TIMESTAMP) <= 30 THEN 'Declining'
        ELSE 'Inactive'
    END as engagement_status
FROM "langara-dev".users u
LEFT JOIN "langara-dev".levelflows lf ON u._id = lf.userid
WHERE u.role = 'student'
GROUP BY u._id, u.username
ORDER BY last_active DESC NULLS LAST;
```

---

### Query 6: Scene Completion Details
**Purpose:** Analyze scene-level performance

```sql
-- Dataset Name: teacher_scene_performance
SELECT 
    u.username as student_name,
    lf.levelname,
    lf.levelno,
    t.sceneNo,
    t.purpose,
    t.sceneComplete,
    t.userPhysicalInteraction,
    lf."create" as level_started,
    COUNT(*) OVER (PARTITION BY u._id, lf.levelname, lf.levelno) as scenes_in_level,
    SUM(CASE WHEN t.sceneComplete = true THEN 1 ELSE 0 END) 
        OVER (PARTITION BY u._id, lf.levelname, lf.levelno) as completed_scenes
FROM "langara-dev".users u
JOIN "langara-dev".levelflows lf ON u._id = lf.userid
CROSS JOIN UNNEST(lf.scene) AS t(
    sceneNo,
    purpose,
    userPhysicalInteraction,
    conversations,
    sceneComplete,
    scene_id,
    created_at,
    turn_index
)
WHERE u.role = 'student'
ORDER BY u.username, lf."create", t.sceneNo;
```

---

### Query 7: Quiz Performance (if applicable)
**Purpose:** Track assessment results

```sql
-- Dataset Name: teacher_quiz_performance
SELECT 
    u.username as student_name,
    aq.levelname,
    aq.score,
    aq.totalscore,
    ROUND((aq.score * 100.0 / NULLIF(aq.totalscore, 0)), 1) as percentage_score,
    aq."create" as quiz_date,
    ROW_NUMBER() OVER (PARTITION BY u._id, aq.levelname ORDER BY aq."create") as attempt_number
FROM "langara-dev".users u
JOIN "langara-dev".attemptquizzes aq ON u._id = aq.userid
WHERE u.role = 'student'
ORDER BY u.username, aq."create";
```

---

### Query 8: Class Summary Statistics
**Purpose:** Overall class performance at a glance

```sql
-- Dataset Name: teacher_class_summary
SELECT 
    COUNT(DISTINCT u._id) as total_students,
    COUNT(DISTINCT CASE 
        WHEN DATE_DIFF('day', MAX(lf."create"), CURRENT_TIMESTAMP) <= 7 
        THEN u._id 
    END) as active_last_7_days,
    COUNT(DISTINCT CASE 
        WHEN DATE_DIFF('day', MAX(lf."create"), CURRENT_TIMESTAMP) <= 30 
        THEN u._id 
    END) as active_last_30_days,
    ROUND(AVG(completion_stats.completion_rate), 1) as avg_completion_rate,
    SUM(completion_stats.total_attempts) as total_class_attempts,
    SUM(completion_stats.completions) as total_class_completions
FROM "langara-dev".users u
LEFT JOIN "langara-dev".levelflows lf ON u._id = lf.userid
LEFT JOIN (
    SELECT 
        userid,
        COUNT(*) as total_attempts,
        COUNT(CASE WHEN levelcomplete = true THEN 1 END) as completions,
        ROUND(
            COUNT(CASE WHEN levelcomplete = true THEN 1 END) * 100.0 / 
            NULLIF(COUNT(*), 0), 
            1
        ) as completion_rate
    FROM "langara-dev".levelflows
    GROUP BY userid
) completion_stats ON u._id = completion_stats.userid
WHERE u.role = 'student'
GROUP BY 1=1;  -- Dummy grouping for aggregate
```

---

## Creating Visualizations in Superset

### Visualization 1: Student Performance Table
**Dataset:** `teacher_student_performance`

**Steps:**
1. Go to **Charts** → **+ Create Chart**
2. Choose dataset: `teacher_student_performance`
3. Choose visualization: **Table**
4. **Configuration:**
   - **Query > Columns:** 
     - student_name
     - total_attempts
     - unique_levels_completed
     - completion_rate
     - last_activity_date
     - days_since_last_activity
   - **Query > Metrics:** (leave empty for table)
   - **Customize > Table Options:**
     - Enable: Page length = 25
     - Enable: Search box
     - Enable: Cell bars (for completion_rate column)
5. **Conditional Formatting:**
   - Click **Customize** tab
   - Add conditional formatting:
     - completion_rate >= 80: Green background
     - completion_rate >= 50: Yellow background
     - completion_rate < 50: Red background
6. Click **Update Chart** then **Save**

---

### Visualization 2: Completion Rate by Student (Bar Chart)
**Dataset:** `teacher_student_performance`

**Steps:**
1. **Charts** → **+ Create Chart**
2. Dataset: `teacher_student_performance`
3. Visualization: **Bar Chart**
4. **Configuration:**
   - **Query > Dimensions:** student_name
   - **Query > Metrics:** 
     - Click **Simple** → Select `completion_rate`
   - **Customize:**
     - Show Values: Yes
     - Sort bars by: completion_rate (descending)
     - Color scheme: Choose appropriate (e.g., "Superset Colors")
5. **Save**

---

### Visualization 3: Class Activity Timeline
**Dataset:** `teacher_student_activity_timeline`

**Steps:**
1. **Charts** → **+ Create Chart**
2. Dataset: `teacher_student_activity_timeline`
3. Visualization: **Time-series Line Chart**
4. **Configuration:**
   - **Time:**
     - Time Column: activity_date
     - Time Grain: Day
     - Time Range: Last 30 days
   - **Query > Metrics:**
     - SUM(level_attempts)
     - SUM(completions)
   - **Customize:**
     - Show legend: Yes
     - Markers: Yes
     - Area chart: Optional (nice for showing volume)
5. **Save**

---

### Visualization 4: Level Difficulty Heatmap
**Dataset:** `teacher_level_difficulty`

**Steps:**
1. **Charts** → **+ Create Chart**
2. Dataset: `teacher_level_difficulty`
3. Visualization: **Heatmap**
4. **Configuration:**
   - **Query:**
     - X-Axis: levelno
     - Y-Axis: levelname
     - Metric: AVG(completion_rate)
   - **Customize:**
     - Color scheme: "red_yellow_blue" (reversed)
     - Show values: Yes
     - Normalize: By column
5. **Save**

---

### Visualization 5: Student Engagement Status (Pie Chart)
**Dataset:** `teacher_student_engagement`

**Steps:**
1. **Charts** → **+ Create Chart**
2. Dataset: `teacher_student_engagement`
3. Visualization: **Pie Chart**
4. **Configuration:**
   - **Query:**
     - Dimension: engagement_status
     - Metric: COUNT(student_name)
   - **Customize:**
     - Show labels: Yes
     - Show legend: Yes
     - Donut chart: Optional
5. **Save**

---

### Visualization 6: Top Performing Students (Big Number with Trendline)
**Dataset:** `teacher_student_performance`

**Steps:**
1. **Charts** → **+ Create Chart**
2. Dataset: `teacher_student_performance`
3. Visualization: **Big Number with Trendline**
4. **Configuration:**
   - **Query:**
     - Metric: COUNT(student_id)
     - Filters: completion_rate >= 80
   - **Customize:**
     - Subheader: "Students with 80%+ completion"
5. **Save**

---

### Visualization 7: Average Time per Level (Bar Chart)
**Dataset:** `teacher_level_difficulty`

**Steps:**
1. **Charts** → **+ Create Chart**
2. Dataset: `teacher_level_difficulty`
3. Visualization: **Bar Chart (Horizontal)**
4. **Configuration:**
   - **Query:**
     - Dimension: levelname
     - Metric: AVG(avg_time_minutes)
   - **Customize:**
     - Show values: Yes
     - Sort descending
5. **Save**

---

### Visualization 8: Student Progress Funnel
**Dataset:** `teacher_student_performance`

**Custom SQL for this specific chart:**
```sql
SELECT 
    'Registered' as stage, 
    COUNT(DISTINCT student_id) as students,
    1 as stage_order
FROM teacher_student_performance
UNION ALL
SELECT 
    'Started Levels' as stage,
    COUNT(DISTINCT CASE WHEN total_attempts > 0 THEN student_id END) as students,
    2 as stage_order
FROM teacher_student_performance
UNION ALL
SELECT 
    'Completed Any Level' as stage,
    COUNT(DISTINCT CASE WHEN completed_attempts > 0 THEN student_id END) as students,
    3 as stage_order
FROM teacher_student_performance
UNION ALL
SELECT 
    '50%+ Completion Rate' as stage,
    COUNT(DISTINCT CASE WHEN completion_rate >= 50 THEN student_id END) as students,
    4 as stage_order
FROM teacher_student_performance
ORDER BY stage_order;
```

**Steps:**
1. Create this as a new dataset first (save the query as dataset)
2. Create **Funnel Chart**
3. Dimension: stage
4. Metric: SUM(students)

---

## Building the Complete Dashboard

### Dashboard Layout: "Teacher Performance Dashboard"

**Top Row (KPIs):**
1. **Big Number**: Total Students
2. **Big Number**: Active Last 7 Days  
3. **Big Number**: Average Completion Rate
4. **Big Number**: Total Completions

**Second Row:**
5. **Student Performance Table** (full width)

**Third Row:**
6. **Completion Rate Bar Chart** (left half)
7. **Engagement Status Pie Chart** (right half)

**Fourth Row:**
8. **Activity Timeline** (full width)

**Fifth Row:**
9. **Level Difficulty Heatmap** (left 60%)
10. **Student Progress Funnel** (right 40%)

---

### Adding Dashboard Filters

After creating the dashboard:

1. Click **Edit Dashboard**
2. Click **+** → **Filter**
3. Add these filters:
   - **Date Range Filter:**
     - Column: last_activity_date
     - Default: Last 30 days
   - **Student Name Filter:**
     - Column: student_name
     - Type: Select (multi-select enabled)
   - **Engagement Status Filter:**
     - Column: engagement_status
     - Type: Select
   - **Level Name Filter:**
     - Column: levelname
     - Type: Select

4. Configure filter scope:
   - Click on each filter
   - Click **Settings**
   - Check which charts should respond to this filter
   - Apply

---

## Testing Your Queries

Before creating visualizations, test each query:

1. **In SQL Lab:**
   - Run each query with `LIMIT 10` first
   - Check for errors
   - Verify data looks correct
   - Remove `LIMIT` when ready

2. **Common Issues:**
   - If you get "`create` is a reserved keyword":
     - Change to `"create"` (with quotes)
   - If no data appears:
     - Check schema name matches your setup
     - Verify `u.role = 'student'` filter
   - If joins fail:
     - Verify `_id` and `userid` columns exist

---

## Tips for Teachers

### Reading the Dashboard:

1. **Completion Rate:**
   - 80%+ = Excellent
   - 50-79% = Good, room for improvement
   - <50% = May need intervention

2. **Days Since Last Activity:**
   - 0-7 days = Active
   - 8-30 days = Check in recommended
   - 30+ days = Intervention needed

3. **Level Difficulty:**
   - <40% completion = Difficult level, may need review
   - 40-70% = Appropriate challenge
   - >70% = Easy level or well-learned

### Actions Based on Data:

- **Low engagement students:** Reach out, offer support
- **Difficult levels:** Review content, provide additional resources
- **High performers:** Offer advanced challenges
- **Inactive students:** Send reminders, check for technical issues

---

## Customization Options

### To Add Custom Metrics:

1. Go to **Data** → **Datasets**
2. Click on your dataset
3. Click **Metrics** tab
4. Click **+ Add Metric**
5. Examples:
   - **Success Rate:** 
     ```sql
     COUNT(CASE WHEN levelcomplete = true THEN 1 END) / COUNT(*)
     ```
   - **Average Session Time:**
     ```sql
     AVG(time_spent_minutes)
     ```

### To Add Custom Columns:

1. Same dataset view
2. Click **Columns** tab
3. Click **+ Add Column**
4. Use SQL expressions like:
   ```sql
   CASE 
     WHEN completion_rate >= 80 THEN 'High'
     WHEN completion_rate >= 50 THEN 'Medium'
     ELSE 'Low'
   END
   ```

---

## Maintenance

### Weekly Tasks:
- Review dashboard for data accuracy
- Check for inactive students
- Note any unusual patterns

### Monthly Tasks:
- Export data for records
- Review level difficulty trends
- Update filters/date ranges as needed

---

## Troubleshooting

### Query Taking Too Long?
- Add date filters: `WHERE lf."create" >= CURRENT_DATE - INTERVAL '90' DAY`
- Reduce data scope temporarily

### Charts Not Updating?
- Click **Refresh** icon on chart
- Check dashboard **Auto-refresh** settings
- Clear cache: **Settings** → **Clear Cache**

### Data Looks Wrong?
- Verify schema name in queries
- Check that `role = 'student'` filter is correct
- Test query in SQL Lab first

---

## Export and Sharing

### To Share Dashboard:
1. Click **Share** → **Copy permalink**
2. Or: Click **...** → **Set access** to control permissions

### To Export Data:
1. On any chart, click **...** → **Download** → Choose format (CSV, Excel, etc.)
2. On table charts, click **Download as CSV**

---

## Next Steps

1. ✅ Test connectivity query from screenshot
2. ✅ Create first dataset: `teacher_student_performance`
3. ✅ Create first visualization: Student Performance Table
4. ✅ Build out remaining visualizations
5. ✅ Assemble dashboard
6. ✅ Add filters
7. ✅ Share with teaching team
8. ✅ Gather feedback and iterate

---

**Need help?** Reference the main implementation guide or test queries individually in SQL Lab!
