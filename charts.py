import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import Optional

# Shared design system constants
THEME_TEMPLATE = "plotly_white"
ACCENT_PINK = "#D81B60"
MUTED_PINK = "rgba(216, 27, 96, 0.25)"
COLOR_TEXT_MAIN = "#212121"
COLOR_TEXT_MUTED = "#616161"
COLOR_GRID = "#F0F0F0"
FONT_FAMILY = "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif"


def _compact_num(val: float) -> str:
    """Formats numeric count into compact readable string."""
    if val >= 1_000_000_000:
        return f"{val / 1_000_000_000:.2f}B"
    if val >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    if val >= 1_000:
        return f"{val / 1_000:.1f}K"
    return f"{int(val):,}"


def fig_monthly_trend(monthly_df: pd.DataFrame, metric: str = "posts") -> go.Figure:
    """
    Line chart with markers over month_label, in chronological order.
    metric is 'posts' or 'posts_per_day'.
    Partial months (is_partial_month == True) get open markers and a dotted line segment.
    """
    fig = go.Figure()

    if monthly_df.empty or len(monthly_df) == 0:
        fig.update_layout(
            template=THEME_TEMPLATE,
            annotations=[dict(
                text="No data available for the selected period",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                font=dict(size=14, color=COLOR_TEXT_MUTED)
            )]
        )
        return fig

    sorted_df = monthly_df.sort_values('month').reset_index(drop=True)
    y_col = metric
    y_title = "Total Posts" if metric == "posts" else "Posts per Day (Active Days)"

    # 1. Connect consecutive points with solid or dotted line segments
    for i in range(len(sorted_df) - 1):
        p1 = sorted_df.iloc[i]
        p2 = sorted_df.iloc[i + 1]
        is_partial_seg = bool(p1['is_partial_month'] or p2['is_partial_month'])

        fig.add_trace(go.Scatter(
            x=[p1['month_label'], p2['month_label']],
            y=[p1[y_col], p2[y_col]],
            mode='lines',
            line=dict(
                color=ACCENT_PINK,
                width=2.5,
                dash='dot' if is_partial_seg else 'solid'
            ),
            showlegend=False,
            hoverinfo='skip'
        ))

    # 2. Markers for full months
    full_df = sorted_df[~sorted_df['is_partial_month']]
    if not full_df.empty:
        fig.add_trace(go.Scatter(
            x=full_df['month_label'],
            y=full_df[y_col],
            mode='markers',
            name='Full month',
            marker=dict(
                color=ACCENT_PINK,
                size=9,
                line=dict(color='#FFFFFF', width=1)
            ),
            customdata=full_df[['posts', 'posts_per_day']].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Posts: %{customdata[0]:,}<br>"
                "Posts/Day: %{customdata[1]:.1f}<br>"
                "Status: Full calendar month"
                "<extra></extra>"
            )
        ))

    # 3. Markers for partial months
    partial_df = sorted_df[sorted_df['is_partial_month']]
    if not partial_df.empty:
        fig.add_trace(go.Scatter(
            x=partial_df['month_label'],
            y=partial_df[y_col],
            mode='markers',
            name='Partial month',
            marker=dict(
                symbol='circle-open',
                size=11,
                line=dict(color=ACCENT_PINK, width=2.5)
            ),
            customdata=partial_df[['posts', 'posts_per_day']].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Posts: %{customdata[0]:,}<br>"
                "Posts/Day: %{customdata[1]:.1f}<br>"
                "Status: Partial tracking month (dotted segment)"
                "<extra></extra>"
            )
        ))

    fig.update_layout(
        template=THEME_TEMPLATE,
        font=dict(family=FONT_FAMILY, color=COLOR_TEXT_MAIN),
        margin=dict(l=20, r=20, t=30, b=30),
        height=380,
        xaxis=dict(
            title="",
            gridcolor=COLOR_GRID,
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            title=y_title,
            gridcolor=COLOR_GRID,
            rangemode='tozero',
            tickfont=dict(size=12)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12)
        )
    )

    return fig


def fig_top_posts(
    top_df: pd.DataFrame,
    value_col: str,
    x_title: str,
    percent: bool = False
) -> go.Figure:
    """
    Horizontal bar chart, highest at the top, y = post_label, x axis starting at 0.
    """
    fig = go.Figure()

    if top_df.empty or len(top_df) == 0:
        fig.update_layout(
            template=THEME_TEMPLATE,
            annotations=[dict(
                text="No posts match the criteria",
                showarrow=False,
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                font=dict(size=14, color=COLOR_TEXT_MUTED)
            )]
        )
        return fig

    plot_df = top_df.iloc[::-1].copy()

    if percent:
        text_labels = [f"{v * 100:.2f}%" for v in plot_df[value_col]]
    else:
        text_labels = [f"{int(v):,}" for v in plot_df[value_col]]

    customdata = plot_df[['reach', 'engagement_rate', 'post_type', 'campaign_type']].values

    fig.add_trace(go.Bar(
        x=plot_df[value_col],
        y=plot_df['post_label'],
        orientation='h',
        marker=dict(
            color=ACCENT_PINK,
            line=dict(color=ACCENT_PINK, width=1)
        ),
        text=text_labels,
        textposition='outside',
        textfont=dict(size=11, color=COLOR_TEXT_MAIN),
        cliponaxis=False,
        customdata=customdata,
        hovertemplate=(
            "<b>%{y}</b><br>"
            f"{x_title}: %{{text}}<br>"
            "Reach: %{customdata[0]:,}<br>"
            "Engagement Rate: %{customdata[1]:.2%}<br>"
            "Type: %{customdata[2]}<br>"
            "Campaign: %{customdata[3]}"
            "<extra></extra>"
        )
    ))

    max_val = plot_df[value_col].max() if len(plot_df) > 0 else 1
    x_max_padding = max_val * 1.15 if max_val > 0 else 1

    fig.update_layout(
        template=THEME_TEMPLATE,
        font=dict(family=FONT_FAMILY, color=COLOR_TEXT_MAIN),
        xaxis=dict(
            title=x_title,
            rangemode='tozero',
            range=[0, x_max_padding],
            gridcolor=COLOR_GRID,
            tickformat='.0%' if percent else ',d',
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            title="",
            automargin=True,
            tickfont=dict(size=11)
        ),
        margin=dict(l=10, r=30, t=20, b=30),
        height=420
    )

    return fig


def fig_post_type_actions(pt_df: pd.DataFrame) -> go.Figure:
    """
    Small multiples in one row, 4 panels:
    avg likes, comments, shares, saves by post type.
    Each panel has its own y-axis starting at 0.
    """
    fig = make_subplots(
        rows=1, cols=4,
        subplot_titles=["Avg Likes", "Avg Comments", "Avg Shares", "Avg Saves"]
    )

    if pt_df.empty or len(pt_df) == 0:
        fig.update_layout(template=THEME_TEMPLATE)
        return fig

    # Ordered by avg_engagement_rate descending
    sorted_df = pt_df.sort_values('avg_engagement_rate', ascending=False).reset_index(drop=True)
    metrics = [
        ('avg_likes', 1, ",.0f"),
        ('avg_comments', 2, ",.0f"),
        ('avg_shares', 3, ",.0f"),
        ('avg_saves', 4, ",.0f")
    ]

    for col_name, col_idx, fmt in metrics:
        text_labels = [f"{v:,.0f}" for v in sorted_df[col_name]]
        fig.add_trace(
            go.Bar(
                x=sorted_df['post_type'],
                y=sorted_df[col_name],
                marker_color=ACCENT_PINK,
                text=text_labels,
                textposition='outside',
                textfont=dict(size=11),
                cliponaxis=False,
                hovertemplate=f"<b>%{{x}}</b><br>{col_name.replace('avg_', 'Avg ').title()}: %{{y:{fmt}}}<extra></extra>",
                showlegend=False
            ),
            row=1, col=col_idx
        )

    fig.update_layout(
        template=THEME_TEMPLATE,
        font=dict(family=FONT_FAMILY, color=COLOR_TEXT_MAIN),
        margin=dict(l=20, r=20, t=40, b=30),
        height=340
    )
    # Ensure every panel's y-axis starts at 0
    fig.update_yaxes(rangemode="tozero", gridcolor=COLOR_GRID)
    fig.update_xaxes(title="", tickfont=dict(size=11))

    return fig


def fig_avg_engagement_rate_by_group(
    group_df: pd.DataFrame,
    group_col: str,
    title: str = ""
) -> go.Figure:
    """
    Bar chart showing avg_engagement_rate by group with 95% CI error bars.
    Y-axis starts at 0.
    """
    fig = go.Figure()

    if group_df.empty or len(group_df) == 0:
        fig.update_layout(template=THEME_TEMPLATE)
        return fig

    sorted_df = group_df.sort_values('avg_engagement_rate', ascending=False).reset_index(drop=True)
    text_labels = [f"{v * 100:.2f}%" for v in sorted_df['avg_engagement_rate']]

    fig.add_trace(go.Bar(
        x=sorted_df[group_col],
        y=sorted_df['avg_engagement_rate'],
        marker_color=ACCENT_PINK,
        text=text_labels,
        textposition='outside',
        cliponaxis=False,
        error_y=dict(
            type='data',
            array=sorted_df['er_ci95'],
            visible=True,
            color=COLOR_TEXT_MAIN,
            thickness=1.5,
            width=5
        ),
        customdata=sorted_df['er_ci95'].values,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Avg Engagement Rate: %{y:.2%}<br>"
            "95% CI: ±%{customdata:.3%}"
            "<extra></extra>"
        )
    ))

    # Add margin for error bars on y axis
    max_er = (sorted_df['avg_engagement_rate'] + sorted_df['er_ci95']).max() if len(sorted_df) > 0 else 0.25
    y_max = max(max_er * 1.18, 0.22)

    fig.update_layout(
        title=title if title else None,
        template=THEME_TEMPLATE,
        font=dict(family=FONT_FAMILY, color=COLOR_TEXT_MAIN),
        xaxis=dict(title="", tickfont=dict(size=11)),
        yaxis=dict(
            title="Avg Engagement Rate",
            rangemode='tozero',
            range=[0, y_max],
            tickformat='.1%',
            gridcolor=COLOR_GRID
        ),
        margin=dict(l=20, r=20, t=30, b=30),
        height=360
    )

    return fig


def fig_weekday_performance(
    weekday_df: pd.DataFrame,
    metric: str = "avg_engagement_rate"
) -> go.Figure:
    """
    Weekday bars with metric switch:
    - avg_engagement_rate (with er_ci95 error bars)
    - avg_total_engagement
    Ordered Monday..Sunday. Y-axis starts at 0.
    """
    fig = go.Figure()

    if weekday_df.empty or len(weekday_df) == 0:
        fig.update_layout(template=THEME_TEMPLATE)
        return fig

    is_er = (metric == "avg_engagement_rate")

    if is_er:
        text_labels = [f"{v * 100:.2f}%" for v in weekday_df['avg_engagement_rate']]
        error_y = dict(
            type='data',
            array=weekday_df['er_ci95'],
            visible=True,
            color=COLOR_TEXT_MAIN,
            thickness=1.5,
            width=5
        )
        customdata = weekday_df['er_ci95'].values
        hover = "<b>%{x}</b><br>Avg Engagement Rate: %{y:.2%}<br>95% CI: ±%{customdata:.3%}<extra></extra>"
        y_title = "Avg Engagement Rate"
        tickformat = ".1%"
        max_val = (weekday_df['avg_engagement_rate'] + weekday_df['er_ci95']).max()
        y_range = [0, max(max_val * 1.18, 0.22)]
    else:
        text_labels = [f"{int(v):,}" for v in weekday_df['avg_total_engagement']]
        error_y = None
        customdata = None
        hover = "<b>%{x}</b><br>Avg Total Engagement: %{y:,.0f}<extra></extra>"
        y_title = "Avg Total Engagement"
        tickformat = ",d"
        max_val = weekday_df['avg_total_engagement'].max()
        y_range = [0, max_val * 1.15]

    fig.add_trace(go.Bar(
        x=weekday_df['weekday'],
        y=weekday_df[metric],
        marker_color=ACCENT_PINK,
        text=text_labels,
        textposition='outside',
        cliponaxis=False,
        error_y=error_y,
        customdata=customdata,
        hovertemplate=hover
    ))

    fig.update_layout(
        template=THEME_TEMPLATE,
        font=dict(family=FONT_FAMILY, color=COLOR_TEXT_MAIN),
        xaxis=dict(title="", tickfont=dict(size=11)),
        yaxis=dict(
            title=y_title,
            rangemode='tozero',
            range=y_range,
            tickformat=tickformat,
            gridcolor=COLOR_GRID
        ),
        margin=dict(l=20, r=20, t=30, b=30),
        height=360
    )

    return fig


def fig_hashtag_usage(hashtag_df: pd.DataFrame) -> go.Figure:
    """
    Posts per hashtag bar chart.
    Ordered by avg_engagement_rate descending. Y-axis starts at 0.
    """
    fig = go.Figure()

    if hashtag_df.empty or len(hashtag_df) == 0:
        fig.update_layout(template=THEME_TEMPLATE)
        return fig

    sorted_df = hashtag_df.sort_values('avg_engagement_rate', ascending=False).reset_index(drop=True)
    text_labels = [f"{int(v):,}" for v in sorted_df['posts']]

    fig.add_trace(go.Bar(
        x=sorted_df['hashtag'],
        y=sorted_df['posts'],
        marker_color=ACCENT_PINK,
        text=text_labels,
        textposition='outside',
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Total Posts: %{y:,}<extra></extra>"
    ))

    max_val = sorted_df['posts'].max() if len(sorted_df) > 0 else 1000

    fig.update_layout(
        template=THEME_TEMPLATE,
        font=dict(family=FONT_FAMILY, color=COLOR_TEXT_MAIN),
        xaxis=dict(title="", tickfont=dict(size=11)),
        yaxis=dict(
            title="Total Posts",
            rangemode='tozero',
            range=[0, max_val * 1.15],
            gridcolor=COLOR_GRID
        ),
        margin=dict(l=20, r=20, t=30, b=30),
        height=360
    )

    return fig


def fig_campaign_follows(campaign_df: pd.DataFrame) -> go.Figure:
    """
    Avg follows per post by campaign type.
    Ordered by avg_engagement_rate descending. Y-axis starts at 0.
    """
    fig = go.Figure()

    if campaign_df.empty or len(campaign_df) == 0:
        fig.update_layout(template=THEME_TEMPLATE)
        return fig

    sorted_df = campaign_df.sort_values('avg_engagement_rate', ascending=False).reset_index(drop=True)
    text_labels = [f"{v:.1f}" for v in sorted_df['avg_follows']]

    fig.add_trace(go.Bar(
        x=sorted_df['campaign_type'],
        y=sorted_df['avg_follows'],
        marker_color=ACCENT_PINK,
        text=text_labels,
        textposition='outside',
        cliponaxis=False,
        hovertemplate="<b>%{x}</b><br>Avg Follows: %{y:.1f}<extra></extra>"
    ))

    max_val = sorted_df['avg_follows'].max() if len(sorted_df) > 0 else 100

    fig.update_layout(
        template=THEME_TEMPLATE,
        font=dict(family=FONT_FAMILY, color=COLOR_TEXT_MAIN),
        xaxis=dict(title="", tickfont=dict(size=11)),
        yaxis=dict(
            title="Avg Follows per Post",
            rangemode='tozero',
            range=[0, max_val * 1.15],
            gridcolor=COLOR_GRID
        ),
        margin=dict(l=20, r=20, t=30, b=30),
        height=360
    )

    return fig


def fig_engagement_funnel(funnel_df: pd.DataFrame) -> go.Figure:
    """
    Engagement funnel (go.Funnel):
    Impressions > Reach > Likes > Comments > Shares > Saves.
    Text shows compact count and '% of reach' for stages after Reach.
    """
    fig = go.Figure()

    if funnel_df.empty or len(funnel_df) == 0:
        fig.update_layout(template=THEME_TEMPLATE)
        return fig

    text_labels = []
    for _, r in funnel_df.iterrows():
        cnt_str = _compact_num(r['count'])
        if r['stage'] in ['Impressions', 'Reach']:
            text_labels.append(cnt_str)
        else:
            pct = (r['pct_of_reach'] * 100) if r['pct_of_reach'] is not None else 0.0
            text_labels.append(f"{cnt_str} ({pct:.1f}% of reach)")

    fig.add_trace(go.Funnel(
        y=funnel_df['stage'],
        x=funnel_df['count'],
        text=text_labels,
        textinfo="text",
        marker=dict(color=ACCENT_PINK),
        connector=dict(line=dict(color=MUTED_PINK, width=1.5)),
        hovertemplate="<b>%{y}</b><br>Total Count: %{x:,}<extra></extra>"
    ))

    fig.update_layout(
        template=THEME_TEMPLATE,
        font=dict(family=FONT_FAMILY, color=COLOR_TEXT_MAIN),
        margin=dict(l=20, r=20, t=30, b=30),
        height=380
    )

    return fig


def fig_actions_per_100_reach(funnel_df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar chart for Likes, Comments, Shares, Saves (pct_of_reach * 100).
    X-axis starts at 0.
    """
    fig = go.Figure()

    if funnel_df.empty or len(funnel_df) == 0:
        fig.update_layout(template=THEME_TEMPLATE)
        return fig

    sub = funnel_df[funnel_df['stage'].isin(['Likes', 'Comments', 'Shares', 'Saves'])].iloc[::-1].copy()
    actions_per_100 = sub['pct_of_reach'].apply(lambda x: x * 100 if x is not None else 0.0)
    text_labels = [f"{v:.2f} per 100" for v in actions_per_100]

    fig.add_trace(go.Bar(
        x=actions_per_100,
        y=sub['stage'],
        orientation='h',
        marker_color=ACCENT_PINK,
        text=text_labels,
        textposition='outside',
        cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>Actions per 100 Reached: %{x:.2f}<extra></extra>"
    ))

    max_val = actions_per_100.max() if len(actions_per_100) > 0 else 10
    x_max = max(max_val * 1.25, 1.0)

    fig.update_layout(
        template=THEME_TEMPLATE,
        font=dict(family=FONT_FAMILY, color=COLOR_TEXT_MAIN),
        xaxis=dict(
            title="Actions per 100 Reached Accounts",
            rangemode='tozero',
            range=[0, x_max],
            gridcolor=COLOR_GRID
        ),
        yaxis=dict(title="", tickfont=dict(size=11)),
        margin=dict(l=10, r=40, t=30, b=30),
        height=380
    )

    return fig


def fig_growth_funnel(growth_df: pd.DataFrame) -> go.Figure:
    """
    Growth funnel (go.Funnel):
    Reach > Profile Visits > Follows.
    Text shows compact count and '% of previous stage'.
    """
    fig = go.Figure()

    if growth_df.empty or len(growth_df) == 0:
        fig.update_layout(template=THEME_TEMPLATE)
        return fig

    text_labels = []
    for _, r in growth_df.iterrows():
        cnt_str = _compact_num(r['count'])
        if r['stage'] == 'Reach':
            text_labels.append(cnt_str)
        elif r['stage'] == 'Profile Visits':
            pct = (r['pct_of_previous'] * 100) if r['pct_of_previous'] is not None else 0.0
            text_labels.append(f"{cnt_str} ({pct:.1f}% of reach)")
        elif r['stage'] == 'Follows':
            pct = (r['pct_of_previous'] * 100) if r['pct_of_previous'] is not None else 0.0
            text_labels.append(f"{cnt_str} ({pct:.1f}% of visits)")
        else:
            text_labels.append(cnt_str)

    fig.add_trace(go.Funnel(
        y=growth_df['stage'],
        x=growth_df['count'],
        text=text_labels,
        textinfo="text",
        marker=dict(color=ACCENT_PINK),
        connector=dict(line=dict(color=MUTED_PINK, width=1.5)),
        hovertemplate="<b>%{y}</b><br>Total Count: %{x:,}<extra></extra>"
    ))

    fig.update_layout(
        template=THEME_TEMPLATE,
        font=dict(family=FONT_FAMILY, color=COLOR_TEXT_MAIN),
        margin=dict(l=20, r=20, t=30, b=30),
        height=300
    )

    return fig
