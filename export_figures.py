import os
import pandas as pd
from data_loader import load_data
from metrics import (
    get_monthly_posts,
    get_top_posts_by_likes,
    get_top_posts_by_engagement_rate,
    get_post_type_performance,
    get_weekday_performance,
    get_engagement_funnel,
    get_growth_funnel,
    get_hashtag_performance,
    get_campaign_performance
)
from charts import (
    fig_monthly_trend,
    fig_top_posts,
    fig_post_type_actions,
    fig_weekday_performance,
    fig_engagement_funnel,
    fig_growth_funnel,
    fig_avg_engagement_rate_by_group,
    fig_hashtag_usage,
    fig_campaign_follows
)

os.makedirs("images", exist_ok=True)
df = load_data()
full_bounds = (df['post_date'].min(), df['post_date'].max())

print("Generating figures on full unfiltered data...")

figures = {
    "images/task2_monthly_trend.png": fig_monthly_trend(get_monthly_posts(df, bounds=full_bounds), metric="posts"),
    "images/task3_top10_likes.png": fig_top_posts(get_top_posts_by_likes(df, 10), value_col="likes", x_title="Likes", percent=False),
    "images/task4_top10_engagement.png": fig_top_posts(get_top_posts_by_engagement_rate(df, 10), value_col="engagement_rate", x_title="Engagement Rate", percent=True),
    "images/task5_post_type.png": fig_post_type_actions(get_post_type_performance(df)),
    "images/task6_weekday.png": fig_weekday_performance(get_weekday_performance(df), metric="avg_engagement_rate"),
    "images/task7_engagement_funnel.png": fig_engagement_funnel(get_engagement_funnel(df)),
    "images/task7_growth_funnel.png": fig_growth_funnel(get_growth_funnel(df)),
    "images/task8_hashtags.png": fig_avg_engagement_rate_by_group(get_hashtag_performance(df), group_col="hashtag", title="Avg Engagement Rate by Hashtag"),
    "images/campaigns.png": fig_avg_engagement_rate_by_group(get_campaign_performance(df), group_col="campaign_type", title="Avg Engagement Rate by Campaign")
}

for path, fig in figures.items():
    print(f"Exporting {path}...")
    fig.write_image(path, width=1200, scale=2)

print("All figures exported successfully!")
