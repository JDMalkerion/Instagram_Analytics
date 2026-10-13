import pandas as pd
import numpy as np
from data_loader import load_data, filter_data
from metrics import (
    get_kpi_summary,
    get_monthly_posts,
    get_top_posts_by_likes,
    get_top_posts_by_engagement_rate
)

print("=" * 80)
print("VERIFICATION: METRICS MODULE CROSS-CHECK & TESTS")
print("=" * 80)

# Load via data_loader
df = load_data()

# Independent raw read for strict cross-checking (do NOT use data_loader)
raw_df = pd.read_excel("Data/sugar_cosmetics_instagram_data.xlsx", sheet_name=0)

# 1. Independent raw recalculation of KPIs
print("\n--- 1. INDEPENDENT RAW CROSS-CHECK OF KPIS ---")
raw_total_likes = int(raw_df['Likes'].sum())
raw_total_comments = int(raw_df['Comments'].sum())
raw_total_reach = int(raw_df['Reach'].sum())
raw_total_engagement = raw_df['Likes'] + raw_df['Comments'] + raw_df['Shares'] + raw_df['Saves']
raw_engagement_rate = raw_total_engagement / raw_df['Reach']
raw_avg_er = float(raw_engagement_rate.mean())
raw_total_posts = len(raw_df)

kpi = get_kpi_summary(df)
print(f"Calculated KPIs: {kpi}")
print(f"Independent Raw: total_posts={raw_total_posts}, total_likes={raw_total_likes}, "
      f"total_comments={raw_total_comments}, total_reach={raw_total_reach}, "
      f"avg_engagement_rate={raw_avg_er:.6f}")

assert kpi['total_posts'] == 50000, f"Expected 50000 posts, got {kpi['total_posts']}"
assert kpi['total_posts'] == raw_total_posts, "Total posts mismatch!"
assert kpi['total_likes'] == raw_total_likes, f"Total likes mismatch: {kpi['total_likes']} vs {raw_total_likes}"
assert kpi['total_comments'] == raw_total_comments, f"Total comments mismatch: {kpi['total_comments']} vs {raw_total_comments}"
assert kpi['total_reach'] == raw_total_reach, f"Total reach mismatch: {kpi['total_reach']} vs {raw_total_reach}"
assert np.isclose(kpi['avg_engagement_rate'], raw_avg_er, atol=1e-9), f"Avg ER mismatch: {kpi['avg_engagement_rate']} vs {raw_avg_er}"
print("✓ KPI cross-check passed: All totals and mean engagement rate match independent raw calculation exactly.")

# 2. get_monthly_posts test & full table
print("\n--- 2. GET_MONTHLY_POSTS TABLE & POSTS SUM ---")
monthly_df = get_monthly_posts(df)
print(f"{'Month':<12} | {'Label':<10} | {'Posts':>6} | {'Partial?':<8} | {'Posts/Day':>10}")
print("-" * 58)
for _, r in monthly_df.iterrows():
    m_str = f"{r['month']:%Y-%m-%d}"
    print(f"{m_str:<12} | {r['month_label']:<10} | {r['posts']:>6} | {str(r['is_partial_month']):<8} | {r['posts_per_day']:>10.2f}")

total_monthly_posts = monthly_df['posts'].sum()
print(f"\nTotal posts across all months: {total_monthly_posts}")
assert total_monthly_posts == 50000, f"Expected monthly sum 50000, got {total_monthly_posts}"
print("✓ get_monthly_posts check passed: Posts sum to 50,000 across all 13 months.")

# 3. Top 10 by likes
print("\n--- 3. TOP 10 POSTS BY LIKES ---")
top_likes = get_top_posts_by_likes(df, n=10)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
print(top_likes.to_string(index=False))

assert top_likes.iloc[0]['likes'] == 11392, f"Expected top likes 11392, got {top_likes.iloc[0]['likes']}"
assert top_likes['likes'].is_monotonic_decreasing, "Top 10 by likes is not sorted descending!"
print("✓ Top 10 by likes check passed: Top row likes == 11392 and sorted descending.")

# 4. Top 10 by engagement rate
print("\n--- 4. TOP 10 POSTS BY ENGAGEMENT RATE ---")
top_er = get_top_posts_by_engagement_rate(df, n=10)
print(top_er.to_string(index=False))

top_er_val = top_er.iloc[0]['engagement_rate']
assert np.isclose(top_er_val, 0.340991, atol=1e-5), f"Expected top ER ~0.340991, got {top_er_val:.6f}"
assert top_er['engagement_rate'].is_monotonic_decreasing, "Top 10 by engagement rate is not sorted descending!"
print(f"✓ Top 10 by engagement rate check passed: Top row ER == {top_er_val:.6f} and sorted descending.")

# 5. Hidden-gem check
print("\n--- 5. HIDDEN-GEM CHECK ---")
overlap_count = len(set(top_er['post_id']).intersection(set(top_likes['post_id'])))
median_er_reach = top_er['reach'].median()
median_all_reach = df['reach'].median()

print(f"Number of top-10 ER posts that ALSO appear in top-10 by likes: {overlap_count} / 10")
print(f"Median reach of top-10 ER posts: {median_er_reach:.1f}")
print(f"Median reach of all posts:       {median_all_reach:.1f}")
print(f"Ratio (Top 10 ER median reach / All posts median reach): {median_er_reach / median_all_reach:.2f}x")
print("\nLikes rank of each top-10 ER post:")
for _, r in top_er.iterrows():
    print(f"  Post ID #{r['post_id']:<5} | ER: {r['engagement_rate']*100:>5.2f}% | Reach: {r['reach']:>5} | Likes: {r['likes']:>5} | Likes Rank: #{r['likes_rank']:>5} out of {len(df)}")

# 6. Weekday spot check
print("\n--- 6. WEEKDAY SPOT CHECK ---")
post_1 = df.loc[df['post_id'] == 1].iloc[0]
post_2 = df.loc[df['post_id'] == 2].iloc[0]
post_3 = df.loc[df['post_id'] == 3].iloc[0]

print(f"Post ID 1: {post_1['post_date']:%Y-%m-%d} -> {post_1['weekday']}")
print(f"Post ID 2: {post_2['post_date']:%Y-%m-%d} -> {post_2['weekday']}")
print(f"Post ID 3: {post_3['post_date']:%Y-%m-%d} -> {post_3['weekday']}")

assert str(post_1['weekday']) == "Monday", f"Expected post 1 to be Monday, got {post_1['weekday']}"
assert str(post_2['weekday']) == "Saturday", f"Expected post 2 to be Saturday, got {post_2['weekday']}"
assert str(post_3['weekday']) == "Sunday", f"Expected post 3 to be Sunday, got {post_3['weekday']}"
print("✓ Weekday spot check passed.")

# 7. Empty-DataFrame test
print("\n--- 7. EMPTY-DATAFRAME ROBUSTNESS TEST ---")
empty_df = filter_data(df, post_types=["NonExistentType"])
assert len(empty_df) == 0, "empty_df is not empty!"

empty_kpi = get_kpi_summary(empty_df)
empty_monthly = get_monthly_posts(empty_df)
empty_top_likes = get_top_posts_by_likes(empty_df)
empty_top_er = get_top_posts_by_engagement_rate(empty_df)

print(f"get_kpi_summary(empty_df):              {empty_kpi}")
print(f"get_monthly_posts(empty_df) shape:        {empty_monthly.shape}")
print(f"get_top_posts_by_likes(empty_df) shape:   {empty_top_likes.shape}")
print(f"get_top_posts_by_er(empty_df) shape:      {empty_top_er.shape}")

assert empty_kpi['total_posts'] == 0
assert empty_kpi['total_likes'] == 0
assert empty_kpi['total_comments'] == 0
assert empty_kpi['total_reach'] == 0
assert empty_kpi['avg_engagement_rate'] is None
assert len(empty_monthly) == 0
assert list(empty_monthly.columns) == ['month', 'month_label', 'posts', 'is_partial_month', 'posts_per_day']
assert len(empty_top_likes) == 0
assert list(empty_top_likes.columns) == ['post_id', 'post_label', 'post_type', 'campaign_type', 'likes', 'reach', 'engagement_rate']
assert len(empty_top_er) == 0
assert list(empty_top_er.columns) == ['post_id', 'post_label', 'post_type', 'campaign_type', 'likes', 'reach', 'engagement_rate', 'likes_rank']
print("✓ Empty-DataFrame test passed: All 4 functions handled empty input gracefully without errors.")

print("\n" + "=" * 80)
print("ALL METRICS VERIFICATION CHECKS PASSED SUCCESSFULLY")
print("=" * 80)
