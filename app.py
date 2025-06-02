import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g # Added g
from werkzeug.utils import secure_filename
import traceback
from werkzeug.security import generate_password_hash, check_password_hash # For passwords
from functools import wraps # For login_required decorator

# --- Import your custom modules ---
MODULES_LOADED_SUCCESSFULLY = True


try:
    from core.python_resume_parser_v9 import extract_text_from_pdf, AdvancedResumeParser
except ImportError as e:
    print(f"Error importing Resume Parser module (core.python_resume_parser_v9): {e}")
    MODULES_LOADED_SUCCESSFULLY = False
    def extract_text_from_pdf(path): return "Error: Parser module (core.python_resume_parser_v9) not loaded."
    class AdvancedResumeParser:
        def parse_resume(self, text): # Ensure this dummy matches expected output structure
            return {"metadata": {"resume_score": 0.0}, "skills": {"all_skills": []}}

try:
    from core.job_scrapper_api_v2 import scrape_jobs, PREDEFINED_SKILLS_KEYWORDS
except ImportError as e:
    print(f"Error importing Job Scrapper module (core.job_scrapper_api_v2): {e}")
    MODULES_LOADED_SUCCESSFULLY = False
    def scrape_jobs(keywords, location, max_jobs_per_source, skills_json_path): return []
    PREDEFINED_SKILLS_KEYWORDS = []

DB_FUNCTIONS_AVAILABLE = True
try:
    from core.database_manager import (
        connect_db,
        save_personalized_search_session,
        get_personalized_search_session,
        delete_personalized_search_session, # This will be the modified version
        save_recommended_job,
        get_recommended_jobs_by_keywords,
        # --- Added User DB functions ---
        create_user,
        get_user_by_username,
        get_user_by_id,
        get_search_sessions_for_user # To fetch history for dashboard
    )
except ImportError as e:
    print(f"Error importing Database Manager module (core.database_manager): {e}")
    print("Database operations will be skipped.")
    DB_FUNCTIONS_AVAILABLE = False
    MODULES_LOADED_SUCCESSFULLY = False # يعتبر خطأ في التحميل الأساسي

    # Dummy functions if database_manager fails to load
    def connect_db(): print("DUMMY DB: connect_db called (core.database_manager not loaded)"); return None
    def save_personalized_search_session(session_id, resume_score, extracted_skills, personalized_job_results, raw_resume_text, user_id=None): # Added user_id
        print("DUMMY DB: save_personalized_search_session called (core.database_manager not loaded)")
    def get_personalized_search_session(session_id):
        print("DUMMY DB: get_personalized_search_session called (core.database_manager not loaded)"); return None
    def delete_personalized_search_session(session_id): # Dummy for modified function
        print("DUMMY DB: delete_personalized_search_session called (core.database_manager not loaded)"); return "error" # Default dummy return
    def save_recommended_job(job_data, source_keywords):
        print("DUMMY DB: save_recommended_job called (core.database_manager not loaded)")
    def get_recommended_jobs_by_keywords(keywords, limit):
        print("DUMMY DB: get_recommended_jobs_by_keywords called (core.database_manager not loaded)"); return []
    # --- Dummy User DB functions ---
    def create_user(username, email, password_hash): print("DUMMY DB: create_user called"); return None
    def get_user_by_username(username): print("DUMMY DB: get_user_by_username called"); return None
    def get_user_by_id(user_id): print("DUMMY DB: get_user_by_id called"); return None
    def get_search_sessions_for_user(user_id, limit=10): print("DUMMY DB: get_search_sessions_for_user called"); return []


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_very_strong_and_random_secret_key_for_prod_!123@') # Ensure this is strong for production
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 MB limit for uploads
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

# Create upload folder if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

from datetime import datetime

@app.context_processor
def utility_processor():
    def get_current_year():
        return datetime.utcnow().year
    return dict(current_year=get_current_year())

def process_resume_file_placeholder(pdf_path: str) -> dict:
    """Placeholder or actual implementation for resume processing."""
    print(f"FLASK_APP: Calling resume parser for: {pdf_path}")
    # Check if actual parser components are loaded
    if "AdvancedResumeParser" not in globals() or "extract_text_from_pdf" not in globals():
         return {"raw_resume_text": "Error: Resume parser components not available.", "extracted_skills": [], "resume_score": 0.0}
    try:
        parser_instance = AdvancedResumeParser()
        raw_text = extract_text_from_pdf(pdf_path)

        # Handle cases where text extraction might fail or return error messages
        if "Error: Parser module" in raw_text or "Error: Parser not loaded" in raw_text : # Check for dummy error messages
             raise ValueError(raw_text) # Propagate parser module loading errors

        if not raw_text or not raw_text.strip():
            # Specific check if file exists but no text extracted (e.g. image-based PDF)
            if not raw_text and os.path.exists(pdf_path):
                 flash("Could not extract text from the PDF. It might be image-based or corrupted.", "error")
            # General error for no text
            raise ValueError("No text could be extracted from the resume. The file might be image-based or corrupted.")

        parsed_data_from_parser = parser_instance.parse_resume(raw_text)
        # Safely get nested data
        resume_score = parsed_data_from_parser.get('metadata', {}).get('resume_score', 0.0)
        all_extracted_skills = parsed_data_from_parser.get('skills', {}).get('all_skills', [])

        return {"raw_resume_text": raw_text, "extracted_skills": all_extracted_skills, "resume_score": resume_score}
    except Exception as e:
        print(f"--- TRACEBACK WITHIN process_resume_file_placeholder ---")
        traceback.print_exc() # Print full traceback for debugging
        print(f"--- END OF TRACEBACK ---")
        print(f"Error in process_resume_file_placeholder: {e}")
        # Return a structured error that the frontend can potentially understand
        return {"raw_resume_text": f"Error processing resume: {str(e)}", "extracted_skills": [], "resume_score": 0.0}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Database Connection ---
db_connection_active = False
db = None # Initialize db to None
if DB_FUNCTIONS_AVAILABLE:
    try:
        db_object_from_connect = connect_db() # Attempt connection
        if db_object_from_connect is not None:
            db = db_object_from_connect # Assign to global 'db' if successful
            db_connection_active = True
            print("INFO: MongoDB connection established and active.")
        else:
            print("CRITICAL: Failed to connect to MongoDB. Database operations will be impacted.")
    except Exception as e_connect: # Catch any exception from connect_db()
        print(f"CRITICAL: MongoDB connection failed on startup: {e_connect}")
else:
    print("INFO: Database functions are not available (DB_FUNCTIONS_AVAILABLE is False). DB operations will be skipped.")


# --- User Session Management ---
@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        if DB_FUNCTIONS_AVAILABLE and db_connection_active: # Check if DB is usable
            g.user = get_user_by_id(user_id) # g.user will store the user object (dict)
            if g.user:
                # Keep username in session for quick display in templates if needed
                session['username'] = g.user.get('username')
            else: # User ID in session but not in DB (e.g. deleted user)
                session.clear() # Clear invalid session
                g.user = None
        else: # DB not available, cannot verify user
            # Potentially clear session if user verification is critical and DB is down
            # For now, just set g.user to None
            g.user = None
            # flash("Warning: Database is currently unavailable. User session cannot be fully verified.", "warning")


def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("You need to be logged in to access this page.", "warning")
            return redirect(url_for('login', next=request.url)) # Save current URL to redirect back after login
        return view(**kwargs)
    return wrapped_view

# --- Main Routes ---
# In app.py
@app.route('/')
def index():
    if g.user:
        # If user is already logged in, maybe show them the resume upload page or dashboard
        return render_template('idx2.html') # Or redirect(url_for('dashboard'))
    else:
        # If no user is logged in, redirect to the login page
        return redirect(url_for('login'))

# --- Authentication Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user: # If already logged in, redirect to dashboard
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        error = False

        if not username or not email or not password:
            flash('All fields are required.', 'error')
            error = True
        elif password != confirm_password:
            flash('Passwords do not match.', 'error')
            error = True
        
        if error: # If basic client-side style errors occurred
            return render_template('register.html', username=username, email=email)


        if DB_FUNCTIONS_AVAILABLE and db_connection_active:
            # Check if username or email already exists
            existing_user = get_user_by_username(username) # Or a new DB function get_user_by_username_or_email
            if existing_user: # Simplified check, you might want separate checks for username and email
                flash('Username already exists. Please choose a different one or login.', 'error') # Consider email check too
            # Add email existence check if desired:
            # elif get_user_by_email(email): # Assuming you would create this function
            #     flash('Email already registered. Please login or use a different email.', 'error')
            else:
                hashed_password = generate_password_hash(password)
                user_id = create_user(username, email, hashed_password)
                if user_id:
                    flash('Registration successful! Please login.', 'success')
                    return redirect(url_for('login'))
                else:
                    # This 'else' implies create_user returned None due to an internal error or race condition if user check failed
                    flash('Registration failed. An unexpected error occurred or user already exists.', 'error') # More specific message
        else:
            flash('Database not available. Registration is currently disabled.', 'error')
        
        # If any error occurred before successful registration or redirect to login
        return render_template('register.html', username=username, email=email) # Re-render with form data

    return render_template('register.html') # For GET request

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user: # If already logged in, redirect to dashboard
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html', username=username) # Re-render with username

        if DB_FUNCTIONS_AVAILABLE and db_connection_active:
            user = get_user_by_username(username) # user is a dict from DB
            if user and check_password_hash(user['password_hash'], password):
                session.clear() # Clear any old session data
                session['user_id'] = str(user['_id']) # Store user's MongoDB ObjectId as string in session
                session['username'] = user['username'] # Store username for display
                g.user = user # Make user globally available for this request
                flash('Login successful!', 'success')
                
                next_page = request.args.get('next') # For redirecting after login
                return redirect(next_page or url_for('dashboard')) # Redirect to 'next' or dashboard
            else:
                flash('Invalid username or password.', 'error')
        else:
            flash('Database not available. Login is currently disabled.', 'error')
        
        return render_template('login.html', username=username) # Re-render with username if login failed

    return render_template('login.html') # For GET request

@app.route('/logout')
def logout():
    session.clear() # Clear all session data
    g.user = None   # Clear global user object
    flash('You have been logged out.', 'success')
    return redirect(url_for('index')) # Redirect to home page

@app.route('/dashboard')
@login_required # Protect this route: only logged-in users can access
def dashboard():
    user_searches = []
    if DB_FUNCTIONS_AVAILABLE and db_connection_active and g.user: # Ensure user is loaded and DB is up
        # g.user['_id'] is an ObjectId, pass it as string if your DB function expects string
        user_searches = get_search_sessions_for_user(str(g.user['_id'])) 
    # Pass user_searches to the dashboard template
    return render_template('dashboard.html', user_searches=user_searches)


# --- API and Existing Routes ---
@app.route('/api/process_resume', methods=['POST'])
def process_resume_api():
    if not MODULES_LOADED_SUCCESSFULLY:
        return jsonify({"status": "error", "message": "Core application modules could not be loaded."}), 500

    if 'resume' not in request.files:
        return jsonify({"status": "error", "message": "No resume file part in the request."}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No resume file selected."}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Create a unique filename to prevent overwrites and for security
        unique_filename = str(uuid.uuid4()) + "_" + filename 
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        try:
            file.save(file_path)
            # This ID is for the specific search/processing event
            processing_session_id = str(uuid.uuid4()) 

            parsed_resume_output = process_resume_file_placeholder(file_path)
            raw_text = parsed_resume_output["raw_resume_text"]
            extracted_skills = parsed_resume_output["extracted_skills"]
            resume_score = parsed_resume_output["resume_score"]
            
            # Handle errors from resume processing
            if raw_text.startswith("Error processing resume:") or \
               raw_text.startswith("Error: Resume parser components not available.") or \
               raw_text.startswith("Error: Parser module"):
                 # More specific error for client based on parser output
                 return jsonify({"status": "error", "message": f"Resume Parsing Error: {raw_text}"}), 500 # Internal server error likely
            if raw_text == "No text could be extracted from the resume. The file might be image-based or corrupted.":
                return jsonify({"status": "error", "message": raw_text}), 400 # Bad request (bad file)


            personalized_job_results = []
            recommended_job_results = [] # Initialize recommended_job_results

            if extracted_skills:
                print(f"FLASK_APP: Scraping personalized jobs for skills: {extracted_skills[:5]}...")
                personalized_job_results = scrape_jobs(
                    keywords=extracted_skills, location=None, max_jobs_per_source=5, skills_json_path=None # Consider passing skills_json_path
                )

            # Fallback to recommended jobs if no personalized ones are found or no skills extracted
            if not personalized_job_results: # This covers cases of empty extracted_skills too
                print(f"FLASK_APP: No personalized jobs found or no skills. Scraping recommended jobs...")
                recommended_job_results = scrape_jobs(
                    keywords=PREDEFINED_SKILLS_KEYWORDS[:10], location=None, max_jobs_per_source=3, skills_json_path=None
                )
            
            # Get current user ID if a user is logged in
            current_user_id = str(g.user['_id']) if g.user else None

            if DB_FUNCTIONS_AVAILABLE and db_connection_active:
                print(f"FLASK_APP: Saving search session to DB: {processing_session_id} for user: {current_user_id}")
                save_personalized_search_session(
                    session_id=processing_session_id, # This is the search_id
                    resume_score=resume_score,
                    extracted_skills=extracted_skills,
                    personalized_job_results=personalized_job_results,
                    raw_resume_text=raw_text, # Save raw text if needed for history
                    user_id=current_user_id # Pass the user_id here
                )
                if recommended_job_results: # Save recommended jobs to their own cache if fetched
                    print(f"FLASK_APP: Saving {len(recommended_job_results)} recommended jobs to cache.")
                    for job in recommended_job_results:
                        save_recommended_job(job_data=job, source_keywords=PREDEFINED_SKILLS_KEYWORDS[:10]) # Or skills_extracted if preferred
            else: # Fallback if DB is not available - store in Flask session (temporary)
                print("FLASK_APP: DB not available or connection inactive. Results for this AJAX request are not saved persistently.")
                session_key_for_temp_results = 'temp_results_' + processing_session_id
                # Store all relevant data for potential display if DB is down
                session[session_key_for_temp_results] = {
                    'search_id': processing_session_id, # Redundant but clear
                    'resume_data': {'resume_score': resume_score, 'extracted_skills': extracted_skills, 'raw_text': raw_text},
                    'personalized_jobs': personalized_job_results,
                    'recommended_jobs': recommended_job_results # Include recommended here too
                }
                # flash("Database not available. Results are temporary and will be lost when session ends.", "warning") # Might be too noisy on AJAX

            return jsonify({
                "status": "success",
                "data": {
                    "search_id": processing_session_id, # This is crucial for linking to results page
                    "resume_data": {"resume_score": resume_score, "extracted_skills": extracted_skills},
                    "personalized_jobs": personalized_job_results,
                    "recommended_jobs": recommended_job_results # Send recommended jobs in response for immediate display
                }
            })

        except ValueError as ve: # Catch specific ValueError from process_resume_file_placeholder
             return jsonify({"status": "error", "message": str(ve)}), 400
        except Exception as e:
            print(f"Error during /api/process_resume: {e}")
            traceback.print_exc() # Log the full traceback for server-side debugging
            return jsonify({"status": "error", "message": f"An internal server error occurred: {str(e)}"}), 500
        finally:
            # Ensure uploaded file is deleted after processing
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e_remove:
                    print(f"Error removing uploaded file {file_path}: {e_remove}")
    else:
        return jsonify({"status": "error", "message": "Invalid file type. Allowed: PDF, DOC, DOCX."}), 400


@app.route('/results_page/<search_id>')
def show_results_page(search_id):
    search_data = None
    source = "Database" # Assume data is from DB initially
    can_clear_from_db = False # Flag to enable 'clear history' button in template

    if DB_FUNCTIONS_AVAILABLE and db_connection_active:
        search_data = get_personalized_search_session(search_id)

    # Fallback to temporary session if DB data not found or DB unavailable
    if not search_data and ('temp_results_' + search_id) in session:
        flash("Displaying temporary results as database is unavailable or data not found in DB.", "warning")
        search_data = session['temp_results_' + search_id]
        source = "Temporary Session"
        # Cannot clear from DB if it's from temporary session and not in DB
        can_clear_from_db = False 

    if not search_data:
        flash('No results found for this search ID, or the session has expired.', 'error')
        # Try to show some generic recommended jobs if main search data is missing
        recommended_jobs_fallback_display = []
        if DB_FUNCTIONS_AVAILABLE and db_connection_active:
            recommended_jobs_fallback_display = get_recommended_jobs_by_keywords(PREDEFINED_SKILLS_KEYWORDS[:5], limit=10)
        
        return render_template('idx2.html', # Or a dedicated error/results_not_found.html page
                               error_message='Search results not found.',
                               resume_data_display=None,
                               jobs_display=None,
                               recommended_jobs_display=recommended_jobs_fallback_display,
                               search_id_display=search_id, # Still pass search_id for context
                               results_source = "Fallback/Not Found")

    # Extract data for template (ensure keys exist)
    resume_data_display = search_data.get('resume_data', {})
    # Ensure score key is consistent for template, e.g. 'resume_score'
    if 'score' in resume_data_display and 'resume_score' not in resume_data_display:
        resume_data_display['resume_score'] = resume_data_display.pop('score')


    personalized_jobs_display = search_data.get('personalized_jobs', [])
    recommended_jobs_display = search_data.get('recommended_jobs', []) # Get from saved session if stored

    # Check if the logged-in user owns this search result (for DB-sourced data)
    # g.user is the user object (dict), g.user['_id'] is ObjectId
    # search_data.get('user_id') from DB is also ObjectId
    if source == "Database" and search_data.get('user_id') and g.user and search_data.get('user_id') == g.user['_id']:
        can_clear_from_db = True

    # If no jobs at all (neither personalized nor recommended in search_data), try to fetch some fresh recommended ones
    if not personalized_jobs_display and not recommended_jobs_display and DB_FUNCTIONS_AVAILABLE and db_connection_active:
        skills_for_rec = resume_data_display.get('extracted_skills', PREDEFINED_SKILLS_KEYWORDS[:5]) # Use extracted skills or fallback
        if skills_for_rec: # Only fetch if there are skills to use
            recommended_jobs_display = get_recommended_jobs_by_keywords(skills_for_rec, limit=10)
            if recommended_jobs_display:
                source += " (plus fresh recommended)" if source == "Database" else " (fresh recommended)"


    return render_template('idx2.html', # Or results.html if you have a separate one
                           resume_data_display=resume_data_display,
                           jobs_display=personalized_jobs_display,
                           recommended_jobs_display=recommended_jobs_display,
                           search_id_display=search_id,
                           results_source = source,
                           can_clear_this_result = can_clear_from_db # For showing clear button
                           )


@app.route('/clear_session_results/<search_id>')
@login_required # User must be logged in to clear their history
def clear_session_data_route(search_id):
    deletion_status = "error" # Default status
    search_doc_for_permission_check = None # Initialize

    if DB_FUNCTIONS_AVAILABLE and db_connection_active:
        # Fetch the document first to check ownership and existence
        search_doc_for_permission_check = get_personalized_search_session(search_id)

        if search_doc_for_permission_check and \
           search_doc_for_permission_check.get('user_id') and \
           g.user and \
           str(search_doc_for_permission_check.get('user_id')) == str(g.user['_id']):
            # User owns this record, proceed with deletion logic (which includes 1-year check)
            deletion_status = delete_personalized_search_session(search_id) # This function returns "deleted", "retained", "not_found", or "error"

            if deletion_status == "deleted":
                flash(f'Your search results (ID: {search_id}) were older than one year and have been successfully cleared.', 'success')
            elif deletion_status == "retained":
                flash(f'Your search results (ID: {search_id}) are less than one year old and have been retained. They were not deleted.', 'info')
            elif deletion_status == "not_found": # Should ideally not happen if search_doc_for_permission_check found it
                 flash(f'Could not clear results (ID: {search_id}). Record not found during deletion or already cleared.', 'warning')
            else: # "error" or any other unexpected status from delete_personalized_search_session
                flash(f'An error occurred trying to clear results (ID: {search_id}) from the database.', 'error')
        
        elif search_doc_for_permission_check: # Document exists but is not owned by the current user
             flash(f'You do not have permission to clear results for ID {search_id}.', 'error')
             deletion_status = "permission_denied" # More specific status
        else: # Document does not exist in DB (or user_id check failed earlier)
             flash(f'Search ID {search_id} not found in database, or you do not have permission to clear it.', 'info')
             deletion_status = "not_found_or_no_permission" # More specific
    else:
        flash('Database not available. Cannot clear persistent results.', 'error')
        deletion_status = "db_unavailable" # Specific status for DB issue

    # --- Clearing temporary session data from the browser session cache (if any) ---
    # This part is independent of DB deletion and should always be attempted for the current user's browser session
    temp_session_key = 'temp_results_' + search_id
    cleared_temp = False
    if temp_session_key in session:
        session.pop(temp_session_key, None)
        cleared_temp = True
        # Flash this only if it was the primary action or a successful secondary one.
        # Avoids message fatigue if a DB operation already gave significant feedback.
        if deletion_status not in ["deleted", "retained", "permission_denied"] or \
           (deletion_status in ["deleted", "retained"] and search_doc_for_permission_check): # If DB op was relevant
            flash(f'Temporary cached results for ID {search_id} (if any) have been cleared from this browser session.', 'success')
    
    # If no temp data was found and no significant DB message was already flashed about this specific search ID.
    if not cleared_temp and deletion_status not in ["deleted", "retained", "permission_denied", "not_found_or_no_permission", "db_unavailable"]:
        # This condition tries to avoid saying "no temp results" if a more important DB message was given
        # or if it was clear that the record itself wasn't found/accessible.
        is_no_db_action_related_to_this_id = (not search_doc_for_permission_check and deletion_status != "db_unavailable")
        if is_no_db_action_related_to_this_id or deletion_status == "error": # If DB error was generic, or no doc found
             flash(f'No active temporary results for ID {search_id} to clear from this browser session.', 'info')


    return redirect(url_for('dashboard')) # Redirect to dashboard to see updated list


if __name__ == '__main__':
    # Initial checks for module loading and DB connection
    if not MODULES_LOADED_SUCCESSFULLY:
        print("WARNING: One or more core project modules could not be loaded. Application functionality may be limited.")
    
    if DB_FUNCTIONS_AVAILABLE and not db_connection_active: # DB functions loaded, but connection failed
        print("WARNING: Database Manager was loaded, but connection to MongoDB failed during app startup. DB features will be impacted.")
    elif not DB_FUNCTIONS_AVAILABLE: # DB module itself not loaded
         print("WARNING: Database Manager module not loaded. Database operations will be skipped.")

    app.run(debug=True, port=5001) # debug=True is for development only