import plotly.graph_objects as go
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


def fig_monthly_trend(monthly_df: pd.DataFrame, metric: str = "posts") -> go.Figure:
    """
    Line chart with markers over month_label, in chronological order.
    metric is 'posts' or 'posts_per_day'.
    Partial months (is_partial_month == True) get open markers and a dotted line segment,
    with legend entries distinguishing full and partial tracking months.
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

    # Ensure sorted by month
    sorted_df = monthly_df.sort_values('month').reset_index(drop=True)
    y_col = metric
    y_title = "Total Posts" if metric == "posts" else "Posts per Day (Active Days)"
    val_format = ",d" if metric == "posts" else ".1f"

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
    Hover shows reach, engagement_rate, post_type and campaign_type.
    When percent=True show values with two decimals (e.g. 34.10%).
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

    # Reverse order so highest rank appears at the top in horizontal orientation
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

    # Add extra margin on x-axis so outside labels are not cut off
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
