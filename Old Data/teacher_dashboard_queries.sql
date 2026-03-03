-- ================================================================
-- TEACHER DASHBOARD SQL QUERIES
-- Langara VR Analytics - Apache Superset
-- ================================================================
-- IMPORTANT: All instances of "create" and "update" are in quotes
-- because they are reserved SQL keywords in Trino
-- ================================================================

-- ================================================================
-- QUERY 1: Student Performance Overview
-- Dataset Name: teacher_student_performance
-- Purpose: Main overview of each student's performance metrics
-- ================================================================

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
WHERE u.role = 'student'
GROUP BY u._id, u.username, u.role, u.created
ORDER BY last_activity_date DESC NULLS LAST;


-- ================================================================
-- QUERY 2: Level-by-Level Student Progress
-- Dataset Name: teacher_level_progress
-- Purpose: Detailed view of which students completed which levels
-- ================================================================

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


-- ================================================================
-- QUERY 3: Student Activity Timeline
-- Dataset Name: teacher_student_activity_timeline
-- Purpose: Daily activity tracking per student
-- ================================================================

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


-- ================================================================
-- QUERY 4: Level Difficulty Analysis
-- Dataset Name: teacher_level_difficulty
-- Purpose: Identify challenging levels based on completion rates
-- ================================================================

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


-- ================================================================
-- QUERY 5: Student Engagement Score
-- Dataset Name: teacher_student_engagement
-- Purpose: Calculate engagement metrics and status for each student
-- ================================================================

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


-- ================================================================
-- QUERY 6: Scene Completion Details
-- Dataset Name: teacher_scene_performance
-- Purpose: Granular scene-level performance analysis
-- ================================================================

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


-- ================================================================
-- QUERY 7: Quiz Performance
-- Dataset Name: teacher_quiz_performance
-- Purpose: Track student assessment results
-- Note: Only run if you have attemptquizzes table
-- ================================================================

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


-- ================================================================
-- QUERY 8: Class Summary Statistics
-- Dataset Name: teacher_class_summary
-- Purpose: High-level KPIs for the entire class
-- ================================================================

SELECT 
    COUNT(DISTINCT u._id) as total_students,
    COUNT(DISTINCT CASE 
        WHEN DATE_DIFF('day', lf.max_create, CURRENT_TIMESTAMP) <= 7 
        THEN u._id 
    END) as active_last_7_days,
    COUNT(DISTINCT CASE 
        WHEN DATE_DIFF('day', lf.max_create, CURRENT_TIMESTAMP) <= 30 
        THEN u._id 
    END) as active_last_30_days,
    ROUND(AVG(completion_stats.completion_rate), 1) as avg_completion_rate,
    SUM(completion_stats.total_attempts) as total_class_attempts,
    SUM(completion_stats.completions) as total_class_completions
FROM "langara-dev".users u
LEFT JOIN (
    SELECT userid, MAX("create") as max_create
    FROM "langara-dev".levelflows
    GROUP BY userid
) lf ON u._id = lf.userid
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
WHERE u.role = 'student';


-- ================================================================
-- QUERY 9: Student Retention Funnel
-- Dataset Name: teacher_student_funnel
-- Purpose: Track student progression through the learning journey
-- ================================================================

WITH student_base AS (
    SELECT 
        u._id,
        COUNT(DISTINCT lf._id) as attempts,
        COUNT(DISTINCT CASE WHEN lf.levelcomplete = true THEN lf._id END) as completions,
        ROUND(
            COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) * 100.0 / 
            NULLIF(COUNT(*), 0), 
            1
        ) as completion_rate
    FROM "langara-dev".users u
    LEFT JOIN "langara-dev".levelflows lf ON u._id = lf.userid
    WHERE u.role = 'student'
    GROUP BY u._id
)
SELECT 
    'All Students' as stage,
    COUNT(*) as student_count,
    1 as stage_order
FROM student_base
UNION ALL
SELECT 
    'Started Any Level' as stage,
    COUNT(*) as student_count,
    2 as stage_order
FROM student_base
WHERE attempts > 0
UNION ALL
SELECT 
    'Completed Any Level' as stage,
    COUNT(*) as student_count,
    3 as stage_order
FROM student_base
WHERE completions > 0
UNION ALL
SELECT 
    '50%+ Completion Rate' as stage,
    COUNT(*) as student_count,
    4 as stage_order
FROM student_base
WHERE completion_rate >= 50
UNION ALL
SELECT 
    '80%+ Completion Rate' as stage,
    COUNT(*) as student_count,
    5 as stage_order
FROM student_base
WHERE completion_rate >= 80
ORDER BY stage_order;


-- ================================================================
-- QUERY 10: Weekly Activity Trends
-- Dataset Name: teacher_weekly_trends
-- Purpose: Track weekly patterns in student activity
-- ================================================================

SELECT 
    DATE_TRUNC('week', lf."create") as week_start,
    COUNT(DISTINCT lf.userid) as active_students,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) as completions,
    ROUND(
        COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 
        1
    ) as weekly_completion_rate,
    ROUND(AVG(DATE_DIFF('minute', lf."create", lf."update")), 1) as avg_session_minutes
FROM "langara-dev".levelflows lf
JOIN "langara-dev".users u ON lf.userid = u._id
WHERE u.role = 'student'
    AND lf."create" >= CURRENT_DATE - INTERVAL '90' DAY
GROUP BY DATE_TRUNC('week', lf."create")
ORDER BY week_start DESC;


-- ================================================================
-- QUERY 11: At-Risk Students
-- Dataset Name: teacher_at_risk_students
-- Purpose: Identify students who may need intervention
-- ================================================================

SELECT 
    u.username as student_name,
    COALESCE(COUNT(DISTINCT lf._id), 0) as total_attempts,
    COALESCE(COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END), 0) as completions,
    COALESCE(ROUND(
        COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 
        1
    ), 0) as completion_rate,
    MAX(lf."create") as last_activity,
    COALESCE(DATE_DIFF('day', MAX(lf."create"), CURRENT_TIMESTAMP), 999) as days_inactive,
    CASE 
        WHEN MAX(lf."create") IS NULL THEN 'Never Active'
        WHEN DATE_DIFF('day', MAX(lf."create"), CURRENT_TIMESTAMP) > 30 THEN 'Inactive 30+ Days'
        WHEN ROUND(
            COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) * 100.0 / 
            NULLIF(COUNT(*), 0), 1) < 30 THEN 'Low Completion Rate'
        WHEN COUNT(*) < 3 AND DATE_DIFF('day', u.created, CURRENT_TIMESTAMP) > 14 THEN 'Low Engagement'
        ELSE 'Monitor'
    END as risk_category
FROM "langara-dev".users u
LEFT JOIN "langara-dev".levelflows lf ON u._id = lf.userid
WHERE u.role = 'student'
GROUP BY u._id, u.username, u.created
HAVING 
    MAX(lf."create") IS NULL 
    OR DATE_DIFF('day', MAX(lf."create"), CURRENT_TIMESTAMP) > 30
    OR ROUND(
        COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 1) < 30
    OR (COUNT(*) < 3 AND DATE_DIFF('day', u.created, CURRENT_TIMESTAMP) > 14)
ORDER BY days_inactive DESC, completion_rate ASC;


-- ================================================================
-- QUERY 12: Top Performers
-- Dataset Name: teacher_top_performers
-- Purpose: Highlight students excelling in the program
-- ================================================================

SELECT 
    u.username as student_name,
    COUNT(*) as total_attempts,
    COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) as completions,
    COUNT(DISTINCT lf.levelname) as unique_levels,
    ROUND(
        COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 
        1
    ) as completion_rate,
    ROUND(AVG(DATE_DIFF('minute', lf."create", lf."update")), 1) as avg_time_per_level,
    MAX(lf."create") as last_activity,
    DATE_DIFF('day', u.created, MAX(lf."create")) as days_active
FROM "langara-dev".users u
JOIN "langara-dev".levelflows lf ON u._id = lf.userid
WHERE u.role = 'student'
GROUP BY u._id, u.username, u.created
HAVING 
    COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) >= 5
    AND ROUND(
        COUNT(CASE WHEN lf.levelcomplete = true THEN 1 END) * 100.0 / 
        NULLIF(COUNT(*), 0), 1) >= 70
ORDER BY completion_rate DESC, completions DESC
LIMIT 20;


-- ================================================================
-- TESTING QUERIES
-- ================================================================

-- Test 1: Verify data exists and reserved keyword handling
SELECT 
    u._id, 
    u.username, 
    lf.levelname,
    lf."create" as level_created  -- Note the quotes!
FROM "langara-dev".users u 
LEFT JOIN "langara-dev".levelflows lf ON u._id = lf.userid 
LIMIT 10;

-- Test 2: Check if student role filter works
SELECT 
    role,
    COUNT(*) as user_count
FROM "langara-dev".users
GROUP BY role;

-- Test 3: Verify date calculations work
SELECT 
    username,
    created as registration_date,
    DATE_DIFF('day', created, CURRENT_TIMESTAMP) as days_registered
FROM "langara-dev".users
WHERE role = 'student'
LIMIT 10;

-- Test 4: Check levelflows table structure
SELECT 
    levelname,
    levelno,
    levelcomplete,
    "create",
    "update",
    CARDINALITY(scene) as scene_count
FROM "langara-dev".levelflows
LIMIT 10;


-- ================================================================
-- NOTES FOR IMPLEMENTATION
-- ================================================================

/*
1. Always use "create" and "update" in quotes (reserved keywords)
2. Schema name is "langara-dev" - adjust if different in your setup
3. Test each query with LIMIT 10 first before creating dataset
4. For date ranges, use: WHERE lf."create" >= CURRENT_DATE - INTERVAL '30' DAY
5. If query is slow, add date filters to reduce data volume

STEP-BY-STEP PROCESS:
1. Open Superset → SQL Lab
2. Select Database: trino
3. Select Schema: langara-dev-client (or your schema name)
4. Copy-paste one query at a time
5. Add LIMIT 10 to test first
6. Click RUN
7. If successful, remove LIMIT and click SAVE → Save Dataset
8. Name the dataset as indicated in comments
9. Move to Charts to create visualizations

TROUBLESHOOTING:
- Error "create is reserved": Add quotes → "create"
- No data: Check schema name and role filter
- Slow query: Add date filters or LIMIT
- UNNEST error: Verify scene array structure
*/
