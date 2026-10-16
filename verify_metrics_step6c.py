import pandas as pd
import numpy as np
from scipy import stats

from data_loader import load_data
from metrics import (
    get_monthly_growth,
    get_audience_emotion_performance,
    get_engagement_source_performance,
    get_group_significance
)

print("=" * 80)
print("VERIFICATION: STEP 6C METRICS, RAW EXCEL RECOMPUTE & GROUP SIGNIFICANCE")
print("=" * 80)

# 1. Raw-Excel recompute
print("\n--- 1. RAW EXCEL RECOMPUTE & SUM ASSERTS ---")
raw_df = pd.read_excel("Data/sugar_cosmetics_instagram_data.xlsx", sheet_name=0)
raw_post_date = pd.to_datetime(raw_df['Post Date'])
raw_month = raw_post_date.dt.to_period('M').dt.to_timestamp()

raw_follows_sum = int(raw_df['Follows'].sum())
raw_profile_visits_sum = int(raw_df['Profile Visits'].sum())
raw_reach_sum = int(raw_df['Reach'].sum())

print(f"Raw Follows Sum:        {raw_follows_sum:,} (expected 8,866,710)")
print(f"Raw Profile Visits Sum: {raw_profile_visits_sum:,} (expected 29,634,798)")
print(f"Raw Reach Sum:          {raw_reach_sum:,}")

assert raw_follows_sum == 8866710, f"Expected 8,866,710 follows, got {raw_follows_sum}"
assert raw_profile_visits_sum == 29634798, f"Expected 29,634,798 profile visits, got {raw_profile_visits_sum}"
print("✓ Monthly follows and profile visits sums asserted successfully.")

# 2. Print unique values and post counts of Audience Emotion and Engagement Source from raw file
print("\n--- 2. RAW EXCEL UNIQUE VALUES & POST COUNTS ---")
print("Audience Emotion value counts (raw):")
emotion_counts = raw_df['Audience Emotion'].value_counts()
for val, cnt in emotion_counts.items():
    print(f"  {val:12s}: {cnt:,} ({cnt/len(raw_df)*100:.2f}%)")

print("\nEngagement Source value counts (raw):")
source_counts = raw_df['Engagement Source'].value_counts()
for val, cnt in source_counts.items():
    print(f"  {val:12s}: {cnt:,} ({cnt/len(raw_df)*100:.2f}%)")

# 3. Cleaned data & independent groupby cross-checks (1e-9)
print("\n--- 3. INDEPENDENT GROUPBY CROSS-CHECK & SIGNIFICANCE TESTS ---")
df = load_data()

# Check Audience Emotion
ae_perf = get_audience_emotion_performance(df)
indep_ae = df.groupby('audience_emotion').agg(
    posts=('post_id', 'count'),
    avg_engagement_rate=('engagement_rate', 'mean'),
    avg_reach=('reach', 'mean'),
    avg_likes=('likes', 'mean'),
    avg_follows=('follows', 'mean')
).reset_index()

# Compute er_ci95 independently
def calc_ci95(series):
    n = len(series)
    if n < 2:
        return 0.0
    return 1.96 * series.std(ddof=1) / np.sqrt(n)

ci95_map_ae = df.groupby('audience_emotion')['engagement_rate'].apply(calc_ci95).to_dict()
indep_ae['er_ci95'] = indep_ae['audience_emotion'].map(ci95_map_ae)
indep_ae = indep_ae.sort_values(by='avg_engagement_rate', ascending=False).reset_index(drop=True)

for col in ['posts', 'avg_engagement_rate', 'er_ci95', 'avg_reach', 'avg_likes', 'avg_follows']:
    diff = np.abs(ae_perf[col].to_numpy() - indep_ae[col].to_numpy()).max()
    assert diff < 1e-9, f"Audience emotion mismatch in {col}: max diff {diff}"
print("✓ Audience emotion performance table matches independent groupby within 1e-9.")

ae_sig = get_group_significance(df, 'audience_emotion')
print(f"Audience Emotion Significance: ANOVA p = {ae_sig['anova_p']:.4f} (F = {ae_sig['anova_f']:.4f}), "
      f"Kruskal p = {ae_sig['kruskal_p']:.4f}, eta^2 = {ae_sig['eta_squared']:.6f} ({ae_sig['eta_squared']*100:.5f}%), "
      f"significant = {ae_sig['significant']}")

# Check Engagement Source
es_perf = get_engagement_source_performance(df)
indep_es = df.groupby('engagement_source').agg(
    posts=('post_id', 'count'),
    avg_engagement_rate=('engagement_rate', 'mean'),
    avg_reach=('reach', 'mean'),
    avg_likes=('likes', 'mean'),
    avg_follows=('follows', 'mean')
).reset_index()

ci95_map_es = df.groupby('engagement_source')['engagement_rate'].apply(calc_ci95).to_dict()
indep_es['er_ci95'] = indep_es['engagement_source'].map(ci95_map_es)
indep_es = indep_es.sort_values(by='avg_engagement_rate', ascending=False).reset_index(drop=True)

for col in ['posts', 'avg_engagement_rate', 'er_ci95', 'avg_reach', 'avg_likes', 'avg_follows']:
    diff = np.abs(es_perf[col].to_numpy() - indep_es[col].to_numpy()).max()
    assert diff < 1e-9, f"Engagement source mismatch in {col}: max diff {diff}"
print("✓ Engagement source performance table matches independent groupby within 1e-9.")

es_sig = get_group_significance(df, 'engagement_source')
print(f"Engagement Source Significance: ANOVA p = {es_sig['anova_p']:.4f} (F = {es_sig['anova_f']:.4f}), "
      f"Kruskal p = {es_sig['kruskal_p']:.4f}, eta^2 = {es_sig['eta_squared']:.6f} ({es_sig['eta_squared']*100:.5f}%), "
      f"significant = {es_sig['significant']}")

# Print detailed group performance tables
print("\nAudience Emotion Performance Table:")
print(ae_perf.to_string(index=False))

print("\nEngagement Source Performance Table:")
print(es_perf.to_string(index=False))

# 4. Print the full monthly growth table
print("\n--- 4. FULL MONTHLY GROWTH TABLE ---")
monthly_growth = get_monthly_growth(df)
print(monthly_growth.to_string(index=False))

# Verify sum of monthly_growth columns matches raw sums
assert monthly_growth['follows'].sum() == raw_follows_sum
assert monthly_growth['profile_visits'].sum() == raw_profile_visits_sum
assert monthly_growth['reach'].sum() == raw_reach_sum
print("✓ Monthly growth sums match raw totals exactly.")

# Check lowest and highest full-month follows_per_day
full_months = monthly_growth[~monthly_growth['is_partial_month']]
lowest_row = full_months.loc[full_months['follows_per_day'].idxmin()]
highest_row = full_months.loc[full_months['follows_per_day'].idxmax()]
print(f"\nLowest full-month follows/day:  {lowest_row['month_label']} at {lowest_row['follows_per_day']:,.1f} ({lowest_row['follows']:,} follows / {lowest_row['follows']/lowest_row['follows_per_day']:.0f} days)")
print(f"Highest full-month follows/day: {highest_row['month_label']} at {highest_row['follows_per_day']:,.1f} ({highest_row['follows']:,} follows / {highest_row['follows']/highest_row['follows_per_day']:.0f} days)")
print(f"Follow rate range across all months: {monthly_growth['follow_rate'].min()*100:.2f}% to {monthly_growth['follow_rate'].max()*100:.2f}%")
print(f"Profile visit rate range across all months: {monthly_growth['profile_visit_rate'].min()*100:.2f}% to {monthly_growth['profile_visit_rate'].max()*100:.2f}%")

print("\n" + "=" * 80)
print("ALL STEP 6C METRICS VERIFICATION CHECKS PASSED SUCCESSFULLY")
print("=" * 80)
