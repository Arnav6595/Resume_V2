import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, g, make_response
from werkzeug.utils import secure_filename
import traceback
from werkzeug.security import generate_password_hash, check_password_hash # For passwords
from functools import wraps # For login_required decorator
from datetime import datetime
import copy # For deepcopy
import re # For parsing Gemini's response
import json

# --- Load .env variables ---
from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file

# --- Google Generative AI SDK ---
GOOGLE_API_KEY_CONFIGURED = False
try:
    import google.generativeai as genai
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    if GOOGLE_API_KEY:
        genai.configure(api_key=GOOGLE_API_KEY)
        GOOGLE_API_KEY_CONFIGURED = True
        print("INFO: Google Generative AI SDK configured successfully.")
    else:
        print("WARNING: GOOGLE_API_KEY not found in environment variables. Gemini AI features will be disabled.")
except ImportError:
    print("WARNING: google-generativeai library not found. Gemini AI features will be disabled. Run 'pip install google-generativeai'")


# --- PDF Generation Library ---
WEASYPRINT_AVAILABLE = False
HTML, CSS = None, None
try:
    from weasyprint import HTML as WeasyHTML, CSS as WeasyCSS
    HTML = WeasyHTML
    CSS = WeasyCSS
    WEASYPRINT_AVAILABLE = True
    print("INFO: WeasyPrint library loaded successfully.")
except ImportError:
    print("WARNING: WeasyPrint library not found. PDF generation will be disabled.")

# --- Import your custom modules ---
MODULES_LOADED_SUCCESSFULLY = True
# ... (rest of your module imports remain the same) ...
try:
    from core.python_resume_parser_v9 import extract_text_from_pdf, AdvancedResumeParser
except ImportError as e:
    print(f"Error importing Resume Parser module (core.python_resume_parser_v9): {e}")
    MODULES_LOADED_SUCCESSFULLY = False
    def extract_text_from_pdf(path): return "Error: Parser module (core.python_resume_parser_v9) not loaded."
    class AdvancedResumeParser:
        def parse_resume(self, text):
            return {"metadata": {"resume_score": 0.0}, "skills": {"all_skills": []}}

try:
    from core.job_scrapper_api_v3 import scrape_jobs, PREDEFINED_SKILLS_KEYWORDS
except ImportError as e:
    print(f"Error importing Job Scrapper module (core.job_scrapper_api_v3): {e}")
    MODULES_LOADED_SUCCESSFULLY = False
    def scrape_jobs(keywords, location, max_jobs_per_source, skills_json_path): return []
    PREDEFINED_SKILLS_KEYWORDS = []

DB_FUNCTIONS_AVAILABLE = True
try:
    from core.database_manager import (
        connect_db,
        save_personalized_search_session,
        get_personalized_search_session,
        delete_personalized_search_session,
        save_recommended_job,
        get_recommended_jobs_by_keywords,
        create_user,
        get_user_by_username,
        get_user_by_id,
        get_search_sessions_for_user,
        create_user_resume,
        get_user_resumes,
        get_user_resume_by_id,
        update_user_resume,
        delete_user_resume
    )
    print("INFO: All database manager functions, including resume builder, loaded.")
except ImportError as e:
    print(f"Error importing Database Manager module (core.database_manager): {e}")
    print("Database operations will be skipped or limited.")
    DB_FUNCTIONS_AVAILABLE = False
    MODULES_LOADED_SUCCESSFULLY = False
    # Dummy DB functions ... (keep your dummy functions here)


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'a_very_strong_and_random_secret_key_for_prod_!123@')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}

RESUME_PDF_TEMPLATE = 'resume_pdf_template.html'

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.context_processor
def utility_processor():
    def get_current_year():
        # Corrected to use datetime.datetime.now(datetime.timezone.utc) for timezone-aware current time
        # However, for just the year, datetime.now().year or datetime.utcnow().year is simpler.
        # Using utcnow() as it's generally good practice for server-side timestamps.
        return datetime.utcnow().year
    return dict(current_year=get_current_year())

def process_resume_file_placeholder(pdf_path: str) -> dict:
    # This function remains as a placeholder for your actual resume processing logic
    print(f"FLASK_APP: Calling resume parser for: {pdf_path}")
    if "AdvancedResumeParser" not in globals() or "extract_text_from_pdf" not in globals():
         return {"raw_resume_text": "Error: Resume parser components not available.", "extracted_skills": [], "resume_score": 0.0}
    try:
        parser_instance = AdvancedResumeParser()
        raw_text = extract_text_from_pdf(pdf_path)
        if "Error: Parser module" in raw_text or "Error: Parser not loaded" in raw_text :
             raise ValueError(raw_text)
        if not raw_text or not raw_text.strip():
            if not raw_text and os.path.exists(pdf_path):
                 flash("Could not extract text from the PDF. It might be image-based or corrupted.", "error") # This flash won't be seen by API caller
            raise ValueError("No text could be extracted from the resume. The file might be image-based or corrupted.")
        parsed_data_from_parser = parser_instance.parse_resume(raw_text)
        resume_score = parsed_data_from_parser.get('metadata', {}).get('resume_score', 0.0)
        all_extracted_skills = parsed_data_from_parser.get('skills', {}).get('all_skills', [])
        return {"raw_resume_text": raw_text, "extracted_skills": all_extracted_skills, "resume_score": resume_score}
    except Exception as e:
        traceback.print_exc()
        print(f"Error in process_resume_file_placeholder: {e}")
        return {"raw_resume_text": f"Error processing resume: {str(e)}", "extracted_skills": [], "resume_score": 0.0}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db_connection_active = False
db_global_object = None
if DB_FUNCTIONS_AVAILABLE:
    try:
        db_object_from_connect = connect_db()
        if db_object_from_connect is not None:
            db_global_object = db_object_from_connect
            db_connection_active = True
            print("INFO: MongoDB connection established and active.")
        else:
            print("CRITICAL: Failed to connect to MongoDB. Database operations will be impacted.")
    except Exception as e_connect:
        print(f"CRITICAL: MongoDB connection failed on startup: {e_connect}")
else:
    print("INFO: Database functions are not available. DB operations will be skipped.")

@app.before_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        if DB_FUNCTIONS_AVAILABLE and db_connection_active:
            g.user = get_user_by_id(user_id) 
            if g.user:
                session['username'] = g.user.get('username') 
            else: 
                session.clear()
                g.user = None
        else:
            g.user = None

def login_required(view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash("You need to be logged in to access this page.", "warning")
            return redirect(url_for('login', next=request.url))
        return view(**kwargs)
    return wrapped_view


# --- Gemini AI Integration Function ---
def call_gemini_to_enhance_resume(original_sections_data, user_custom_prompt):
    """
    Calls the Gemini API to enhance resume content based on user prompt.
    """
    print("---- DEBUG: START call_gemini_to_enhance_resume ----")
    # import json # Already imported at the top
    # print("---- Input original_sections_data: ----")
    # print(json.dumps(original_sections_data, indent=2))


    if not GOOGLE_API_KEY_CONFIGURED:
        flash("Gemini AI service is not configured. Using basic processing.", "error")
        enhanced_data = copy.deepcopy(original_sections_data)
        # Modify summary in personal_info if it exists, otherwise the top-level summary
        if 'personal_info' in enhanced_data and isinstance(enhanced_data['personal_info'], dict):
            summary_val = enhanced_data['personal_info'].get('summary', '')
            enhanced_data['personal_info']['summary'] = summary_val + \
                f"\n\n[AI Note (Service Not Configured): User Prompt was '{user_custom_prompt}'.]"
        elif 'summary' in enhanced_data:
            enhanced_data['summary'] = enhanced_data.get('summary', '') + \
                 f"\n\n[AI Note (Service Not Configured): User Prompt was '{user_custom_prompt}'.]"
        return enhanced_data

    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')

        # --- 1. Format resume data into a text block for Gemini ---
        text_for_gemini = "Current Resume Content:\n"
        pi = original_sections_data.get('personal_info', {})
        if isinstance(pi, dict): # Ensure pi is a dict
            text_for_gemini += f"  Name: {pi.get('full_name', 'N/A')}\n" # Changed 'name' to 'full_name'
            contact_parts = [pi.get('email'), pi.get('phone'), pi.get('location')]
            contact_str = " | ".join(filter(None, contact_parts))
            if contact_str:
                text_for_gemini += f"  Contact: {contact_str}\n"
        
        # Use the top-level summary key as it's used by the PDF template
        actual_summary = original_sections_data.get('summary', '')
        if actual_summary:
            text_for_gemini += "  Summary:\n" + actual_summary + "\n\n"
        else:
            text_for_gemini += "  Summary: [Not provided or empty]\n\n"


        experience_list = original_sections_data.get('experience', [])
        if isinstance(experience_list, list) and experience_list:
            text_for_gemini += "  Experience:\n"
            for i, exp in enumerate(experience_list[:2]): # Send first 2 experiences
                if isinstance(exp, dict):
                    text_for_gemini += f"    Job {i+1}:\n"
                    text_for_gemini += f"      Title: {exp.get('job_title', 'N/A')}\n"
                    text_for_gemini += f"      Company: {exp.get('company', 'N/A')}\n"
                    text_for_gemini += f"      Dates: {exp.get('start_date', '')} - {exp.get('end_date', '')}\n"
                    responsibilities = exp.get('responsibilities', []) # Key used by JS and PDF
                    if isinstance(responsibilities, list) and responsibilities:
                        text_for_gemini += "      Description (Responsibilities):\n" + "\n".join([f"        - {item}" for item in responsibilities]) + "\n"
                    elif isinstance(responsibilities, str) and responsibilities:
                         text_for_gemini += f"      Description (Responsibilities): {responsibilities}\n"
                    else:
                        text_for_gemini += "      Description (Responsibilities): [Not provided or empty]\n"
            text_for_gemini += "\n"

        skills_list = original_sections_data.get('skills', []) # Key used by JS and PDF
        if isinstance(skills_list, list) and skills_list:
            text_for_gemini += "  Current Skills:\n" + ", ".join(skills_list) + "\n\n"
        else:
            text_for_gemini += "  Current Skills: [Not provided or empty]\n\n"
        
        # Consider adding Education, Projects in a similar detailed manner if they need to be enhanced.

        if len(text_for_gemini) < len("Current Resume Content:\n") + 50: # Check if substantial content was added
            text_for_gemini += "  [Other sections like Education, Projects might exist but are not detailed here for brevity unless specifically targeted by the user's prompt.]"


        # --- 2. Construct the full prompt for Gemini ---
        full_prompt_to_gemini = f"""
        You are an expert AI resume writing assistant. Your task is to enhance the provided resume content based on the user's specific goal.

        User's Goal: "{user_custom_prompt}"

        {text_for_gemini}
        --------------------------------

        Instructions for AI:
        1. Analyze the "User's Goal" and the "Current Resume Content".
        2. Generate enhanced text *only* for the sections explicitly mentioned or clearly implied by the "User's Goal" AND for which content was provided above.
        3. Structure your response clearly. For each section you modify, use these specific start and end markers:
           - For the summary: Start with "AI_ENHANCED_SUMMARY_START" on a new line, then the enhanced summary text, and end with "AI_ENHANCED_SUMMARY_END" on a new line.
           - For the first job experience's responsibilities: Start with "AI_ENHANCED_EXPERIENCE_1_RESPONSIBILITIES_START", then the enhanced responsibilities (as a list of bullet points, each starting with '- ' on a new line if the original was a list), and end with "AI_ENHANCED_EXPERIENCE_1_RESPONSIBILITIES_END".
           - For the second job experience's responsibilities (if applicable): Use "AI_ENHANCED_EXPERIENCE_2_RESPONSIBILITIES_START" and "AI_ENHANCED_EXPERIENCE_2_RESPONSIBILITIES_END".
           - For skills: Start with "AI_ENHANCED_SKILLS_START", then a comma-separated list of all skills (original plus any additions or modifications based on the user's goal), and end with "AI_ENHANCED_SKILLS_END".
        4. If the user asks to "add a skill X", ensure "X" is included in the comma-separated list in the skills output.
        5. If content for a requested section was marked as "[Not provided or empty]" in the input, and the user goal is to enhance it, state that you cannot enhance non-existent content for that section within your markers, e.g., "AI_ENHANCED_SUMMARY_START\n(No original summary was provided to enhance.)\nAI_ENHANCED_SUMMARY_END".
        6. Return *only* the enhanced sections with their specified start/end markers. Do not add any conversational text, apologies, or greetings outside these markers. Each marked section should be on new lines.
        """

        print(f"DEBUG: Sending prompt to Gemini (first 500 chars):\n{full_prompt_to_gemini[:500]}...")

        model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
        response = model.generate_content(full_prompt_to_gemini)
        
        gemini_text_response = ""
        if not response.parts:
            gemini_text_response = response.text
            if not gemini_text_response:
                if response.candidates and response.candidates[0].content.parts:
                    gemini_text_response = "".join(part.text for part in response.candidates[0].content.parts)
                else:
                    gemini_text_response = "[GEMINI RESPONSE WAS EMPTY OR MALFORMED]"
        else:
            gemini_text_response = "".join(part.text for part in response.parts)

        print(f"---- DEBUG: RAW GEMINI RESPONSE ----\n{gemini_text_response}\n---- END DEBUG ----")

        # --- 4. Parse Gemini's response and update sections_data ---
        enhanced_data = copy.deepcopy(original_sections_data)

        # Parse Summary
        summary_match = re.search(r"AI_ENHANCED_SUMMARY_START\s*(.*?)\s*AI_ENHANCED_SUMMARY_END", gemini_text_response, re.DOTALL | re.IGNORECASE)
        if summary_match:
            enhanced_summary = summary_match.group(1).strip()
            enhanced_data['summary'] = enhanced_summary # Update top-level summary for PDF
            if 'personal_info' not in enhanced_data or not isinstance(enhanced_data['personal_info'], dict):
                enhanced_data['personal_info'] = {} # Should already exist from deepcopy if it was there
            enhanced_data['personal_info']['summary'] = enhanced_summary # Keep consistent if used elsewhere
            print(f"INFO: Updated summary from Gemini response: '{enhanced_summary[:100]}...'")
        else:
            print("WARNING: Did NOT find 'AI_ENHANCED_SUMMARY_START' markers in Gemini response. Summary not updated from AI.")

        # Parse Experience Responsibilities
        for i in range(2): # Max 2 experiences sent
            exp_start_marker = f"AI_ENHANCED_EXPERIENCE_{i+1}_RESPONSIBILITIES_START"
            exp_end_marker = f"AI_ENHANCED_EXPERIENCE_{i+1}_RESPONSIBILITIES_END"
            exp_match = re.search(rf"{exp_start_marker}\s*(.*?)\s*{exp_end_marker}", gemini_text_response, re.DOTALL | re.IGNORECASE)
            
            if exp_match and 'experience' in enhanced_data and \
               isinstance(enhanced_data.get('experience'), list) and len(enhanced_data['experience']) > i and \
               isinstance(enhanced_data['experience'][i], dict):
                
                enhanced_responsibilities_text = exp_match.group(1).strip()
                if enhanced_responsibilities_text:
                    # Convert bulleted list from Gemini into a list of strings
                    parsed_responsibilities = [
                        point.replace("-","",1).strip() for point in enhanced_responsibilities_text.split('\n') 
                        if point.strip() and (point.strip().startswith("-") or point.strip()) # Accept lines starting with - or any non-empty line if not bulleted
                    ]
                    if not parsed_responsibilities and enhanced_responsibilities_text: # If splitting by newline didn't work well (e.g. single paragraph)
                        parsed_responsibilities = [enhanced_responsibilities_text]

                    enhanced_data['experience'][i]['responsibilities'] = parsed_responsibilities
                    print(f"INFO: Updated experience {i+1} responsibilities from Gemini response.")
                else:
                    print(f"INFO: Gemini returned empty content for experience {i+1} responsibilities.")
            # else:
                # print(f"WARNING: Did not find markers for experience {i+1} responsibilities or data structure issue.")


        # Parse Skills
        skills_match = re.search(r"AI_ENHANCED_SKILLS_START\s*(.*?)\s*AI_ENHANCED_SKILLS_END", gemini_text_response, re.DOTALL | re.IGNORECASE)
        if skills_match:
            enhanced_skills_str = skills_match.group(1).strip()
            if enhanced_skills_str:
                enhanced_data['skills'] = [s.strip() for s in enhanced_skills_str.split(',') if s.strip()]
                print(f"INFO: Successfully parsed and updated skills from Gemini: {enhanced_data['skills']}")
            else:
                print("WARNING: 'AI_ENHANCED_SKILLS_START'...'AI_ENHANCED_SKILLS_END' markers found, but content was empty. Skills not updated from AI.")
        else:
            print("WARNING: Did NOT find 'AI_ENHANCED_SKILLS_START'...'AI_ENHANCED_SKILLS_END' markers in Gemini response. Skills not updated from AI.")
        
        flash("Resume content processed with Gemini AI. Review the generated PDF.", "success")
        return enhanced_data

    except Exception as e:
        print(f"ERROR: Error during Gemini API call or processing: {e}")
        traceback.print_exc()
        flash(f"An error occurred while communicating with the AI service: {str(e)}. Using basic processing instead.", "error")
        enhanced_data = copy.deepcopy(original_sections_data) # Fallback
        error_note = f"\n\n[AI Note (Error: {str(e)[:50]}...): User Prompt was '{user_custom_prompt}'. AI processing failed.]"
        if 'summary' in enhanced_data:
            enhanced_data['summary'] = enhanced_data.get('summary', '') + error_note
        elif 'personal_info' in enhanced_data and isinstance(enhanced_data.get('personal_info'), dict):
            enhanced_data['personal_info']['summary'] = enhanced_data['personal_info'].get('summary', '') + error_note
        return enhanced_data


# --- Main Application Routes (index, register, login, logout, dashboard) ---
@app.route('/')
def index():
    if g.user: 
        return render_template('idx2.html') 
    else:
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if g.user: 
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        error = False
        if not username or not email or not password:
            flash('All fields are required.', 'error'); error = True
        elif password != confirm_password:
            flash('Passwords do not match.', 'error'); error = True
        
        if error: 
            return render_template('register.html', username=username, email=email)

        if DB_FUNCTIONS_AVAILABLE and db_connection_active:
            existing_user = get_user_by_username(username) 
            if existing_user:
                flash('Username already exists. Please choose a different one or login.', 'error')
            else:
                hashed_password = generate_password_hash(password)
                user_id = create_user(username, email, hashed_password) 
                if user_id:
                    flash('Registration successful! Please login.', 'success')
                    return redirect(url_for('login'))
                else:
                    flash('Registration failed. An unexpected error occurred or user already exists.', 'error')
        else:
            flash('Database not available. Registration is currently disabled.', 'error')
        return render_template('register.html', username=username, email=email)
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user: 
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html', username=username)

        if DB_FUNCTIONS_AVAILABLE and db_connection_active:
            user = get_user_by_username(username) 
            if user and check_password_hash(user['password_hash'], password):
                session.clear() 
                session['user_id'] = str(user['_id']) 
                session['username'] = user['username'] 
                g.user = user 
                flash('Login successful!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard')) 
            else:
                flash('Invalid username or password.', 'error')
        else:
            flash('Database not available. Login is currently disabled.', 'error')
        return render_template('login.html', username=username) 
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    g.user = None
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_searches = []
    if DB_FUNCTIONS_AVAILABLE and db_connection_active and g.user:
        user_searches = get_search_sessions_for_user(str(g.user['_id'])) 
    return render_template('dashboard.html', user_searches=user_searches)


# --- Resume Builder Routes ---
@app.route('/resume-builder')
@login_required
def resume_builder_dashboard():
    user_built_resumes = []
    if DB_FUNCTIONS_AVAILABLE and db_connection_active:
        user_built_resumes = get_user_resumes(str(g.user['_id'])) 
    return render_template('resume_builder_dashboard.html', user_resumes=user_built_resumes)

@app.route('/resume-builder/new', methods=['GET', 'POST'])
@login_required
def resume_builder_new():
    if request.method == 'POST':
        if not DB_FUNCTIONS_AVAILABLE or not db_connection_active:
            return jsonify({"status": "error", "message": "Database unavailable"}), 503 
        try:
            data = request.get_json() 
            if not data:
                return jsonify({"status": "error", "message": "No data received"}), 400
            resume_name = data.get('resume_name')
            sections_data = data.get('sections')
            if not resume_name or not sections_data or not isinstance(sections_data, dict):
                return jsonify({"status": "error", "message": "Invalid data: Resume name and sections object are required."}), 400
            new_resume_id = create_user_resume(str(g.user['_id']), resume_name, sections_data) 
            if new_resume_id:
                flash('Resume created successfully!', 'success') 
                return jsonify({"status": "success", "message": "Resume created", "redirect_url": url_for('resume_builder_dashboard')})
            else:
                return jsonify({"status": "error", "message": "Failed to save resume to database"}), 500
        except Exception as e:
            print(f"Error in POST /resume-builder/new: {e}")
            traceback.print_exc()
            return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500
    return render_template('resume_builder_form.html', resume_data=None, form_action=url_for('resume_builder_new'))

@app.route('/resume-builder/<resume_id>/edit', methods=['GET', 'POST'])
@login_required
def resume_builder_edit(resume_id):
    if not DB_FUNCTIONS_AVAILABLE or not db_connection_active:
        if request.method == 'POST': # For AJAX calls
             return jsonify({"status": "error", "message": "Database unavailable"}), 503
        else: # For GET requests
            flash('Database not available. Cannot edit resume.', 'error')
            return redirect(url_for('resume_builder_dashboard'))

    if request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                 return jsonify({"status": "error", "message": "No data received for update"}), 400
            new_resume_name = data.get('resume_name')
            updated_sections_data = data.get('sections')
            if not new_resume_name and not updated_sections_data: 
                 return jsonify({"status": "info", "message": "No changes submitted", "redirect_url": url_for('resume_builder_dashboard')})
            success = update_user_resume(resume_id, str(g.user['_id']), 
                                         updated_resume_data=updated_sections_data, 
                                         new_resume_name=new_resume_name) 
            if success:
                flash('Resume updated successfully!', 'success') 
                return jsonify({"status": "success", "message": "Resume updated", "redirect_url": url_for('resume_builder_dashboard')})
            else:
                 return jsonify({"status": "error", "message": "Failed to update resume or no permission"}), 500
        except Exception as e:
            print(f"Error in POST /resume-builder/.../edit: {e}")
            traceback.print_exc()
            return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500
    
    existing_resume_data = get_user_resume_by_id(resume_id, str(g.user['_id'])) 
    if not existing_resume_data:
        flash('Resume not found or you do not have permission to edit it.', 'error')
        return redirect(url_for('resume_builder_dashboard'))
    return render_template('resume_builder_form.html', resume_data=existing_resume_data, form_action=url_for('resume_builder_edit', resume_id=resume_id))

@app.route('/resume-builder/<resume_id>/delete', methods=['POST'])
@login_required
def resume_builder_delete(resume_id):
    if not DB_FUNCTIONS_AVAILABLE or not db_connection_active:
        flash('Database not available. Cannot delete resume.', 'error')
    else:
        success = delete_user_resume(resume_id, str(g.user['_id'])) 
        if success:
            flash('Resume deleted successfully.', 'success')
        else:
            flash('Failed to delete resume or permission denied.', 'error')
    return redirect(url_for('resume_builder_dashboard'))


@app.route('/resume-builder/<resume_id>/download_pdf')
@login_required
def resume_builder_download_pdf(resume_id):
    if not WEASYPRINT_AVAILABLE:
        flash("PDF generation service is currently unavailable. Please try again later.", "error")
        return redirect(url_for('resume_builder_dashboard'))
    if not DB_FUNCTIONS_AVAILABLE or not db_connection_active:
        flash('Database not available. Cannot fetch resume data for PDF generation.', 'error')
        return redirect(url_for('resume_builder_dashboard'))
    resume_doc = get_user_resume_by_id(resume_id, str(g.user['_id'])) 
    if not resume_doc:
        flash('Resume not found or you do not have permission to download it.', 'error')
        return redirect(url_for('resume_builder_dashboard'))
    resume_data_for_template = resume_doc.get('sections', {})
    resume_name_for_file = resume_doc.get('resume_name', 'resume')
    safe_resume_name = secure_filename(resume_name_for_file) if resume_name_for_file else "resume"
    try:
        html_string = render_template(RESUME_PDF_TEMPLATE, 
                                      resume=resume_data_for_template, 
                                      resume_doc=resume_doc)
        pdf_stylesheets = []
        css_file_path = os.path.join(app.static_folder, 'css', 'resume_pdf_styles.css') 
        if os.path.exists(css_file_path) and CSS is not None: 
            pdf_stylesheets.append(CSS(filename=css_file_path))
        else:
            if CSS is not None: 
                 print(f"WARNING: PDF CSS file not found at {css_file_path} or CSS class not loaded. Using minimal default styles.")
            basic_pdf_css_string = """
                @page { size: A4; margin: 1.5cm; }
                body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; font-size: 10pt; line-height: 1.4; color: #333; }"""
            if CSS is not None: 
                pdf_stylesheets.append(CSS(string=basic_pdf_css_string))
        if HTML is None: 
            raise ImportError("WeasyPrint HTML class not loaded, cannot generate PDF.")
        pdf_bytes = HTML(string=html_string, base_url=request.url_root).write_pdf(stylesheets=pdf_stylesheets if pdf_stylesheets else None)
        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{safe_resume_name}.pdf"'
        return response
    except FileNotFoundError: 
        print(f"ERROR: PDF template '{RESUME_PDF_TEMPLATE}' not found.")
        flash(f"PDF template '{RESUME_PDF_TEMPLATE}' is missing. Cannot generate PDF.", "error")
    except ImportError as ie: 
        print(f"Error during PDF generation due to missing WeasyPrint components: {ie}")
        flash("PDF generation failed due to a setup issue. Please contact support.", "error")
    except Exception as e:
        print(f"Error generating PDF for resume ID {resume_id}: {e}")
        traceback.print_exc()
        flash("An error occurred while generating the PDF. Please try again.", "error")
    return redirect(url_for('resume_builder_dashboard'))


# --- NEW: Resume Builder AI Enhancement Routes ---
@app.route('/resume-builder/<resume_id>/enhance', methods=['GET'])
@login_required
def resume_builder_enhance_prompt_page(resume_id):
    if not DB_FUNCTIONS_AVAILABLE or not db_connection_active:
        flash('Database not available. Cannot load resume for enhancement.', 'error')
        return redirect(url_for('resume_builder_dashboard'))

    resume_doc = get_user_resume_by_id(resume_id, str(g.user['_id']))
    if not resume_doc:
        flash('Resume not found or you do not have permission to access it.', 'error')
        return redirect(url_for('resume_builder_dashboard'))

    return render_template('resume_builder_enhance_prompt.html', 
                           resume_name=resume_doc.get('resume_name', 'Untitled Resume'),
                           resume_id=resume_id)

@app.route('/resume-builder/<resume_id>/process-ai', methods=['POST'])
@login_required
def resume_builder_process_with_ai(resume_id):
    if not WEASYPRINT_AVAILABLE:
        flash("PDF generation service is currently unavailable. Cannot process with AI.", "error")
        return redirect(url_for('resume_builder_enhance_prompt_page', resume_id=resume_id))

    if not DB_FUNCTIONS_AVAILABLE or not db_connection_active:
        flash('Database not available. Cannot fetch resume data for AI processing.', 'error')
        return redirect(url_for('resume_builder_enhance_prompt_page', resume_id=resume_id))

    user_prompt = request.form.get('user_prompt', '').strip()
    if not user_prompt:
        flash('Please provide a prompt to guide the AI.', 'warning')
        return redirect(url_for('resume_builder_enhance_prompt_page', resume_id=resume_id))

    original_resume_doc = get_user_resume_by_id(resume_id, str(g.user['_id']))
    if not original_resume_doc:
        flash('Original resume not found or permission denied.', 'error')
        return redirect(url_for('resume_builder_dashboard'))

    original_sections_data = original_resume_doc.get('sections', {})
    original_resume_name = original_resume_doc.get('resume_name', 'UntitledResume')
    
    enhanced_sections_data = call_gemini_to_enhance_resume(original_sections_data, user_prompt)
    
    safe_resume_name = secure_filename(original_resume_name + "_AI_Enhanced")
    
    print("---- DEBUG: FINAL ENHANCED DATA TO PDF TEMPLATE ----")
    # import json # Already imported at the top
    print(json.dumps(enhanced_sections_data, indent=2))
    print("---- END DEBUG ----")

    try:
        html_string = render_template(RESUME_PDF_TEMPLATE,
                                      resume=enhanced_sections_data, 
                                      resume_doc=original_resume_doc 
                                     )
        pdf_stylesheets = []
        css_file_path = os.path.join(app.static_folder, 'css', 'resume_pdf_styles.css')
        if WEASYPRINT_AVAILABLE and CSS and os.path.exists(css_file_path):
            pdf_stylesheets.append(CSS(filename=css_file_path))
        elif WEASYPRINT_AVAILABLE and CSS:
             print(f"WARNING: PDF CSS file not found at {css_file_path}. Using minimal default styles for AI enhanced PDF.")
             basic_pdf_css_string = "@page { size: A4; margin: 1.5cm; } body { font-family: sans-serif; font-size: 10pt; line-height: 1.4; }"
             pdf_stylesheets.append(CSS(string=basic_pdf_css_string))

        if not WEASYPRINT_AVAILABLE or not HTML:
            raise ImportError("WeasyPrint HTML or CSS components not loaded, cannot generate AI enhanced PDF.")

        pdf_bytes = HTML(string=html_string, base_url=request.url_root).write_pdf(stylesheets=pdf_stylesheets if pdf_stylesheets else None)

        response = make_response(pdf_bytes)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{safe_resume_name}.pdf"'
        return response

    except FileNotFoundError:
        print(f"ERROR: PDF template '{RESUME_PDF_TEMPLATE}' not found for AI enhanced PDF.")
        flash(f"PDF template '{RESUME_PDF_TEMPLATE}' is missing. Cannot generate AI enhanced PDF.", "error")
    except ImportError as ie:
        print(f"Error during AI PDF generation due to missing WeasyPrint components: {ie}")
        flash("PDF generation failed for AI enhanced resume due to a setup issue. Please contact support.", "error")
    except Exception as e:
        print(f"Error generating AI enhanced PDF for resume ID {resume_id}: {e}")
        traceback.print_exc()
        flash("An error occurred while generating the AI enhanced PDF. Please try again.", "error")
    
    return redirect(url_for('resume_builder_enhance_prompt_page', resume_id=resume_id))


# --- API and Existing Routes (Resume Parser/Job Scraper) ---
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
        unique_filename = str(uuid.uuid4()) + "_" + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        try:
            file.save(file_path)
            processing_session_id = str(uuid.uuid4())
            parsed_resume_output = process_resume_file_placeholder(file_path) 
            raw_text = parsed_resume_output["raw_resume_text"]
            extracted_skills = parsed_resume_output["extracted_skills"]
            resume_score = parsed_resume_output["resume_score"]
            if raw_text.startswith("Error processing resume:") or \
               raw_text.startswith("Error: Resume parser components not available.") or \
               raw_text.startswith("Error: Parser module"):
                 return jsonify({"status": "error", "message": f"Resume Parsing Error: {raw_text}"}), 500
            if raw_text == "No text could be extracted from the resume. The file might be image-based or corrupted.": 
                return jsonify({"status": "error", "message": raw_text}), 400
            personalized_job_results = []
            recommended_job_results = [] 
            if extracted_skills:
                print(f"FLASK_APP: Scraping jobs with extracted skills: {extracted_skills[:5]}")
                personalized_job_results = scrape_jobs( 
                    keywords=extracted_skills, location=None, max_jobs_per_source=5, skills_json_path=None 
                )
            if not personalized_job_results: 
                print("FLASK_APP: No personalized jobs found, scraping with recommended keywords.")
                recommended_job_results = scrape_jobs( 
                    keywords=PREDEFINED_SKILLS_KEYWORDS[:10], location=None, max_jobs_per_source=3, skills_json_path=None
                )
            current_user_id = str(g.user['_id']) if g.user else None
            if DB_FUNCTIONS_AVAILABLE and db_connection_active:
                save_personalized_search_session( 
                    session_id=processing_session_id,
                    resume_score=resume_score,
                    extracted_skills=extracted_skills,
                    personalized_job_results=personalized_job_results,
                    raw_resume_text=raw_text,
                    user_id=current_user_id
                )
                if recommended_job_results: 
                    for job in recommended_job_results:
                        save_recommended_job(job_data=job, source_keywords=PREDEFINED_SKILLS_KEYWORDS[:10]) 
            else: 
                session_key_for_temp_results = 'temp_results_' + processing_session_id
                session[session_key_for_temp_results] = {
                    'search_id': processing_session_id,
                    'resume_data': {'resume_score': resume_score, 'extracted_skills': extracted_skills, 'raw_text': raw_text},
                    'personalized_jobs': personalized_job_results,
                    'recommended_jobs': recommended_job_results 
                }
                print(f"FLASK_APP: Saved results to session key: {session_key_for_temp_results}")
            return jsonify({
                "status": "success",
                "data": {
                    "search_id": processing_session_id,
                    "resume_data": {"resume_score": resume_score, "extracted_skills": extracted_skills}, 
                    "personalized_jobs": personalized_job_results,
                    "recommended_jobs": recommended_job_results 
                }
            })
        except ValueError as ve: 
             return jsonify({"status": "error", "message": str(ve)}), 400
        except Exception as e:
            traceback.print_exc() 
            return jsonify({"status": "error", "message": f"An internal server error occurred: {str(e)}"}), 500
        finally:
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e_remove:
                    print(f"Error removing uploaded file {file_path}: {e_remove}")
    else:
        return jsonify({"status": "error", "message": "Invalid file type. Allowed: PDF, DOC, DOCX."}), 400

@app.route('/results_page/<search_id>')
def show_results_page(search_id):
    search_data = None; source = "Database"; can_clear_from_db = False
    if DB_FUNCTIONS_AVAILABLE and db_connection_active:
        search_data = get_personalized_search_session(search_id) 
    if not search_data and ('temp_results_' + search_id) in session: 
        flash("Displaying temporary results as database is unavailable or data not found in DB.", "warning")
        search_data = session['temp_results_' + search_id]; source = "Temporary Session"; can_clear_from_db = False
    if not search_data:
        flash('No results found for this search ID, or the session has expired.', 'error')
        recommended_jobs_fallback_display = []
        if DB_FUNCTIONS_AVAILABLE and db_connection_active: 
            recommended_jobs_fallback_display = get_recommended_jobs_by_keywords(PREDEFINED_SKILLS_KEYWORDS[:5], limit=10) 
        return render_template('idx2.html', error_message='Search results not found.', resume_data_display=None,
                               jobs_display=None, recommended_jobs_display=recommended_jobs_fallback_display,
                               search_id_display=search_id, results_source = "Fallback/Not Found")
    resume_data_display = search_data.get('resume_data', {})
    if 'score' in resume_data_display and 'resume_score' not in resume_data_display:
        resume_data_display['resume_score'] = resume_data_display.pop('score')
    personalized_jobs_display = search_data.get('personalized_jobs', [])
    recommended_jobs_display = search_data.get('recommended_jobs', []) 
    if source == "Database" and search_data.get('user_id') and g.user and \
       str(search_data.get('user_id')) == str(g.user['_id']):
        can_clear_from_db = True
    if not personalized_jobs_display and not recommended_jobs_display and DB_FUNCTIONS_AVAILABLE and db_connection_active:
        skills_for_rec = resume_data_display.get('extracted_skills', PREDEFINED_SKILLS_KEYWORDS[:5]) 
        if skills_for_rec: 
            recommended_jobs_display = get_recommended_jobs_by_keywords(skills_for_rec, limit=10) 
            if recommended_jobs_display: source += " (plus fresh recommended)" if source == "Database" else " (fresh recommended)"
    return render_template('idx2.html', resume_data_display=resume_data_display, jobs_display=personalized_jobs_display,
                           recommended_jobs_display=recommended_jobs_display, search_id_display=search_id,
                           results_source = source, can_clear_this_result = can_clear_from_db)

@app.route('/clear_session_results/<search_id>')
@login_required
def clear_session_data_route(search_id):
    deletion_status = "error"; search_doc_for_permission_check = None
    if DB_FUNCTIONS_AVAILABLE and db_connection_active:
        search_doc_for_permission_check = get_personalized_search_session(search_id) 
        if search_doc_for_permission_check and \
           search_doc_for_permission_check.get('user_id') and \
           g.user and \
           str(search_doc_for_permission_check.get('user_id')) == str(g.user['_id']): 
            deletion_status = delete_personalized_search_session(search_id) 
            if deletion_status == "deleted": flash(f'Search results (ID: {search_id}) older than one year cleared from database.', 'success')
            elif deletion_status == "retained": flash(f'Search results (ID: {search_id}) are recent and retained in database.', 'info')
            elif deletion_status == "not_found": flash(f'Could not clear from database (ID: {search_id}). Record not found or already cleared.', 'warning')
            else: flash(f'Error clearing results from database (ID: {search_id}).', 'error')
        elif search_doc_for_permission_check: 
            flash(f'You do not have permission to clear database results for ID {search_id}.', 'error')
            deletion_status = "permission_denied"
        else: 
            flash(f'Search ID {search_id} not found in database or no permission.', 'info')
            deletion_status = "not_found_or_no_permission"
    else: 
        flash('Database unavailable. Cannot clear results from database.', 'error')
        deletion_status = "db_unavailable"
    temp_session_key = 'temp_results_' + search_id; cleared_temp = False
    if temp_session_key in session:
        session.pop(temp_session_key, None)
        cleared_temp = True
    if cleared_temp and deletion_status not in ["deleted", "retained", "permission_denied"]:
        flash(f'Temporary cached results for ID {search_id} cleared from this browser session.', 'success')
    elif not cleared_temp and deletion_status not in ["deleted", "retained", "permission_denied", "not_found_or_no_permission", "db_unavailable"]:
        is_no_db_action_related_to_this_id = (not search_doc_for_permission_check and deletion_status != "db_unavailable")
        if is_no_db_action_related_to_this_id or deletion_status == "error": 
             flash(f'No active temporary results for ID {search_id} to clear from this browser session.', 'info')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    if not MODULES_LOADED_SUCCESSFULLY:
        print("WARNING: One or more core project modules could not be loaded. Application functionality may be limited.")
    if DB_FUNCTIONS_AVAILABLE and not db_connection_active:
        print("WARNING: Database Manager was loaded, but connection to MongoDB failed during app startup. DB features will be impacted.")
    elif not DB_FUNCTIONS_AVAILABLE:
         print("WARNING: Database Manager module not loaded. Database operations will be skipped.")
    app.run(debug=True, port=5001)


