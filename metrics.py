import pandas as pd
import numpy as np
from typing import Optional, Tuple, Any, Dict

TOP_POSTS_COLS = [
    'post_id', 'post_label', 'post_type', 'campaign_type', 'likes', 'reach', 'engagement_rate'
]
TOP_POSTS_ER_COLS = TOP_POSTS_COLS + ['likes_rank']
MONTHLY_POSTS_COLS = [
    'month', 'month_label', 'posts', 'is_partial_month', 'posts_per_day'
]


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
    ranked_df['likes_rank'] = ranked_df['likes'].rank(ascending=False, method='min').astype(int)

    sorted_df = ranked_df.sort_values(
        by=['engagement_rate', 'likes', 'post_id'],
        ascending=[False, False, True]
    ).head(n)

    return sorted_df[TOP_POSTS_ER_COLS].reset_index(drop=True)
