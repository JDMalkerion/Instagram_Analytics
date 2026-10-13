import pandas as pd
import numpy as np
from streamlit.testing.v1 import AppTest

print("=" * 80)
print("VERIFICATION: APP.PY AUTOMATED TESTS VIA STREAMLIT APPTEST")
print("=" * 80)

# Load raw Excel data independently
print("\nLoading raw Excel data independently for ground-truth cross-checks...")
raw_df = pd.read_excel("Data/sugar_cosmetics_instagram_data.xlsx", sheet_name=0)
raw_post_date = pd.to_datetime(raw_df['Post Date'])
raw_month_label = raw_post_date.dt.strftime('%b %Y')
raw_tags_list = raw_df['Hashtags'].astype(str).str.split(', ')

# Ground truth expected counts
expected_default_count = len(raw_df)
assert expected_default_count == 50000

expected_reels_count = len(raw_df[raw_df['Post Type'] == 'Reel'])
assert expected_reels_count == 12599

expected_may_count = len(raw_df[raw_month_label == 'May 2024'])
assert expected_may_count == 4250

expected_vegan_count = sum(1 for tags in raw_tags_list if '#VeganBeauty' in tags)
assert expected_vegan_count == 19982

combined_mask = (
    (raw_df['Post Type'] == 'Reel') &
    (raw_month_label == 'May 2024') &
    (raw_df['Campaign Type'] == 'Giveaway')
)
expected_combined_count = len(raw_df[combined_mask])

print(f"Ground-truth expected numbers from raw Excel:")
print(f"  - Default: {expected_default_count:,}")
print(f"  - Reel only: {expected_reels_count:,}")
print(f"  - May 2024 only: {expected_may_count:,}")
print(f"  - #VeganBeauty only: {expected_vegan_count:,}")
print(f"  - Combined (Reel + May 2024 + Giveaway): {expected_combined_count:,}")

# Helper to verify clean run
def assert_no_exceptions(at, test_name):
    if len(at.exception) > 0:
        err_msgs = [e.message for e in at.exception]
        raise AssertionError(f"[{test_name}] Encounted exceptions: {err_msgs}")

# Test 1: Default run
print("\n--- TEST 1: DEFAULT RUN ---")
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
assert_no_exceptions(at, "Test 1: Default run")
default_posts_str = at.metric[0].value
default_posts_num = int(default_posts_str.replace(",", ""))
print(f"Expected: {expected_default_count:,} | Actual: {default_posts_str}")
assert default_posts_str == "50,000", f"Expected '50,000', got '{default_posts_str}'"
assert default_posts_num == expected_default_count
print("✓ Test 1 passed: Total posts metric correctly shows 50,000.")

# Test 2: flt_post_type = ["Reel"]
print("\n--- TEST 2: POST_TYPE = ['Reel'] ---")
at.multiselect(key="flt_post_type").set_value(["Reel"]).run()
assert_no_exceptions(at, "Test 2: Reel filter")
reels_posts_str = at.metric[0].value
reels_posts_num = int(reels_posts_str.replace(",", ""))
print(f"Expected: {expected_reels_count:,} | Actual: {reels_posts_str}")
assert reels_posts_num == expected_reels_count, f"Expected {expected_reels_count}, got {reels_posts_num}"
assert reels_posts_str == "12,599", f"Expected '12,599', got '{reels_posts_str}'"
print("✓ Test 2 passed: Reel filter correctly returns 12,599 posts.")

# Test 3: flt_months = ("May 2024", "May 2024")
print("\n--- TEST 3: MONTHS = ('May 2024', 'May 2024') ---")
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
at.select_slider(key="flt_months").set_value(("May 2024", "May 2024")).run()
assert_no_exceptions(at, "Test 3: May 2024 filter")
may_posts_str = at.metric[0].value
may_posts_num = int(may_posts_str.replace(",", ""))
print(f"Expected: {expected_may_count:,} | Actual: {may_posts_str}")
assert may_posts_num == expected_may_count, f"Expected {expected_may_count}, got {may_posts_num}"
assert may_posts_str == "4,250", f"Expected '4,250', got '{may_posts_str}'"
print("✓ Test 3 passed: May 2024 filter correctly returns 4,250 posts.")

# Test 4: flt_hashtags = ["#VeganBeauty"]
print("\n--- TEST 4: HASHTAGS = ['#VeganBeauty'] ---")
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
at.multiselect(key="flt_hashtags").set_value(["#VeganBeauty"]).run()
assert_no_exceptions(at, "Test 4: #VeganBeauty filter")
vegan_posts_str = at.metric[0].value
vegan_posts_num = int(vegan_posts_str.replace(",", ""))
print(f"Expected: {expected_vegan_count:,} | Actual: {vegan_posts_str}")
assert vegan_posts_num == expected_vegan_count, f"Expected {expected_vegan_count}, got {vegan_posts_num}"
assert vegan_posts_str == "19,982", f"Expected '19,982', got '{vegan_posts_str}'"
print("✓ Test 4 passed: #VeganBeauty filter correctly returns 19,982 posts.")

# Test 5: Combined filter (Reel + May 2024 + Giveaway)
print("\n--- TEST 5: COMBINED FILTERS (Reel + May 2024 + Giveaway) ---")
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
at.multiselect(key="flt_post_type").set_value(["Reel"])
at.select_slider(key="flt_months").set_value(("May 2024", "May 2024"))
at.multiselect(key="flt_campaign").set_value(["Giveaway"]).run()
assert_no_exceptions(at, "Test 5: Combined filter")
comb_posts_str = at.metric[0].value
comb_posts_num = int(comb_posts_str.replace(",", ""))
print(f"Expected: {expected_combined_count:,} | Actual: {comb_posts_str}")
assert comb_posts_num == expected_combined_count, f"Expected {expected_combined_count}, got {comb_posts_num}"
print(f"✓ Test 5 passed: Combined filter returns {comb_posts_str} posts (matches raw Excel ground truth).")

# Test 6: Empty flt_post_type filter
print("\n--- TEST 6: EMPTY POST_TYPE FILTER ---")
at = AppTest.from_file("app.py", default_timeout=60)
at.run()
at.multiselect(key="flt_post_type").set_value([]).run()
assert_no_exceptions(at, "Test 6: Empty filter")
assert len(at.warning) > 0, "Expected a warning for empty filter, but none found"
warning_text = at.warning[0].value
print(f"Expected: Warning 'No posts match the current filters.' | Actual: '{warning_text}'")
assert "No posts match the current filters." in warning_text
print("✓ Test 6 passed: Empty filter displays warning cleanly and stops without crashing.")

print("\n" + "=" * 80)
print("ALL APPTEST VERIFICATION CHECKS PASSED SUCCESSFULLY")
print("=" * 80)
