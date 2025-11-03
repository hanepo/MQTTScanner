from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import json
import threading
import time
import uuid
from datetime import datetime
import logging
from scanner import MQTTScanner

# --- App Setup ---
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default-weak-secret-key-change-me')

CORS(app, supports_credentials=True)
logging.basicConfig(level=logging.INFO)

# --- Global Variables ---
scanner = MQTTScanner()
scan_jobs = {}  # Store scan jobs and their status

# --- Storage Setup ---
STORAGE_DIR = 'storage'
SCANS_DIR = os.path.join(STORAGE_DIR, 'scans')
os.makedirs(SCANS_DIR, exist_ok=True)

class ScanJob:
    def __init__(self, job_id, scan_type, host=None):
        self.job_id = job_id
        self.scan_type = scan_type
        self.host = host
        self.status = 'pending'  # pending, running, completed, error
        self.results = None
        self.error = None
        self.created_at = datetime.now()
        self.completed_at = None

def run_scan_job(job_id):
    """Run a scan job in background thread"""
    job = scan_jobs.get(job_id)
    if not job:
        return
    
    try:
        job.status = 'running'
        
        if job.scan_type == 'network':
            results = scanner.scan_network()
        elif job.scan_type == 'specific' and job.host:
            results = scanner.scan_host(job.host)
        else:
            raise ValueError("Invalid scan type or missing host")
        
        job.results = results
        job.status = 'completed'
        job.completed_at = datetime.now()
        
        # Save results to file
        result_file = os.path.join(SCANS_DIR, f'{job_id}.json')
        with open(result_file, 'w') as f:
            json.dump({
                'job_id': job_id,
                'scan_type': job.scan_type,
                'host': job.host,
                'results': results,
                'created_at': job.created_at.isoformat(),
                'completed_at': job.completed_at.isoformat()
            }, f, indent=2)
            
    except Exception as e:
        job.status = 'error'
        job.error = str(e)
        job.completed_at = datetime.now()
        logging.error(f"Scan job {job_id} failed: {e}")

# --- Web Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard_pretty.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication (in production, use proper auth)
        if username == 'admin' and password == 'password':
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# --- API Routes ---
@app.route('/api/scan', methods=['POST'])
def start_scan():
    """Start a new scan job"""
    try:
        data = request.get_json() or {}
        scan_type = data.get('scan_type', 'network')
        host = data.get('host')
        
        # Generate unique job ID
        job_id = str(uuid.uuid4())
        
        # Create and store job
        job = ScanJob(job_id, scan_type, host)
        scan_jobs[job_id] = job
        
        # Start scan in background thread
        thread = threading.Thread(target=run_scan_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'job_id': job_id,
            'status': 'started'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scan/<job_id>/status')
def scan_status(job_id):
    """Get status of a scan job"""
    job = scan_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    response = {
        'job_id': job_id,
        'status': job.status,
        'scan_type': job.scan_type,
        'created_at': job.created_at.isoformat()
    }
    
    if job.host:
        response['host'] = job.host
    
    if job.error:
        response['error'] = job.error
    
    if job.completed_at:
        response['completed_at'] = job.completed_at.isoformat()
    
    return jsonify(response)

@app.route('/api/scan/<job_id>/results')
def scan_results(job_id):
    """Get results of a completed scan job"""
    job = scan_jobs.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    if job.status != 'completed':
        return jsonify({
            'error': 'Scan not completed yet',
            'status': job.status
        }), 400
    
    return jsonify({
        'job_id': job_id,
        'results': job.results or [],
        'scan_type': job.scan_type,
        'host': job.host,
        'completed_at': job.completed_at.isoformat() if job.completed_at else None
    })

@app.route('/api/jobs')
def list_jobs():
    """List all scan jobs"""
    jobs_list = []
    for job_id, job in scan_jobs.items():
        jobs_list.append({
            'job_id': job_id,
            'scan_type': job.scan_type,
            'host': job.host,
            'status': job.status,
            'created_at': job.created_at.isoformat(),
            'completed_at': job.completed_at.isoformat() if job.completed_at else None
        })
    
    return jsonify({'jobs': jobs_list})

if __name__ == '__main__':
    print("Starting MQTT Scanner Web Application")
    print("Access the web interface at: http://127.0.0.1:5000")
    print("Dashboard available at: http://127.0.0.1:5000/dashboard")
    app.run(host='0.0.0.0', port=5000, debug=True)