#!/usr/bin/env python3
"""
Flask Backend API for Swiggy App Store Review Trend Analysis
Provides REST API endpoints for the web dashboard
"""

import os
import json
import uuid
import threading
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from main import (
    scrape_reviews, extract_all_topics, consolidate_topics,
    map_topics_to_canonical, generate_trend_report, extract_app_id_from_link,
    SWIGGY_APP_ID, OUTPUT_DIR
)
from config.cache_db import JobDatabase

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

# Initialize persistent job database
job_db = JobDatabase()

# Cancellation flags for active jobs
cancel_flags = {}
cancel_flags_lock = threading.Lock()


def is_job_cancelled(job_id: str) -> bool:
    """Check if job has been cancelled"""
    with cancel_flags_lock:
        if job_id in cancel_flags:
            return cancel_flags[job_id].is_set()
    return False


def update_job_progress(job_id, phase, progress_pct, message, status="running", metrics=None):
    """
    Update job progress in database

    Args:
        metrics (dict, optional): Additional progress metrics like:
            - processed: int - items processed so far
            - total: int - total items to process
    """
    updates = {
        'status': status,
        'phase': phase,
        'progress_pct': progress_pct,
        'message': message
    }

    # Add metrics if provided
    if metrics:
        updates['metrics'] = json.dumps(metrics)

    # Add completion timestamp if completed
    if status == 'completed':
        updates['completed_at'] = datetime.now().isoformat()
    elif status == 'failed':
        updates['error'] = message

    job_db.update_job(job_id, updates)


def run_analysis_job(job_id, app_id, target_date, days):
    """
    Background job that runs the analysis pipeline
    Updates job state at each phase
    """
    try:
        # Phase 1: Data Collection
        update_job_progress(job_id, 'Data Collection', 10, 'Starting data collection...')

        end_date = target_date
        start_date = target_date - timedelta(days=days - 1)

        reviews_by_date = scrape_reviews(app_id, start_date, end_date)
        total_reviews = sum(len(reviews) for reviews in reviews_by_date.values())

        update_job_progress(
            job_id,
            'Data Collection',
            20,
            f'Found {total_reviews:,} reviews',
            metrics={'total': total_reviews, 'processed': total_reviews}
        )

        # Phase 2: Topic Extraction
        update_job_progress(job_id, 'Topic Extraction', 30, 'Extracting topics from reviews...')

        topics_by_date = extract_all_topics(
            reviews_by_date,
            progress_callback=lambda processed, total: update_job_progress(
                job_id,
                'Topic Extraction',
                30 + int((processed / total) * 20),  # 30-50%
                f'Extracting topics from {processed:,}/{total:,} reviews...',
                metrics={'processed': processed, 'total': total}
            )
        )
        total_topics = sum(len(topics) for topics in topics_by_date.values())

        update_job_progress(
            job_id,
            'Topic Extraction',
            50,
            f'Extracted {total_topics:,} topics',
            metrics={'total': total_topics}
        )

        # Phase 3: Topic Consolidation
        all_extracted_topics = []
        for topics in topics_by_date.values():
            all_extracted_topics.extend(topics)

        unique_count = len(set(all_extracted_topics))

        update_job_progress(
            job_id,
            'Topic Consolidation',
            60,
            f'Consolidating {unique_count:,} unique topics...',
            metrics={'total': unique_count}
        )

        canonical_mapping = consolidate_topics(all_extracted_topics)

        update_job_progress(
            job_id,
            'Topic Consolidation',
            75,
            f'Consolidated to {len(canonical_mapping):,} canonical topics',
            metrics={'processed': len(canonical_mapping), 'total': unique_count}
        )

        # Phase 4: Trend Analysis
        update_job_progress(job_id, 'Trend Analysis', 80, 'Analyzing trends...')

        canonical_counts, unmapped_topics = map_topics_to_canonical(topics_by_date, canonical_mapping)

        update_job_progress(job_id, 'Trend Analysis', 85, 'Trend analysis complete')

        # Phase 5: Report Generation
        update_job_progress(job_id, 'Report Generation', 90, 'Generating Excel report...')

        # Generate output filename
        app_name = app_id.split('.')[-2] if '.' in app_id else app_id
        output_file = OUTPUT_DIR / f"{app_name}_trend_report_{target_date.strftime('%Y-%m-%d')}.xlsx"

        generate_trend_report(canonical_counts, target_date, str(output_file), canonical_mapping, unmapped_topics)

        # Prepare results data for charts
        results_data = prepare_results_data(canonical_counts, canonical_mapping, target_date, days)

        # Mark job as complete in database
        job_db.update_job(job_id, {
            'status': 'completed',
            'phase': 'Complete',
            'progress_pct': 100,
            'message': 'Analysis complete!',
            'result_file': str(output_file),
            'results_data': json.dumps(results_data),
            'completed_at': datetime.now().isoformat()
            })

    except Exception as e:
        # Check if it was cancelled
        error_msg = str(e)
        if is_job_cancelled(job_id) or "cancelled" in error_msg.lower():
            status = 'cancelled'
            phase = 'Cancelled'
        else:
            status = 'failed'
            phase = 'Error'

        # Mark job as failed or cancelled in database
        job_db.update_job(job_id, {
            'status': status,
            'phase': phase,
            'progress_pct': 0,
            'message': error_msg,
            'error': error_msg
        })
    finally:
        # Cleanup cancellation flag
        with cancel_flags_lock:
            if job_id in cancel_flags:
                del cancel_flags[job_id]


def prepare_results_data(canonical_counts, canonical_mapping, target_date, days):
    """
    Prepare JSON data for frontend charts
    """
    # Calculate date range
    start_date = target_date - timedelta(days=days - 1)
    date_range = [start_date + timedelta(days=i) for i in range(days)]
    date_strs = [d.strftime("%Y-%m-%d") for d in date_range]
    date_labels = [d.strftime("%b %d") for d in date_range]

    # Collect all topics and their total counts
    topic_totals = {}
    for date_str in date_strs:
        if date_str in canonical_counts:
            for topic, count in canonical_counts[date_str].items():
                topic_totals[topic] = topic_totals.get(topic, 0) + count

    # Sort topics by frequency
    sorted_topics = sorted(topic_totals.items(), key=lambda x: x[1], reverse=True)

    # Top 10 topics for line chart
    top_10_topics = [topic for topic, _ in sorted_topics[:10]]

    # Prepare line chart data
    line_chart_data = {
        'labels': date_labels,
        'datasets': []
    }

    # Color palette for lines
    colors = [
        'rgb(59, 130, 246)',   # blue
        'rgb(239, 68, 68)',    # red
        'rgb(34, 197, 94)',    # green
        'rgb(251, 146, 60)',   # orange
        'rgb(168, 85, 247)',   # purple
        'rgb(236, 72, 153)',   # pink
        'rgb(14, 165, 233)',   # cyan
        'rgb(234, 179, 8)',    # yellow
        'rgb(20, 184, 166)',   # teal
        'rgb(244, 63, 94)',    # rose
    ]

    for idx, topic in enumerate(top_10_topics):
        data = []
        for date_str in date_strs:
            count = canonical_counts.get(date_str, {}).get(topic, 0)
            data.append(count)

        line_chart_data['datasets'].append({
            'label': topic,
            'data': data,
            'borderColor': colors[idx % len(colors)],
            'backgroundColor': colors[idx % len(colors)].replace('rgb', 'rgba').replace(')', ', 0.1)'),
            'tension': 0.3
        })

    # Top 15 topics for bar chart
    top_15_topics = sorted_topics[:15]
    bar_chart_data = {
        'labels': [topic for topic, _ in top_15_topics],
        'datasets': [{
            'label': 'Total Mentions',
            'data': [count for _, count in top_15_topics],
            'backgroundColor': 'rgba(59, 130, 246, 0.8)',
            'borderColor': 'rgb(59, 130, 246)',
            'borderWidth': 1
        }]
    }

    # All topics for table
    all_topics_table = [
        {
            'topic': topic,
            'total_count': count,
            'variation_count': len(canonical_mapping.get(topic, [topic]))
        }
        for topic, count in sorted_topics
    ]

    return {
        'line_chart': line_chart_data,
        'bar_chart': bar_chart_data,
        'topics_table': all_topics_table,
        'summary': {
            'total_reviews': sum(sum(canonical_counts.get(d, {}).values()) for d in date_strs),
            'total_topics': len(sorted_topics),
            'date_range': f"{date_range[0].strftime('%b %d, %Y')} - {date_range[-1].strftime('%b %d, %Y')}"
        }
    }


# ============================================
# API Routes
# ============================================

@app.route('/')
def index():
    """Serve the main dashboard"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    """
    Start a new analysis job

    Request body:
    {
        "app_id": "in.swiggy.android" or "Play Store URL",
        "target_date": "2025-12-24" (optional, defaults to today),
        "days": 30 (optional, defaults to 30)
    }
    """
    try:
        data = request.get_json()

        # Extract and validate app ID
        app_id_input = data.get('app_id', SWIGGY_APP_ID)
        app_id = extract_app_id_from_link(app_id_input) if app_id_input else SWIGGY_APP_ID

        # Parse target date
        target_date_str = data.get('target_date')
        if target_date_str:
            target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
        else:
            target_date = datetime.now()

        # Get days parameter
        days = int(data.get('days', 30))
        if days < 1 or days > 90:
            return jsonify({'error': 'Days must be between 1 and 90'}), 400

        # Create job
        job_id = str(uuid.uuid4())

        # Create job in database
        job_db.create_job({
            'job_id': job_id,
            'status': 'started',
            'phase': 'Initializing',
            'message': 'Starting analysis...',
            'app_id': app_id,
            'app_name': data.get('app_name'),  # Optional app name
            'target_date': target_date.isoformat(),
            'days': days
        })

        # Register cancellation flag
        with cancel_flags_lock:
            cancel_flags[job_id] = threading.Event()

        # Start background job
        thread = threading.Thread(
            target=run_analysis_job,
            args=(job_id, app_id, target_date, days),
            daemon=True
        )
        thread.start()

        return jsonify({
            'job_id': job_id,
            'status': 'started',
            'message': 'Analysis job started successfully'
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get the current status of a job"""
    job = job_db.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    # Remove large data from status response
    if 'results_data' in job:
        job.pop('results_data')

    return jsonify(job)


@app.route('/api/results/<job_id>', methods=['GET'])
def get_job_results(job_id):
    """Get the results data for charts"""
    job = job_db.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed yet'}), 400

    if 'results_data' not in job or not job['results_data']:
        return jsonify({'error': 'Results data not available'}), 404

    return jsonify(job['results_data'])


@app.route('/api/download/<job_id>', methods=['GET'])
def download_report(job_id):
    """Download the Excel report for a completed job"""
    job = job_db.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404

    if job['status'] != 'completed':
        return jsonify({'error': 'Job not completed yet'}), 400

    if 'result_file' not in job or not job['result_file']:
        return jsonify({'error': 'Result file not available'}), 404

    result_file = job['result_file']

    if not os.path.exists(result_file):
        return jsonify({'error': 'Result file not found on disk'}), 404

    return send_file(
        result_file,
            as_attachment=True,
            download_name=os.path.basename(result_file),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )


@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List all jobs (for debugging/admin)"""
    jobs_list = job_db.get_job_history(limit=100)
    # Remove large data
    for job in jobs_list:
        if 'results_data' in job:
            job.pop('results_data')
    return jsonify({'jobs': jobs_list})


@app.route('/api/history', methods=['GET'])
def get_job_history():
    """Get job history"""
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    status = request.args.get('status')  # Optional filter by status

    history = job_db.get_job_history(limit, offset, status)
    return jsonify({
        'jobs': history,
        'limit': limit,
        'offset': offset
    })


@app.route('/api/job/<job_id>', methods=['GET'])
def get_job_details(job_id):
    """Get full job details including results"""
    job = job_db.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify(job)


@app.route('/api/cancel/<job_id>', methods=['POST'])
def cancel_job(job_id):
    """Cancel a running job"""
    # Mark in database
    job_db.cancel_job(job_id)

    # Set cancellation flag
    with cancel_flags_lock:
        if job_id in cancel_flags:
            cancel_flags[job_id].set()
            return jsonify({'success': True, 'message': 'Job cancellation requested'})
        else:
            # Job might already be completed or not found
            return jsonify({'success': True, 'message': 'Job marked as cancelled'})


@app.route('/api/delete/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job from history"""
    try:
        job = job_db.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404

        # Don't allow deleting running jobs
        if job['status'] in ['running', 'started']:
            return jsonify({'error': 'Cannot delete a running job. Cancel it first.'}), 400

        job_db.delete_job(job_id)
        return jsonify({'success': True, 'message': 'Job deleted successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat/<job_id>', methods=['POST'])
def chat_with_results(job_id):
    """Answer questions about analysis results using LLM"""
    try:
        data = request.json
        user_question = data.get('question', '')

        if not user_question:
            return jsonify({'error': 'No question provided'}), 400

        # Get job results
        job = job_db.get_job(job_id)
        if not job or job['status'] != 'completed':
            return jsonify({'error': 'Job not found or not completed'}), 404

        # Prepare context from results
        results_summary = "Analysis results:\n"
        if job.get('results_data'):
            results_data = job['results_data']
            if isinstance(results_data, str):
                results_data = json.loads(results_data)

            # Add top topics summary
            if 'top_topics' in results_data:
                results_summary += "\nTop Topics:\n"
                for topic in results_data['top_topics'][:10]:
                    results_summary += f"- {topic.get('topic', 'N/A')}: {topic.get('count', 0)} mentions\n"

        # Query LLM
        from config.llm_client import get_llm_client
        llm_client = get_llm_client()

        prompt = f"""You are analyzing app review trends. Here's the analysis data:

{results_summary}

User question: {user_question}

Provide a clear, concise answer based on the data above. If the question cannot be answered with the available data, say so."""

        response = llm_client.chat(prompt, max_tokens=500)

        return jsonify({
            'question': user_question,
            'answer': response,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health/llm', methods=['GET'])
def check_llm_health():
    """
    Check the status of the configured LLM provider (Ollama or cloud)

    Returns JSON with:
    - status: 'ok', 'warning', or 'error'
    - message: Human-readable status message
    - provider: LLM provider being used
    - models: Available models (for Ollama)
    """
    try:
        from config.llm_client import check_llm_status

        health_data = check_llm_status()

        # Determine HTTP status code based on health status
        if health_data['status'] == 'error':
            status_code = 503  # Service Unavailable
        elif health_data['status'] == 'warning':
            status_code = 200  # OK but with warnings
        else:
            status_code = 200  # OK

        return jsonify(health_data), status_code

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to check LLM health: {str(e)}',
            'provider': 'unknown'
        }), 500


if __name__ == '__main__':
    # Create output directory if it doesn't exist
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Run Flask app
    port = int(os.environ.get('PORT', 8000))
    print("=" * 60)
    print("Swiggy App Store Review Trend Analysis - Web Dashboard")
    print("=" * 60)
    print("\n🚀 Starting Flask server...")
    print(f"📊 Dashboard: http://localhost:{port}")
    print(f"📡 API Docs: http://localhost:{port}/api/jobs\n")

    app.run(debug=True, host='0.0.0.0', port=port)
