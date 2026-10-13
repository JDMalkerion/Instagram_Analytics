import pandas as pd
import numpy as np
from streamlit.testing.v1 import AppTest

from data_loader import load_data, filter_data
from metrics import (
    get_monthly_posts,
    get_post_type_performance,
    get_weekday_performance,
    get_engagement_funnel,
    get_growth_funnel,
    get_hashtag_performance,
    get_campaign_performance,
    get_top_posts_by_likes,
    get_top_posts_by_engagement_rate
)
from charts import (
    fig_monthly_trend,
    fig_top_posts,
    fig_post_type_actions,
    fig_avg_engagement_rate_by_group,
    fig_weekday_performance,
    fig_hashtag_usage,
    fig_campaign_follows,
    fig_engagement_funnel,
    fig_actions_per_100_reach,
    fig_growth_funnel
)

print("=" * 80)
print("VERIFICATION: APP.PY & CHARTS.PY COMPREHENSIVE TESTS")
print("=" * 80)

# Load raw Excel data independently
print("\nLoading raw Excel data independently for ground-truth cross-checks...")
raw_df = pd.read_excel("Data/sugar_cosmetics_instagram_data.xlsx", sheet_name=0)
raw_post_date = pd.to_datetime(raw_df['Post Date'])
raw_month_label = raw_post_date.dt.strftime('%b %Y')
raw_tags_list = raw_df['Hashtags'].astype(str).str.split(', ')

expected_default_count = len(raw_df)
expected_reels_count = len(raw_df[raw_df['Post Type'] == 'Reel'])
expected_may_count = len(raw_df[raw_month_label == 'May 2024'])
expected_vegan_count = sum(1 for tags in raw_tags_list if '#VeganBeauty' in tags)

combined_mask = (
    (raw_df['Post Type'] == 'Reel') &
    (raw_month_label == 'May 2024') &
    (raw_df['Campaign Type'] == 'Giveaway')
)
expected_combined_count = len(raw_df[combined_mask])


def assert_no_exceptions(at, test_name):
    if len(at.exception) > 0:
        err_msgs = [e.message for e in at.exception]
        raise AssertionError(f"[{test_name}] Encountered exceptions: {err_msgs}")


# --- PART 1: STREAMLIT APPTEST TESTS ---
print("\n--- PART 1: STREAMLIT APPTEST INTERACTIVE TESTS ---")

# Test 1: Default run
print("\n[Test 1: Default run]")
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
assert_no_exceptions(at, "Test 1: Default run")
default_posts_str = at.metric[0].value
print(f"  Expected: {expected_default_count:,} | Actual: {default_posts_str}")
assert default_posts_str == "50,000"
print("  ✓ Total posts metric correctly shows 50,000.")

# Test 2: flt_post_type = ["Reel"]
print("\n[Test 2: Reel filter]")
at.multiselect(key="flt_post_type").set_value(["Reel"]).run()
assert_no_exceptions(at, "Test 2: Reel filter")
reels_posts_str = at.metric[0].value
print(f"  Expected: {expected_reels_count:,} | Actual: {reels_posts_str}")
assert int(reels_posts_str.replace(",", "")) == expected_reels_count
print("  ✓ Reel filter correctly returns 12,599 posts.")

# Check for "Select at least two" caption in Reel-only run
captions_text = [c.value for c in at.caption]
has_select_two = any("Select at least two" in txt for txt in captions_text)
assert has_select_two, "Expected caption containing 'Select at least two' when 1 post type is selected!"
print("  ✓ 'Select at least two' caption verified when post type has only 1 option.")

# Test 3: flt_months = ("May 2024", "May 2024")
print("\n[Test 3: May 2024 filter]")
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
at.select_slider(key="flt_months").set_value(("May 2024", "May 2024")).run()
assert_no_exceptions(at, "Test 3: May 2024 filter")
may_posts_str = at.metric[0].value
print(f"  Expected: {expected_may_count:,} | Actual: {may_posts_str}")
assert int(may_posts_str.replace(",", "")) == expected_may_count
print("  ✓ May 2024 filter correctly returns 4,250 posts.")

# Test 4: flt_hashtags = ["#VeganBeauty"]
print("\n[Test 4: #VeganBeauty filter]")
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
at.multiselect(key="flt_hashtags").set_value(["#VeganBeauty"]).run()
assert_no_exceptions(at, "Test 4: #VeganBeauty filter")
vegan_posts_str = at.metric[0].value
print(f"  Expected: {expected_vegan_count:,} | Actual: {vegan_posts_str}")
assert int(vegan_posts_str.replace(",", "")) == expected_vegan_count
print("  ✓ #VeganBeauty filter correctly returns 19,982 posts.")

# Test 5: Combined filter
print("\n[Test 5: Combined filters]")
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
at.multiselect(key="flt_post_type").set_value(["Reel"])
at.select_slider(key="flt_months").set_value(("May 2024", "May 2024"))
at.multiselect(key="flt_campaign").set_value(["Giveaway"]).run()
assert_no_exceptions(at, "Test 5: Combined filter")
comb_posts_str = at.metric[0].value
print(f"  Expected: {expected_combined_count:,} | Actual: {comb_posts_str}")
assert int(comb_posts_str.replace(",", "")) == expected_combined_count
print("  ✓ Combined filter correctly returns 198 posts.")

# Test 6: Empty filter warning
print("\n[Test 6: Empty post_type filter]")
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
at.multiselect(key="flt_post_type").set_value([]).run()
assert_no_exceptions(at, "Test 6: Empty filter")
assert len(at.warning) > 0
print(f"  Warning displayed: '{at.warning[0].value}'")
assert "No posts match the current filters." in at.warning[0].value
print("  ✓ Empty filter warning confirmed.")

# Test 7: Sequential multi-filter stability test (Default -> Reel -> Jan 2025..Mar 2025)
print("\n[Test 7: Sequential filter transitions test]")
at_seq = AppTest.from_file("app.py", default_timeout=60)
at_seq.run()
assert_no_exceptions(at_seq, "Seq 1: Default")
at_seq.multiselect(key="flt_post_type").set_value(["Reel"]).run()
assert_no_exceptions(at_seq, "Seq 2: Reel only")
at_seq.select_slider(key="flt_months").set_value(("Jan 2025", "Mar 2025")).run()
assert_no_exceptions(at_seq, "Seq 3: Jan-Mar 2025")
print(f"  Sequential run posts selected: {at_seq.metric[0].value}")
print("  ✓ Sequence of transitions completed cleanly without any exceptions.")


# --- PART 2: DIRECT FIGURE-BUILDER CHECKS (NO STREAMLIT) ---
print("\n--- PART 2: DIRECT CHARTS.PY FIGURE-BUILDER INTEGRITY CHECKS ---")
df = load_data()

# 1. Post type facet values equal get_post_type_performance values
pt_df = get_post_type_performance(df)
fig_facets = fig_post_type_actions(pt_df)
print("\n[Check: Post-type facet values]")
assert list(fig_facets.data[0].y) == list(pt_df['avg_likes']), "Facet avg_likes mismatch"
assert list(fig_facets.data[1].y) == list(pt_df['avg_comments']), "Facet avg_comments mismatch"
assert list(fig_facets.data[2].y) == list(pt_df['avg_shares']), "Facet avg_shares mismatch"
assert list(fig_facets.data[3].y) == list(pt_df['avg_saves']), "Facet avg_saves mismatch"
print("  ✓ All 4 facet panel y-values match get_post_type_performance exactly.")

# 2. Funnel counts equal raw sums of impressions, reach, likes, comments, shares, saves
print("\n[Check: Engagement funnel raw counts]")
eng_funnel_df = get_engagement_funnel(df)
fig_funnel = fig_engagement_funnel(eng_funnel_df)
raw_funnel_sums = [
    int(raw_df['Impressions'].sum()),
    int(raw_df['Reach'].sum()),
    int(raw_df['Likes'].sum()),
    int(raw_df['Comments'].sum()),
    int(raw_df['Shares'].sum()),
    int(raw_df['Saves'].sum())
]
assert list(fig_funnel.data[0].x) == raw_funnel_sums, "Funnel counts mismatch raw Excel sums"
print(f"  Funnel counts in figure: {fig_funnel.data[0].x}")
print("  ✓ Engagement funnel counts match raw sums exactly.")

# 3. Weekday figure categories are in Monday..Sunday order
print("\n[Check: Weekday figure category order]")
wk_df = get_weekday_performance(df)
fig_wk = fig_weekday_performance(wk_df, metric="avg_engagement_rate")
expected_days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
assert list(fig_wk.data[0].x) == expected_days, f"Weekday order mismatch: {list(fig_wk.data[0].x)}"
print(f"  Weekday categories in figure: {list(fig_wk.data[0].x)}")
print("  ✓ Weekday figure strictly follows Monday..Sunday order.")

# 4. Every bar figure's value axis range starts at 0
print("\n[Check: Value axis range starts at 0 across all bar charts]")

def check_value_axis_zero(fig, name, orientation='v'):
    if orientation == 'v':
        rangemode = getattr(fig.layout.yaxis, 'rangemode', None)
        rng = getattr(fig.layout.yaxis, 'range', None)
        assert rangemode == 'tozero' or (rng and rng[0] == 0), f"[{name}] Y-axis does not start at 0"
    elif orientation == 'h':
        rangemode = getattr(fig.layout.xaxis, 'rangemode', None)
        rng = getattr(fig.layout.xaxis, 'range', None)
        assert rangemode == 'tozero' or (rng and rng[0] == 0), f"[{name}] X-axis does not start at 0"
    elif orientation == 'facets':
        for key in fig.layout:
            if key.startswith('yaxis'):
                axis = getattr(fig.layout, key)
                assert getattr(axis, 'rangemode', None) == 'tozero', f"[{name}] {key} does not have rangemode='tozero'"

check_value_axis_zero(fig_top_posts(get_top_posts_by_likes(df, 10), 'likes', 'Likes'), "fig_top_posts (likes)", 'h')
check_value_axis_zero(fig_top_posts(get_top_posts_by_engagement_rate(df, 10), 'engagement_rate', 'ER', percent=True), "fig_top_posts (er)", 'h')
check_value_axis_zero(fig_post_type_actions(pt_df), "fig_post_type_actions", 'facets')
check_value_axis_zero(fig_avg_engagement_rate_by_group(pt_df, "post_type"), "fig_avg_engagement_rate_by_group (post_type)", 'v')
check_value_axis_zero(fig_weekday_performance(wk_df, "avg_engagement_rate"), "fig_weekday_performance (er)", 'v')
check_value_axis_zero(fig_weekday_performance(wk_df, "avg_total_engagement"), "fig_weekday_performance (tot)", 'v')
check_value_axis_zero(fig_hashtag_usage(get_hashtag_performance(df)), "fig_hashtag_usage", 'v')
check_value_axis_zero(fig_campaign_follows(get_campaign_performance(df)), "fig_campaign_follows", 'v')
check_value_axis_zero(fig_actions_per_100_reach(eng_funnel_df), "fig_actions_per_100_reach", 'h')

print("  ✓ Confirmed: All 9 bar charts start their value axis strictly at 0.")


# --- PART 3: REEL APR 2024 BOUNDS NORMALIZATION CHECK ---
print("\n--- PART 3: PARTIAL MONTH NORMALIZATION FOR REEL SUBSET ---")
full_bounds = (df['post_date'].min(), df['post_date'].max())
reels_df = df[df['post_type'] == 'Reel']
reels_monthly = get_monthly_posts(reels_df, bounds=full_bounds)
apr_row = reels_monthly[reels_monthly['month_label'] == 'Apr 2024'].iloc[0]

raw_reel_apr_posts = len(raw_df[(raw_df['Post Type'] == 'Reel') & (raw_month_label == 'Apr 2024')])
expected_reels_ppd = raw_reel_apr_posts / 12.0

print(f"  Reel posts in Apr 2024: {apr_row['posts']} (raw count: {raw_reel_apr_posts})")
print(f"  Actual posts_per_day:   {apr_row['posts_per_day']:.4f}")
print(f"  Expected (count / 12):  {expected_reels_ppd:.4f}")
assert np.isclose(apr_row['posts_per_day'], expected_reels_ppd, atol=1e-9)
print("  ✓ posts_per_day equals Reel posts in Apr 2024 divided by 12 exactly.")

print("\n" + "=" * 80)
print("ALL EXTENDED VERIFICATION CHECKS PASSED SUCCESSFULLY")
print("=" * 80)
