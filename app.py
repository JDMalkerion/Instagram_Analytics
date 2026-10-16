import streamlit as st
import pandas as pd
import numpy as np

from data_loader import load_data, filter_data, explode_hashtags
from metrics import (
    get_kpi_summary,
    get_monthly_posts,
    get_top_posts_by_likes,
    get_top_posts_by_engagement_rate,
    get_post_type_performance,
    get_weekday_performance,
    get_engagement_funnel,
    get_growth_funnel,
    get_hashtag_performance,
    get_campaign_performance,
    get_group_significance,
    get_hashtag_significance,
    get_monthly_growth,
    get_audience_emotion_performance,
    get_engagement_source_performance
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
    fig_growth_funnel,
    fig_monthly_growth
)

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

all_post_types = sorted(full_df['post_type'].unique().tolist())
all_campaigns = sorted(full_df['campaign_type'].unique().tolist())

month_order_df = (
    full_df[['month', 'month_label']]
    .drop_duplicates()
    .sort_values('month')
    .reset_index(drop=True)
)
all_month_labels = month_order_df['month_label'].tolist()
label_to_month = dict(zip(month_order_df['month_label'], month_order_df['month']))

all_hashtags = sorted(explode_hashtags(full_df)['hashtag'].unique().tolist())


def significance_caption(result: dict, label: str) -> str:
    """
    Turns a get_group_significance result into a clean one-sentence statistical summary.
    """
    if result.get("anova_p") is None or result.get("n_groups", 0) < 2:
        return "Select at least two options to run a significance test."

    anova_p = result["anova_p"]
    kruskal_p = result["kruskal_p"]
    eta_pct = (result["eta_squared"] * 100) if result.get("eta_squared") is not None else 0.0

    sig_phrase = "are statistically significant" if result.get("significant") else "are not statistically significant"

    plural_map = {
        "post type": "post types",
        "day of week": "days of the week",
        "campaign type": "campaign types",
        "audience emotion": "audience emotions",
        "engagement source": "engagement sources"
    }
    plural_label = plural_map.get(label, f"{label}s")

    return (
        f"ANOVA p = {anova_p:.3f}, Kruskal-Wallis p = {kruskal_p:.3f}: "
        f"differences between {plural_label} {sig_phrase} "
        f"({label} explains {eta_pct:.2f}% of the variation in engagement rate)."
    )


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

if not sel_post_types or not sel_campaigns or not sel_hashtags:
    st.warning("No posts match the current filters.")
    st.stop()

post_types_arg = None if len(sel_post_types) == len(all_post_types) else sel_post_types
campaign_types_arg = None if len(sel_campaigns) == len(all_campaigns) else sel_campaigns
hashtags_arg = None if len(sel_hashtags) == len(all_hashtags) else sel_hashtags

if sel_months == (all_month_labels[0], all_month_labels[-1]):
    months_arg = None
else:
    start_idx = all_month_labels.index(sel_months[0])
    end_idx = all_month_labels.index(sel_months[1])
    active_labels = all_month_labels[start_idx : end_idx + 1]
    months_arg = [label_to_month[lbl] for lbl in active_labels]

filtered_df = filter_data(
    full_df,
    post_types=post_types_arg,
    months=months_arg,
    hashtags=hashtags_arg,
    campaign_types=campaign_types_arg
)

st.sidebar.markdown(f"**{len(filtered_df):,} of {len(full_df):,} posts selected**")

if filtered_df.empty:
    st.warning("No posts match the current filters.")
    st.stop()

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
        index=1,
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
    # A) Post Type Comparison
    st.subheader("Post type comparison")
    pt_sig = get_group_significance(filtered_df, "post_type")
    st.caption(significance_caption(pt_sig, "post type"))

    pt_df = get_post_type_performance(filtered_df)
    st.plotly_chart(fig_post_type_actions(pt_df), use_container_width=True)
    st.plotly_chart(fig_avg_engagement_rate_by_group(pt_df, "post_type", "Avg Engagement Rate by Post Type"), use_container_width=True)
    st.caption("Error bars show the 95% confidence interval.")

    st.markdown("---")

    # B) Day of Week Performance
    st.subheader("Day of week performance")
    wk_sig = get_group_significance(filtered_df, "weekday")
    st.caption(significance_caption(wk_sig, "day of week"))

    wk_metric_choice = st.radio(
        "Metric:",
        options=["Engagement rate", "Total engagement"],
        horizontal=True,
        key="rad_weekday_metric"
    )
    metric_key = "avg_engagement_rate" if wk_metric_choice == "Engagement rate" else "avg_total_engagement"
    wk_df = get_weekday_performance(filtered_df)
    st.plotly_chart(fig_weekday_performance(wk_df, metric=metric_key), use_container_width=True)
    if metric_key == "avg_engagement_rate":
        st.caption("Error bars show the 95% confidence interval.")

    st.markdown("---")

    # C) Hashtag Performance
    st.subheader("Hashtag performance")
    ht_df = get_hashtag_performance(filtered_df)
    col_ht1, col_ht2 = st.columns(2)
    with col_ht1:
        st.plotly_chart(fig_hashtag_usage(ht_df), use_container_width=True)
    with col_ht2:
        st.plotly_chart(fig_avg_engagement_rate_by_group(ht_df, "hashtag", "Avg Engagement Rate by Hashtag"), use_container_width=True)
    st.caption("Posts with several hashtags count once per tag, so the groups overlap. Error bars show the 95% confidence interval.")

    with st.expander("Significance by hashtag"):
        ht_sig_df = get_hashtag_significance(filtered_df)
        st.dataframe(
            ht_sig_df[['hashtag', 'diff_pp', 'p_value', 'p_bonferroni', 'significant']],
            use_container_width=True
        )

    st.markdown("---")

    # D) Campaign Performance
    st.subheader("Campaign performance")
    cp_sig = get_group_significance(filtered_df, "campaign_type")
    st.caption(significance_caption(cp_sig, "campaign type"))

    cp_df = get_campaign_performance(filtered_df)
    col_cp1, col_cp2 = st.columns(2)
    with col_cp1:
        st.plotly_chart(fig_avg_engagement_rate_by_group(cp_df, "campaign_type", "Avg Engagement Rate by Campaign"), use_container_width=True)
    with col_cp2:
        st.plotly_chart(fig_campaign_follows(cp_df), use_container_width=True)
    st.caption("Error bars show the 95% confidence interval.")

    st.markdown("---")

    # E) Audience Emotion
    st.subheader("Audience emotion")
    emo_sig = get_group_significance(filtered_df, "audience_emotion")
    st.caption(significance_caption(emo_sig, "audience emotion"))

    emo_df = get_audience_emotion_performance(filtered_df)
    col_em1, col_em2 = st.columns(2)
    with col_em1:
        st.plotly_chart(fig_avg_engagement_rate_by_group(emo_df, "audience_emotion", "Avg Engagement Rate by Audience Emotion"), use_container_width=True)
    with col_em2:
        st.plotly_chart(fig_campaign_follows(emo_df, "audience_emotion"), use_container_width=True)
    st.caption("Error bars show the 95% confidence interval.")

    st.markdown("---")

    # F) Engagement Source
    st.subheader("Engagement source")
    src_sig = get_group_significance(filtered_df, "engagement_source")
    st.caption(significance_caption(src_sig, "engagement source"))

    src_df = get_engagement_source_performance(filtered_df)
    col_sr1, col_sr2 = st.columns(2)
    with col_sr1:
        st.plotly_chart(fig_avg_engagement_rate_by_group(src_df, "engagement_source", "Avg Engagement Rate by Engagement Source"), use_container_width=True)
    with col_sr2:
        st.plotly_chart(fig_campaign_follows(src_df, "engagement_source"), use_container_width=True)
    st.caption("Error bars show the 95% confidence interval.")

with tab_growth:
    # A) Growth Trend by Month
    st.subheader("Growth trend by month")
    growth_metric_choice = st.radio(
        "Growth metric:",
        options=["Follows per day", "Follow rate (%)"],
        horizontal=True,
        key="rad_growth_metric"
    )
    growth_metric_key = "follows_per_day" if growth_metric_choice == "Follows per day" else "follow_rate"
    monthly_growth_df = get_monthly_growth(filtered_df, bounds=full_bounds)
    fig_mg = fig_monthly_growth(monthly_growth_df, metric=growth_metric_key)
    st.plotly_chart(fig_mg, use_container_width=True)

    full_m = monthly_growth_df[~monthly_growth_df['is_partial_month']]
    if not full_m.empty:
        low_row = full_m.loc[full_m['follows_per_day'].idxmin()]
        high_row = full_m.loc[full_m['follows_per_day'].idxmax()]
        dynamic_growth_sentence = (
            f" Among full tracking months, follows per day ranged from "
            f"{low_row['follows_per_day']:,.0f} ({low_row['month_label']}) to "
            f"{high_row['follows_per_day']:,.0f} ({high_row['month_label']})."
        )
    else:
        dynamic_growth_sentence = ""

    st.caption(
        f"Follows attributed to posts. The dataset has no follower totals or unfollows, so this is a growth proxy, not net follower count.{dynamic_growth_sentence}"
    )

    st.markdown("---")

    # B) Engagement Funnel & Conversion
    st.subheader("Engagement funnel")
    eng_funnel_df = get_engagement_funnel(filtered_df)
    col_ef1, col_ef2 = st.columns(2)
    with col_ef1:
        st.plotly_chart(fig_engagement_funnel(eng_funnel_df), use_container_width=True)
    with col_ef2:
        st.plotly_chart(fig_actions_per_100_reach(eng_funnel_df), use_container_width=True)
    st.caption("Likes, comments, shares and saves are parallel actions, not sequential steps; percentages are of reach.")

    st.markdown("---")

    # C) Profile Growth Funnel
    st.subheader("Growth funnel")
    growth_df = get_growth_funnel(filtered_df)
    st.plotly_chart(fig_growth_funnel(growth_df), use_container_width=True)

    pv_rows = growth_df[growth_df['stage'] == 'Profile Visits']
    fol_rows = growth_df[growth_df['stage'] == 'Follows']
    if not pv_rows.empty and not fol_rows.empty and pv_rows['pct_of_reach'].iloc[0] is not None and fol_rows['pct_of_previous'].iloc[0] is not None:
        pv_pct = pv_rows['pct_of_reach'].iloc[0] * 100
        fol_pct = fol_rows['pct_of_previous'].iloc[0] * 100
        st.caption(f"{pv_pct:.1f}% of reached accounts visit the profile; {fol_pct:.1f}% of visitors follow.")
    else:
        st.caption("Insufficient data for growth conversion metrics.")

