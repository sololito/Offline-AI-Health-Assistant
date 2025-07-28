# /web_app/app.py

from flask import Flask, render_template, request, redirect, url_for, jsonify, session, make_response, send_from_directory, flash
from flask_wtf.csrf import generate_csrf, CSRFProtect
from datetime import datetime, timezone
import sys
import os
import logging
import json
import secrets
import hashlib
import csv
import pandas as pd
import subprocess
import signal
import atexit
from pathlib import Path
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

# User credentials (in a real app, use a proper database)
USERS = {
    'admin': {
        'password': 'admin',  # In production, store hashed passwords
        'name': 'Administrator'
    },
    'user': {
        'password': 'password',  # In production, store hashed passwords
        'name': 'Regular User'
    }
}

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app_debug.log')
    ]
)
logger = logging.getLogger(__name__)

# Add project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.assistant import HealthAssistant

def inject_now():
    return {'now': datetime.now(timezone.utc).isoformat()}

app = Flask(__name__)
app.context_processor(inject_now)

# Configure session and security
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
app.config['SESSION_REFRESH_EACH_REQUEST'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-123'  # Change this in production

# Initialize CSRF protection
csrf = CSRFProtect(app)

def add_security_headers(response):
    """Add security headers to all responses."""
    # Basic security headers
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Development CSP - very permissive
    csp = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: *; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https: http:; "
        "style-src 'self' 'unsafe-inline' https: http:; "
        "img-src 'self' data: blob: https: http:; "
        "font-src 'self' data: https: http:; "
        "connect-src 'self' https: http: ws: wss:;"
    )
    response.headers['Content-Security-Policy'] = csp
    return response

app.after_request(add_security_headers)

# Basic app configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-123'  # Change this in production
app.config['WTF_CSRF_ENABLED'] = False
app.config['WTF_CSRF_CHECK_DEFAULT'] = False
app.config['WTF_CSRF_METHODS'] = []  # Disable CSRF for all methods
app.config['WTF_CSRF_HEADERS'] = []  # Disable CSRF headers

# Initialize CSRF protection if available
try:
    from flask_wtf.csrf import CSRFProtect
    csrf = CSRFProtect(app)
    # We'll exempt the diagnose route after it's defined
    CSRF_ENABLED = True
except ImportError:
    csrf = None
    CSRF_ENABLED = False
    logger.warning("Flask-WTF not found. CSRF protection is disabled.")

# Disable CSRF protection for all routes
app.config.update(
    WTF_CSRF_ENABLED=False,
    WTF_CSRF_CHECK_DEFAULT=False
)

logger.info("Flask app initialized")

# Make sure we have a secret key
if not app.secret_key:
    app.secret_key = os.urandom(24)
    logger.warning("Using random secret key - this is not recommended for production")

# Authentication setup
USERS = {
    'admin': {
        'password': 'admin123',  # In production, use proper password hashing
        'name': 'Administrator'
    }
}

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    # Initialize session if it doesn't exist
    if '_permanent' not in session:
        session.permanent = True
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Check credentials against USERS dictionary
        if username in USERS and USERS[username]['password'] == password:
            session['logged_in'] = True
            session['username'] = username
            flash('Successfully logged in!', 'success')
            next_page = request.args.get('next') or url_for('diagnostic_center')
            return redirect(next_page)
        else:
            flash('Invalid username or password', 'error')
    
    # For GET requests, show the login page directly
    return render_template('diagnostic_center.html', active_tab='diagnostic')

@app.route('/logout')
def logout():
    """Handle user logout."""
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('You were successfully logged out', 'success')
    return redirect(url_for('home'))

assistant = HealthAssistant()

# Voice Assistant Process Management
voice_process = None

def cleanup_voice_process():
    """Cleanup the voice assistant process on application exit."""
    global voice_process
    if voice_process:
        try:
            voice_process.terminate()
            voice_process.wait(timeout=5)
        except Exception as e:
            logger.error(f"Error cleaning up voice process: {e}")
        finally:
            voice_process = None

# Register cleanup function
atexit.register(cleanup_voice_process)

def init_session():
    """Initialize session if it doesn't exist."""
    if '_permanent' not in session:
        session.permanent = True
        logger.debug("Initialized new session")
    
    # Ensure we have a CSRF token in the session
    if '_csrf_token' not in session:
        session['_csrf_token'] = generate_csrf()
        logger.debug(f"Generated new CSRF token for session: {session['_csrf_token'][:10]}...")
    
    return session['_csrf_token']

# Educational PDFs directory - using web_app/templates/docs as the base
EDUCATIONAL_DIR = os.path.join('web_app', 'templates', 'docs')
EDUCATIONAL_PDF_DIR = os.path.join(EDUCATIONAL_DIR, 'educational')

# Ensure the educational directories exist
os.makedirs(EDUCATIONAL_PDF_DIR, exist_ok=True)

# Load educational content index
EDUCATION_INDEX = {
    'categories': [],
    'documents': []
}

def load_education_index():
    """Load the education index from JSON file."""
    index_path = os.path.join(EDUCATIONAL_DIR, 'index.json')
    logger.info(f"Loading education index from: {os.path.abspath(index_path)}")
    
    # Check if file exists
    if not os.path.exists(index_path):
        logger.warning(f"Education index not found at {index_path}. Creating a new one.")
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(index_path), exist_ok=True)
            # Create the file with default structure
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(EDUCATION_INDEX, f, indent=2)
            logger.info("Created new education index file with default structure.")
            return
        except Exception as e:
            logger.error(f"Failed to create education index: {str(e)}")
            return
    
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.debug(f"Loaded index data: {json.dumps(data, indent=2)}")
            
            # Validate the structure
            if not isinstance(data, dict):
                raise ValueError("Index data is not a JSON object")
                
            if 'categories' not in data:
                raise ValueError("Missing 'categories' field in index")
                
            if 'documents' not in data:
                raise ValueError("Missing 'documents' field in index")
            
            # Update the in-memory index
            EDUCATION_INDEX.update({
                'categories': data.get('categories', []),
                'documents': data.get('documents', [])
            })
            
            logger.info(f"Successfully loaded {len(EDUCATION_INDEX['documents'])} documents and {len(EDUCATION_INDEX['categories'])} categories")
            
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing education index: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading education index: {str(e)}", exc_info=True)

# Load the education index when the app starts
load_education_index()

def get_pdf_path(filename):
    """Get the full path to a PDF file in the educational directory."""
    return os.path.join(EDUCATIONAL_DIR, filename)

def log_request_info():
    """Log request information for debugging."""
    if request.method == 'POST':
        app.logger.info('Form data: %s', request.form)
        app.logger.info('CSRF Token in form: %s', request.form.get('csrf_token'))
        app.logger.info('Debug Token in form: %s', request.form.get('debug_token'))

@app.before_request
def log_request_info():
    """Log request information for debugging."""
    try:
        logger.debug(f"\n{'='*50}")
        logger.debug(f"New Request: {request.method} {request.path}")
        
        # Initialize session and get CSRF token
        csrf_token = init_session()
        
        # Log request headers (excluding sensitive information)
        headers = {k: v for k, v in request.headers.items() 
                  if k.lower() not in ['authorization', 'cookie']}
        logger.debug(f"Request Headers: {headers}")
        
        # Log session information safely
        try:
            session_data = {k: v for k, v in session.items() if not k.startswith('_')}
            logger.debug(f"Session Data: {session_data}")
            logger.debug(f"CSRF Token in session: {csrf_token[:10]}...")
        except Exception as e:
            logger.warning(f"Error accessing session data: {str(e)}")
        
        # Skip CSRF checks for safe methods
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return None
            
        # Log form data for non-GET requests
        try:
            if request.is_json:
                form_data = request.get_json()
            else:
                form_data = dict(request.form)
                
            # Don't log sensitive data
            if isinstance(form_data, dict):
                form_data = {k: '***REDACTED***' if 'pass' in k.lower() else v 
                           for k, v in form_data.items()}
                
            logger.debug(f"Request Data: {form_data}")
            
            # Log CSRF token from form if present
            form_csrf = None
            if request.is_json:
                form_csrf = form_data.get('csrf_token')
            else:
                form_csrf = request.form.get('csrf_token')
                
            if form_csrf:
                logger.debug(f"CSRF Token in request: {form_csrf[:10]}...")
            else:
                logger.warning("No CSRF token found in request data")
                
        except Exception as e:
            logger.warning(f"Error processing request data: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error in log_request_info: {str(e)}", exc_info=True)
        # Don't let debug logging break the app
        pass
    
    return None

@app.route("/", methods=["GET", "POST"])
def home():
    """Render the home page."""
    if request.method == 'POST':
        logger.warning("POST request received at root URL, redirecting to /diagnose")
        return redirect(url_for('diagnose'))
    
    # Initialize session
    init_session()
    
    # Prepare template context
    context = {
        'active_tab': 'home',
        'session': session
    }
    
    # Create response
    response = make_response(render_template("home.html", **context))
    
    # Set security headers
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # CSP for development
    csp = (
        "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: *; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https: http:; "
        "style-src 'self' 'unsafe-inline' https: http:; "
        "img-src 'self' data: https: http:; "
        "font-src 'self' data: https: http:; "
        "connect-src 'self' https: http: ws: wss:;"
    )
    response.headers['Content-Security-Policy'] = csp
    
    logger.info("Rendered home page")
    return response

def format_diagnosis_response(results, symptoms, csrf_token, error=None, status_code=200):
    """Format the diagnosis response as JSON."""
    if results is None and error is None:
        return jsonify({
            'results': [],
            'symptoms': symptoms,
            'csrf_token': csrf_token,
            'success': True,
            'error': None,
            'status': 'success'
        }), 200
        
    if error is not None:
        return jsonify({
            'results': [],
            'symptoms': symptoms,
            'csrf_token': csrf_token,
            'success': False,
            'error': error,
            'status': 'error'
        }), status_code
    
    # Format results to match frontend expectations
    formatted_results = []
    for result in results:
        # Extract confidence percentage from the result (already formatted as a string with %)
        confidence = int(result['confidence'].rstrip('%'))
        
        # Determine severity based on confidence
        if confidence >= 70:
            severity = 'High'
        elif confidence >= 40:
            severity = 'Medium'
        else:
            severity = 'Low'
            
        # Create a formatted result entry
        formatted_result = {
            'condition': result['disease'],
            'confidence': confidence,
            'severity': severity,
            'description': f"Matched {result.get('matched_symptoms', 'some')} symptoms.",
            'recommendations': result.get('recommendations', [
                'Consult with a healthcare professional for an accurate diagnosis.',
                'Monitor your symptoms and seek medical attention if they worsen.'
            ])
        }
        formatted_results.append(formatted_result)
    
    response = {
        'results': formatted_results,
        'symptoms': symptoms,
        'csrf_token': csrf_token,
        'success': True,
        'error': None,
        'status': 'success'
    }
    return jsonify(response), status_code

@app.route("/diagnose", methods=["GET", "POST"])
@csrf.exempt if CSRF_ENABLED and csrf else lambda f: f
def diagnose():
    """Handle symptom submission and return diagnosis results."""
    logger.debug(f"\n{'='*50}")
    logger.debug(f"Diagnose route called with method: {request.method}")
    
    # Initialize session
    init_session()
    
    # For GET requests, just show the form
    if request.method == 'GET':
        logger.debug("Handling GET request for /diagnose")
        
        # Check if it's an AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json':
            return format_diagnosis_response(None, "", session.get('_csrf_token', ''))
            
        # Regular GET request - render the full page
        context = {
            'results': None,
            'symptoms': "",
            'active_tab': 'diagnose',
            'session': session
        }
        
        logger.debug(f"Template context for GET request: { {k: type(v).__name__ for k, v in context.items()} }")
        
        return render_template("diagnose.html", **context)
    
    # Handle POST request
    logger.debug(f"Form data received: {request.form}")
    
    # Check if it's an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('Accept') == 'application/json'
    
    # Get CSRF token from form
    form_csrf_token = request.form.get('csrf_token')
    session_csrf_token = session.get('_csrf_token')
    
    # Log detailed CSRF token information
    logger.debug(f"Form CSRF Token: {form_csrf_token}")
    logger.debug(f"Session CSRF Token: {session_csrf_token}")
    logger.debug(f"Session contents: {dict(session)}")
    
    # Temporarily disable CSRF protection
    logger.warning("CSRF protection is currently disabled for debugging purposes")
    
    # Keep the token generation for consistency, but don't validate it
    if not session_csrf_token:
        session_csrf_token = init_session()
    
    try:
        # Process symptoms
        raw_symptoms = request.form.get("symptoms", "").strip()
        logger.debug(f"Raw symptoms: {raw_symptoms}")
        
        if not raw_symptoms:
            error_msg = "Please enter symptoms to diagnose."
            logger.warning(error_msg)
            new_csrf_token = init_session()
            
            if is_ajax:
                return format_diagnosis_response(
                    None, 
                    "", 
                    new_csrf_token, 
                    error_msg, 
                    400
                )
            else:
                return render_template("diagnose.html",
                                    error=error_msg,
                                    results=None,
                                    symptoms="",
                                    active_tab='diagnose',
                                    csrf_token=new_csrf_token), 400
        
        user_symptoms = [s.strip().lower() for s in raw_symptoms.split(",") if s.strip()]
        logger.debug(f"Processed symptoms: {user_symptoms}")
        
        if not user_symptoms:
            error_msg = "Please enter valid symptoms separated by commas."
            logger.warning(error_msg)
            new_csrf_token = init_session()
            
            if is_ajax:
                return format_diagnosis_response(
                    None, 
                    raw_symptoms, 
                    new_csrf_token, 
                    error_msg, 
                    400
                )
            else:
                return render_template("diagnose.html",
                                    error=error_msg,
                                    results=None,
                                    symptoms=raw_symptoms,
                                    active_tab='diagnose',
                                    csrf_token=new_csrf_token), 400
        
        logger.info(f"Processing symptoms: {user_symptoms}")
        
        try:
            # Generate diagnosis results
            results = assistant.diagnose(user_symptoms)
            logger.debug(f"Diagnosis results: {results}")
            
            # Generate a new CSRF token for the next request
            new_csrf_token = init_session()
            logger.debug(f"Generated new CSRF token for next request: {new_csrf_token[:10]}...")
            
            if is_ajax:
                return format_diagnosis_response(
                    results,
                    raw_symptoms,
                    new_csrf_token
                )
            else:
                return render_template("diagnose.html", 
                                    results=results, 
                                    symptoms=raw_symptoms,
                                    active_tab='diagnose',
                                    csrf_token=new_csrf_token)
                                    
        except Exception as e:
            logger.error(f"Error in diagnosis: {str(e)}", exc_info=True)
            error_msg = f"An error occurred while processing your symptoms: {str(e)}"
            new_csrf_token = init_session()
            
            if is_ajax:
                return format_diagnosis_response(
                    None,
                    raw_symptoms,
                    new_csrf_token,
                    error_msg,
                    500
                )
            else:
                return render_template("diagnose.html",
                                    error=error_msg,
                                    results=None,
                                    symptoms=raw_symptoms,
                                    active_tab='diagnose',
                                    csrf_token=new_csrf_token), 500
    
    except Exception as e:
        logger.error(f"Unexpected error in diagnose: {str(e)}", exc_info=True)
        # Generate a new CSRF token even on error
        new_csrf_token = init_session()
        error_msg = f"An unexpected error occurred while processing your request: {str(e)}"
        
        if is_ajax:
            return format_diagnosis_response(
                None,
                request.form.get('symptoms', ''),
                new_csrf_token,
                error_msg,
                500
            )
        else:
            return render_template("diagnose.html",
                                error=error_msg,
                                results=None,
                                symptoms=request.form.get('symptoms', ''),
                                active_tab='diagnose',
                                csrf_token=new_csrf_token), 500

@app.route('/education')
def education():
    """Render the educational resources page."""
    try:
        # Initialize session
        init_session()
        
        # Log initial state of EDUCATION_INDEX
        logger.info(f"Initial EDUCATION_INDEX state: {json.dumps(EDUCATION_INDEX, indent=2)}")
        
        # Reload the education index in case it was updated
        load_education_index()
        
        # Log the state after loading
        logger.info(f"After load_education_index(), EDUCATION_INDEX has {len(EDUCATION_INDEX.get('documents', []))} documents and {len(EDUCATION_INDEX.get('categories', []))} categories")
        
        # Get recent documents from session (last 5 viewed)
        recent_docs = session.get('recent_docs', [])
        logger.info(f"Found {len(recent_docs)} recent documents in session")
        
        # Get favorite topics from session
        favorite_topics = session.get('favorite_topics', [])
        logger.info(f"Found {len(favorite_topics)} favorite topics in session")
        
        # Get all categories - ensure we're getting them correctly
        categories = EDUCATION_INDEX.get('categories', [])
        logger.info(f"Categories from EDUCATION_INDEX: {json.dumps(categories, indent=2)}")
        logger.info(f"Loaded {len(categories)} categories")
        
        # Get all documents with their full category info
        documents = []
        for doc in EDUCATION_INDEX.get('documents', []):
            doc_categories = []
            for cat_id in doc.get('categories', []):
                cat = next((c for c in categories if c['id'] == cat_id), None)
                if cat:
                    doc_categories.append(cat)
            
            doc_copy = doc.copy()
            doc_copy['category_objects'] = doc_categories
            
            # Ensure all expected fields are present with defaults
            doc_copy.setdefault('description', 'No description available')
            doc_copy.setdefault('thumbnail', 'fa-file-pdf')
            doc_copy.setdefault('duration', '5 min read')
            
            documents.append(doc_copy)
        
        logger.info(f"Processed {len(documents)} documents for the template")
        
        # Log sample document data for debugging
        if documents:
            logger.debug(f"Sample document data: {documents[0]}")
        
        # Create response with the new template
        response = make_response(render_template(
            "education_new.html",  # Using the new template
            active_tab='education',  # This must match the check in base.html
            categories=categories,
            documents=documents,
            recent_docs=recent_docs,
            favorite_topics=favorite_topics,
            session=session
        ))
        
        return response
    except Exception as e:
        logger.error(f"Error in education route: {str(e)}", exc_info=True)
        return str(e), 500

@app.route("/first-aid")
def first_aid():
    """Render the First Aid & Emergency Procedures page."""
    try:
        # Initialize session
        init_session()
        
        # First aid topics data
        first_aid_topics = [
            {
                'id': 'cpr',
                'title': 'CPR (Cardiopulmonary Resuscitation)',
                'description': 'Learn how to perform CPR on adults, children, and infants.',
                'icon': 'fa-heartbeat',
                'tags': ['cpr', 'resuscitation', 'breathing', 'cardiac arrest']
            },
            {
                'id': 'choking',
                'title': 'Choking Response',
                'description': 'Learn how to help someone who is choking.',
                'icon': 'fa-lungs',
                'tags': ['choking', 'airway', 'heimlich', 'first aid']
            },
            {
                'id': 'burns',
                'title': 'Burns Treatment',
                'description': 'First aid for different types of burns.',
                'icon': 'fa-fire',
                'tags': ['burns', 'first aid', 'emergency']
            },
            {
                'id': 'bleeding',
                'title': 'Bleeding Control',
                'description': 'How to control bleeding from wounds.',
                'icon': 'fa-tint',
                'tags': ['bleeding', 'wounds', 'first aid']
            }
        ]
        
        # Create response
        response = make_response(render_template(
            "first_aid.html",
            active_tab='first_aid',
            first_aid_topics=first_aid_topics,
            session=session
        ))
        
        return response
    except Exception as e:
        logger.error(f"Error in first_aid route: {str(e)}", exc_info=True)
        return str(e), 500

@app.route('/education/pdf/<path:filename>')
def serve_pdf(filename):
    """Serve PDF files from the educational directory and track recent views."""
    try:
        # Log the requested filename and full path for debugging
        # PDFs are in the 'educational' subdirectory of EDUCATIONAL_DIR
        # app.root_path already includes 'web_app', so we need to go up one level first
        base_dir = os.path.dirname(app.root_path)  # Go up from web_app
        pdf_dir = os.path.join(base_dir, EDUCATIONAL_DIR, 'educational')
        pdf_path = os.path.join(pdf_dir, filename)
        
        logger.info(f"PDF request - Filename: {filename}")
        logger.info(f"PDF directory: {pdf_dir}")
        logger.info(f"Full PDF path: {pdf_path}")
        
        # Check if file exists
        if not os.path.exists(pdf_path):
            logger.error(f"PDF not found at: {pdf_path}")
            logger.info(f"Contents of {pdf_dir}: {os.listdir(pdf_dir)}")
            return f"PDF not found: {filename}", 404
        
        # Update recent documents in session
        if 'recent_docs' not in session:
            session['recent_docs'] = []
        
        # Find the document in our index
        document = next((doc for doc in EDUCATION_INDEX['documents'] 
                        if doc['filename'] == filename), None)
        
        if document:
            # Remove if already in recent docs
            session['recent_docs'] = [d for d in session['recent_docs'] 
                                    if d.get('id') != document['id']]
            
            # Add to beginning of recent docs
            session['recent_docs'].insert(0, {
                'id': document['id'],
                'title': document['title'],
                'filename': document['filename'],
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            
            # Keep only the last 10 recent documents
            session['recent_docs'] = session['recent_docs'][:10]
            
            # Mark session as modified
            session.modified = True
        
        logger.info(f"Serving PDF: {filename} from {pdf_dir}")
        
        # Serve the PDF file from the same directory as index.json
        response = send_from_directory(
            pdf_dir,
            filename,
            as_attachment=False
        )
        
        # Add headers to help with debugging
        response.headers['X-PDF-Path'] = pdf_path
        response.headers['X-Requested-File'] = filename
        
        return response
        
    except Exception as e:
        logger.error(f"Error serving PDF {filename}: {str(e)}", exc_info=True)
        return f"Error serving PDF: {str(e)}", 500

@app.route('/api/education/favorites', methods=['GET'])
def get_favorites():
    """Get the user's favorite documents."""
    try:
        if not session.get('logged_in'):
            return jsonify({'success': False, 'error': 'Not logged in'}), 401
            
        favorite_topics = session.get('favorite_topics', [])
        favorite_ids = [doc['id'] for doc in favorite_topics if 'id' in doc]
        
        return jsonify({
            'success': True,
            'favorites': favorite_ids
        })
    except Exception as e:
        logger.error(f"Error getting favorites: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/education/favorites/toggle', methods=['POST'])
@login_required
def toggle_favorite():
    """Add or remove a document from favorites."""
    try:
        data = request.get_json()
        doc_id = data.get('doc_id')
        action = data.get('action')  # 'add' or 'remove'
        
        if not doc_id or action not in ['add', 'remove']:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
        # Initialize favorites in session if not exists
        if 'favorite_topics' not in session:
            session['favorite_topics'] = []
        
        # Find the document in our index
        document = next((doc for doc in EDUCATION_INDEX['documents'] 
                        if doc['id'] == doc_id), None)
        
        if not document:
            return jsonify({'success': False, 'error': 'Document not found'}), 404
        
        if action == 'add':
            # Check if already in favorites
            if not any(doc.get('id') == doc_id for doc in session['favorite_topics']):
                session['favorite_topics'].append({
                    'id': document['id'],
                    'title': document['title'],
                    'filename': document['filename']
                })
        else:  # remove
            session['favorite_topics'] = [doc for doc in session['favorite_topics'] 
                                        if doc.get('id') != doc_id]
        
        # Mark session as modified
        session.modified = True
        
        return jsonify({
            'success': True,
            'favorites': [doc['id'] for doc in session['favorite_topics']]
        })
    except Exception as e:
        logger.error(f"Error toggling favorite: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route("/diagnostic-center")
def diagnostic_center():
    """Render the diagnostic center page."""
    # Initialize session if it doesn't exist
    if '_permanent' not in session:
        session.permanent = True
    
    # Check if user is logged in
    if not session.get('logged_in'):
        # Show login form
        return render_template(
            "diagnostic_center.html",
            active_tab='diagnostic',
            show_login=True
        )
    
    # User is logged in, show diagnostic center
    return render_template(
        "diagnostic_center.html",
        active_tab='diagnostic',
        show_login=False,
        username=session.get('username')
    )


def load_health_diagnostics():
    """Load health diagnostics data from CSV."""
    try:
        # Get the path to the health_diagnostics.csv file
        data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'health_diagnostics.csv')
        
        # Load the CSV data
        df = pd.read_csv(data_path)
        
        # Convert all columns to string type to handle missing values consistently
        df = df.astype(str)
        
        # Replace 'nan' strings with empty strings
        df = df.replace('nan', '')
        
        return df
    except Exception as e:
        logger.error(f"Error loading health diagnostics data: {str(e)}")
        return pd.DataFrame()

def find_matching_diagnosis(form_data, diagnostics_df):
    """Find the best matching diagnosis based on form data."""
    if diagnostics_df.empty:
        return None
    
    # Convert form data to a format that can be compared with the CSV
    form_values = {
        'Body Temp (°C)': form_data.get('body_temp', ''),
        'Systolic (mmHg)': form_data.get('systolic', ''),
        'Diastolic (mmHg)': form_data.get('diastolic', ''),
        'Pulse (BPM)': form_data.get('pulse', ''),
        'Glucose (mg/dL)': form_data.get('glucose', ''),
        'Glucose Type': form_data.get('glucose_type', '').capitalize(),
        'Oxygen (%)': form_data.get('oxygen', ''),
        'Weight (kg)': form_data.get('weight', ''),
        'Height (cm)': form_data.get('height', ''),
        'Symptoms': form_data.get('symptoms', '').lower()
    }
    
    # Calculate match scores for each row in the diagnostics data
    max_score = 0
    best_match = None
    
    for _, row in diagnostics_df.iterrows():
        score = 0
        matched_fields = []
        
        # Check each field for matches
        for field, form_value in form_values.items():
            if not form_value:  # Skip empty form fields
                continue
                
            csv_value = str(row.get(field, '')).lower()
            
            # For numeric fields, check if they're within a range
            if field in ['Body Temp (°C)', 'Systolic (mmHg)', 'Diastolic (mmHg)', 'Pulse (BPM)', 
                        'Glucose (mg/dL)', 'Oxygen (%)', 'Weight (kg)', 'Height (cm)']:
                try:
                    form_num = float(form_value)
                    if '-' in csv_value:  # Handle ranges in CSV (e.g., '120-129')
                        low, high = map(float, csv_value.split('-'))
                        if low <= form_num <= high:
                            score += 1
                            matched_fields.append(field)
                except (ValueError, AttributeError):
                    # If parsing fails, do simple string comparison
                    if form_value.lower() in csv_value.lower():
                        score += 1
                        matched_fields.append(field)
            # For symptoms, check if any symptom from form is in the CSV symptoms
            elif field == 'Symptoms' and form_value:
                form_symptoms = [s.strip() for s in form_value.split(',')]
                csv_symptoms = [s.strip() for s in csv_value.split(',')]
                matched = sum(1 for s in form_symptoms if s and s in csv_symptoms)
                if matched > 0:
                    score += matched * 0.5  # Give partial credit for symptom matches
                    matched_fields.append(f"{matched} symptom(s) matched")
            # For other fields (like Glucose Type), do simple string comparison
            else:
                if form_value.lower() in csv_value.lower():
                    score += 1
                    matched_fields.append(field)
        
        # Update best match if current row has higher score
        if score > max_score:
            max_score = score
            best_match = {
                'diagnosis': row.get('Possible Diagnoses', ''),
                'recommendations': row.get('Recommendations', ''),
                'score': score,
                'matched_fields': matched_fields
            }
    
    return best_match if best_match and best_match['score'] > 0 else None

@app.route('/submit_diagnostic_data', methods=['POST'])
def submit_diagnostic_data():
    """Handle submission of diagnostic data and return analysis results."""
    try:
        # Ensure user is logged in
        if not session.get('logged_in'):
            return jsonify({
                'success': False,
                'error': 'Please log in to use the diagnostic center'
            }), 401
        
        # Get form data
        form_data = request.form.to_dict()
        logger.debug(f"Received diagnostic data: {form_data}")
        
        # Validate that we have at least 5 fields filled
        filled_fields = sum(1 for k, v in form_data.items() 
                          if k not in ['symptoms', 'csrf_token'] and v.strip())
        
        if filled_fields < 5:
            return jsonify({
                'success': False,
                'error': 'Please fill in at least 5 health metrics for accurate analysis.'
            }), 400
        
        # Load diagnostics data
        diagnostics_df = load_health_diagnostics()
        if diagnostics_df.empty:
            return jsonify({
                'success': False,
                'error': 'Diagnostic reference data not available. Please try again later.'
            }), 500
        
        # Find matching diagnosis
        diagnosis = find_matching_diagnosis(form_data, diagnostics_df)
        
        if not diagnosis:
            return jsonify({
                'success': True,
                'diagnosis': 'No specific diagnosis found based on the provided data.',
                'recommendations': 'Please consult with a healthcare professional for a comprehensive evaluation.'
            })
        
        # Generate response
        response = {
            'success': True,
            'diagnosis': diagnosis['diagnosis'],
            'recommendations': diagnosis['recommendations'].split('; '),
            'matched_fields': diagnosis['matched_fields'],
            'confidence': min(100, int(diagnosis['score'] * 15))  # Scale score to 0-100%
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in submit_diagnostic_data: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An error occurred while processing your request. Please try again.'
        }), 500

# Serve static files
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files from the static directory."""
    return send_from_directory('static', filename)

@app.route('/assistant')
def assistant_page():
    """Render the AI Assistant page."""
    return render_template('assistant.html', active_tab='assistant')

@app.route('/upcoming')
def upcoming():
    """Render the upcoming features page."""
    return render_template('upcoming.html', active_tab='upcoming')

def check_auth():
    """Check if user is authenticated and return appropriate response."""
    if 'username' not in session:
        return jsonify({
            'status': 'error',
            'message': 'Authentication required',
            'authenticated': False
        }), 401
    return None

@app.route('/api/assistant/query', methods=['POST'])
def query_assistant():
    """Handle text queries to the assistant with command processing and voice output."""
    try:
        # Get the query from the request
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing query parameter'
            }), 400
            
        query = data['query'].strip().lower()
        
        # Import the VoiceAssistant class
        from main import VoiceAssistant
        
        # Initialize the assistant
        assistant = VoiceAssistant(text_mode=True)
        
        # Check for special commands
        if query in ['exit', 'quit', 'goodbye']:
            response = {
                'text': 'Goodbye! Take care of your health!',
                'speech': 'Goodbye! Take care of your health!',
                'type': 'command_response'
            }
        elif query in ['help', '?']:
            help_text = """
            🤖 AI Health Assistant - Available Commands:
            
            1. Symptom Analysis:
               - Describe your symptoms (e.g., "I have a headache and fever")
               - Ask about conditions (e.g., "What are the symptoms of flu?")
            
            2. Health Information:
               - Ask about health topics (e.g., "Tell me about diabetes")
               - Get advice (e.g., "How to lower blood pressure?")
            
            3. Navigation:
               - "help" - Show this help message
               - "exit" or "quit" - End the session
            
            Note: For medical emergencies, please contact a healthcare professional immediately.
            """
            response = {
                'text': help_text,
                'speech': "I can help with symptom analysis and health information. You can describe your symptoms or ask health-related questions. Type 'help' anytime for assistance.",
                'type': 'help_response'
            }
        else:
            # Process regular queries
            response = assistant.process_text_input(query)
            
            # Ensure response has the expected format
            if isinstance(response, str):
                response = {
                    'text': response,
                    'speech': response,
                    'type': 'general_response'
                }
            elif not isinstance(response, dict):
                response = {
                    'text': str(response),
                    'speech': str(response),
                    'type': 'general_response'
                }
            
            # Add speech text if not present
            if 'speech' not in response:
                response['speech'] = response.get('text', 'I apologize, but I encountered an error.')
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        logger.error(f"Error in query_assistant: {str(e)}", exc_info=True)
        error_msg = f"I'm sorry, I encountered an error: {str(e)}"
        return jsonify({
            'success': False,
            'response': {
                'text': error_msg,
                'speech': error_msg,
                'type': 'error'
            }
        }), 500

@app.route('/api/voice/status', methods=['GET'])
def voice_status():
    """Check if the voice assistant is running."""
    # Check authentication
    auth_response = check_auth()
    if auth_response:
        return auth_response
        
    global voice_process
    is_running = voice_process is not None and voice_process.poll() is None
    return jsonify({
        'status': 'running' if is_running else 'stopped',
        'pid': voice_process.pid if is_running and voice_process else None,
        'authenticated': True
    })

@app.route('/api/voice/start', methods=['POST'])
def start_voice():
    """Start the voice assistant process."""
    # Check authentication
    auth_response = check_auth()
    if auth_response:
        return auth_response
        
    global voice_process
    
    # Check if already running
    if voice_process and voice_process.poll() is None:
        return jsonify({
            'status': 'already_running',
            'pid': voice_process.pid,
            'authenticated': True
        }), 200
    
    try:
        # Get the absolute path to main.py
        main_py = Path(__file__).parent.parent / 'main.py'
        
        # Start the voice assistant process
        voice_process = subprocess.Popen(
            [sys.executable, str(main_py), '--voice'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
        
        logger.info(f"Started voice assistant with PID: {voice_process.pid}")
        return jsonify({
            'status': 'started',
            'pid': voice_process.pid,
            'authenticated': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting voice assistant: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'authenticated': True
        }), 500

@app.route('/api/voice/stop', methods=['POST'])
def stop_voice():
    """Stop the voice assistant process."""
    # Check authentication
    auth_response = check_auth()
    if auth_response:
        return auth_response
        
    global voice_process
    
    if not voice_process:
        return jsonify({
            'status': 'not_running',
            'authenticated': True
        }), 200
    
    try:
        # Try to terminate gracefully first
        voice_process.terminate()
        try:
            voice_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if it doesn't terminate
            voice_process.kill()
            voice_process.wait()
            
        logger.info(f"Stopped voice assistant with PID: {voice_process.pid}")
        return jsonify({
            'status': 'stopped',
            'pid': voice_process.pid,
            'authenticated': True
        }), 200
        
    except Exception as e:
        logger.error(f"Error stopping voice assistant: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'authenticated': True
        }), 500
    finally:
        voice_process = None

if __name__ == "__main__":
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Ensure cleanup on normal exit
    atexit.register(cleanup_voice_process)
    
    # Run the application
    app.run(debug=True)
