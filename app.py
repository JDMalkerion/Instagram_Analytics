import streamlit as pd_st  # for any naming if needed
import streamlit as st
import pandas as pd
import numpy as np

from data_loader import load_data, filter_data, explode_hashtags
from metrics import (
    get_kpi_summary,
    get_monthly_posts,
    get_top_posts_by_likes,
    get_top_posts_by_engagement_rate
)
from charts import fig_monthly_trend, fig_top_posts

# 1. Page Configuration
st.set_page_config(
    layout="wide",
    page_title="Sugar Cosmetics - Instagram Performance",
    page_icon="💄"
)


# 2. Data Loading with Cache
@st.cache_data
def get_cached_data() -> pd.DataFrame:
    return load_data()


full_df = get_cached_data()
full_bounds = (full_df['post_date'].min(), full_df['post_date'].max())

# Distinct options for filters
all_post_types = sorted(full_df['post_type'].unique().tolist())
all_campaigns = sorted(full_df['campaign_type'].unique().tolist())

# Chronological month labels and their datetime month values
month_order_df = (
    full_df[['month', 'month_label']]
    .drop_duplicates()
    .sort_values('month')
    .reset_index(drop=True)
)
all_month_labels = month_order_df['month_label'].tolist()
label_to_month = dict(zip(month_order_df['month_label'], month_order_df['month']))

# Exploded hashtags list for unique choices
all_hashtags = sorted(explode_hashtags(full_df)['hashtag'].unique().tolist())

# 3. Sidebar Filters
st.sidebar.header("Filter Posts")

sel_post_types = st.sidebar.multiselect(
    "Post Type",
    options=all_post_types,
    default=all_post_types,
    key="flt_post_type"
)

sel_campaigns = st.sidebar.multiselect(
    "Campaign Type",
    options=all_campaigns,
    default=all_campaigns,
    key="flt_campaign"
)

sel_months = st.sidebar.select_slider(
    "Date Range",
    options=all_month_labels,
    value=(all_month_labels[0], all_month_labels[-1]),
    help="Apr 2024 and Apr 2025 are partial months",
    key="flt_months"
)

sel_hashtags = st.sidebar.multiselect(
    "Hashtag (posts containing any selected)",
    options=all_hashtags,
    default=all_hashtags,
    key="flt_hashtags"
)

# Convert selections to filter_data arguments (None when all selected)
if not sel_post_types or not sel_campaigns or not sel_hashtags:
    st.warning("No posts match the current filters.")
    st.stop()

post_types_arg = None if len(sel_post_types) == len(all_post_types) else sel_post_types
campaign_types_arg = None if len(sel_campaigns) == len(all_campaigns) else sel_campaigns
hashtags_arg = None if len(sel_hashtags) == len(all_hashtags) else sel_hashtags

# Handle month slider bounds
if sel_months == (all_month_labels[0], all_month_labels[-1]):
    months_arg = None
else:
    start_idx = all_month_labels.index(sel_months[0])
    end_idx = all_month_labels.index(sel_months[1])
    active_labels = all_month_labels[start_idx : end_idx + 1]
    months_arg = [label_to_month[lbl] for lbl in active_labels]

# Apply filtering
filtered_df = filter_data(
    full_df,
    post_types=post_types_arg,
    months=months_arg,
    hashtags=hashtags_arg,
    campaign_types=campaign_types_arg
)

# Count indicator under sidebar filters
st.sidebar.markdown(f"**{len(filtered_df):,} of {len(full_df):,} posts selected**")

if filtered_df.empty:
    st.warning("No posts match the current filters.")
    st.stop()

# Sidebar Expander for Metric Definitions
with st.sidebar.expander("Metric definitions"):
    st.markdown(
        "• **Engagement rate**: `(likes + comments + shares + saves) / reach` per post, "
        "averaged across posts.\n\n"
        "• **Total reach**: Sum of per-post reach, not unique accounts.\n\n"
        "• **Post labelling**: The dataset has no caption column, so posts are labelled "
        "by ID, date, type and campaign."
    )

# 4. Header & KPI Row
st.title("Sugar Cosmetics - Instagram Performance Dashboard")
st.caption(f"Data window: {full_bounds[0]:%d %b %Y} to {full_bounds[1]:%d %b %Y}")

kpis = get_kpi_summary(filtered_df)


def format_compact(num: int) -> str:
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return f"{num:,}"


kpi_col1, kpi_col2, kpi_col3, kpi_col4, kpi_col5 = st.columns(5)
with kpi_col1:
    st.metric(
        label="Total posts",
        value=f"{kpis['total_posts']:,}",
        help=f"Exact count: {kpis['total_posts']:,} posts"
    )
with kpi_col2:
    st.metric(
        label="Total likes",
        value=format_compact(kpis['total_likes']),
        help=f"Exact count: {kpis['total_likes']:,} likes"
    )
with kpi_col3:
    st.metric(
        label="Total comments",
        value=format_compact(kpis['total_comments']),
        help=f"Exact count: {kpis['total_comments']:,} comments"
    )
with kpi_col4:
    st.metric(
        label="Total reach",
        value=format_compact(kpis['total_reach']),
        help=f"Exact sum: {kpis['total_reach']:,} reach"
    )
with kpi_col5:
    er_val = kpis['avg_engagement_rate']
    er_str = f"{er_val * 100:.2f}%" if er_val is not None else "N/A"
    st.metric(
        label="Avg engagement rate",
        value=er_str,
        help=f"Exact mean: {er_val:.6f}" if er_val is not None else None
    )

# 5. Main Navigation Tabs
tab_overview, tab_content, tab_growth = st.tabs([
    "Overview",
    "Content performance",
    "Engagement & growth"
])

with tab_overview:
    # A) Monthly Posting Trend
    st.subheader("Monthly Posting Trend")
    metric_selection = st.radio(
        "Metric",
        options=["Posts", "Posts per day"],
        horizontal=True,
        key="rad_monthly_metric"
    )
    metric_col = "posts" if metric_selection == "Posts" else "posts_per_day"

    monthly_summary = get_monthly_posts(filtered_df, bounds=full_bounds)
    fig_trend = fig_monthly_trend(monthly_summary, metric=metric_col)
    st.plotly_chart(fig_trend, use_container_width=True)
    st.caption(
        "April 2024 (19–30 Apr, 12 active days) and April 2025 (1–19 Apr, 19 active days) "
        "are partial tracking months. 'Posts per day' normalises by active days to allow fair comparison."
    )

    st.markdown("---")

    # B) Top 10 Posts (Likes vs Engagement Rate)
    col_top_likes, col_top_er = st.columns(2)

    with col_top_likes:
        st.subheader("Top 10 posts by likes")
        top_likes_df = get_top_posts_by_likes(filtered_df, n=10)
        fig_likes = fig_top_posts(top_likes_df, value_col="likes", x_title="Likes", percent=False)
        st.plotly_chart(fig_likes, use_container_width=True)
        with st.expander("Show table"):
            st.dataframe(top_likes_df, use_container_width=True)

    with col_top_er:
        st.subheader("Top 10 posts by engagement rate")
        top_er_df = get_top_posts_by_engagement_rate(filtered_df, n=10)
        fig_er = fig_top_posts(top_er_df, value_col="engagement_rate", x_title="Engagement Rate", percent=True)
        st.plotly_chart(fig_er, use_container_width=True)

        if len(top_er_df) > 1:
            spread_pp = (top_er_df.iloc[0]['engagement_rate'] - top_er_df.iloc[-1]['engagement_rate']) * 100
        else:
            spread_pp = 0.0
        st.caption(f"Spread between #1 and #10: {spread_pp:.2f} percentage points - treat the order as near-ties.")

        with st.expander("Show table"):
            st.dataframe(top_er_df, use_container_width=True)

with tab_content:
    st.info("Coming in the next step")

with tab_growth:
    st.info("Coming in the next step")
