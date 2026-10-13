import pandas as pd
import numpy as np
from scipy import stats
from typing import Optional, Tuple, Any, Dict, List
from data_loader import explode_hashtags, WEEKDAY_ORDER

TOP_POSTS_COLS = [
    'post_id', 'post_label', 'post_type', 'campaign_type', 'likes', 'reach', 'engagement_rate'
]
TOP_POSTS_ER_COLS = TOP_POSTS_COLS + ['likes_rank']
MONTHLY_POSTS_COLS = [
    'month', 'month_label', 'posts', 'is_partial_month', 'posts_per_day'
]
POST_TYPE_PERF_COLS = [
    'post_type', 'posts', 'avg_likes', 'avg_comments', 'avg_shares', 'avg_saves',
    'avg_reach', 'avg_engagement_rate', 'er_ci95'
]
WEEKDAY_PERF_COLS = [
    'weekday', 'posts', 'avg_total_engagement', 'avg_engagement_rate', 'er_ci95'
]
ENGAGEMENT_FUNNEL_COLS = [
    'stage', 'count', 'pct_of_impressions', 'pct_of_reach', 'pct_of_previous'
]
GROWTH_FUNNEL_COLS = [
    'stage', 'count', 'pct_of_reach', 'pct_of_previous'
]
HASHTAG_PERF_COLS = [
    'hashtag', 'posts', 'avg_engagement_rate', 'er_ci95', 'avg_reach', 'avg_likes'
]
CAMPAIGN_PERF_COLS = [
    'campaign_type', 'posts', 'avg_engagement_rate', 'er_ci95', 'avg_reach', 'avg_likes', 'avg_follows'
]
HASHTAG_SIGNIFICANCE_COLS = [
    'hashtag', 'posts_with', 'mean_with', 'mean_without', 'diff_pp', 'p_value', 'p_bonferroni', 'significant'
]


def _ci95(series: pd.Series) -> float:
    """
    Computes 95% confidence interval half-width:
    1.96 * std(ddof=1) / sqrt(n); returns 0.0 if n < 2.
    """
    clean = series.dropna()
    n = len(clean)
    if n < 2:
        return 0.0
    s = clean.std(ddof=1)
    if np.isnan(s) or s == 0:
        return 0.0
    return float(1.96 * s / np.sqrt(n))


def get_kpi_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes summary KPIs:
    - total_posts: row count
    - total_likes, total_comments: sums
    - total_reach: sum of per-post reach
    - avg_engagement_rate: mean of per-post engagement_rate, as a fraction (0-1)
    On an empty DataFrame return 0 for the totals and None for avg_engagement_rate.
    """
    if df.empty or len(df) == 0:
        return {
            'total_posts': 0,
            'total_likes': 0,
            'total_comments': 0,
            'total_reach': 0,
            'avg_engagement_rate': None
        }

    return {
        'total_posts': int(len(df)),
        'total_likes': int(df['likes'].sum()),
        'total_comments': int(df['comments'].sum()),
        'total_reach': int(df['reach'].sum()),
        'avg_engagement_rate': float(df['engagement_rate'].mean())
    }


def get_monthly_posts(
    df: pd.DataFrame,
    bounds: Optional[Tuple[Any, Any]] = None
) -> pd.DataFrame:
    """
    Aggregates posts per month with daily rate normalized by active bounds.
    Columns: month, month_label, posts, is_partial_month, posts_per_day
    Sorted chronologically by month.
    posts_per_day = posts / number of days of that month that fall inside bounds.
    bounds is a (start_date, end_date) tuple; if None, use min and max post_date of df.
    """
    if df.empty or len(df) == 0:
        return pd.DataFrame(columns=MONTHLY_POSTS_COLS)

    if bounds is None:
        start_date = pd.Timestamp(df['post_date'].min()).floor('D')
        end_date = pd.Timestamp(df['post_date'].max()).floor('D')
    else:
        start_date = pd.Timestamp(bounds[0]).floor('D')
        end_date = pd.Timestamp(bounds[1]).floor('D')

    grouped = (
        df.groupby(['month', 'month_label', 'is_partial_month'], as_index=False)
        .size()
        .rename(columns={'size': 'posts'})
    )
    grouped = grouped.sort_values('month').reset_index(drop=True)

    posts_per_day_list = []
    for _, row in grouped.iterrows():
        m_start = pd.Timestamp(row['month']).floor('D')
        m_end = (m_start + pd.offsets.MonthEnd(1)).floor('D')

        overlap_start = max(m_start, start_date)
        overlap_end = min(m_end, end_date)

        if overlap_end >= overlap_start:
            days_in_bounds = (overlap_end - overlap_start).days + 1
        else:
            days_in_bounds = 0

        if days_in_bounds > 0:
            ppd = row['posts'] / days_in_bounds
        else:
            ppd = 0.0
        posts_per_day_list.append(ppd)

    grouped['posts_per_day'] = posts_per_day_list
    return grouped[MONTHLY_POSTS_COLS]


def get_top_posts_by_likes(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Returns top n posts by likes.
    Columns: post_id, post_label, post_type, campaign_type, likes, reach, engagement_rate
    Sorted by likes descending; ties broken by engagement_rate descending, then post_id ascending.
    """
    if df.empty or len(df) == 0:
        return pd.DataFrame(columns=TOP_POSTS_COLS)

    sorted_df = df.sort_values(
        by=['likes', 'engagement_rate', 'post_id'],
        ascending=[False, False, True]
    ).head(n)

    return sorted_df[TOP_POSTS_COLS].reset_index(drop=True)


def get_top_posts_by_engagement_rate(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """
    Returns top n posts by engagement rate.
    Columns: post_id, post_label, post_type, campaign_type, likes, reach, engagement_rate, likes_rank
    Sorted by engagement_rate descending; ties broken by likes descending, then post_id ascending.
    likes_rank is the post's rank by likes across the whole df (1 = most likes).
    """
    if df.empty or len(df) == 0:
        return pd.DataFrame(columns=TOP_POSTS_ER_COLS)

    ranked_df = df.copy()
    # Uses rank(ascending=False, method="min") so tied posts receive the standard minimum competition rank
    ranked_df['likes_rank'] = ranked_df['likes'].rank(ascending=False, method="min").astype(int)

    sorted_df = ranked_df.sort_values(
        by=['engagement_rate', 'likes', 'post_id'],
        ascending=[False, False, True]
    ).head(n)

    return sorted_df[TOP_POSTS_ER_COLS].reset_index(drop=True)


def get_post_type_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates performance by post type.
    Columns: post_type, posts, avg_likes, avg_comments, avg_shares, avg_saves,
             avg_reach, avg_engagement_rate, er_ci95
    """
    if df.empty or len(df) == 0:
        return pd.DataFrame(columns=POST_TYPE_PERF_COLS)

    records = []
    for pt, group in df.groupby('post_type', observed=True):
        records.append({
            'post_type': pt,
            'posts': len(group),
            'avg_likes': float(group['likes'].mean()),
            'avg_comments': float(group['comments'].mean()),
            'avg_shares': float(group['shares'].mean()),
            'avg_saves': float(group['saves'].mean()),
            'avg_reach': float(group['reach'].mean()),
            'avg_engagement_rate': float(group['engagement_rate'].mean()),
            'er_ci95': _ci95(group['engagement_rate'])
        })

    res = pd.DataFrame(records)
    return res.sort_values('avg_engagement_rate', ascending=False).reset_index(drop=True)


def get_weekday_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates performance by day of week.
    Columns: weekday, posts, avg_total_engagement, avg_engagement_rate, er_ci95
    Ordered Monday..Sunday.
    """
    if df.empty or len(df) == 0:
        return pd.DataFrame(columns=WEEKDAY_PERF_COLS)

    records = []
    for day in WEEKDAY_ORDER:
        group = df[df['weekday'] == day]
        if len(group) == 0:
            continue
        records.append({
            'weekday': day,
            'posts': len(group),
            'avg_total_engagement': float(group['total_engagement'].mean()),
            'avg_engagement_rate': float(group['engagement_rate'].mean()),
            'er_ci95': _ci95(group['engagement_rate'])
        })

    res = pd.DataFrame(records)
    res['weekday'] = pd.Categorical(res['weekday'], categories=WEEKDAY_ORDER, ordered=True)
    return res.sort_values('weekday').reset_index(drop=True)


def get_engagement_funnel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Engagement conversion funnel.
    Stages in this order: Impressions, Reach, Likes, Comments, Shares, Saves
    Columns: stage, count, pct_of_impressions, pct_of_reach (None for Impressions), pct_of_previous
    Stored as fractions (0-1).
    """
    if df.empty or len(df) == 0:
        return pd.DataFrame(columns=ENGAGEMENT_FUNNEL_COLS)

    imp = int(df['impressions'].sum())
    reach = int(df['reach'].sum())
    likes = int(df['likes'].sum())
    comments = int(df['comments'].sum())
    shares = int(df['shares'].sum())
    saves = int(df['saves'].sum())

    stages_data = [
        ('Impressions', imp),
        ('Reach', reach),
        ('Likes', likes),
        ('Comments', comments),
        ('Shares', shares),
        ('Saves', saves),
    ]

    records = []
    for i, (stage, count) in enumerate(stages_data):
        pct_imp = count / imp if imp > 0 else 0.0
        pct_reach = (count / reach if reach > 0 else 0.0) if stage != 'Impressions' else None
        if i == 0:
            pct_prev = None
        else:
            prev_count = stages_data[i - 1][1]
            pct_prev = count / prev_count if prev_count > 0 else 0.0

        records.append({
            'stage': stage,
            'count': count,
            'pct_of_impressions': pct_imp,
            'pct_of_reach': pct_reach,
            'pct_of_previous': pct_prev
        })

    return pd.DataFrame(records)[ENGAGEMENT_FUNNEL_COLS]


def get_growth_funnel(df: pd.DataFrame) -> pd.DataFrame:
    """
    Growth conversion funnel.
    Stages: Reach, Profile Visits, Follows
    Columns: stage, count, pct_of_reach, pct_of_previous
    Stored as fractions (0-1).
    """
    if df.empty or len(df) == 0:
        return pd.DataFrame(columns=GROWTH_FUNNEL_COLS)

    reach = int(df['reach'].sum())
    pv = int(df['profile_visits'].sum())
    follows = int(df['follows'].sum())

    stages_data = [
        ('Reach', reach),
        ('Profile Visits', pv),
        ('Follows', follows)
    ]

    records = []
    for i, (stage, count) in enumerate(stages_data):
        pct_reach = count / reach if reach > 0 else 0.0
        if i == 0:
            pct_prev = None
        else:
            prev_count = stages_data[i - 1][1]
            pct_prev = count / prev_count if prev_count > 0 else 0.0

        records.append({
            'stage': stage,
            'count': count,
            'pct_of_reach': pct_reach,
            'pct_of_previous': pct_prev
        })

    return pd.DataFrame(records)[GROWTH_FUNNEL_COLS]


def get_hashtag_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates performance by hashtag using exploded hashtags.
    Columns: hashtag, posts, avg_engagement_rate, er_ci95, avg_reach, avg_likes
    Sorted by avg_engagement_rate descending.
    """
    if df.empty or len(df) == 0:
        return pd.DataFrame(columns=HASHTAG_PERF_COLS)

    exploded = explode_hashtags(df)
    records = []
    for tag, group in exploded.groupby('hashtag', observed=True):
        records.append({
            'hashtag': tag,
            'posts': len(group),
            'avg_engagement_rate': float(group['engagement_rate'].mean()),
            'er_ci95': _ci95(group['engagement_rate']),
            'avg_reach': float(group['reach'].mean()),
            'avg_likes': float(group['likes'].mean())
        })

    res = pd.DataFrame(records)
    return res.sort_values('avg_engagement_rate', ascending=False).reset_index(drop=True)


def get_campaign_performance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates performance by campaign type.
    Columns: campaign_type, posts, avg_engagement_rate, er_ci95, avg_reach, avg_likes, avg_follows
    Sorted by avg_engagement_rate descending.
    """
    if df.empty or len(df) == 0:
        return pd.DataFrame(columns=CAMPAIGN_PERF_COLS)

    records = []
    for ct, group in df.groupby('campaign_type', observed=True):
        records.append({
            'campaign_type': ct,
            'posts': len(group),
            'avg_engagement_rate': float(group['engagement_rate'].mean()),
            'er_ci95': _ci95(group['engagement_rate']),
            'avg_reach': float(group['reach'].mean()),
            'avg_likes': float(group['likes'].mean()),
            'avg_follows': float(group['follows'].mean())
        })

    res = pd.DataFrame(records)
    return res.sort_values('avg_engagement_rate', ascending=False).reset_index(drop=True)


def get_group_significance(df: pd.DataFrame, group_col: str) -> Dict[str, Any]:
    """
    Compares engagement_rate across groups with:
      - One-way ANOVA (scipy.stats.f_oneway) -> anova_f, anova_p
      - Kruskal-Wallis (scipy.stats.kruskal) -> kruskal_p
    Also returns: n_groups, n_posts, eta_squared, significant.
    Returns None values on empty df or groups with fewer than 2 rows.
    """
    default_res = {
        'n_groups': 0,
        'n_posts': 0,
        'anova_f': None,
        'anova_p': None,
        'kruskal_p': None,
        'eta_squared': None,
        'significant': False
    }

    if df.empty or len(df) == 0 or group_col not in df.columns:
        return default_res

    grouped = df.groupby(group_col, observed=True)
    groups = [g['engagement_rate'].dropna().values for _, g in grouped]
    groups = [g for g in groups if len(g) > 0]
    n_groups = len(groups)
    n_posts = sum(len(g) for g in groups)

    if n_groups < 2 or any(len(g) < 2 for g in groups):
        return {
            'n_groups': n_groups,
            'n_posts': n_posts,
            'anova_f': None,
            'anova_p': None,
            'kruskal_p': None,
            'eta_squared': None,
            'significant': False
        }

    try:
        f_res = stats.f_oneway(*groups)
        k_res = stats.kruskal(*groups)
        anova_f = float(f_res.statistic)
        anova_p = float(f_res.pvalue)
        kruskal_p = float(k_res.pvalue)
    except Exception:
        return {
            'n_groups': n_groups,
            'n_posts': n_posts,
            'anova_f': None,
            'anova_p': None,
            'kruskal_p': None,
            'eta_squared': None,
            'significant': False
        }

    all_vals = np.concatenate(groups)
    grand_mean = np.mean(all_vals)
    ss_total = np.sum((all_vals - grand_mean) ** 2)
    ss_between = sum(len(g) * (np.mean(g) - grand_mean) ** 2 for g in groups)
    eta_squared = float(ss_between / ss_total) if ss_total > 0 else 0.0

    significant = bool(anova_p < 0.05 and kruskal_p < 0.05)

    return {
        'n_groups': int(n_groups),
        'n_posts': int(n_posts),
        'anova_f': anova_f,
        'anova_p': anova_p,
        'kruskal_p': kruskal_p,
        'eta_squared': eta_squared,
        'significant': significant
    }


def get_hashtag_significance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compares engagement_rate of posts WITH each hashtag vs posts WITHOUT it
    using Welch's t-test (scipy.stats.ttest_ind, equal_var=False).
    Columns: hashtag, posts_with, mean_with, mean_without, diff_pp,
             p_value, p_bonferroni, significant
    """
    if df.empty or len(df) == 0 or 'hashtag_list' not in df.columns:
        return pd.DataFrame(columns=HASHTAG_SIGNIFICANCE_COLS)

    unique_tags = sorted(list({tag for tags in df['hashtag_list'].dropna() for tag in tags}))
    if not unique_tags:
        return pd.DataFrame(columns=HASHTAG_SIGNIFICANCE_COLS)

    n_tags = len(unique_tags)
    records = []

    for tag in unique_tags:
        with_mask = df['hashtag_list'].apply(lambda tags: tag in tags if isinstance(tags, (list, set)) else False)
        with_vals = df.loc[with_mask, 'engagement_rate'].dropna()
        without_vals = df.loc[~with_mask, 'engagement_rate'].dropna()

        posts_with = len(with_vals)
        if len(with_vals) < 2 or len(without_vals) < 2:
            mean_with = float(with_vals.mean()) if len(with_vals) > 0 else None
            mean_without = float(without_vals.mean()) if len(without_vals) > 0 else None
            diff_pp = (mean_with - mean_without) * 100 if mean_with is not None and mean_without is not None else None
            p_val = None
            p_bonf = None
            sig = False
        else:
            mean_with = float(with_vals.mean())
            mean_without = float(without_vals.mean())
            diff_pp = (mean_with - mean_without) * 100
            t_res = stats.ttest_ind(with_vals, without_vals, equal_var=False)
            p_val = float(t_res.pvalue)
            p_bonf = float(min(1.0, p_val * n_tags))
            sig = bool(p_bonf < 0.05)

        records.append({
            'hashtag': tag,
            'posts_with': posts_with,
            'mean_with': mean_with,
            'mean_without': mean_without,
            'diff_pp': diff_pp,
            'p_value': p_val,
            'p_bonferroni': p_bonf,
            'significant': sig
        })

    res = pd.DataFrame(records)
    return res.sort_values('diff_pp', ascending=False).reset_index(drop=True)
