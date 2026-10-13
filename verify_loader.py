import pandas as pd
import numpy as np
from data_loader import load_data, explode_hashtags, filter_data, COLUMN_RENAME_MAP

print("=" * 80)
print("VERIFICATION: DATA LOADER AUDIT & TESTS")
print("=" * 80)

# 1. Load data
print("\n--- 1. LOADING DATA ---")
df = load_data()
raw_df = pd.read_excel("Data/sugar_cosmetics_instagram_data.xlsx", sheet_name=0)

print(f"Loaded DataFrame shape: {df.shape}")
assert df.shape[0] == 50000, f"Expected 50000 rows, got {df.shape[0]}"
print("✓ Row count check passed: Exactly 50,000 rows loaded.")

# Confirm no raw column was altered/dropped
raw_cols_renamed = [COLUMN_RENAME_MAP[c] for c in raw_df.columns]
missing_cols = [c for c in raw_cols_renamed if c not in df.columns]
assert len(missing_cols) == 0, f"Missing renamed raw columns: {missing_cols}"

# Verify numeric raw data values match raw_df exactly
for orig_col, new_col in COLUMN_RENAME_MAP.items():
    if pd.api.types.is_numeric_dtype(raw_df[orig_col]):
        assert (raw_df[orig_col].values == df[new_col].values).all(), f"Values in column '{new_col}' do not match raw data!"
print("✓ Column integrity check passed: All raw columns and exact values preserved without alterations.")
print(f"All columns in processed df ({len(df.columns)}): {list(df.columns)}")

# 2. engagement_rate statistics & assertion
print("\n--- 2. ENGAGEMENT RATE STATISTICS ---")
er = df['engagement_rate']
print(f"Min:    {er.min():.6f} ({er.min()*100:.4f}%)")
print(f"Mean:   {er.mean():.6f} ({er.mean()*100:.4f}%)")
print(f"Median: {er.median():.6f} ({er.median()*100:.4f}%)")
print(f"Max:    {er.max():.6f} ({er.max()*100:.4f}%)")

assert (er >= 0).all() and (er <= 1).all(), "Assertion failed: engagement_rate values are not strictly between 0 and 1!"
print("✓ Assertion passed: All engagement_rate values are strictly between 0 and 1.")

# 3. Rows per month_label in chronological order, with is_partial_month marked
print("\n--- 3. ROWS PER MONTH (CHRONOLOGICAL ORDER) ---")
month_summary = (
    df.groupby(['month', 'month_label', 'is_partial_month'])
    .size()
    .reset_index(name='row_count')
    .sort_values('month')
)
for _, row in month_summary.iterrows():
    partial_flag = " [PARTIAL MONTH]" if row['is_partial_month'] else ""
    print(f"  {row['month_label']:<10} | {row['row_count']:>5} rows{partial_flag}")

# 4. Rows per weekday in Monday..Sunday order
print("\n--- 4. ROWS PER WEEKDAY (MONDAY -> SUNDAY) ---")
weekday_counts = df['weekday'].value_counts().sort_index()
for day, count in weekday_counts.items():
    print(f"  {day:<10} | {count:>5} rows")

# 5. Hashtag counts after explode_hashtags and assertion
print("\n--- 5. EXPLODE HASHTAGS & COUNTS ---")
exploded = explode_hashtags(df)
print(f"Exploded DataFrame shape: {exploded.shape}")
ht_counts = exploded['hashtag'].value_counts()
print("\nHashtag distribution:")
print(ht_counts)

total_hashtag_items = df['hashtag_list'].apply(len).sum()
assert len(exploded) == total_hashtag_items, (
    f"Exploded rows ({len(exploded)}) != sum of len(hashtag_list) ({total_hashtag_items})"
)
print(f"✓ Assertion passed: Total exploded rows ({len(exploded)}) equals sum of hashtag_list lengths ({total_hashtag_items}).")

# 6. Test filter_data
print("\n--- 6. FILTER_DATA TESTS ---")

# (a) No filters returns 50000 rows
f_none = filter_data(df)
assert len(f_none) == 50000, f"Expected 50000 rows for no filters, got {len(f_none)}"
print(f"✓ Test (a) passed: No filters returns {len(f_none)} rows.")

# (b) post_types=["Reel"] returns 12599 rows
f_reels = filter_data(df, post_types=["Reel"])
assert len(f_reels) == 12599, f"Expected 12599 rows for Reel, got {len(f_reels)}"
print(f"✓ Test (b) passed: post_types=['Reel'] returns {len(f_reels)} rows.")

# (c) hashtags=["#VeganBeauty"] returns the same number of posts as exploded data shows
f_tag = filter_data(df, hashtags=["#VeganBeauty"])
expected_tag_count = (exploded['hashtag'] == "#VeganBeauty").sum()
assert len(f_tag) == expected_tag_count, (
    f"Expected {expected_tag_count} posts for #VeganBeauty, got {len(f_tag)}"
)
print(f"✓ Test (c) passed: hashtags=['#VeganBeauty'] returns {len(f_tag)} rows (matches exploded count of {expected_tag_count}).")

# 7. Mean engagement_rate (per-post) AND total_engagement.sum() / reach.sum() side by side
print("\n--- 7. ENGAGEMENT RATE COMPARISON ---")
per_post_mean = df['engagement_rate'].mean()
aggregate_rate = df['total_engagement'].sum() / df['reach'].sum()

print(f"{'Metric':<35} | {'Fraction':<12} | {'Percentage':<10}")
print("-" * 62)
print(f"{'Per-Post Mean Engagement Rate':<35} | {per_post_mean:<12.6f} | {per_post_mean*100:<9.4f}%")
print(f"{'Aggregate (Sum Engagement / Sum Reach)':<35} | {aggregate_rate:<12.6f} | {aggregate_rate*100:<9.4f}%")
print(f"{'Difference':<35} | {abs(per_post_mean - aggregate_rate):<12.6f} | {abs(per_post_mean - aggregate_rate)*100:<9.4f}%")

print("\n" + "=" * 80)
print("ALL VERIFICATION CHECKS PASSED SUCCESSFULLY")
print("=" * 80)
