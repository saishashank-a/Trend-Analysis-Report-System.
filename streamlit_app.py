#!/usr/bin/env python3
"""
Streamlit Frontend for App Store Review Trend Analysis
Complete replacement for Flask backend with all features
"""

import os
import json
import uuid
import time
from datetime import datetime, timedelta
from pathlib import Path

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

from google_play_scraper import app as get_app_details

from main import (
    scrape_reviews, extract_all_topics, consolidate_topics,
    map_topics_to_canonical, generate_trend_report, extract_app_id_from_link,
    OUTPUT_DIR
)
from config.cache_db import JobDatabase

# Check if sentiment analysis is enabled
ENABLE_SENTIMENT = os.getenv('ENABLE_SENTIMENT', 'false').lower() == 'true'

# ============================================
# Page Configuration
# ============================================

st.set_page_config(
    page_title="Review Trend Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# Hide Streamlit default elements and apply dark theme matching Flask
st.markdown("""
<style>
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: visible;}
    header [data-testid="stToolbar"] {display: none;}
    header [data-testid="collapsedControl"] {display: block !important;}
    .stDeployButton {display: none;}

    /* Dark theme - matching Flask */
    .stApp {
        background-color: #0a0a0a;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #111111;
        border-right: 1px solid #1a1a1a;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #e5e5e5;
    }

    /* Input fields */
    .stTextInput input, .stSelectbox select, .stDateInput input {
        background-color: #0a0a0a !important;
        border: 1px solid #2a2a2a !important;
        color: #ffffff !important;
        border-radius: 8px !important;
    }

    .stTextInput input:focus, .stSelectbox select:focus {
        border-color: #3a3a3a !important;
        box-shadow: none !important;
    }

    /* Buttons */
    .stButton > button {
        background-color: #ffffff;
        color: #000000;
        border: none;
        border-radius: 8px;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s;
    }

    .stButton > button:hover {
        background-color: #e5e5e5;
        color: #000000;
    }

    .stButton > button[kind="secondary"] {
        background-color: #111111;
        color: #ffffff;
        border: 1px solid #2a2a2a;
    }

    .stButton > button[kind="secondary"]:hover {
        background-color: #1a1a1a;
    }

    /* Cards */
    .metric-card {
        background-color: #111111;
        border: 1px solid #1a1a1a;
        border-radius: 8px;
        padding: 20px;
    }

    .metric-card .value {
        font-size: 1.75rem;
        font-weight: 600;
        color: #ffffff;
    }

    .metric-card .label {
        font-size: 0.75rem;
        color: #888888;
        text-transform: uppercase;
        margin-bottom: 4px;
    }

    /* Progress metrics */
    .progress-metrics {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        margin-top: 12px;
    }

    .metric-card-sm {
        background-color: #111111;
        border: 1px solid #1a1a1a;
        border-radius: 8px;
        padding: 12px;
        flex: 1 1 160px;
        min-width: 160px;
    }

    .metric-card-sm .label {
        font-size: 0.7rem;
        color: #888888;
        text-transform: uppercase;
        margin-bottom: 4px;
        letter-spacing: 0.03em;
    }

    .metric-card-sm .value {
        font-size: 1.1rem;
        font-weight: 600;
        color: #ffffff;
    }

    .phase-metrics {
        margin-top: 12px;
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
    }

    .phase-box {
        background-color: #0f0f0f;
        border: 1px solid #1a1a1a;
        border-radius: 8px;
        padding: 12px;
    }

    .phase-box .title {
        font-size: 0.7rem;
        color: #e5e5e5;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }

    .phase-box .item {
        font-size: 0.85rem;
        color: #888888;
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
    }

    .phase-box .item:last-child {
        margin-bottom: 0;
    }

    /* Progress bar */
    .stProgress > div > div {
        background-color: #3b82f6;
    }

    .stProgress > div {
        background-color: #1a1a1a;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: transparent;
        gap: 0;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #888888;
        border-bottom: 2px solid transparent;
        padding: 10px 20px;
    }

    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #ffffff;
        border-bottom: 2px solid #ffffff;
    }

    /* Dataframe */
    .stDataFrame {
        background-color: #111111;
        border: 1px solid #1a1a1a;
        border-radius: 8px;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: #111111;
        border: 1px solid #1a1a1a;
        border-radius: 8px;
    }

    /* Chat messages */
    .stChatMessage {
        background-color: #111111;
        border: 1px solid #1a1a1a;
    }

    /* Info/Warning/Error boxes */
    .stAlert {
        background-color: #111111;
        border: 1px solid #1a1a1a;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }

    ::-webkit-scrollbar-track {
        background: #1a1a1a;
    }

    ::-webkit-scrollbar-thumb {
        background: #404040;
        border-radius: 4px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #505050;
    }

    /* Phase checklist */
    .phase-item {
        display: flex;
        align-items: center;
        padding: 8px 0;
        color: #666666;
        font-size: 0.9rem;
    }

    .phase-item.active {
        color: #3b82f6;
    }

    .phase-item.completed {
        color: #22c55e;
    }

    /* History item */
    .history-item {
        padding: 12px;
        border-radius: 8px;
        cursor: pointer;
        transition: background-color 0.2s;
        margin-bottom: 4px;
    }

    .history-item:hover {
        background-color: #1a1a1a;
    }

    /* Download button special */
    .download-btn {
        background-color: #111111 !important;
        border: 1px solid #2a2a2a !important;
        color: #ffffff !important;
    }

    /* Status indicator */
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 8px;
    }

    .status-dot.green { background-color: #22c55e; }
    .status-dot.blue { background-color: #3b82f6; }
    .status-dot.red { background-color: #ef4444; }
    .status-dot.gray { background-color: #666666; }

    /* Past conversations panel */
    .past-panel {
        display: flex;
        flex-direction: column;
        gap: 10px;
    }

    .past-item-spacer {
        height: 10px;
    }

    /* Only the past conversations expander scrolls */
    div[data-testid="stExpander"] div[role="region"]:has(> div > div.past-panel-marker) {
        max-height: calc(100vh - 320px);
        overflow-y: auto;
        padding-right: 6px;
    }

    /* Center action icons in past conversation buttons */
    .action-btn .stButton > button {
        width: auto;
        height: auto;
        min-width: 0;
        padding: 0;
        display: grid;
        place-items: center;
        text-align: center;
        line-height: 1;
        font-size: 1.05rem;
        background: transparent;
        border: none;
        box-shadow: none;
    }

    .action-btn .stButton > button span {
        width: 100%;
        height: 100%;
        display: grid;
        place-items: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# Session State
# ============================================

if 'job_db' not in st.session_state:
    st.session_state.job_db = JobDatabase()

if 'current_job_id' not in st.session_state:
    st.session_state.current_job_id = None

if 'job_running' not in st.session_state:
    st.session_state.job_running = False

if 'show_config' not in st.session_state:
    st.session_state.show_config = True


# ============================================
# Helper Functions
# ============================================

def get_app_name(app_id: str) -> str:
    try:
        app_details = get_app_details(app_id, lang='en', country='us')
        return app_details.get('title', app_id.split('.')[-2] if '.' in app_id else app_id)
    except Exception:
        return app_id.split('.')[-2] if '.' in app_id else app_id


def format_time_ago(dt_str: str) -> str:
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        now = datetime.now()
        diff = now - dt.replace(tzinfo=None)
        if diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds >= 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"
    except Exception:
        return ""


def create_line_chart(df: pd.DataFrame) -> go.Figure:
    """Create line chart matching Flask style"""
    fig = go.Figure()

    colors = ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#8b5cf6',
              '#06b6d4', '#ec4899', '#84cc16', '#f43f5e', '#14b8a6']

    for i, col in enumerate(df.columns[1:]):
        fig.add_trace(go.Scatter(
            x=df['Date'], y=df[col],
            mode='lines+markers',
            name=col,
            line=dict(color=colors[i % len(colors)], width=2),
            marker=dict(size=4)
        ))

    fig.update_layout(
        paper_bgcolor='#111111',
        plot_bgcolor='#111111',
        font=dict(color='#888888', size=12),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
            bgcolor='rgba(0,0,0,0)', font=dict(size=10)
        ),
        xaxis=dict(showgrid=True, gridcolor='#1a1a1a', tickfont=dict(color='#888888')),
        yaxis=dict(showgrid=True, gridcolor='#1a1a1a', tickfont=dict(color='#888888')),
        margin=dict(l=40, r=20, t=40, b=40),
        height=350,
        hovermode='x unified'
    )

    return fig


def create_bar_chart(df: pd.DataFrame) -> go.Figure:
    """Create bar chart matching Flask style"""
    fig = go.Figure(go.Bar(
        x=df['Count'],
        y=df['Topic'],
        orientation='h',
        marker=dict(color='#3b82f6')
    ))

    fig.update_layout(
        paper_bgcolor='#111111',
        plot_bgcolor='#111111',
        font=dict(color='#888888', size=12),
        xaxis=dict(showgrid=True, gridcolor='#1a1a1a', tickfont=dict(color='#888888')),
        yaxis=dict(showgrid=False, tickfont=dict(color='#e5e5e5', size=11), categoryorder='total ascending'),
        margin=dict(l=150, r=20, t=20, b=40),
        height=350
    )

    return fig


def check_llm_health():
    """Check the health of the LLM connection"""
    try:
        from config.llm_client import check_llm_status
        return check_llm_status()
    except Exception as e:
        return {'status': 'error', 'message': str(e), 'provider': 'unknown'}


def render_past_conversations(panel_key: str):
    st.markdown('<div class="past-panel">', unsafe_allow_html=True)
    if st.button("+ New Analysis", use_container_width=True, type="secondary", key=f"new_analysis_{panel_key}"):
        st.session_state.show_config = True
        st.session_state.current_job_id = None
        st.session_state.job_running = False
        st.rerun()

    with st.expander("Past Conversations", expanded=True):
        st.markdown('<div class="past-panel-marker"></div>', unsafe_allow_html=True)
        conversations = st.session_state.job_db.get_conversation_summaries(limit=50)
        if conversations:
            for idx, convo in enumerate(conversations):
                job_id = convo.get('job_id')
                app_name = convo.get('app_name') or convo.get('app_id') or "Unknown app"
                status = convo.get('status', 'unknown')
                role = "You" if convo.get('last_role') == 'user' else "Assistant"
                content = (convo.get('last_message') or "").strip().replace("\n", " ")
                snippet = (content[:90] + "...") if len(content) > 90 else content
                subtitle = f"{role}: {snippet}" if snippet else "No messages yet."

                row = st.columns([6, 0.7, 0.7])
                with row[0]:
                    if st.button(f"{app_name}", key=f"open_{panel_key}_{job_id}", use_container_width=True, type="secondary"):
                        st.session_state.current_job_id = job_id
                        st.session_state.show_config = False
                        st.session_state.job_running = False
                        st.rerun()
                    st.caption(f"{subtitle} • {status}")
                with row[1]:
                    if status in ["running", "started"]:
                        st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                        if st.button("⏹", key=f"stop_{panel_key}_{job_id}", use_container_width=False, help="Stop analysis"):
                            st.session_state.job_db.cancel_job(job_id)
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)
                with row[2]:
                    st.markdown('<div class="action-btn">', unsafe_allow_html=True)
                    if st.button("🗑", key=f"del_{panel_key}_{job_id}", use_container_width=False, help="Delete record"):
                        st.session_state.job_db.delete_job(job_id)
                        if st.session_state.current_job_id == job_id:
                            st.session_state.current_job_id = None
                            st.session_state.show_config = True
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

                if idx < len(conversations) - 1:
                    st.markdown('<div class="past-item-spacer"></div>', unsafe_allow_html=True)
        else:
            st.caption("No conversation history yet.")
    st.markdown("</div>", unsafe_allow_html=True)


def prepare_results_data(canonical_counts, canonical_mapping, target_date, days, reviews_by_date=None):
    start_date = target_date - timedelta(days=days - 1)
    date_range = [start_date + timedelta(days=i) for i in range(days)]
    date_strs = [d.strftime("%Y-%m-%d") for d in date_range]
    date_labels = [d.strftime("%b %d") for d in date_range]

    # Check if sentiment data is available
    has_sentiment = reviews_by_date and any(
        'sentiment' in r for reviews in reviews_by_date.values() for r in reviews
    )

    topic_totals = {}
    for date_str in date_strs:
        if date_str in canonical_counts:
            for topic, count in canonical_counts[date_str].items():
                topic_totals[topic] = topic_totals.get(topic, 0) + count

    # Calculate sentiment metrics if available
    sentiment_by_topic = {}
    if has_sentiment:
        all_topics = list(topic_totals.keys())
        for topic in all_topics:
            topic_sentiments = []
            for date_str in date_strs:
                if date_str in canonical_counts and topic in canonical_counts[date_str]:
                    date_reviews = reviews_by_date.get(date_str, [])
                    sentiments = [r['sentiment']['score'] for r in date_reviews if 'sentiment' in r]
                    if sentiments:
                        topic_sentiments.extend(sentiments)
            if topic_sentiments:
                sentiment_by_topic[topic] = sum(topic_sentiments) / len(topic_sentiments)
            else:
                sentiment_by_topic[topic] = 0.0

    sorted_topics = sorted(topic_totals.items(), key=lambda x: x[1], reverse=True)

    # Line chart data (as dict for JSON serialization)
    top_10 = [t for t, _ in sorted_topics[:10]]
    line_chart_data = {'Date': date_labels}
    for topic in top_10:
        line_chart_data[topic] = [canonical_counts.get(d, {}).get(topic, 0) for d in date_strs]

    # Bar chart data (as dict for JSON serialization)
    bar_chart_data = {
        'Topic': [t for t, _ in sorted_topics[:15]],
        'Count': [c for _, c in sorted_topics[:15]]
    }

    # Table data with sentiment if available
    table_data = []
    for t, c in sorted_topics:
        row = {'Topic': t, 'Mentions': c, 'Variations': len(canonical_mapping.get(t, [t]))}
        if has_sentiment and t in sentiment_by_topic:
            row['Sentiment'] = round(sentiment_by_topic[t], 2)
            row['Sentiment Label'] = (
                'Positive' if sentiment_by_topic[t] > 0.3 else
                'Negative' if sentiment_by_topic[t] < -0.3 else
                'Neutral'
            )
        table_data.append(row)

    # Prepare sentiment summary
    sentiment_summary = None
    sentiment_trend_data = None
    if has_sentiment and reviews_by_date:
        all_reviews_flat = [r for reviews in reviews_by_date.values() for r in reviews]
        total = len(all_reviews_flat)
        positive = sum(1 for r in all_reviews_flat if r.get('sentiment', {}).get('score', 0) > 0.3)
        negative = sum(1 for r in all_reviews_flat if r.get('sentiment', {}).get('score', 0) < -0.3)
        neutral = total - positive - negative
        avg_sentiment = sum(r.get('sentiment', {}).get('score', 0) for r in all_reviews_flat) / total if total > 0 else 0

        sentiment_summary = {
            'total': total,
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'positive_pct': round((positive / total * 100) if total > 0 else 0, 1),
            'negative_pct': round((negative / total * 100) if total > 0 else 0, 1),
            'neutral_pct': round((neutral / total * 100) if total > 0 else 0, 1),
            'avg_sentiment': round(avg_sentiment, 2)
        }

        # Sentiment trend by date
        sentiment_by_date = []
        for date_str in date_strs:
            date_reviews = reviews_by_date.get(date_str, [])
            if date_reviews:
                sentiments = [r['sentiment']['score'] for r in date_reviews if 'sentiment' in r]
                avg = sum(sentiments) / len(sentiments) if sentiments else 0
                sentiment_by_date.append(round(avg, 2))
            else:
                sentiment_by_date.append(0)

        sentiment_trend_data = {
            'labels': date_labels,
            'data': sentiment_by_date
        }

    return {
        'line_chart_df': line_chart_data,
        'bar_chart_df': bar_chart_data,
        'table_data': table_data,
        'date_range': f"{date_range[0].strftime('%b %d, %Y')} - {date_range[-1].strftime('%b %d, %Y')}",
        'total_topics': len(sorted_topics),
        'total_reviews': sum(topic_totals.values()),
        'has_sentiment': has_sentiment,
        'sentiment_summary': sentiment_summary,
        'sentiment_trend': sentiment_trend_data
    }


def format_duration(seconds: float) -> str:
    if seconds is None:
        return "N/A"
    seconds = max(0, int(seconds))
    if seconds < 60:
        return f"{seconds}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {sec}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes}m"


def build_progress_html(metrics: dict) -> str:
    completion = metrics.get('completion_pct', 0)
    elapsed = format_duration(metrics.get('elapsed_seconds'))
    eta = format_duration(metrics.get('eta_seconds'))
    reviews_total = metrics.get('reviews_total', 0)
    topics_total = metrics.get('topics_total', 0)
    canonical_topics = metrics.get('canonical_topics', 0)
    extraction_processed = metrics.get('extraction_processed')
    extraction_total = metrics.get('extraction_total')
    parsing_time = format_duration(metrics.get('parsing_seconds'))
    consolidation_time = format_duration(metrics.get('consolidation_seconds'))
    collection_time = format_duration(metrics.get('collection_seconds'))
    sentiment_time = format_duration(metrics.get('sentiment_seconds'))
    sentiment_counts = metrics.get('sentiment_counts')
    unmapped_topics = metrics.get('unmapped_topics')

    extraction_progress = "N/A"
    if extraction_processed is not None and extraction_total:
        extraction_progress = f"{extraction_processed:,}/{extraction_total:,}"

    sentiment_label = "N/A"
    if sentiment_counts:
        sentiment_label = f"{sentiment_counts.get('positive', 0)} / {sentiment_counts.get('neutral', 0)} / {sentiment_counts.get('negative', 0)}"

    return f"""
    <div class="progress-metrics">
        <div class="metric-card-sm">
            <div class="label">Completion</div>
            <div class="value">{completion}%</div>
        </div>
        <div class="metric-card-sm">
            <div class="label">Elapsed</div>
            <div class="value">{elapsed}</div>
        </div>
        <div class="metric-card-sm">
            <div class="label">ETA</div>
            <div class="value">{eta}</div>
        </div>
        <div class="metric-card-sm">
            <div class="label">Reviews Collected</div>
            <div class="value">{reviews_total:,}</div>
        </div>
    </div>
    <div class="phase-metrics">
        <div class="phase-box">
            <div class="title">Topic Extraction</div>
            <div class="item"><span>Parsed Reviews</span><span>{extraction_progress}</span></div>
            <div class="item"><span>Topics Extracted</span><span>{topics_total:,}</span></div>
            <div class="item"><span>Parsing Time</span><span>{parsing_time}</span></div>
        </div>
        <div class="phase-box">
            <div class="title">Topic Consolidation</div>
            <div class="item"><span>Canonical Topics</span><span>{canonical_topics:,}</span></div>
            <div class="item"><span>Unmapped Topics</span><span>{unmapped_topics if unmapped_topics is not None else 'N/A'}</span></div>
            <div class="item"><span>Consolidation Time</span><span>{consolidation_time}</span></div>
        </div>
        <div class="phase-box">
            <div class="title">Data Collection</div>
            <div class="item"><span>Reviews Extracted</span><span>{reviews_total:,}</span></div>
            <div class="item"><span>Collection Time</span><span>{collection_time}</span></div>
        </div>
        <div class="phase-box">
            <div class="title">Sentiment</div>
            <div class="item"><span>Positive / Neutral / Negative</span><span>{sentiment_label}</span></div>
            <div class="item"><span>Sentiment Time</span><span>{sentiment_time}</span></div>
        </div>
    </div>
    """


def run_analysis(app_id: str, days: int, progress_placeholder, phase_placeholder, detail_placeholder):
    """Run analysis with progress updates including sentiment analysis"""
    job_id = str(uuid.uuid4())
    job_db = st.session_state.job_db
    start_time = time.time()
    metrics = {
        'completion_pct': 0,
        'elapsed_seconds': 0,
        'eta_seconds': None,
        'reviews_total': 0,
        'topics_total': 0,
        'canonical_topics': 0,
        'extraction_processed': None,
        'extraction_total': None,
        'parsing_seconds': None,
        'consolidation_seconds': None,
        'collection_seconds': None,
        'sentiment_seconds': None,
        'sentiment_counts': None,
        'unmapped_topics': None
    }

    class JobCancelled(Exception):
        pass

    def check_cancelled():
        job = job_db.get_job(job_id)
        return job and job.get('status') == 'cancelled'

    def update_progress(pct: int, message: str, updates: dict = None):
        progress_placeholder.progress(pct, text=message)
        if updates:
            metrics.update(updates)
        metrics['completion_pct'] = pct
        metrics['elapsed_seconds'] = time.time() - start_time
        if pct > 0:
            metrics['eta_seconds'] = metrics['elapsed_seconds'] * (100 - pct) / pct
        detail_placeholder.markdown(build_progress_html(metrics), unsafe_allow_html=True)
        if check_cancelled():
            raise JobCancelled()

    # Use custom dates from session state if available, otherwise calculate from days
    if 'end_date' in st.session_state and 'start_date' in st.session_state:
        end_date = datetime.combine(st.session_state.end_date, datetime.min.time())
        start_date = datetime.combine(st.session_state.start_date, datetime.min.time())
        days = (end_date - start_date).days + 1
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days - 1)

    app_name = get_app_name(app_id)

    job_db.create_job({
        'job_id': job_id, 'status': 'running', 'phase': 'Initializing',
        'message': 'Starting analysis...',
        'app_id': app_id, 'app_name': app_name,
        'target_date': end_date.isoformat(), 'days': days
    })

    st.session_state.current_job_id = job_id
    st.session_state.job_running = True

    # Dynamic phases based on sentiment setting
    if ENABLE_SENTIMENT:
        phases = ['Data Collection', 'Sentiment Analysis', 'Topic Extraction', 'Topic Consolidation', 'Trend Analysis', 'Report Generation']
    else:
        phases = ['Data Collection', 'Topic Extraction', 'Topic Consolidation', 'Trend Analysis', 'Report Generation']

    def update_phases(current_idx):
        html = ""
        for i, phase in enumerate(phases):
            if i < current_idx:
                html += f'<div class="phase-item completed">✓ {phase}</div>'
            elif i == current_idx:
                html += f'<div class="phase-item active">● {phase}</div>'
            else:
                html += f'<div class="phase-item">○ {phase}</div>'
        phase_placeholder.markdown(html, unsafe_allow_html=True)

    try:
        phase_idx = 0

        # Phase 1: Data Collection
        update_phases(phase_idx)
        collection_start = time.time()
        update_progress(10, "Collecting reviews...")
        reviews_by_date = scrape_reviews(app_id, start_date, end_date)
        total_reviews = sum(len(r) for r in reviews_by_date.values())
        update_progress(20, f"Found {total_reviews:,} reviews", {
            'reviews_total': total_reviews,
            'collection_seconds': time.time() - collection_start
        })
        phase_idx += 1

        # Phase 1b: Sentiment Analysis (if enabled)
        if ENABLE_SENTIMENT and total_reviews > 0:
            update_phases(phase_idx)
            sentiment_start = time.time()
            update_progress(25, "Analyzing sentiment...")
            try:
                from utils.sentiment_analyzer import SentimentAnalyzer
                analyzer = SentimentAnalyzer(method='rating')

                processed = 0
                for date_str in reviews_by_date:
                    for review in reviews_by_date[date_str]:
                        sentiment = analyzer.analyze_review_sentiment(review)
                        review['sentiment'] = sentiment
                        processed += 1

                positive = sum(1 for d in reviews_by_date.values() for r in d if r.get('sentiment', {}).get('score', 0) > 0.3)
                negative = sum(1 for d in reviews_by_date.values() for r in d if r.get('sentiment', {}).get('score', 0) < -0.3)
                neutral = processed - positive - negative

                update_progress(28, f"Sentiment: {positive} positive, {neutral} neutral, {negative} negative", {
                    'sentiment_seconds': time.time() - sentiment_start,
                    'sentiment_counts': {
                        'positive': positive,
                        'neutral': neutral,
                        'negative': negative
                    }
                })
            except Exception as e:
                update_progress(28, f"Sentiment analysis skipped: {str(e)[:50]}", {
                    'sentiment_seconds': time.time() - sentiment_start
                })
            phase_idx += 1

        # Phase 2: Topic Extraction
        update_phases(phase_idx)
        extraction_start = time.time()
        update_progress(30, "Extracting topics...")

        def callback(processed, total):
            pct = 30 + int((processed / total) * 30)
            update_progress(pct, f"Extracting topics ({processed:,}/{total:,})...", {
                'extraction_processed': processed,
                'extraction_total': total,
                'parsing_seconds': time.time() - extraction_start
            })

        topics_by_date = extract_all_topics(reviews_by_date, progress_callback=callback)
        total_topics = sum(len(t) for t in topics_by_date.values())
        update_progress(60, f"Extracted {total_topics:,} topics", {
            'topics_total': total_topics,
            'parsing_seconds': time.time() - extraction_start
        })
        phase_idx += 1

        # Phase 3: Topic Consolidation
        update_phases(phase_idx)
        consolidation_start = time.time()
        update_progress(65, "Consolidating topics...")
        all_topics = [t for topics in topics_by_date.values() for t in topics]
        canonical_mapping = consolidate_topics(all_topics, app_id=app_id)
        update_progress(75, f"Consolidated to {len(canonical_mapping):,} topics", {
            'canonical_topics': len(canonical_mapping),
            'consolidation_seconds': time.time() - consolidation_start
        })
        phase_idx += 1

        # Phase 4: Trend Analysis
        update_phases(phase_idx)
        update_progress(80, "Analyzing trends...")
        canonical_counts, unmapped = map_topics_to_canonical(topics_by_date, canonical_mapping, app_id=app_id)
        update_progress(82, "Analyzing trends...", {
            'unmapped_topics': len(unmapped) if unmapped else 0
        })
        phase_idx += 1

        # Phase 5: Report Generation
        update_phases(phase_idx)
        update_progress(90, "Generating report...")

        safe_name = "".join(c for c in app_name if c.isalnum() or c in ' -_').strip().replace(' ', '_')
        output_file = OUTPUT_DIR / f"{safe_name}_trend_report_{end_date.strftime('%Y-%m-%d')}.xlsx"
        generate_trend_report(canonical_counts, end_date, str(output_file), canonical_mapping, unmapped, reviews_by_date)

        results = prepare_results_data(canonical_counts, canonical_mapping, end_date, days, reviews_by_date)

        job_db.update_job(job_id, {
            'status': 'completed', 'phase': 'Complete', 'progress_pct': 100,
            'result_file': str(output_file),
            'results_data': json.dumps(results, default=str),
            'completed_at': datetime.now().isoformat()
        })

        update_phases(len(phases))
        update_progress(100, "Analysis complete!")
        st.session_state.job_running = False
        st.session_state.show_config = False

        return job_id, results, str(output_file)

    except JobCancelled:
        job_db.update_job(job_id, {
            'status': 'cancelled',
            'phase': 'Cancelled',
            'progress_pct': metrics.get('completion_pct', 0),
            'cancelled_at': datetime.now().isoformat()
        })
        st.session_state.job_running = False
        return None, None, None
    except Exception as e:
        job_db.update_job(job_id, {'status': 'failed', 'error': str(e)})
        st.session_state.job_running = False
        raise e


# ============================================
# Sidebar
# ============================================

with st.sidebar:
    # New Analysis Button
    if st.button("+ New Analysis", use_container_width=True, type="secondary"):
        st.session_state.show_config = True
        st.session_state.current_job_id = None
        st.rerun()

    st.markdown("---")

    # Search
    search = st.text_input("Search history...", label_visibility="collapsed", placeholder="Search history...")

    # History List
    jobs = st.session_state.job_db.get_job_history(limit=20)
    if search:
        jobs = [j for j in jobs if search.lower() in j.get('app_name', '').lower() or search.lower() in j.get('app_id', '').lower()]

    if jobs:
        for job in jobs:
            status = job.get('status', '')
            icon = {'completed': '✓', 'running': '●', 'failed': '✗', 'cancelled': '⊘'}.get(status, '○')
            name = job.get('app_name', job.get('app_id', 'Unknown'))[:20]
            time_ago = format_time_ago(job.get('created_at'))

            col1, col2 = st.columns([5, 2])
            with col1:
                if st.button(f"{icon} {name}", key=f"h_{job['job_id']}", use_container_width=True, type="secondary"):
                    st.session_state.current_job_id = job['job_id']
                    st.session_state.show_config = False
                    st.rerun()
            with col2:
                st.caption(time_ago)
    else:
        st.markdown("<div style='text-align:center;color:#666;padding:20px;'>No history yet</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Past conversations
    with st.expander("Past conversations", expanded=False):
        render_past_conversations("fallback")

    st.markdown("---")

    # LLM Health Check
    llm_health = check_llm_health()
    if llm_health['status'] == 'ok':
        status_dot = 'green'
        status_text = 'Ollama Connected'
    elif llm_health['status'] == 'warning':
        status_dot = 'blue'
        status_text = 'Ollama Warning'
    else:
        status_dot = 'red'
        status_text = 'Ollama Disconnected'

    st.markdown(f"""
    <div style="text-align:center;font-size:0.75rem;color:#666;">
        <div style="display:flex;align-items:center;justify-content:center;gap:8px;margin-bottom:4px;">
            <span class="status-dot {status_dot}"></span>
            <span>{status_text}</span>
        </div>
        <div>Powered by {llm_health.get('provider', 'Ollama')}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================
# Main Content
# ============================================

# Header
st.markdown("### Review Trend Analysis")

# Show configuration panel or results
if st.session_state.show_config and not st.session_state.job_running:
    # Configuration Panel
    left_col, main_col = st.columns([1, 3])
    with left_col:
        render_past_conversations("config")
    with main_col:
        st.markdown("## Start a New Analysis")
        st.caption("Analyze Google Play Store reviews and identify trending topics")

        app_id_input = st.text_input(
            "App Package ID or Play Store Link",
            value="in.swiggy.android",
            placeholder="in.swiggy.android"
        )

        # Date selection method
        date_method = st.radio(
            "Date Selection",
            options=["Quick Select", "Custom Date Range"],
            horizontal=True,
            label_visibility="collapsed"
        )

        if date_method == "Quick Select":
            days_options = {
                "Last 7 days": 7,
                "Last 14 days": 14,
                "Last 30 days": 30,
                "Last 60 days": 60,
                "Last 90 days": 90
            }

            selected_period = st.selectbox(
                "Quick Select Period",
                options=list(days_options.keys()),
                index=2  # Default to 30 days
            )

            days = days_options[selected_period]
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days - 1)
        else:
            # Custom date range
            col_start, col_end = st.columns(2)
            with col_start:
                start_date = st.date_input(
                    "Start Date",
                    value=datetime.now().date() - timedelta(days=29),
                    max_value=datetime.now().date()
                )
            with col_end:
                end_date = st.date_input(
                    "End Date",
                    value=datetime.now().date(),
                    max_value=datetime.now().date()
                )

            # Calculate days from date range
            if start_date > end_date:
                st.error("Start date must be before end date")
                days = 0
            else:
                days = (end_date - start_date).days + 1
                if days > 365:
                    st.warning("Date range cannot exceed 365 days")
                    days = 0

        st.markdown("")

        # Show selected date range
        if days > 0:
            st.caption(f"📅 Analyzing: {start_date.strftime('%b %d, %Y')} → {end_date.strftime('%b %d, %Y')} ({days} days)")

        st.markdown("")

        if st.button("⚡ Start Analysis", use_container_width=True, type="primary", disabled=(days == 0)):
            app_id = extract_app_id_from_link(app_id_input)
            if app_id:
                st.session_state.app_id_input = app_id_input
                st.session_state.days = days
                st.session_state.start_date = start_date
                st.session_state.end_date = end_date
                st.session_state.job_running = True
                st.rerun()

elif st.session_state.job_running:
    # Progress Panel
    left_col, main_col = st.columns([1, 3])
    with left_col:
        render_past_conversations("running")
    with main_col:
        st.markdown("### ⚡ Analysis in Progress")

        progress_placeholder = st.empty()
        phase_placeholder = st.empty()
        detail_placeholder = st.empty()

        # Get form values from session or use defaults
        app_id_input = st.session_state.get('app_id_input', 'in.swiggy.android')
        days = st.session_state.get('days', 30)

        app_id = extract_app_id_from_link(app_id_input)
        if app_id:
            try:
                job_id, results, output_file = run_analysis(
                    app_id,
                    days,
                    progress_placeholder,
                    phase_placeholder,
                    detail_placeholder
                )
                if job_id is None:
                    st.warning("Analysis cancelled.")
                else:
                    st.success("Analysis complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Analysis failed: {str(e)}")
                st.session_state.job_running = False

elif st.session_state.current_job_id:
    # Results Panel
    job = st.session_state.job_db.get_job(st.session_state.current_job_id)

    if job and job.get('status') == 'completed':
        results = job.get('results_data')
        if isinstance(results, str):
            results = json.loads(results)

        left_col, main_col = st.columns([1, 3])
        with left_col:
            render_past_conversations("results")
        with main_col:
            # Header with job actions
            col1, col2, col3 = st.columns([4, 1, 1])
            with col1:
                st.markdown(f"#### {job.get('app_name', 'Analysis Results')}")
            with col2:
                if st.button("🔄 Re-run", type="secondary", use_container_width=True):
                    # Create new job with same parameters
                    st.session_state.app_id_input = job.get('app_id')
                    st.session_state.days = job.get('days', 30)
                    st.session_state.job_running = True
                    st.rerun()
            with col3:
                if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                    st.session_state.job_db.delete_job(st.session_state.current_job_id)
                    st.session_state.current_job_id = None
                    st.session_state.show_config = True
                    st.rerun()

            # Summary Cards
            if results.get('has_sentiment') and results.get('sentiment_summary'):
                # 4 cards with sentiment
                col1, col2, col3, col4 = st.columns(4)
                sentiment = results['sentiment_summary']
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label">Total Reviews</div>
                        <div class="value">{results.get('total_reviews', 0):,}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label">Topics Identified</div>
                        <div class="value">{results.get('total_topics', 0)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    avg_sent = sentiment.get('avg_sentiment', 0)
                    sent_color = '#22c55e' if avg_sent > 0.3 else '#ef4444' if avg_sent < -0.3 else '#888888'
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label">Avg Sentiment</div>
                        <div class="value" style="color:{sent_color};">{avg_sent:+.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label">Positive / Negative</div>
                        <div class="value" style="font-size:1.2rem;">
                            <span style="color:#22c55e">{sentiment.get('positive_pct', 0)}%</span> /
                            <span style="color:#ef4444">{sentiment.get('negative_pct', 0)}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                # 3 cards without sentiment
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label">Total Reviews</div>
                        <div class="value">{results.get('total_reviews', 0):,}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label">Topics Identified</div>
                        <div class="value">{results.get('total_topics', 0)}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div class="label">Date Range</div>
                        <div class="value" style="font-size:1.1rem;">{results.get('date_range', 'N/A')}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Download Button
            if job.get('result_file') and os.path.exists(job['result_file']):
                with open(job['result_file'], 'rb') as f:
                    st.download_button(
                        "📥 Download Excel Report",
                        f,
                        file_name=os.path.basename(job['result_file']),
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        type="secondary"
                    )

            st.markdown("<br>", unsafe_allow_html=True)

            # Sentiment Trend Chart (if available)
            if results.get('has_sentiment') and results.get('sentiment_trend'):
                st.markdown("#### Sentiment Over Time")
                sentiment_data = results['sentiment_trend']
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=sentiment_data['labels'],
                    y=sentiment_data['data'],
                    mode='lines+markers',
                    name='Sentiment',
                    line=dict(color='#8b5cf6', width=2),
                    marker=dict(size=6),
                    fill='tozeroy',
                    fillcolor='rgba(139, 92, 246, 0.1)'
                ))
                fig.add_hline(y=0, line_dash="dash", line_color="#666666")
                fig.update_layout(
                    paper_bgcolor='#111111',
                    plot_bgcolor='#111111',
                    font=dict(color='#888888', size=12),
                    xaxis=dict(showgrid=True, gridcolor='#1a1a1a', tickfont=dict(color='#888888')),
                    yaxis=dict(showgrid=True, gridcolor='#1a1a1a', tickfont=dict(color='#888888'), range=[-1.1, 1.1]),
                    margin=dict(l=40, r=20, t=20, b=40),
                    height=250,
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
                st.markdown("<br>", unsafe_allow_html=True)

            # Charts
            st.markdown("#### Topic Trends Over Time")

            if 'line_chart_df' in results:
                df = pd.DataFrame(results['line_chart_df'])
                if len(df.columns) > 1:
                    fig = create_line_chart(df)
                    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### Top Topics by Frequency")

            if 'bar_chart_df' in results:
                df = pd.DataFrame(results['bar_chart_df'])
                fig = create_bar_chart(df)
                st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

            st.markdown("<br>", unsafe_allow_html=True)

            # Topics Table
            st.markdown("#### All Topics")

            if 'table_data' in results:
                df = pd.DataFrame(results['table_data'])
                search = st.text_input("Search topics...", key="topic_search", label_visibility="collapsed", placeholder="Search topics...")
                if search:
                    df = df[df['Topic'].str.lower().str.contains(search.lower())]

                # Build column config based on available columns
                column_config = {
                    "Topic": st.column_config.TextColumn("Topic", width="large"),
                    "Mentions": st.column_config.NumberColumn("Mentions", format="%d"),
                    "Variations": st.column_config.NumberColumn("Variations", format="%d")
                }
                if 'Sentiment' in df.columns:
                    column_config["Sentiment"] = st.column_config.NumberColumn("Sentiment", format="%.2f")
                    column_config["Sentiment Label"] = st.column_config.TextColumn("Sentiment Label")

                st.dataframe(
                    df,
                    use_container_width=True,
                    height=400,
                    column_config=column_config,
                    hide_index=True
                )

            st.markdown("<br>", unsafe_allow_html=True)

            # Chat Interface
            st.markdown("#### Ask About Results")

            chat_history = st.session_state.job_db.get_chat_history(st.session_state.current_job_id)
            for msg in chat_history:
                with st.chat_message(msg['role']):
                    st.write(msg['content'])

            # Quick questions
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Top trends", type="secondary", use_container_width=True):
                    st.session_state.quick_q = "What are the top 3 trending topics?"
            with col2:
                if st.button("Declining topics", type="secondary", use_container_width=True):
                    st.session_state.quick_q = "Which topics are declining?"
            with col3:
                if st.button("Main issues", type="secondary", use_container_width=True):
                    st.session_state.quick_q = "Summarize the main issues"

            prompt = st.chat_input("Ask a question about the trends...")

            if prompt or st.session_state.get('quick_q'):
                question = prompt or st.session_state.pop('quick_q', None)
                if question:
                    with st.chat_message("user"):
                        st.write(question)
                    st.session_state.job_db.save_chat_message(st.session_state.current_job_id, 'user', question)

                    with st.chat_message("assistant"):
                        with st.spinner("Thinking..."):
                            try:
                                from config.llm_client import get_llm_client
                                llm = get_llm_client()
                                context = f"Analysis for {job.get('app_name')}: {results.get('total_topics')} topics from {results.get('total_reviews')} reviews. Top topics: {', '.join([t['Topic'] for t in results.get('table_data', [])[:5]])}"
                                response = llm.chat(f"{context}\n\nQuestion: {question}\n\nAnswer:", max_tokens=400)
                                st.write(response)
                                st.session_state.job_db.save_chat_message(st.session_state.current_job_id, 'assistant', response)
                            except Exception as e:
                                st.error(f"Error: {e}")

    elif job and job.get('status') == 'failed':
        st.error(f"Analysis failed: {job.get('error', 'Unknown error')}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Retry", type="primary", use_container_width=True):
                # Retry with same parameters
                st.session_state.app_id_input = job.get('app_id')
                st.session_state.days = job.get('days', 30)
                st.session_state.job_running = True
                st.rerun()
        with col2:
            if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                st.session_state.job_db.delete_job(st.session_state.current_job_id)
                st.session_state.current_job_id = None
                st.session_state.show_config = True
                st.rerun()

    elif job and job.get('status') == 'cancelled':
        st.warning(f"Analysis was cancelled")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Retry", type="primary", use_container_width=True):
                st.session_state.app_id_input = job.get('app_id')
                st.session_state.days = job.get('days', 30)
                st.session_state.job_running = True
                st.rerun()
        with col2:
            if st.button("🗑️ Delete", type="secondary", use_container_width=True):
                st.session_state.job_db.delete_job(st.session_state.current_job_id)
                st.session_state.current_job_id = None
                st.session_state.show_config = True
                st.rerun()

    elif job and job.get('status') in ['running', 'started']:
        st.info(f"Analysis in progress: {job.get('phase', 'Processing')}...")
        st.progress(job.get('progress_pct', 0) / 100)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", type="secondary", use_container_width=True):
                st.rerun()
        with col2:
            if st.button("⏹️ Cancel", type="secondary", use_container_width=True):
                st.session_state.job_db.cancel_job(st.session_state.current_job_id)
                st.rerun()

    else:
        st.warning("Job not found")
        if st.button("Start New Analysis"):
            st.session_state.show_config = True
            st.session_state.current_job_id = None
            st.rerun()

else:
    # Default: show config
    st.session_state.show_config = True
    st.rerun()
