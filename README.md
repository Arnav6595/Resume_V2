# AI Resume Parser, Builder & Job Matcher

## 🚀 Description

This project is a Flask web application designed to help users analyze their existing resumes, build new ones from scratch, and find relevant job opportunities.

**Resume Analysis & Job Matching:** Users can upload their resume (PDF format), which is then parsed to extract key information such as skills, experience, and education. The system also calculates a resume score. Based on the extracted skills, it fetches job listings from various APIs. If no specific skills are found or they yield few results, predefined keywords are used to suggest general job opportunities.

**Resume Builder:** Users can create professional resumes section by section using a guided form. They can save these created resumes, edit them, and download them as PDFs.

**AI Enhancement (Resume Builder):** For resumes created with the builder, users can leverage Google's Gemini AI to enhance the content based on custom prompts (e.g., "make the summary more professional," "add specific skills").

All processing results, including parsed resume data, job listings, and user-created resumes, are stored in a MongoDB Atlas database.

## ✨ Features

* **Resume Upload & Analysis:**
    * Supports PDF resume uploads.
    * **Advanced Resume Parsing:** Extracts contact information, summary, skills (categorized and overall), work experience, education, projects, certifications, and languages.
    * **Resume Scoring:** Provides a heuristic-based score for uploaded resumes.
* **Job Matching:**
    * **Personalized Job Scraping:** Fetches job listings from multiple APIs based on skills extracted from the user's uploaded resume.
    * **Recommended Job Scraping:** Uses a predefined set of keywords to find general job opportunities if personalized results are insufficient.
* **Resume Builder:**
    * Create new resumes section by section (Personal Info, Summary, Experience, Education, Skills, Projects).
    * Dynamically add multiple entries for experience, education, and projects.
    * Save, view, edit, and delete created resumes.
    * Download created resumes as PDF documents.
* **AI Resume Enhancement (for built resumes):**
    * Utilizes Google's Gemini AI to refine and improve content of built resumes.
    * Users provide prompts to guide the AI (e.g., enhance summary, rephrase experience, add skills).
    * Generates a new PDF with AI-suggested modifications for review.
* **User Authentication:** Secure registration and login for users to manage their parsed sessions and built resumes. [cite: 1]
* **MongoDB Integration:**
    * Stores user accounts. [cite: 1]
    * Stores personalized search sessions (parsed resume data + jobs found for that resume). [cite: 1]
    * Stores user-created resumes from the Resume Builder. [cite: 1]
    * Maintains a cache for recommended job listings. [cite: 1]
* **Web Interface:** User-friendly interface for all features.
* **Dynamic Results Display:** Uses JavaScript for asynchronous processing and dynamic UI updates. [cite: 1]

## 🛠️ Tech Stack & Key Libraries

* **Backend:** Python, Flask [cite: 1]
* **Frontend:** HTML, CSS, JavaScript (Fetch API) [cite: 1]
* **Database:** MongoDB Atlas [cite: 1]
* **Resume Parsing:**
    * `PyPDF2` (for PDF text extraction) [cite: 1]
    * `spaCy` (for NLP tasks, NER, sentence segmentation) [cite: 1]
    * `nltk` (for stopwords, potentially other NLP utilities) [cite: 1]
    * `fuzzywuzzy` & `python-Levenshtein` (for string matching) [cite: 1]
    * `phonenumbers` (for phone number parsing) [cite: 1]
    * `email-validator` (for email validation) [cite: 1]
    * `python-dateutil` (for date parsing) [cite: 1]
* **Job Scraping:**
    * `requests` (for making API calls) [cite: 1]
* **AI Integration:**
    * `google-generativeai` (for Google Gemini API)
* **PDF Generation (Resume Builder):**
    * `WeasyPrint`
* **Environment Management:**
    * `python-dotenv` (for managing environment variables) [cite: 1]
* **MongoDB Interaction:**
    * `pymongo` [cite: 1]
    * `dnspython` (for MongoDB+SRV URIs) [cite: 1]
* **Password Hashing:**
    * `Werkzeug` (for `generate_password_hash`, `check_password_hash`)

## 📁 Project Structure (Updated)

/your_project_name/
|
|-- .venv/                     # Virtual environment
|
|-- app.py                     # Main Flask application [cite: 1]
|
|-- core/                      # Core backend logic modules [cite: 1]
|   |-- __init__.py
|   |-- python_resume_parser_v9.py [cite: 1]
|   |-- job_scrapper_api_v3.py     # (Updated from v2 in original README) [cite: 1]
|   |-- database_manager.py        [cite: 1]
|
|-- static/                    # CSS, client-side JS, images [cite: 1]
|   |-- css/
|   |   |-- style.css              # Main styles
|   |   |-- resume_pdf_styles.css  # Styles for generated PDFs from resume builder
|   |-- js/
|   |   |-- main.js                # JS for resume parser/job matcher part [cite: 1]
|   |   |-- resume_builder.js      # JS for resume builder form interactions
|
|-- templates/                 # HTML templates [cite: 1]
|   |-- layout.html              # Base layout template
|   |-- index.html               # Main page for resume parser (original functionality, or might be login redirect)
|   |-- idx2.html                # Main page for resume parser (after login/upload)
|   |-- login.html
|   |-- register.html
|   |-- dashboard.html           # User dashboard (for parsed resumes)
|   |-- resume_builder_dashboard.html # Dashboard for created resumes
|   |-- resume_builder_form.html      # Form to create/edit resumes
|   |-- resume_builder_enhance_prompt.html # Page for AI enhancement prompt
|   |-- resume_pdf_template.html  # Template for generating PDFs from resume builder
|
|-- uploads/                   # Temporary storage for uploaded resumes (add to .gitignore) [cite: 1]
|
|-- .env                       # Environment variables (API keys, DB URI, Flask secret key) - DO NOT COMMIT [cite: 1]
|-- .gitignore                 # Specifies files for Git to ignore [cite: 1]
|-- requirements.txt           # Python package dependencies [cite: 1]
|-- README.md                  # This file [cite: 1]

## ⚙️ Setup and Installation

1.  **Prerequisites:**
    * Python 3.9+ [cite: 1]
    * `pip` (Python package installer) [cite: 1]
    * Git [cite: 1]
    * A MongoDB Atlas account and a cluster set up. [cite: 1]
    * (For WeasyPrint PDF generation) System-level libraries like Pango, Cairo, GDK-PixBuf. Refer to WeasyPrint documentation for OS-specific installation.

2.  **Clone the Repository (if applicable):**
    ```bash
    git clone <your-repository-url>
    cd your_project_name
    ```
    [cite: 1]

3.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv .venv
    # On Windows
    .venv\Scripts\activate
    # On macOS/Linux
    source .venv/bin/activate
    ```
    [cite: 1]

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    [cite: 1]

5.  **Download SpaCy NLP Model:**
    ```bash
    python -m spacy download en_core_web_sm
    ```
    [cite: 1]

6.  **NLTK Data (Stopwords, if parser uses it extensively):**
    ```python
    import nltk
    nltk.download('stopwords')
    ```
    [cite: 1]

7.  **Set up Environment Variables (`.env` file):**
    Create a `.env` file in the root directory. Add:
    ```env
    # Flask
    FLASK_SECRET_KEY='your_very_strong_and_random_secret_key_here' # Change this! [cite: 1]

    # MongoDB Atlas
    MONGO_ATLAS_URI="mongodb+srv://<username>:<password>@<your_cluster_address>/<your_database_name>?retryWrites=true&w=majority" [cite: 1]

    # Job Scraper API Keys (update to v3 if names changed)
    USAJOBS_API_KEY=your_usajobs_key [cite: 1]
    USAJOBS_USER_AGENT=YourAppName/1.0 (your.email@example.com) [cite: 1]
    RAPIDAPI_JSEARCH_KEY=your_jsearch_key [cite: 1] # If still used by job_scrapper_api_v3.py
    ADZUNA_APP_ID=your_adzuna_app_id [cite: 1]       # If still used
    ADZUNA_APP_KEY=your_adzuna_app_key [cite: 1]     # If still used
    
    # Google Gemini API Key
    GOOGLE_API_KEY=your_gemini_api_key_here
    ```
    * Replace placeholders. [cite: 1]
    * Ensure MongoDB Atlas cluster network access is configured. [cite: 1]

## Running the Application

1.  Activate virtual environment. [cite: 1]
2.  Ensure `.env` variables are set. [cite: 1]
3.  Run Flask development server:
    ```bash
    python app.py
    ```
    [cite: 1]
4.  Open browser to `http://127.0.0.1:5001` (or configured port). [cite: 1]

## 📋 Usage

**Resume Parser & Job Matcher:**
1.  Register or Log in.
2.  Navigate to the main dashboard or resume analysis page.
3.  Upload your resume (PDF).
4.  View analysis (score, skills) and personalized/recommended job listings. [cite: 1]

**Resume Builder:**
1.  Navigate to the "Resume Builder" dashboard from the main dashboard.
2.  Click "Create New Resume" or "Edit" an existing one.
3.  Fill in the sections: Personal Information, Summary, Work Experience, Education, Skills, Projects.
4.  Save the resume. It will appear on your Resume Builder dashboard.
5.  From the dashboard, you can:
    * Edit the resume.
    * Download it as a PDF.
    * Delete it.
    * Click **"Enhance with AI"**:
        * You'll be taken to a page to enter a prompt (e.g., "Make my summary more impactful for a software engineering role.").
        * Submit the prompt. The system will use Gemini AI to process your resume content.
        * A new PDF with AI-suggested enhancements will be generated for download. (Note: AI changes are not automatically saved back to the stored resume.)

## 📦 Modules Overview (Updated)

* **`app.py`**: Main Flask application. Handles web routes, orchestrates resume parsing, job scraping, resume building, AI enhancement requests, interacts with the database manager, and renders HTML templates. [cite: 1]
* **`core/python_resume_parser_v9.py`**: Parses uploaded PDF resumes. [cite: 1]
* **`core/job_scrapper_api_v3.py`**: Fetches job listings from external APIs. [cite: 1]
* **`core/database_manager.py`**: Manages MongoDB interactions for users, parsed resume sessions, built resumes, and job caches. [cite: 1]
* **`templates/`**: Contains all HTML templates, including those for the resume builder (`resume_builder_dashboard.html`, `resume_builder_form.html`, `resume_builder_enhance_prompt.html`, `resume_pdf_template.html`) and user authentication. [cite: 1]
* **`static/js/resume_builder.js`**: Client-side JavaScript for resume builder form interactions (adding/removing dynamic sections, collecting data for submission).

## 💡 Troubleshooting (General)

* **Import Errors:** Ensure all dependencies from `requirements.txt` are installed. [cite: 1]
* **API Key Errors (Job Scrapers, Gemini):** Double-check `.env` file for correct keys and permissions. [cite: 1]
* **MongoDB Connection Issues:** Verify URI and IP whitelisting. [cite: 1]
* **PDF Generation (WeasyPrint):** Ensure system dependencies for WeasyPrint are installed if PDFs are not generating correctly. Check Flask console for WeasyPrint errors.
* **AI Enhancement Issues:**
    * Verify `GOOGLE_API_KEY` is correct and the Gemini API is enabled for your project.
    * Check Flask console logs for errors during the API call or response parsing in `app.py`.
    * Refine prompts for better AI output.

## 🚀 Future Enhancements (Updated)

* Support for more resume file formats (e.g., .docx, .txt) for the parser. [cite: 1]
* More sophisticated resume scoring algorithm. [cite: 1]
* Advanced filtering and sorting for job results. [cite: 1]
* Direct application capabilities or links to application portals. [cite: 1]
* Skill gap analysis and AI-driven suggestions for resume improvement *directly within the builder form*.
* Option to save AI-enhanced versions of resumes.
* More resume templates for the builder.
* Deployment to a cloud platform. [cite: 1]

---