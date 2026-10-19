# Instagram Performance Analytics for Sugar Cosmetics

An interactive Streamlit analytics dashboard for evaluating post-level performance, audience conversion, and campaign engagement for **Sugar Cosmetics** across 50,000 Instagram posts.

---

## Streamlit App Link: 
https://instagramanalytics-awu29g4zgsyhetu7kiwxz6.streamlit.app/

---

## 1. Business Problem

Beauty brands on Instagram compete in a high-frequency, algorithm-driven feed where content creators, brands, and consumers interact through multiple formats (Reels, Stories, Feed Images, Videos) and promotional campaigns.

Key operational questions addressed by this dashboard:
1. **Content Format Efficacy**: Do Reels drive higher engagement rates compared to Stories, static Images, or Videos?
2. **Timing & Cadence**: Does posting on specific weekdays materially lift engagement?
3. **Hashtag Association**: Which hashtags correlate with superior engagement rates?
4. **Campaign Performance**: Which campaign angles (e.g., Influencer Collabs vs. Giveaways vs. Tutorials) yield higher conversion and follower acquisition?
5. **Audience Conversion**: How efficiently do impressions translate into reach, post interactions, profile visits, and new followers?

---

## 2. Dataset & Data Audit

- **Volume & Range**: 50,000 post records spanning **19 April 2024 to 19 April 2025** (366 calendar days).
- **Aggregate Totals**:
  - Total Likes: **147,728,279**
  - Total Comments: **18,459,361**
  - Total Shares: **8,115,338**
  - Total Saves: **8,861,439**
  - Total Engagement: **183,164,417**
  - Total Reach: **987,423,288** (sum of per-post reach)
  - Total Impressions: **1,276,045,750**
  - Total Profile Visits: **29,634,798**
  - Total Follows: **8,866,710**
  - Average Engagement Rate: **18.54%**
- **Data Completeness**:
  - **14 raw columns**: `Post Date`, `Post Type`, `Campaign Type`, `Hashtags`, `Audience Emotion`, `Engagement Source`, `Impressions`, `Reach`, `Likes`, `Comments`, `Shares`, `Saves`, `Profile Visits`, `Follows`.
  - **Zero missing values**: 0 nulls across all 50,000 rows.
  - **Zero duplicates**: 0 fully duplicate records.
  - **Logical consistency**: 0 rows where `Impressions < Reach`, 0 rows where `Reach == 0`, and 0 rows where `(Likes + Comments + Shares + Saves) > Reach`.
  - **Missing Column Note**: The dataset contains **no post caption column**. Posts are identified by `#post_id | Date | Type | Campaign`.

---

## 3. Methodology

### 3.1 Metric Definitions
- **Per-Post Engagement Rate (ER)**:
  $$\text{Engagement Rate} = \frac{\text{Likes} + \text{Comments} + \text{Shares} + \text{Saves}}{\text{Reach}}$$
  Calculated on each post and averaged across posts (fraction stored as `0–1`, displayed as percentage).
- **Macro Aggregate Engagement Rate**:
  $$\frac{\sum \text{Total Engagement}}{\sum \text{Reach}} = \frac{183,164,417}{987,423,288} = 18.55\%$$
  Very close to the per-post average of $18.54\%$, indicating stable reach weighting across post sizes.
- **Total Reach**: Sum of per-post reach figures, reflecting total viewer touchpoints rather than deduplicated unique individual accounts.

### 3.2 Calendar & Partial Month Normalization
- The dataset starts on **19 Apr 2024** and ends on **19 Apr 2025**.
- **April 2024** contains 12 active tracking days (19–30 Apr).
- **April 2025** contains 19 active tracking days (1–19 Apr).
- To prevent artificial dips in monthly volume charts, `posts_per_day` is computed as:
  $$\text{Posts Per Day} = \frac{\text{Monthly Posts}}{\text{Active Tracking Days within Dataset Bounds}}$$
  This normalises April 2024 (1,626 / 12 = **135.5 posts/day**) and April 2025 (2,460 / 19 = **129.5 posts/day**) to fair cadence levels.

### 3.3 Multi-Tag Hashtags
- Posts contain 1 to 3 hashtags separated by `", "`.
- 66.75% of posts have multiple tags; 33.25% have a single tag.
- Posts are exploded so that each post counts toward every hashtag it includes.
- Because groups overlap, Welch's two-sample t-test (comparing posts *with* a tag vs. *without* it) is utilized with Bonferroni correction, rather than standard ANOVA.

### 3.4 Statistical Significance Testing
- **Group Comparisons**: One-way ANOVA ($F$-statistic) and non-parametric Kruskal-Wallis ($H$-statistic) test differences across post types, weekdays, and campaign types.
- **Effect Size**: Eta-squared ($\eta^2 = SS_{\text{between}} / SS_{\text{total}}$) measures the percentage of total variance in engagement rate explained by the categorical dimension.
- **Confidence Intervals**: 95% confidence intervals are displayed as error bars:
  $$\text{CI}_{95} = \bar{x} \pm 1.96 \times \frac{s}{\sqrt{n}}$$

---

## 4. Key Findings

> **Primary Strategic Takeaway**:  
> **No categorical group difference in engagement rate is statistically significant.**  
> Across post formats, days of the week, campaigns, and hashtags, each factor explains roughly **0.01% of the total variance** ($\eta^2 \approx 0.0001$). Differences across formats are under 0.25 percentage points. Consequently, brand recommendations must be approached as an **iterative experimentation framework** rather than prescriptive rules.

1. **Cadence Consistency**:
   - Posting frequency is remarkably stable across the year, averaging **130 to 141 posts per day** in every single month.
2. **Post Formats**:
   - Reel: **18.61%** average ER (highest)
   - Story: **18.60%** average ER
   - Video: **18.51%** average ER
   - Image: **18.43%** average ER (lowest)
   - Spread: **0.18 percentage points** (ANOVA $p = 0.152$, Kruskal-Wallis $p = 0.167$, $\eta^2 = 0.011\%$). All 95% confidence intervals overlap.
3. **Day of the Week**:
   - Wednesday: **18.63%** average ER (highest)
   - Sunday: **18.42%** average ER (lowest)
   - Spread: **0.21 percentage points** (ANOVA $p = 0.566$, Kruskal-Wallis $p = 0.568$, $\eta^2 = 0.010\%$).
4. **Campaign Angles**:
   - Influencer Collab: **18.60%** average ER (highest)
   - Tutorial: **18.58%** average ER
   - Giveaway: **18.57%** average ER
   - Product Launch: **18.49%** average ER
   - Festive Offer: **18.44%** average ER (lowest)
   - Spread: **0.16 percentage points** (ANOVA $p = 0.478$, Kruskal-Wallis $p = 0.456$, $\eta^2 = 0.007\%$).
5. **Audience Emotion**:
   - Curious: **18.62%** average ER (highest, 10,027 posts)
   - Confident: **18.57%** average ER (9,891 posts)
   - Inspired: **18.51%** average ER (10,137 posts)
   - Happy: **18.50%** average ER (9,884 posts)
   - Excited: **18.47%** average ER (lowest, 10,061 posts)
   - Spread: **0.16 percentage points** (ANOVA $p = 0.562$, Kruskal-Wallis $p = 0.572$, $\eta^2 = 0.006\%$).
6. **Engagement Source**:
   - Collab: **18.59%** average ER (highest, 12,633 posts)
   - Influencer: **18.58%** average ER (12,501 posts)
   - Paid: **18.53%** average ER (12,358 posts)
   - Organic: **18.44%** average ER (lowest, 12,508 posts)
   - Spread: **0.14 percentage points** (ANOVA $p = 0.349$, Kruskal-Wallis $p = 0.363$, $\eta^2 = 0.007\%$).
7. **Hashtags**:
   - `#VeganBeauty`: **18.61%** ER (highest) vs. `#MakeupGoals`: **18.51%** ER (lowest).
   - Difference: **0.12 percentage points**. Smallest Bonferroni-adjusted $p$-value is **0.377** (not statistically significant).
8. **Engagement Funnel**:
   - **Reach to Impressions**: Reach represents **77.4%** of impressions ($987.4\text{M} / 1.28\text{B}$).
   - **Likes**: **15.0%** of reached accounts ($147.7\text{M} / 987.4\text{M}$).
   - **Comments**: **1.87%** of reached accounts ($18.5\text{M} / 987.4\text{M}$).
   - **Saves**: **0.90%** of reached accounts ($8.86\text{M} / 987.4\text{M}$).
   - **Shares**: **0.82%** of reached accounts ($8.12\text{M} / 987.4\text{M}$).
9. **Growth Funnel & Monthly Growth Proxy**:
   - **3.0%** of reached accounts visit the brand profile ($29.6\text{M} / 987.4\text{M}$).
   - **29.9%** of profile visitors convert into followers ($8.87\text{M} / 29.6\text{M}$).
   - Net follower conversion from total reach is **0.90%** ($8.87\text{M} / 987.4\text{M}$).
   - **Monthly Growth Proxy**: Total post-attributed follows sum to **8,866,710** and profile visits to **29,634,798**. Because the dataset does not record total account follower counts or unfollows, follows attributed to posts serve as an acquisition growth proxy.
   - Across full tracking months, follows per day remained remarkably stable, ranging from a low of **23,299 follows/day** in **Jul 2024** (722,283 follows / 31 days) to a high of **25,072 follows/day** in **Jun 2024** (752,157 follows / 30 days). The post-level follow rate remained tightly bounded between **0.88%** and **0.91%** of reach across all months.
10. **Top Posts & "Hidden Gems"**:
   - The top 10 posts by likes all have high reach between **44,307 and 46,789** (peaking at 11,392 likes).
   - The top 10 posts by engagement rate span a tight range of **33.82% to 34.10%** with lower reach (median 23,485).
   - **0 of the top 10 engagement rate posts appear in the top 10 by likes**, highlighting high-efficiency posts that captured intense engagement despite modest distribution.

---

## 5. Dashboard Guide

The dashboard is structured into interactive controls and three primary tabs:

- **Sidebar Controls**:
  - `flt_post_type`: Multiselect filter for post types (Reel, Story, Video, Image).
  - `flt_campaign`: Multiselect filter for campaign categories.
  - `flt_months`: Range select slider across chronological months.
  - `flt_hashtags`: Multiselect filter matching any chosen hashtag.
  - Selection counter (`n of N posts selected`) and defensive zero-selection alert.
  - Expandable reference explaining metrics and post label format.
- **Top KPI Row**:
  - Total Posts, Total Likes, Total Comments, Total Reach, and Avg Engagement Rate with exact tooltip figures.
- **Tab 1: Overview**:
  - Monthly Posting Trend with a radio switch between absolute post counts and active-day normalized posts/day.
  - Side-by-side Top 10 by Likes vs. Top 10 by Engagement Rate horizontal bar charts with expandable data tables.
- **Tab 2: Content Performance**:
  - 4-panel small multiples breaking down average Likes, Comments, Shares, and Saves by format.
  - Post Type average ER with 95% CI error bars and dynamic ANOVA / Kruskal-Wallis significance caption.
  - Weekday performance chart with metric toggle (ER vs. Total Engagement).
  - Hashtag volume vs. ER bar charts with expandable Welch's t-test statistical significance summary.
  - Campaign performance: average ER with 95% CI error bars alongside average follows per post.
  - Audience emotion: average ER with 95% CI error bars alongside average follows per post and significance test caption.
  - Engagement source: average ER with 95% CI error bars alongside average follows per post and significance test caption.
- **Tab 3: Engagement & Growth**:
  - Full funnel conversion chart paired with actions per 100 reached accounts.
  - Growth funnel (Reach $\to$ Profile Visits $\to$ Follows) with dynamic conversion rate annotations.
  - Growth trend by month: chronological line chart of follows per day with a radio switch to follow rate (% of reach), partial months styled with open markers and dotted line segments, accompanied by dynamic callout of lowest (Jul 2024 at 23,299 follows/day) and highest (Jun 2024 at 25,072 follows/day) full months.

---

## 6. Screenshots

*Screenshots from the dashboard interface can be reviewed in the `images/` directory:*

- **Overview Tab**: `images/dashboard_overview.png`
- **Content Performance Tab**: `images/dashboard_content_performance.png`
- **Engagement & Growth Tab**: `images/dashboard_engagement_growth.png`

---

## 7. How to Run Locally

### Prerequisites
- Python 3.10+ (tested on Python 3.14)
- Git

### Setup Steps
```bash
# 1. Clone repository (if applicable) and enter directory
cd Instagram_Analytics

# 2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Place dataset file
# Note: Data/ is ignored in git. Place the Excel file at:
# Data/sugar_cosmetics_instagram_data.xlsx

# 5. Run verification test suite
python verify_loader.py
python verify_metrics.py
python verify_metrics_step4.py
python verify_metrics_step5.py
python verify_metrics_step6c.py
python verify_app.py

# 6. Launch the Streamlit dashboard
streamlit run app.py
```
Access the application at `http://localhost:8501`.

---

## 8. Project Structure

```text
Instagram_Analytics/
├── .gitignore               # Excludes venv/, __pycache__/, Data/, etc.
├── README.md                # Project documentation and analytical report
├── requirements.txt         # Dependencies (streamlit, pandas, plotly, openpyxl, scipy)
├── app.py                   # Streamlit analytics dashboard application
├── data_loader.py           # Data ingestion, snake_case renaming, derived columns, filtering
├── metrics.py               # Aggregations, funnel calculations, ANOVA, Kruskal, Welch t-tests
├── charts.py                # Reusable Plotly figures with consistent design tokens
├── audit_data.py            # Initial dataset audit and integrity check
├── verify_loader.py         # Verification tests for data_loader
├── verify_metrics.py        # Independent verification tests for Tasks 1-4
├── verify_metrics_step4.py  # Independent verification tests for Tasks 5-8
├── verify_metrics_step5.py  # Independent verification tests for formal significance tests
├── verify_metrics_step6c.py # Independent verification tests for Step 6c growth & emotion/source metrics
├── verify_app.py            # Automated Streamlit AppTest test suite
├── Data/                    # Untracked folder containing raw Excel file
└── images/                  # Exported visuals and screenshots
```

---

## 9. Limitations & Analytical Considerations

1. **Homogeneous Distribution**: The observed distributions across post types, weekdays, and campaigns show minimal variance ($\eta^2 \approx 0.01\%$, all $p > 0.15$). In real-world Instagram environments, format differences (e.g., Reels vs. static images) typically exhibit substantial algorithmic variance.
2. **Elevated Baseline Engagement Rate**: The average engagement rate of **18.54%** across 50,000 posts is significantly higher than industry beauty-brand benchmarks on Instagram (typically 1%–3%). All metrics must be interpreted as **relative performance within this dataset**, rather than external industry benchmarks.
3. **Cumulative Reach vs. Unique Reach**: Reach in this dataset represents the sum of per-post reach, not deduplicated reach across unique accounts over time.
4. **Absence of Textual Data**: The dataset contains no caption text, comment sentiment, visual media content, or audience demographic breakdown.
5. **Static Follower Count**: Follows are recorded per post rather than as a continuous account-level follower growth time series.
