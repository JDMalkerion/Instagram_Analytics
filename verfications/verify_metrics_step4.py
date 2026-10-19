import pandas as pd
import numpy as np
from data_loader import load_data, filter_data, WEEKDAY_ORDER
from metrics import (
    _ci95,
    get_post_type_performance,
    get_weekday_performance,
    get_engagement_funnel,
    get_growth_funnel,
    get_hashtag_performance,
    get_campaign_performance
)

print("=" * 80)
print("VERIFICATION: STEP 4 METRICS CROSS-CHECK & STATISTICAL TESTS")
print("=" * 80)

# 1. Load via data_loader and load raw Excel directly
df = load_data()
raw_df = pd.read_excel("Data/sugar_cosmetics_instagram_data.xlsx", sheet_name=0)

# Build independent raw calculated series
raw_total_eng = raw_df['Likes'] + raw_df['Comments'] + raw_df['Shares'] + raw_df['Saves']
raw_er = raw_total_eng / raw_df['Reach']
raw_post_date = pd.to_datetime(raw_df['Post Date'])
raw_weekday = raw_post_date.dt.day_name()

def check_overlap(grouped_df, name):
    """
    Evaluates spread and statistical separation between top and bottom groups.
    """
    top_row = grouped_df.iloc[0]
    bottom_row = grouped_df.iloc[-1]
    spread_pp = (top_row['avg_engagement_rate'] - bottom_row['avg_engagement_rate']) * 100
    top_lower = top_row['avg_engagement_rate'] - top_row['er_ci95']
    bottom_upper = bottom_row['avg_engagement_rate'] + bottom_row['er_ci95']
    is_separated = top_lower > bottom_upper
    status = "SEPARATED" if is_separated else "OVERLAP"
    
    print(f"\n[{name} Statistical Significance Analysis]")
    print(f"  Spread of avg_engagement_rate (Max - Min): {spread_pp:.4f} percentage points")
    print(f"  Top group ({top_row.iloc[0]}): mean={top_row['avg_engagement_rate']*100:.3f}% ± {top_row['er_ci95']*100:.3f}% -> CI [{top_lower*100:.3f}%, {(top_row['avg_engagement_rate']+top_row['er_ci95'])*100:.3f}%]")
    print(f"  Bottom group ({bottom_row.iloc[0]}): mean={bottom_row['avg_engagement_rate']*100:.3f}% ± {bottom_row['er_ci95']*100:.3f}% -> CI [{(bottom_row['avg_engagement_rate']-bottom_row['er_ci95'])*100:.3f}%, {bottom_upper*100:.3f}%]")
    print(f"  Result: {status}")
    return spread_pp, status

# 2. Post-Type Performance
print("\n--- 1. POST TYPE PERFORMANCE ---")
pt_perf = get_post_type_performance(df)
print(pt_perf.to_string(index=False))

# Raw independent cross-check
raw_pt_df = raw_df.assign(er=raw_er)
for _, r in pt_perf.iterrows():
    pt = r['post_type']
    sub = raw_pt_df[raw_pt_df['Post Type'] == pt]
    assert r['posts'] == len(sub)
    assert np.isclose(r['avg_likes'], sub['Likes'].mean(), atol=1e-9)
    assert np.isclose(r['avg_comments'], sub['Comments'].mean(), atol=1e-9)
    assert np.isclose(r['avg_shares'], sub['Shares'].mean(), atol=1e-9)
    assert np.isclose(r['avg_saves'], sub['Saves'].mean(), atol=1e-9)
    assert np.isclose(r['avg_reach'], sub['Reach'].mean(), atol=1e-9)
    assert np.isclose(r['avg_engagement_rate'], sub['er'].mean(), atol=1e-9)
    assert np.isclose(r['er_ci95'], _ci95(sub['er']), atol=1e-9)
print("✓ Post-type independent cross-check passed with 1e-9 tolerance.")
check_overlap(pt_perf, "Post Type")

# 3. Weekday Performance
print("\n--- 2. WEEKDAY PERFORMANCE ---")
wk_perf = get_weekday_performance(df)
print(wk_perf.to_string(index=False))

# Raw independent cross-check
raw_wk_df = raw_df.assign(weekday=raw_weekday, er=raw_er, tot_eng=raw_total_eng)
for _, r in wk_perf.iterrows():
    day = r['weekday']
    sub = raw_wk_df[raw_wk_df['weekday'] == day]
    assert r['posts'] == len(sub)
    assert np.isclose(r['avg_total_engagement'], sub['tot_eng'].mean(), atol=1e-9)
    assert np.isclose(r['avg_engagement_rate'], sub['er'].mean(), atol=1e-9)
    assert np.isclose(r['er_ci95'], _ci95(sub['er']), atol=1e-9)
print("✓ Weekday independent cross-check passed with 1e-9 tolerance.")
wk_sorted = wk_perf.sort_values('avg_engagement_rate', ascending=False)
check_overlap(wk_sorted, "Weekday")

# 4. Engagement Funnel
print("\n--- 3. ENGAGEMENT FUNNEL ---")
eng_funnel = get_engagement_funnel(df)
print(eng_funnel.to_string(index=False))

# Raw cross-check
raw_imp = raw_df['Impressions'].sum()
raw_reach = raw_df['Reach'].sum()
raw_likes = raw_df['Likes'].sum()
raw_comments = raw_df['Comments'].sum()
raw_shares = raw_df['Shares'].sum()
raw_saves = raw_df['Saves'].sum()

expected_eng_counts = {
    'Impressions': raw_imp,
    'Reach': raw_reach,
    'Likes': raw_likes,
    'Comments': raw_comments,
    'Shares': raw_shares,
    'Saves': raw_saves
}
for _, r in eng_funnel.iterrows():
    stage = r['stage']
    assert r['count'] == expected_eng_counts[stage], f"Mismatch in {stage} count"
print("✓ Engagement funnel totals match raw Excel sums exactly.")

# 5. Growth Funnel
print("\n--- 4. GROWTH FUNNEL ---")
growth_funnel = get_growth_funnel(df)
print(growth_funnel.to_string(index=False))

raw_pv = raw_df['Profile Visits'].sum()
raw_follows = raw_df['Follows'].sum()
expected_growth_counts = {
    'Reach': raw_reach,
    'Profile Visits': raw_pv,
    'Follows': raw_follows
}
for _, r in growth_funnel.iterrows():
    stage = r['stage']
    assert r['count'] == expected_growth_counts[stage], f"Mismatch in {stage} growth count"
print("✓ Growth funnel totals match raw Excel sums exactly.")

# 6. Hashtag Performance
print("\n--- 5. HASHTAG PERFORMANCE ---")
ht_perf = get_hashtag_performance(df)
print(ht_perf.to_string(index=False))

# Raw independent cross-check using raw string split on ', '
raw_ht_exploded = raw_df.assign(
    hashtag=raw_df['Hashtags'].astype(str).str.split(', '),
    er=raw_er
).explode('hashtag')

expected_ht_counts = {
    '#CrueltyFree': 20197,
    '#MakeupGoals': 20018,
    '#VeganBeauty': 19982,
    '#BoldLooks': 19956,
    '#SugarCosmetics': 19891
}

for tag, exp_cnt in expected_ht_counts.items():
    row = ht_perf[ht_perf['hashtag'] == tag].iloc[0]
    assert row['posts'] == exp_cnt, f"Expected {exp_cnt} for {tag}, got {row['posts']}"
    raw_sub = raw_ht_exploded[raw_ht_exploded['hashtag'] == tag]
    assert len(raw_sub) == exp_cnt
    assert np.isclose(row['avg_engagement_rate'], raw_sub['er'].mean(), atol=1e-9)
    assert np.isclose(row['er_ci95'], _ci95(raw_sub['er']), atol=1e-9)
    assert np.isclose(row['avg_reach'], raw_sub['Reach'].mean(), atol=1e-9)
    assert np.isclose(row['avg_likes'], raw_sub['Likes'].mean(), atol=1e-9)
print("✓ Hashtag independent cross-check passed with exact expected counts and 1e-9 tolerance.")
check_overlap(ht_perf, "Hashtag")

# 7. Campaign Performance
print("\n--- 6. CAMPAIGN PERFORMANCE ---")
camp_perf = get_campaign_performance(df)
print(camp_perf.to_string(index=False))

raw_camp_df = raw_df.assign(er=raw_er)
for _, r in camp_perf.iterrows():
    ct = r['campaign_type']
    sub = raw_camp_df[raw_camp_df['Campaign Type'] == ct]
    assert r['posts'] == len(sub)
    assert np.isclose(r['avg_engagement_rate'], sub['er'].mean(), atol=1e-9)
    assert np.isclose(r['er_ci95'], _ci95(sub['er']), atol=1e-9)
    assert np.isclose(r['avg_reach'], sub['Reach'].mean(), atol=1e-9)
    assert np.isclose(r['avg_likes'], sub['Likes'].mean(), atol=1e-9)
    assert np.isclose(r['avg_follows'], sub['Follows'].mean(), atol=1e-9)
print("✓ Campaign independent cross-check passed with 1e-9 tolerance.")
check_overlap(camp_perf, "Campaign")

# 8. Empty-DataFrame test for all six functions
print("\n--- 7. EMPTY-DATAFRAME ROBUSTNESS TEST ---")
empty_df = filter_data(df, post_types=["DoesNotExist"])
assert len(empty_df) == 0

e_pt = get_post_type_performance(empty_df)
e_wk = get_weekday_performance(empty_df)
e_ef = get_engagement_funnel(empty_df)
e_gf = get_growth_funnel(empty_df)
e_ht = get_hashtag_performance(empty_df)
e_cp = get_campaign_performance(empty_df)

assert len(e_pt) == 0 and len(e_pt.columns) == 9
assert len(e_wk) == 0 and len(e_wk.columns) == 5
assert len(e_ef) == 0 and len(e_ef.columns) == 5
assert len(e_gf) == 0 and len(e_gf.columns) == 4
assert len(e_ht) == 0 and len(e_ht.columns) == 6
assert len(e_cp) == 0 and len(e_cp.columns) == 7

print("✓ All 6 new functions handled empty input DataFrame gracefully without crashing.")

print("\n" + "=" * 80)
print("ALL STEP 4 VERIFICATION CHECKS PASSED SUCCESSFULLY")
print("=" * 80)
