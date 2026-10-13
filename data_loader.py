import pandas as pd
import numpy as np
from typing import Optional, List

DATA_PATH = "Data/sugar_cosmetics_instagram_data.xlsx"

COLUMN_RENAME_MAP = {
    'Post Date': 'post_date',
    'Post Type': 'post_type',
    'Campaign Type': 'campaign_type',
    'Hashtags': 'hashtags',
    'Audience Emotion': 'audience_emotion',
    'Engagement Source': 'engagement_source',
    'Impressions': 'impressions',
    'Reach': 'reach',
    'Likes': 'likes',
    'Comments': 'comments',
    'Shares': 'shares',
    'Saves': 'saves',
    'Profile Visits': 'profile_visits',
    'Follows': 'follows'
}

WEEKDAY_ORDER = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
]


def load_data(file_path: str = DATA_PATH) -> pd.DataFrame:
    """
    Loads Sugar Cosmetics Instagram data from Excel (sheet by index 0),
    renames columns to snake_case, and adds derived columns.
    Does not drop or filter any rows.
    """
    # 1. Read first sheet by index (due to trailing period in sheet name)
    df = pd.read_excel(file_path, sheet_name=0)

    # 2. Rename columns to snake_case
    df = df.rename(columns=COLUMN_RENAME_MAP)

    # 3. Add derived columns
    # post_id: 1..N in original row order (assign BEFORE any sorting)
    df['post_id'] = np.arange(1, len(df) + 1)

    # Ensure post_date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['post_date']):
        df['post_date'] = pd.to_datetime(df['post_date'])

    # month: first day of the post's month (datetime), for correct sorting
    df['month'] = df['post_date'].dt.to_period('M').dt.to_timestamp()

    # month_label: e.g. "Apr 2024"
    df['month_label'] = df['post_date'].dt.strftime('%b %Y')

    # is_partial_month: True for 2024-04 and 2025-04 (the two edge months), else False
    df['is_partial_month'] = df['post_date'].dt.strftime('%Y-%m').isin(['2024-04', '2025-04'])

    # weekday: day name as an ordered categorical Monday..Sunday
    df['weekday'] = pd.Categorical(
        df['post_date'].dt.day_name(),
        categories=WEEKDAY_ORDER,
        ordered=True
    )

    # total_engagement: likes + comments + shares + saves
    df['total_engagement'] = df['likes'] + df['comments'] + df['shares'] + df['saves']

    # engagement_rate: total_engagement / reach, stored as a fraction (0-1)
    df['engagement_rate'] = df['total_engagement'] / df['reach']

    # post_label: f"#{post_id} | {post_date:%d %b %Y} | {post_type} | {campaign_type}"
    df['post_label'] = [
        f"#{pid} | {pdate:%d %b %Y} | {ptype} | {ctype}"
        for pid, pdate, ptype, ctype in zip(
            df['post_id'], df['post_date'], df['post_type'], df['campaign_type']
        )
    ]

    # hashtag_list: hashtags split on ", " into a list
    df['hashtag_list'] = df['hashtags'].astype(str).str.split(', ')

    return df


def explode_hashtags(df: pd.DataFrame) -> pd.DataFrame:
    """
    One row per (post, hashtag), using hashtag_list, with a 'hashtag' column.
    """
    exploded = df.explode('hashtag_list').rename(columns={'hashtag_list': 'hashtag'})
    return exploded


def filter_data(
    df: pd.DataFrame,
    post_types: Optional[List[str]] = None,
    months: Optional[List] = None,
    hashtags: Optional[List[str]] = None,
    campaign_types: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Filters DataFrame by post_types, months, hashtags, and campaign_types.
    Each argument is a list or None (None means no filter).
    Hashtags filter keeps posts that contain ANY of the selected hashtags.
    """
    filtered = df

    if post_types is not None:
        filtered = filtered[filtered['post_type'].isin(post_types)]

    if months is not None:
        # Support month_label (e.g. 'Apr 2024'), month (Timestamp), or string date
        if len(months) > 0 and isinstance(months[0], str) and months[0] in filtered['month_label'].values:
            filtered = filtered[filtered['month_label'].isin(months)]
        else:
            filtered = filtered[filtered['month'].isin(months)]

    if campaign_types is not None:
        filtered = filtered[filtered['campaign_type'].isin(campaign_types)]

    if hashtags is not None:
        selected_tags = set(hashtags)
        mask = filtered['hashtag_list'].apply(lambda tags: bool(selected_tags.intersection(tags)))
        filtered = filtered[mask]

    return filtered
