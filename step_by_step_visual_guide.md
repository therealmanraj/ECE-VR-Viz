# Step-by-Step Visual Guide: Building the Teacher Dashboard

## 📋 Prerequisites Checklist
- [ ] Access to Superset instance
- [ ] Database connection configured (Trino)
- [ ] Schema accessible: `langara-dev-client`
- [ ] SQL queries file downloaded: `teacher_dashboard_queries.sql`

---

## Part 1: Creating Your First Dataset

### Step 1: Access SQL Lab
1. Open Superset in your browser
2. Click **SQL** in the top navigation menu
3. Click **SQL Lab**

**What you should see:**
- Left sidebar with DATABASE and SCHEMA dropdowns
- Large SQL editor area in the center
- RUN button below the editor

---

### Step 2: Configure Database Connection
**In the left sidebar:**

1. **DATABASE dropdown:** 
   - Select: `trino`
   
2. **SCHEMA dropdown:**
   - Select: `langara-dev-client` (or the schema name from your screenshot)
   - Click the refresh icon if needed

**Visual check:** Your screen should match the screenshot you provided, with these selections visible.

---

### Step 3: Test Your First Query

**Copy this test query:**
```sql
SELECT 
    u._id, 
    u.username, 
    lf.levelname,
    lf."create" as level_created
FROM "langara-dev".users u 
LEFT JOIN "langara-dev".levelflows lf ON u._id = lf.userid 
WHERE u.role = 'student'
LIMIT 10;
```

**Actions:**
1. Paste into the SQL editor (the large text area)
2. Click the blue **RUN** button
3. Wait for results to appear below

**Success indicators:**
- ✅ Green timer showing execution time (e.g., "00:00:01.23")
- ✅ **RESULTS** tab becomes active
- ✅ Data table appears with columns: _id, username, levelname, level_created

**If you see an error:**
- Red error message? Check the schema name matches yours
- "create is reserved keyword"? Ensure you have quotes: `"create"`
- No data? The role filter might need adjustment

---

### Step 4: Create Your First Dataset

**After successful query:**

1. Click **SAVE** button (top right, near RUN)
2. A modal dialog appears: "Save or Overwrite Dataset"

**Fill in the form:**
- **Dataset Name:** `teacher_student_performance`
- **Database:** Should auto-fill as `trino`
- **Schema:** Should auto-fill as `langara-dev-client`

3. Click **SAVE & EXPLORE** button

**What happens next:**
- You'll be redirected to the Chart creation page
- The dataset is now available in Data → Datasets
- You can now create visualizations!

---

## Part 2: Creating Your First Visualization

### Step 5: Create Student Performance Table

**You should now be on the "Create Chart" page.**

**Chart Type Selection:**
1. If not already selected, find **Table** in the visualization types
2. Click on **Table** icon

**Configuration Panel (left side):**

#### DATA Tab:

**Query Section:**
1. **Columns:** Click "+ Add column"
   - Add these columns one by one:
     - `student_name`
     - `total_attempts`
     - `unique_levels_completed`
     - `completion_rate`
     - `last_activity_date`
     - `days_since_last_activity`

2. **Metrics:** Leave empty (we're showing raw columns)

3. **Filters:** (optional for now)
   - Click "+ Add filter" if you want to filter data
   - Example: `completion_rate >= 0`

#### CUSTOMIZE Tab:

1. **Table Options:**
   - **Page Length:** Select `25` from dropdown
   - **Search Box:** Toggle ON (green)
   - **Cell Bars:** Toggle ON
   - **Align +/- values:** Toggle ON

2. **Conditional Formatting:**
   - Click "+ Add formatting rule"
   - **Rule 1:**
     - Column: `completion_rate`
     - Operator: `>=`
     - Value: `80`
     - Color: Green (#52C41A)
   - Click "+ Add formatting rule" again
   - **Rule 2:**
     - Column: `completion_rate`
     - Operator: `<`
     - Value: `50`
     - Color: Red (#FF4D4F)

**Actions:**
1. Click **UPDATE CHART** (bottom left)
2. Wait for chart to render
3. If it looks good, click **SAVE** (top right)

**Save Dialog:**
- **Chart Name:** `Student Performance Table`
- **Add to Dashboard:** 
  - Select: **+ Create new dashboard**
  - **Dashboard Name:** `Teacher Performance Dashboard`
- Click **SAVE**

---

### Step 6: Create Completion Rate Bar Chart

**From the dashboard:**
1. Click **+ CREATE CHART** button (or Charts → + Create Chart)

**Configure:**
1. **Choose Dataset:** `teacher_student_performance`
2. **Choose Chart Type:** Bar Chart
3. Click **CREATE NEW CHART**

#### DATA Tab:

**Query:**
- **Dimensions:** 
  - Click, select: `student_name`
- **Metrics:**
  - Click "+ Add metric"
  - Select: `AVG(completion_rate)`

**Filters:**
- Optional: Add filter to show only students with attempts
- `total_attempts > 0`

#### CUSTOMIZE Tab:

**Chart Options:**
- **Orientation:** Vertical
- **Show Values:** Toggle ON
- **Sort Bars By:** `AVG(completion_rate)`
- **Sort Descending:** ON

**Color:**
- **Color Scheme:** Select "Superset Colors" or preferred scheme

**Actions:**
1. Click **UPDATE CHART**
2. Click **SAVE**
3. **Chart Name:** `Completion Rate by Student`
4. **Add to Dashboard:** Select `Teacher Performance Dashboard`
5. Click **SAVE**

---

### Step 7: Create Activity Timeline

**Create new chart:**
1. Dataset: `teacher_student_activity_timeline`
2. Chart Type: **Time-series Line Chart**

#### DATA Tab:

**Query:**
- **Time Column:** `activity_date`
- **Time Grain:** Day
- **Metrics:**
  - Click "+ Add metric"
  - Add: `SUM(level_attempts)`
  - Add: `SUM(completions)`

**Time Range:**
- Last 30 days

#### CUSTOMIZE Tab:

**Chart Options:**
- **Show Legend:** ON
- **Markers:** ON
- **Area Chart:** Optional (try both ways)

**Actions:**
1. **UPDATE CHART**
2. **SAVE** as `Student Activity Timeline`
3. Add to `Teacher Performance Dashboard`

---

### Step 8: Create KPI Big Numbers

**For each KPI, create a new chart:**

**KPI 1: Total Students**
1. Dataset: `teacher_class_summary`
2. Chart Type: **Big Number**
3. **Metric:** `total_students`
4. **Subheader:** "Registered Students"
5. Save as: `Total Students KPI`

**KPI 2: Active Last 7 Days**
1. Dataset: `teacher_class_summary`
2. Chart Type: **Big Number**
3. **Metric:** `active_last_7_days`
4. **Subheader:** "Active This Week"
5. Save as: `Active Students KPI`

**KPI 3: Average Completion Rate**
1. Dataset: `teacher_class_summary`
2. Chart Type: **Big Number**
3. **Metric:** `avg_completion_rate`
4. **Number Format:** `,.1f%` (for percentage)
5. **Subheader:** "Class Average"
6. Save as: `Avg Completion Rate KPI`

---

## Part 3: Building the Dashboard

### Step 9: Arrange Dashboard Layout

**Navigate to your dashboard:**
1. **Dashboards** → `Teacher Performance Dashboard`
2. Click **EDIT DASHBOARD** (top right)

**You're now in edit mode. You can:**
- Drag charts to reposition
- Resize charts by dragging corners
- Add components

**Recommended Layout:**

```
┌─────────────────────────────────────────────────────┐
│  Row 1: KPIs (4 across)                             │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐           │
│  │ KPI1 │  │ KPI2 │  │ KPI3 │  │ KPI4 │           │
│  └──────┘  └──────┘  └──────┘  └──────┘           │
├─────────────────────────────────────────────────────┤
│  Row 2: Main Table (full width)                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  Student Performance Table                   │   │
│  │  (shows all student metrics)                 │   │
│  └─────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  Row 3: Charts (2 across)                           │
│  ┌──────────────────────┐  ┌──────────────────┐   │
│  │  Completion Rate     │  │  Engagement      │   │
│  │  Bar Chart           │  │  Pie Chart       │   │
│  └──────────────────────┘  └──────────────────┘   │
├─────────────────────────────────────────────────────┤
│  Row 4: Timeline (full width)                       │
│  ┌─────────────────────────────────────────────┐   │
│  │  Activity Timeline                           │   │
│  │  (line chart showing daily activity)         │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

**To resize charts:**
1. Hover over chart
2. Grab the bottom-right corner
3. Drag to desired size

**To add rows/columns:**
1. Click **+ icon** → **Row** or **Column**
2. Drag charts into new sections

---

### Step 10: Add Dashboard Filters

**In edit mode:**

1. Click **+** → **Filter**
2. A filter component appears

**Configure Student Name Filter:**
1. Click on the filter box
2. **Filter Name:** Student Name
3. **Dataset:** `teacher_student_performance`
4. **Column:** `student_name`
5. **Filter Type:** Select filter (multi-select)
6. **Default Value:** (leave empty)

**Configure filter scope:**
1. Click **⚙️ Settings** on the filter
2. Check which charts should be affected:
   - ✅ Student Performance Table
   - ✅ Completion Rate Bar Chart
   - ✅ Activity Timeline
3. Click **SAVE**

**Add more filters:**

**Date Range Filter:**
1. Add new filter
2. **Filter Name:** Date Range
3. **Dataset:** `teacher_student_performance`
4. **Column:** `last_activity_date`
5. **Filter Type:** Time range
6. **Default:** Last 30 days

**Engagement Status Filter:**
1. Add new filter
2. **Filter Name:** Engagement Status
3. **Dataset:** `teacher_student_engagement`
4. **Column:** `engagement_status`
5. **Filter Type:** Select filter
6. Configure scope for relevant charts

---

### Step 11: Add Dashboard Tabs (Optional)

**To organize by category:**

1. Click **+** → **Tab**
2. Name it: "Overview"
3. Add another tab: "Individual Students"
4. Add another tab: "Level Analysis"

**Move charts to appropriate tabs:**
- **Overview tab:** KPIs, class-level charts
- **Individual Students tab:** Student table, individual metrics
- **Level Analysis tab:** Level difficulty, scene analysis

---

### Step 12: Final Touches

**Dashboard Settings:**

1. Click **⋮** (three dots) → **Settings**

**Configure:**
- **Title:** Teacher Performance Dashboard
- **Slug:** teacher-dashboard
- **Owners:** Add yourself
- **Color Scheme:** Choose preferred theme
- **Refresh Frequency:** 
  - Auto-refresh: 5 minutes (optional)
- **Dashboard Mode:** 
  - Published: ON (when ready to share)

**Add Text/Markdown:**

1. Click **+** → **Markdown**
2. Add instructions or notes:

```markdown
# Teacher Dashboard Instructions

**How to use this dashboard:**
- Use filters to focus on specific students or date ranges
- Click on chart elements to drill down
- Export data using the ⋮ menu on each chart

**Color Coding:**
- 🟢 Green: 80%+ completion rate (excellent)
- 🟡 Yellow: 50-79% completion rate (good)
- 🔴 Red: <50% completion rate (needs attention)

Last updated: [Auto]
```

---

### Step 13: Save and Publish

1. Click **SAVE** (top right)
2. Review your dashboard
3. Click **EDIT DASHBOARD** again to make changes
4. When satisfied, click **SAVE** and exit edit mode

**Share your dashboard:**
1. Click **Share** → **Copy permalink**
2. Send link to other teachers
3. Or click **⋮** → **Set access** to manage permissions

---

## Part 4: Common Tasks

### How to Edit an Existing Chart

1. Navigate to the chart (on dashboard or Charts page)
2. Click **⋮** → **Edit chart**
3. Make changes in the configuration panel
4. Click **UPDATE CHART**
5. Click **SAVE** → **OVERWRITE**

---

### How to Add a New Chart to Dashboard

1. Create chart following steps above
2. When saving, select **Add to Dashboard**
3. Choose `Teacher Performance Dashboard`
4. Chart appears on dashboard
5. Edit dashboard to position it properly

---

### How to Export Data

**From a chart:**
1. Click **⋮** on the chart
2. Select **Download** → Choose format:
   - CSV
   - Excel
   - JSON

**From a table:**
1. Click **Download as CSV** button

---

### How to Schedule Email Reports

1. On dashboard, click **⋮**
2. Select **Set up email report**
3. Configure:
   - **Recipient emails:** Your email(s)
   - **Schedule:** Daily, Weekly, etc.
   - **Format:** PDF or PNG
4. Click **ADD**

---

## Part 5: Advanced Features

### Creating Custom Metrics

**Example: Success Rate Custom Metric**

1. **Data** → **Datasets**
2. Click on `teacher_student_performance`
3. Click **Metrics** tab
4. Click **+ Add Metric**
5. **Metric name:** `success_rate`
6. **SQL Expression:** 
   ```sql
   COUNT(CASE WHEN completion_rate >= 70 THEN 1 END) / COUNT(*)
   ```
7. **Metric Type:** Percentage
8. **Format:** `,.1f%`
9. Click **SAVE**

**Use in charts:**
- Now available in metric dropdown
- Shows calculated success rate

---

### Creating Calculated Columns

**Example: Performance Category**

1. **Data** → **Datasets** → `teacher_student_performance`
2. Click **Columns** tab
3. Click **+ Add Column**
4. **Column name:** `performance_category`
5. **SQL Expression:**
   ```sql
   CASE 
       WHEN completion_rate >= 80 THEN 'High Performer'
       WHEN completion_rate >= 50 THEN 'Average'
       ELSE 'Needs Support'
   END
   ```
6. Click **SAVE**

**Use in charts:**
- Group by `performance_category`
- Filter by `performance_category`

---

### Adding Drill-Through

**Make charts interactive:**

1. Edit a chart
2. **Customize** tab
3. Find **Drill to detail**
4. **Enable:** ON
5. **Drill to detail target:** Choose dashboard or URL
6. **SAVE**

**Now users can:**
- Click on chart elements
- Drill down to detailed view

---

## Part 6: Troubleshooting

### Chart Not Updating

**Solutions:**
1. Click **↻ Refresh** icon on chart
2. **⋮** → **Force refresh**
3. Clear cache: **Settings** → **Clear cache**

---

### Query Timeout

**Solutions:**
1. Add date filters to reduce data:
   ```sql
   WHERE lf."create" >= CURRENT_DATE - INTERVAL '90' DAY
   ```
2. Increase timeout: **Settings** → **SQL Lab** → **Query timeout**
3. Create materialized view for complex queries

---

### Data Looks Incorrect

**Debugging steps:**
1. Go to **SQL Lab**
2. Run query manually with `LIMIT 10`
3. Check:
   - Schema name correct?
   - Role filter working? (`WHERE u.role = 'student'`)
   - Quotes around reserved keywords? (`"create"`)
4. Compare with source data in database

---

### Filter Not Working

**Fixes:**
1. Edit dashboard
2. Click on filter → **⚙️ Settings**
3. Verify **Filter scope** includes the chart
4. Check dataset connection
5. Ensure column names match

---

## Part 7: Best Practices

### Performance Tips

1. **Use date filters everywhere:**
   - Default to last 30-90 days
   - Users can expand if needed

2. **Limit rows in tables:**
   - Set page length to 25-50
   - Enable pagination

3. **Cache results:**
   - **Settings** → **Cache timeout** → 3600 seconds

4. **Create views for complex queries:**
   - Run in SQL Lab:
     ```sql
     CREATE VIEW v_student_performance AS
     [your query here]
     ```

---

### Design Tips

1. **Consistent colors:**
   - Use same color scheme across all charts
   - Green = good, Red = needs attention

2. **Clear labels:**
   - Descriptive chart titles
   - Add units (%, minutes, count)

3. **Logical grouping:**
   - Put related charts together
   - Use tabs to separate concerns

4. **Mobile responsive:**
   - Test on different screen sizes
   - Adjust chart sizes accordingly

---

### Security Tips

1. **Row-level security:**
   - If teachers should only see their students
   - Configure in **Settings** → **Security**

2. **Access control:**
   - Set dashboard permissions
   - Create user roles (Teacher, Admin)

3. **Data privacy:**
   - Don't expose sensitive student info
   - Use student IDs instead of names where appropriate

---

## Part 8: Maintenance Schedule

### Daily Tasks
- [ ] Check dashboard loads correctly
- [ ] Review any alerts for at-risk students
- [ ] Verify data freshness

### Weekly Tasks
- [ ] Review overall class performance
- [ ] Identify trends in activity
- [ ] Update filters/date ranges as needed

### Monthly Tasks
- [ ] Archive old data (if needed)
- [ ] Review and update metrics
- [ ] Gather teacher feedback
- [ ] Add new visualizations based on needs

---

## Quick Reference

### Keyboard Shortcuts

- **Run query:** `Ctrl + Enter` (SQL Lab)
- **Save chart:** `Ctrl + S`
- **Toggle edit mode:** (none, use button)

### Common SQL Patterns

**Date filtering:**
```sql
WHERE lf."create" >= CURRENT_DATE - INTERVAL '30' DAY
```

**Null handling:**
```sql
COALESCE(column_name, default_value)
```

**Percentage calculation:**
```sql
ROUND(numerator * 100.0 / NULLIF(denominator, 0), 1)
```

---

## Getting Help

### Resources
- **Superset Docs:** https://superset.apache.org/docs/intro
- **Trino SQL Ref:** https://trino.io/docs/current/sql.html
- **Your Implementation Guide:** See `superset_implementation_guide.md`

### Support Process
1. Check this guide first
2. Test query in SQL Lab
3. Check Superset logs (if admin access)
4. Ask IT/Database admin
5. Review Superset documentation

---

## Success Checklist

After completing this guide, you should have:
- [ ] 8+ datasets created
- [ ] 12+ visualizations created
- [ ] 1 complete dashboard with filters
- [ ] Ability to export data
- [ ] Understanding of how to create new charts
- [ ] Dashboard shared with other teachers

**Congratulations! You now have a fully functional Teacher Performance Dashboard!** 🎉
