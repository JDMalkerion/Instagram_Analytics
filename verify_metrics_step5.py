import pandas as pd
import numpy as np
from scipy import stats
from data_loader import load_data, filter_data
from metrics import get_group_significance, get_hashtag_significance

print("=" * 80)
print("VERIFICATION: STEP 5 STATISTICAL SIGNIFICANCE TESTS")
print("=" * 80)

# 1. Load via data_loader and load raw Excel directly
df = load_data()
raw_df = pd.read_excel("Data/sugar_cosmetics_instagram_data.xlsx", sheet_name=0)

# Independent raw calculations
raw_er = (raw_df['Likes'] + raw_df['Comments'] + raw_df['Shares'] + raw_df['Saves']) / raw_df['Reach']
raw_post_date = pd.to_datetime(raw_df['Post Date'])
raw_weekday = raw_post_date.dt.day_name()

# 2. Group Significance for post_type, weekday, campaign_type
print("\n--- 1. GROUP SIGNIFICANCE TESTS (ANOVA & KRUSKAL-WALLIS) ---")

group_configs = [
    ('post_type', raw_df['Post Type']),
    ('weekday', raw_weekday),
    ('campaign_type', raw_df['Campaign Type'])
]

group_summary_rows = []

for col_name, raw_series in group_configs:
    # Function output
    fn_res = get_group_significance(df, col_name)
    
    # Independent raw calculation
    raw_groups_dict = {}
    for g_val, er_val in zip(raw_series, raw_er):
        raw_groups_dict.setdefault(g_val, []).append(er_val)
    raw_group_arrays = [np.array(vals) for vals in raw_groups_dict.values()]
    
    raw_f_stat, raw_anova_p = stats.f_oneway(*raw_group_arrays)
    raw_k_stat, raw_kruskal_p = stats.kruskal(*raw_group_arrays)
    
    all_raw = np.concatenate(raw_group_arrays)
    grand_mean = np.mean(all_raw)
    ss_tot = np.sum((all_raw - grand_mean) ** 2)
    ss_bet = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in raw_group_arrays)
    raw_eta_sq = ss_bet / ss_tot if ss_tot > 0 else 0.0
    
    # Assertions to 1e-9 tolerance
    assert np.isclose(fn_res['anova_p'], raw_anova_p, atol=1e-9), f"ANOVA p mismatch for {col_name}"
    assert np.isclose(fn_res['kruskal_p'], raw_kruskal_p, atol=1e-9), f"Kruskal p mismatch for {col_name}"
    assert np.isclose(fn_res['anova_f'], raw_f_stat, atol=1e-9), f"ANOVA F mismatch for {col_name}"
    assert np.isclose(fn_res['eta_squared'], raw_eta_sq, atol=1e-9), f"Eta-squared mismatch for {col_name}"
    
    group_summary_rows.append({
        'group_dimension': col_name,
        'n_groups': fn_res['n_groups'],
        'anova_f': fn_res['anova_f'],
        'anova_p': fn_res['anova_p'],
        'kruskal_p': fn_res['kruskal_p'],
        'eta_squared_pct': fn_res['eta_squared'] * 100,
        'significant': fn_res['significant']
    })

group_table = pd.DataFrame(group_summary_rows)
print(f"{'Dimension':<15} | {'ANOVA F':>10} | {'ANOVA p':>10} | {'Kruskal p':>10} | {'Eta Sq (%)':>12} | {'Significant?':<12}")
print("-" * 82)
for _, r in group_table.iterrows():
    print(f"{r['group_dimension']:<15} | {r['anova_f']:>10.4f} | {r['anova_p']:>10.4f} | {r['kruskal_p']:>10.4f} | {r['eta_squared_pct']:>11.5f}% | {str(r['significant']):<12}")

print("✓ All group significance tests match independent raw calculations to 1e-9.")

# 3. Hashtag Significance (Welch's t-test with Bonferroni correction)
print("\n--- 2. HASHTAG SIGNIFICANCE TESTS (WELCH'S T-TEST & BONFERRONI) ---")
ht_sig_df = get_hashtag_significance(df)

# Independent raw calculation
raw_tag_lists = raw_df['Hashtags'].astype(str).str.split(', ')
raw_unique_tags = sorted(list({t for sub in raw_tag_lists for t in sub}))
n_tags = len(raw_unique_tags)

for _, r in ht_sig_df.iterrows():
    tag = r['hashtag']
    raw_with_mask = np.array([tag in tl for tl in raw_tag_lists])
    raw_with_vals = raw_er[raw_with_mask].values
    raw_without_vals = raw_er[~raw_with_mask].values
    
    assert r['posts_with'] == len(raw_with_vals)
    assert np.isclose(r['mean_with'], np.mean(raw_with_vals), atol=1e-9)
    assert np.isclose(r['mean_without'], np.mean(raw_without_vals), atol=1e-9)
    
    raw_t_stat, raw_p_val = stats.ttest_ind(raw_with_vals, raw_without_vals, equal_var=False)
    raw_p_bonf = min(1.0, raw_p_val * n_tags)
    
    assert np.isclose(r['p_value'], raw_p_val, atol=1e-9), f"p_value mismatch for {tag}"
    assert np.isclose(r['p_bonferroni'], raw_p_bonf, atol=1e-9), f"p_bonferroni mismatch for {tag}"

print(ht_sig_df.to_string(index=False))
print("✓ All hashtag Welch's t-tests and Bonferroni adjustments match independent raw calculation to 1e-9.")

# 4. Empty-DataFrame and small-group tests
print("\n--- 3. EMPTY-DATAFRAME & EDGE-CASE ROBUSTNESS TESTS ---")
empty_df = filter_data(df, post_types=["DoesNotExist"])
assert len(empty_df) == 0

e_group = get_group_significance(empty_df, "post_type")
e_ht = get_hashtag_significance(empty_df)

print(f"Empty df get_group_significance: {e_group}")
print(f"Empty df get_hashtag_significance shape: {e_ht.shape}")

assert e_group['anova_p'] is None
assert e_group['kruskal_p'] is None
assert e_group['eta_squared'] is None
assert e_group['significant'] is False
assert len(e_ht) == 0
assert list(e_ht.columns) == ['hashtag', 'posts_with', 'mean_with', 'mean_without', 'diff_pp', 'p_value', 'p_bonferroni', 'significant']

# Test single-row edge case (groups < 2 rows)
single_row_df = df.head(1).copy()
single_group = get_group_significance(single_row_df, "post_type")
assert single_group['anova_p'] is None
assert single_group['kruskal_p'] is None
assert single_group['significant'] is False
print(f"Single-row df get_group_significance: {single_group}")

print("✓ Edge cases handled gracefully without crashing.")

print("\n" + "=" * 80)
print("ALL STEP 5 VERIFICATION CHECKS PASSED SUCCESSFULLY")
print("=" * 80)
