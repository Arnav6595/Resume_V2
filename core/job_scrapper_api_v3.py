import os
import requests
import json
import re
from urllib.parse import quote_plus # For URL encoding search terms
from dotenv import load_dotenv # To load .env file for local development

load_dotenv() # This loads all variables from .env into environment variables

# --- Configuration & Constants ---
# API Key Placeholders - these should be set as environment variables
USAJOBS_API_KEY = os.environ.get('USAJOBS_API_KEY')
USAJOBS_USER_AGENT = os.environ.get('USAJOBS_USER_AGENT')
RAPIDAPI_JSEARCH_KEY = os.environ.get('RAPIDAPI_JSEARCH_KEY')
RAPIDAPI_HOST = "jsearch.p.rapidapi.com"
ADZUNA_APP_ID = os.environ.get('ADZUNA_APP_ID')
ADZUNA_APP_KEY = os.environ.get('ADZUNA_APP_KEY')

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 ResumeJobMatcher/1.0'

PREDEFINED_SKILLS_KEYWORDS = [
    # Programming Languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift',
    'kotlin', 'scala', 'r', 'matlab', 'perl', 'shell scripting', 'bash', 'powershell', 'c',
    'objective-c', 'groovy', 'dart', 'lua', 'assembly',
    # Web Development - Frontend
    'html', 'html5', 'css', 'css3', 'react', 'react.js', 'angular', 'angular.js', 'vue', 'vue.js',
    'next.js', 'nuxt.js', 'gatsby', 'jquery', 'bootstrap', 'tailwind css', 'sass', 'less',
    'webpack', 'babel', 'gulp', 'grunt', 'ember.js', 'svelte', 'webassembly', 'restful apis',
    'soap apis', 'graphql', 'ajax', 'json', 'xml', 'jwt', 'websockets', 'ssr', 'csr', 'pwa',
    'responsive design', 'cross-browser compatibility',
    # Web Development - Backend
    'node.js', 'express', 'express.js', 'django', 'flask', 'spring', 'spring boot', 'asp.net', '.net core',
    'laravel', 'ruby on rails', 'phoenix', 'elixir', 'fastapi', 'hapi', 'koa', 'nestJS', 'strapi',
    'serverless framework', 'firebase', 'api development', 'api design',
    # Databases & Data Storage
    'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'mongo', 'redis', 'oracle db', 'sqlite',
    'cassandra', 'dynamodb', 'elasticsearch', 'neo4j', 'couchdb', 'mariadb', 'ms sql server',
    'nosql', 'firebase realtimedb', 'firebase firestore', 'influxdb', 'etcd', 'data warehousing',
    'database design', 'database administration', 'data modeling', 'query optimization', 'sql alchemy',
    'hibernate', 'typeorm', 'prisma',
    # Cloud Platforms & Services
    'aws', 'amazon web services', 'azure', 'microsoft azure', 'gcp', 'google cloud platform',
    'google cloud', 'heroku', 'digitalocean', 'linode', 'ovh', 'alibaba cloud', 'ibm cloud',
    'oracle cloud infrastructure', 'oci', 'vmware', 'openshift', 'lambda', 'azure functions',
    'google cloud functions', 's3', 'ec2', 'rds', 'azure blob storage', 'azure virtual machines',
    'google cloud storage', 'google compute engine', 'cloudformation', 'azure resource manager',
    'google cloud deployment manager', 'cloudwatch', 'azure monitor', 'stackdriver',
    # DevOps & Infrastructure
    'docker', 'kubernetes', 'k8s', 'terraform', 'ansible', 'jenkins', 'gitlab ci', 'github actions',
    'circleci', 'travis ci', 'chef', 'puppet', 'vagrant', 'prometheus', 'grafana', 'elk stack',
    'splunk', 'nagios', 'zabbix', 'infrastructure as code', 'iac', 'ci/cd', 'continuous integration',
    'continuous delivery', 'continuous deployment', 'configuration management', 'monitoring',
    'logging', 'alerting', 'site reliability engineering', 'sre', 'devops', 'sysadmin',
    # Operating Systems
    'linux', 'unix', 'windows server', 'macos', 'ubuntu', 'centos', 'debian', 'red hat', 'fedora',
    'coreos', 'alpine linux',
    # Data Science, Machine Learning, AI
    'machine learning', 'ml', 'deep learning', 'dl', 'data analysis', 'data science', 'statistics',
    'natural language processing', 'nlp', 'computer vision', 'cv', 'artificial intelligence', 'ai',
    'pandas', 'numpy', 'scipy', 'scikit-learn', 'sklearn', 'tensorflow', 'keras', 'pytorch', 'torch',
    'matplotlib', 'seaborn', 'plotly', 'jupyter notebooks', 'rstudio', 'tableau', 'power bi',
    'apache spark', 'spark', 'hadoop', 'kafka', 'apache kafka', 'airflow', 'apache airflow',
    'hive', 'presto', 'dask', 'xgboost', 'lightgbm', 'catboost', 'shap', 'nltk', 'spacy', 'opencv',
    'data mining', 'data visualization', 'big data', 'etl', 'feature engineering', 'model deployment',
    'recommender systems', 'time series analysis', 'a/b testing', 'reinforcement learning', 'mlops',
    # Mobile Development
    'mobile development', 'ios', 'android development', 'react native', 'flutter', 'xamarin',
    'cordova', 'ionic', 'swift', 'objective-c', 'kotlin', 'java (android)', 'swiftui',
    'jetpack compose', 'kotlin multiplatform', 'xcode', 'android studio',
    # Software Engineering Practices & Tools
    'git', 'github', 'gitlab', 'bitbucket', 'svn', 'jira', 'confluence', 'slack',
    'microsoft teams', 'trello', 'asana', 'notion', 'unit testing', 'integration testing',
    'end-to-end testing', 'test driven development', 'tdd', 'behavior driven development', 'bdd',
    'design patterns', 'software architecture', 'microservices architecture', 'agile', 'scrum',
    'kanban', 'waterfall', 'lean', 'six sigma', 'oop', 'object-oriented programming',
    'functional programming', 'rest api design', 'api security', 'oauth', 'saml', 'sso',
    'software development life cycle', 'sdlc', 'code review', 'pair programming', 'version control',
    # Cybersecurity
    'cybersecurity', 'information security', 'network security', 'application security',
    'penetration testing', 'ethical hacking', 'vulnerability assessment', 'siem', 'ids/ips',
    'firewalls', 'cryptography', 'iam', 'identity and access management', 'gdpr', 'hipaa',
    'iso 27001', 'soc2', 'owasp', 'malware analysis', 'digital forensics',
    # Design & UX/UI
    'ui/ux', 'ui design', 'ux design', 'user interface design', 'user experience design',
    'figma', 'adobe xd', 'sketch', 'invision', 'zeplin', 'adobe photoshop', 'photoshop',
    'adobe illustrator', 'illustrator', 'user research', 'wireframing', 'prototyping',
    'usability testing', 'design thinking', 'interaction design', 'visual design', 'design systems',
    # Business & Management
    'project management', 'product management', 'business analysis', 'stakeholder management',
    'requirements gathering', 'business development', 'strategy', 'market research',
    'financial analysis', 'risk management', 'quality assurance', 'qa', 'erp', 'sap', 'salesforce',
    'microsoft dynamics', 'supply chain management', 'logistics',
    # Soft Skills
    'communication', 'verbal communication', 'written communication', 'teamwork', 'collaboration',
    'problem solving', 'analytical skills', 'critical thinking', 'leadership', 'team leadership',
    'time management', 'adaptability', 'flexibility', 'creativity', 'innovation',
    'attention to detail', 'mentoring', 'coaching', 'negotiation', 'conflict resolution',
    'decision making', 'public speaking', 'presentation skills', 'customer service', 'client relations',
    # General/Entry Level Terms
    'fresher', 'entry level', 'trainee', 'intern', 'junior', 'Software Development', 'Design', 'Product',
    'Data Analysis','DevOps','Sysadmin',
    # Domain Specific
    'healthcare IT', 'fintech', 'ecommerce', 'blockchain', 'iot', 'internet of things',
    'bioinformatics', 'gis', 'game development', 'unreal engine', 'unity',
    # Certifications
    'aws certified', 'azure certified', 'gcp certified', 'pmp', 'csm', 'comptia',
    'cissp', 'ccna', 'cisa'
]
PREDEFINED_SKILLS_LOWER = [skill.lower() for skill in PREDEFINED_SKILLS_KEYWORDS]

# --- Helper Functions ---
def make_request(url: str, headers: dict = None, params: dict = None, timeout: int = 15) -> dict | None:
    if headers is None:
        headers = {'User-Agent': DEFAULT_USER_AGENT}
    try:
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        print(f"Timeout error fetching URL: {url}")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - URL: {url}")
        if response is not None:
            print(f"Response content: {response.text[:500]}")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
    except json.JSONDecodeError as e_json:
        print(f"Error decoding JSON from {url}: {e_json}")
        if response is not None:
            print(f"Response content that failed to parse: {response.text[:500]}")
    return None

def extract_skills_from_text(text: str, skill_list: list) -> list[str]:
    if not text: return []
    found_skills = set()
    text_lower = text.lower()
    # Sort skill_list by length in descending order to match longer phrases first
    sorted_skill_list = sorted(skill_list, key=len, reverse=True) # skill_list here is PREDEFINED_SKILLS_LOWER
    for skill_keyword_lower in sorted_skill_list:
        try:
            # Use word boundaries to match whole words/phrases
            pattern = r'\b' + re.escape(skill_keyword_lower) + r'\b'
            if re.search(pattern, text_lower):
                # Try to get the original casing from PREDEFINED_SKILLS_KEYWORDS
                try:
                    original_casing_skill = PREDEFINED_SKILLS_KEYWORDS[PREDEFINED_SKILLS_LOWER.index(skill_keyword_lower)]
                    found_skills.add(original_casing_skill)
                except ValueError: # Should not happen if PREDEFINED_SKILLS_LOWER is derived correctly
                    found_skills.add(skill_keyword_lower) # Fallback to the lowercased keyword
        except re.error as e_re:
            # This might happen if a skill keyword contains special regex characters
            # that re.escape didn't fully handle or if the skill itself forms an invalid pattern.
            print(f"Regex error for skill '{skill_keyword_lower}': {e_re}")
            continue # Skip this skill and continue with the next
    return sorted(list(found_skills))

# --- API Specific Fetch Functions ---

def fetch_remotive_jobs(keywords: list[str], limit: int = 5) -> list[dict]:
    print(f"\nFetching jobs from Remotive for keywords: {keywords}...")
    if not keywords: print("Remotive: No keywords provided."); return []
    base_url = "https://remotive.com/api/remote-jobs"
    search_query = " ".join(keywords)
    params = {'search': search_query, 'limit': limit}
    data = make_request(base_url, params=params)
    jobs = []
    if data and 'jobs' in data:
        for job_entry in data['jobs']:
            description = job_entry.get('description', '')
            cleaned_description = re.sub(r'<[^>]+>', ' ', description) # Remove HTML tags
            cleaned_description = re.sub(r'\s+', ' ', cleaned_description).strip() # Normalize whitespace
            jobs.append({
                'title': job_entry.get('title'),
                'company': job_entry.get('company_name'),
                'location': job_entry.get('candidate_required_location', 'Remote'),
                'description_text': cleaned_description,
                'extracted_skills': extract_skills_from_text(cleaned_description, PREDEFINED_SKILLS_LOWER),
                'url': job_entry.get('url'),
                'publication_date': job_entry.get('publication_date'),
                'source_site': 'Remotive API'
            })
        print(f"Found {len(jobs)} jobs from Remotive.")
    else:
        print("No jobs found or error fetching from Remotive.")
    return jobs

def fetch_arbeitnow_jobs(keywords: list[str], limit: int = 5, location_query: str = None) -> list[dict]:
    print(f"\nFetching jobs from Arbeitnow for keywords: {keywords}, location: {location_query if location_query else 'Global'}...")
    if not keywords: print("Arbeitnow: No keywords provided."); return []
    base_url = "https://arbeitnow.com/api/job-board-api"
    search_query = " ".join(keywords)
    # Arbeitnow's 'q' parameter seems to handle location as part of the query string
    # However, their docs mention 'location' as a separate field for filtering but it's for their main search, not this specific API endpoint.
    # We'll stick to adding "in location" to the query if provided.
    # if location_query and location_query.lower() != "any":
    #     search_query += f" in {location_query}" # This might not be how Arbeitnow API expects location filtering
    
    params = {'q': search_query, 'page': 1} # q seems to be the primary way for keywords & location combined
    # For more specific location filtering with Arbeitnow, one might need to explore if their API supports structured location fields.
    # For now, `location_query` is mainly for print statement and potentially for `q`.

    data = make_request(base_url, params=params)
    jobs = []
    if data and 'data' in data:
        for i, job_entry in enumerate(data['data']):
            if i >= limit: break # Respect the limit
            description = job_entry.get('description', '')
            cleaned_description = re.sub(r'<[^>]+>', ' ', description)
            cleaned_description = re.sub(r'\s+', ' ', cleaned_description).strip()
            jobs.append({
                'title': job_entry.get('title'),
                'company': job_entry.get('company_name'),
                'location': job_entry.get('location', location_query if location_query and location_query.lower() != "any" else "Not specified"),
                'description_text': cleaned_description,
                'extracted_skills': extract_skills_from_text(cleaned_description, PREDEFINED_SKILLS_LOWER),
                'url': job_entry.get('url'),
                'publication_date': job_entry.get('created_at'),
                'source_site': 'Arbeitnow API'
            })
        print(f"Found {len(jobs)} jobs from Arbeitnow (up to limit {limit}).")
    else:
        print("No jobs found or error fetching from Arbeitnow.")
    return jobs

def fetch_usajobs(keywords: list[str], limit: int = 5, location_name: str = None) -> list[dict]:
    # This function will now primarily be used when skills_json is successfully loaded.
    # The extensive fallback is handled directly in scrape_jobs.
    print(f"\nFetching jobs from USAJOBS (standard search) for keywords: {keywords[:5]}..., location: {location_name if location_name else 'US Nationwide'}...")
    if not USAJOBS_API_KEY or not USAJOBS_USER_AGENT:
        print("USAJOBS_API_KEY or USAJOBS_USER_AGENT not set. Skipping USAJOBS.")
        return []
    if not keywords:
        print("USAJOBS: No keywords provided for standard search.")
        return []

    base_url = "https://data.usajobs.gov/api/search"
    headers = {'Authorization-Key': USAJOBS_API_KEY, 'User-Agent': USAJOBS_USER_AGENT, 'Host': 'data.usajobs.gov'}
    params = {'Keyword': " ".join(keywords), 'ResultsPerPage': limit}
    if location_name:
        params['LocationName'] = location_name

    data = make_request(base_url, headers=headers, params=params)
    jobs = []
    if data and data.get('SearchResult', {}).get('SearchResultItems'):
        for item in data['SearchResult']['SearchResultItems']:
            job_entry = item.get('MatchedObjectDescriptor', {})
            desc_parts = [
                job_entry.get('UserArea', {}).get('Details', {}).get('JobSummary'),
                job_entry.get('UserArea', {}).get('Details', {}).get('MajorDuties'),
                job_entry.get('UserArea', {}).get('Details', {}).get('Requirements')
            ]
            desc = " ".join(str(p) for p in desc_parts if p) # Ensure parts are strings
            cleaned_desc = re.sub(r'\s+', ' ', desc).strip()
            jobs.append({
                'title': job_entry.get('PositionTitle'),
                'company': job_entry.get('OrganizationName'),
                'location': job_entry.get('PositionLocationDisplay'),
                'description_text': cleaned_desc,
                'extracted_skills': extract_skills_from_text(cleaned_desc, PREDEFINED_SKILLS_LOWER),
                'url': job_entry.get('PositionURI'),
                'publication_date': job_entry.get('PublicationStartDate'),
                'source_site': 'USAJOBS API'
            })
        print(f"Found {len(jobs)} jobs from USAJOBS (standard search).")
    else:
        print("No jobs found or error fetching from USAJOBS (standard search).")
    return jobs

def fetch_adzuna_jobs(keywords: list[str], limit: int = 5, location_query: str = None, country_code: str = "gb") -> list[dict]:
    print(f"\nFetching jobs from Adzuna for keywords: {keywords}, country: {country_code}" + (f", location: {location_query}" if location_query and location_query.lower() != "any" else ", location: Global within country") + "...")
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("ADZUNA_APP_ID or ADZUNA_APP_KEY not set. Skipping Adzuna.")
        return []
    if not keywords:
        print("Adzuna: No keywords provided.")
        return []

    base_url = f"http://api.adzuna.com/v1/api/jobs/{country_code.lower()}/search/1" # Adzuna uses http
    params = {
        'app_id': ADZUNA_APP_ID,
        'app_key': ADZUNA_APP_KEY,
        'results_per_page': limit,
        'what': " ".join(keywords), # Keywords for the 'what' parameter
        'content-type': 'application/json'
    }
    if location_query and location_query.lower() != "any":
        params['where'] = location_query # Location for the 'where' parameter

    data = make_request(base_url, params=params)
    jobs = []
    if data and 'results' in data:
        for job_entry in data['results']:
            desc = job_entry.get('description', '')
            cleaned_desc = re.sub(r'\s+', ' ', desc).strip() # Basic cleaning
            jobs.append({
                'title': job_entry.get('title'),
                'company': job_entry.get('company', {}).get('display_name'),
                'location': job_entry.get('location', {}).get('display_name'),
                'description_text': cleaned_desc,
                'extracted_skills': extract_skills_from_text(cleaned_desc, PREDEFINED_SKILLS_LOWER),
                'url': job_entry.get('redirect_url'), # Adzuna uses redirect_url
                'publication_date': job_entry.get('created'), # 'created' is typically the posting date
                'source_site': 'Adzuna API'
            })
        print(f"Found {len(jobs)} jobs from Adzuna.")
    else:
        print("No jobs found or error fetching from Adzuna.")
        if data: print(f"Adzuna response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    return jobs

def fetch_github_jobs_mirror(keywords: list[str], limit: int = 5, location_query: str = None) -> list[dict]:
    print(f"\nFetching jobs from GitHub Jobs Mirror for keywords: {keywords}...")
    # GitHub Jobs API is deprecated. This function now acts as a proxy or conceptual placeholder.
    # We can try to find GitHub-related or general developer jobs via another source like Arbeitnow.
    if not keywords:
        print("GitHub Mirror: No keywords provided.")
        return []

    # If keywords suggest a developer/GitHub focus, use Arbeitnow as a proxy
    if "github" in [kw.lower() for kw in keywords] or \
       any(dev_kw in " ".join(keywords).lower() for dev_kw in ["developer", "engineer", "software", "code", "repository"]):
        print("Attempting to find GitHub-like jobs via Arbeitnow as a proxy...")
        # Enhance keywords for better proxy search if needed
        proxy_keywords = list(set(keywords + ["developer", "engineer", "software", "remote"]))
        return fetch_arbeitnow_jobs(proxy_keywords, limit, location_query)
    
    print("Direct GitHub Jobs API is deprecated. Could not determine suitable proxy search via GitHub Mirror.")
    return []


def fetch_jsearch_jobs(keywords: list[str], limit: int = 5, location_query: str = None) -> list[dict]:
    print(f"\nFetching jobs from JSearch (RapidAPI) for keywords: {keywords}, location: {location_query if location_query else 'Global'}...")
    if not RAPIDAPI_JSEARCH_KEY:
        print("RAPIDAPI_JSEARCH_KEY not set. Skipping JSearch.")
        return []
    if not keywords:
        print("JSearch: No keywords provided.")
        return []

    base_url = f"https://{RAPIDAPI_HOST}/search"
    
    # JSearch query parameter expects a single string.
    # We can join keywords. Location is also part of the query.
    search_query_parts = [" ".join(keywords)]
    if location_query and location_query.lower() != "any":
        search_query_parts.append(f"in {location_query}")

    querystring = {
        "query": " ".join(search_query_parts),
        "page": "1", # JSearch pagination starts at 1
        "num_pages": "1" # Controls how many pages of results (related to 'limit' indirectly)
        # The JSearch API doesn't have a direct 'limit' or 'ResultsPerPage' like others for number of items.
        # It returns a page of results (typically 10-20). We'll fetch one page and then slice by `limit`.
    }
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_JSEARCH_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    data = make_request(base_url, headers=headers, params=querystring)
    jobs = []
    if data and 'data' in data:
        for i, job_entry in enumerate(data['data']):
            if i >= limit: # Apply the limit to the results received
                break
            
            desc = job_entry.get('job_description', '')
            # Basic cleaning for JSearch description
            cleaned_desc = re.sub(r'<[^>]+>', ' ', desc) # Remove HTML
            cleaned_desc = re.sub(r'\s+', ' ', cleaned_desc).strip() # Normalize whitespace

            # Construct location string
            loc_parts = [job_entry.get('job_city'), job_entry.get('job_state'), job_entry.get('job_country')]
            job_loc = ", ".join(filter(None, loc_parts)) or "Not specified" # Filter out None values before joining

            jobs.append({
                'title': job_entry.get('job_title'),
                'company': job_entry.get('employer_name'),
                'location': job_loc,
                'description_text': cleaned_desc,
                'extracted_skills': extract_skills_from_text(cleaned_desc, PREDEFINED_SKILLS_LOWER),
                'url': job_entry.get('job_apply_link') or job_entry.get('job_google_link'), # Prefer apply link
                'publication_date': job_entry.get('job_posted_at_datetime_utc'),
                'source_site': 'JSearch API (RapidAPI)'
            })
        print(f"Found {len(jobs)} jobs from JSearch (up to limit {limit}).")
    else:
        print("No jobs found or error fetching from JSearch.")
        if data : print(f"JSearch response structure: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
    return jobs

# --- Main Orchestrator ---
def scrape_jobs(
    keywords: list[str],
    location: str = None,
    max_jobs_per_source: int = 2,
    skills_json_path: str = "extracted_skills.json"
) -> list[dict]:
    final_keywords_to_use = []
    using_skills_from_json = False

    try:
        # Ensure skills_json_path is a valid path string before attempting to open
        if skills_json_path and isinstance(skills_json_path, str):
            with open(skills_json_path, 'r', encoding='utf-8') as f_skills_json:
                loaded_skills = json.load(f_skills_json)
            if isinstance(loaded_skills, list) and all(isinstance(s, str) for s in loaded_skills) and loaded_skills:
                print(f"INFO: Using skills from '{skills_json_path}' for job search: {loaded_skills[:10]}...")
                final_keywords_to_use = loaded_skills
                using_skills_from_json = True
                print(f"INFO: Successfully used skills from '{skills_json_path}'. The file has not been deleted.")
            else:
                print(f"INFO: '{skills_json_path}' is empty or not a valid list of skills. Using provided/recommended keywords: {keywords}")
                final_keywords_to_use = keywords
        else: # skills_json_path is None or not a string
             print(f"INFO: Invalid or no skills_json_path ('{skills_json_path}'). Using provided/recommended keywords for job search: {keywords}")
             final_keywords_to_use = keywords
             # using_skills_from_json remains False

    except FileNotFoundError:
        print(f"INFO: '{skills_json_path}' not found. Using provided/recommended keywords for job search: {keywords}")
        final_keywords_to_use = keywords
    except json.JSONDecodeError:
        print(f"ERROR: Decoding JSON from '{skills_json_path}'. Using provided/recommended keywords: {keywords}")
        final_keywords_to_use = keywords
    except Exception as e: # Catch other potential errors like TypeError if path is None
        print(f"ERROR: An unexpected error occurred while loading skills from '{skills_json_path}': {e}. Using provided/recommended keywords: {keywords}")
        final_keywords_to_use = keywords

    if not final_keywords_to_use: # If 'keywords' was also empty or skills file led to empty list
        print("WARNING: No keywords available for job scraping. Using default generic keywords.")
        final_keywords_to_use = ["developer", "software", "IT"] # Ultimate fallback

    print(f"--- Starting Job Scraping with effective keywords: {final_keywords_to_use[:10]}..., Location: {location if location else 'Global'} ---")
    all_jobs = []

    # --- Fetching from other APIs ---
    current_remotive_keywords = final_keywords_to_use[:] # Create a copy
    if "remote" not in [kw.lower() for kw in current_remotive_keywords]:
        current_remotive_keywords.append("remote")
    all_jobs.extend(fetch_remotive_jobs(keywords=current_remotive_keywords, limit=max_jobs_per_source))

    all_jobs.extend(fetch_arbeitnow_jobs(keywords=final_keywords_to_use, limit=max_jobs_per_source, location_query=location))
    
    adzuna_search_location_query = location # Adzuna can take general location query
    adzuna_country_code = "gb" # Default to Great Britain
    if location: # Try to map common locations to Adzuna country codes
        country_code_map = {"india": "in", "usa": "us", "united states": "us", "uk": "gb", "united kingdom": "gb", "germany": "de", "singapore": "sg", "canada": "ca", "australia": "au"}
        adzuna_country_code = country_code_map.get(location.lower(), "gb") # Fallback to 'gb' if not mapped
    all_jobs.extend(fetch_adzuna_jobs(keywords=final_keywords_to_use, limit=max_jobs_per_source, location_query=adzuna_search_location_query, country_code=adzuna_country_code))

    all_jobs.extend(fetch_jsearch_jobs(keywords=final_keywords_to_use, limit=max_jobs_per_source, location_query=location))
    
    # --- USAJOBS LOGIC: INTEGRATING minimal_usajobs_test.py AS FALLBACK ---
    usajobs_search_location_name = None
    # Determine if the search is for the US for USAJOBS
    is_us_search_for_usajobs = False
    if location and (location.lower() in ["usa", "united states"] or "us" in location.lower().split()):
        usajobs_search_location_name = location # Use specific US location if provided
        is_us_search_for_usajobs = True
    elif not location: # No location means global, so USAJOBS should search nationwide US
        is_us_search_for_usajobs = True
        usajobs_search_location_name = None # For nationwide US search

    if is_us_search_for_usajobs and USAJOBS_API_KEY and USAJOBS_USER_AGENT:
        if using_skills_from_json:
            # If skills_json was successfully used, use the standard fetch_usajobs with those skills
            keywords_for_usajobs = final_keywords_to_use
            print(f"\nUSAJOBS: Using personalized keywords from JSON: {keywords_for_usajobs[:5]}...")
            print(f"Attempting USAJOBS search with personalized keywords (Targeting US: {usajobs_search_location_name if usajobs_search_location_name else 'Nationwide'})...")
            all_jobs.extend(fetch_usajobs(keywords=keywords_for_usajobs, limit=max_jobs_per_source, location_name=usajobs_search_location_name))
        else:
            # FALLBACK: Use the extensive search logic from minimal_usajobs_test.py
            print(f"\nUSAJOBS: JSON skills not used. Initiating extensive fallback keyword search (Targeting US: {usajobs_search_location_name if usajobs_search_location_name else 'Nationwide'})...")
            
            usajobs_fallback_jobs = []
            job_ids_displayed_usajobs = set()
            target_fallback_jobs = max_jobs_per_source 

            for keyword_to_search in PREDEFINED_SKILLS_KEYWORDS: 
                if len(usajobs_fallback_jobs) >= target_fallback_jobs:
                    print(f"  USAJOBS Fallback: Reached target of {target_fallback_jobs} jobs. Stopping keyword iteration.")
                    break

                # This print can be very verbose, consider removing or reducing frequency
                # print(f"  USAJOBS Fallback: Searching for keyword: '{keyword_to_search}'...") 
                
                current_usajobs_params = {
                    "Keyword": keyword_to_search,
                    "ResultsPerPage": 25 
                }
                if usajobs_search_location_name: # Apply location if specified for US
                    current_usajobs_params['LocationName'] = usajobs_search_location_name

                headers_usajobs = {'Authorization-Key': USAJOBS_API_KEY, 'User-Agent': USAJOBS_USER_AGENT, 'Host': 'data.usajobs.gov'}
                usajobs_api_url = "https://data.usajobs.gov/api/search"
                data = make_request(usajobs_api_url, headers=headers_usajobs, params=current_usajobs_params)

                if data and data.get('SearchResult', {}).get('SearchResultItems'):
                    search_items = data['SearchResult']['SearchResultItems']
                    if not search_items:
                        continue 
                    
                    for item_data in search_items:
                        if len(usajobs_fallback_jobs) >= target_fallback_jobs:
                            break 
                        
                        job_entry_desc = item_data.get('MatchedObjectDescriptor', {})
                        job_id = job_entry_desc.get('PositionID') or item_data.get('MatchedObjectId') # Prefer PositionID

                        if job_id and job_id not in job_ids_displayed_usajobs:
                            desc_parts_usajobs = [
                                job_entry_desc.get('UserArea', {}).get('Details', {}).get('JobSummary'),
                                job_entry_desc.get('UserArea', {}).get('Details', {}).get('MajorDuties'),
                                job_entry_desc.get('UserArea', {}).get('Details', {}).get('Requirements')
                            ]
                            desc_usajobs = " ".join(str(p) for p in desc_parts_usajobs if p)
                            cleaned_desc_usajobs = re.sub(r'\s+', ' ', desc_usajobs).strip()
                            
                            job_dict = {
                                'title': job_entry_desc.get('PositionTitle'),
                                'company': job_entry_desc.get('OrganizationName'),
                                'location': job_entry_desc.get('PositionLocationDisplay'),
                                'description_text': cleaned_desc_usajobs,
                                'extracted_skills': extract_skills_from_text(cleaned_desc_usajobs, PREDEFINED_SKILLS_LOWER),
                                'url': job_entry_desc.get('PositionURI'),
                                'publication_date': job_entry_desc.get('PublicationStartDate'),
                                'source_site': 'USAJOBS API (Fallback Search)'
                            }
                            usajobs_fallback_jobs.append(job_dict)
                            job_ids_displayed_usajobs.add(job_id)
            print(f"USAJOBS Fallback: Found {len(usajobs_fallback_jobs)} unique jobs after extensive keyword search.")
            all_jobs.extend(usajobs_fallback_jobs)
    elif is_us_search_for_usajobs: # If it's a US search but keys are missing
        print("\nWARNING: USAJOBS_API_KEY or USAJOBS_USER_AGENT not set. Skipping USAJOBS for US search.")
    # If not is_us_search_for_usajobs, USAJOBS is skipped silently unless keys are also missing (which is covered by the outer if)
    # --- END OF USAJOBS LOGIC ---

    all_jobs.extend(fetch_github_jobs_mirror(keywords=final_keywords_to_use, limit=max_jobs_per_source, location_query=location))

    print(f"\n--- Total jobs fetched before deduplication: {len(all_jobs)} ---")

    seen_identifiers = set() # Use a more generic name as it can store URLs or tuples
    unique_jobs = []
    for job in all_jobs:
        job_url = job.get('url')
        if job_url and job_url.strip(): # Check if URL exists and is not just whitespace
            identifier = job_url
            if identifier not in seen_identifiers:
                unique_jobs.append(job)
                seen_identifiers.add(identifier)
        else: # Fallback for jobs without a URL, using a tuple of other fields
            # Ensure all parts of the key are strings to avoid issues with None
            title_key = job.get('title','').lower() if job.get('title') else ""
            company_key = job.get('company','').lower() if job.get('company') else ""
            location_key = job.get('location','').lower() if job.get('location') else ""
            # Add description hash for more uniqueness if other fields are too common
            # For simplicity now, using title, company, location
            identifier = (title_key, company_key, location_key) 
            
            if identifier not in seen_identifiers: # Only add if truly unique based on this composite key
                 unique_jobs.append(job)
                 seen_identifiers.add(identifier)

    print(f"--- Total unique jobs (by URL or content signature): {len(unique_jobs)} ---")
    return unique_jobs

# --- Example Usage ---
if __name__ == "__main__":
    print("Job Scraper Initializing (API Version)...")

    # Check for API keys at the start
    if not USAJOBS_API_KEY or not USAJOBS_USER_AGENT:
        print("WARNING: USAJOBS_API_KEY or USAJOBS_USER_AGENT is not set in .env. USAJOBS scraping might be skipped or fail.")
    if not RAPIDAPI_JSEARCH_KEY:
        print("WARNING: RAPIDAPI_JSEARCH_KEY is not set in .env. JSearch scraping will be skipped.")
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("WARNING: ADZUNA_APP_ID or ADZUNA_APP_KEY is not set in .env. Adzuna scraping will be skipped.")

    # Define example search parameters
    example_search_keywords = ["Software Developer", "IT Support", "Data Analyst", "Fresher", "Developer", "Python", "Java", "Software", "IT"]
    skills_file_path = "extracted_skills.json" # Path for skills extracted by resume parser
    
    # This is the single place to change the job limit for test runs
    test_run_limit = 5 # Changed back to 5 for this example, was 15 in your file

    # --- SCENARIO 1: Using skills from 'extracted_skills.json' (if it exists and is valid) ---
    # Create a dummy extracted_skills.json for testing if it doesn't exist
    # In a real app, this file would be generated by the resume parser.
    if not os.path.exists(skills_file_path):
        print(f"Creating a dummy '{skills_file_path}' for testing Scenario 1.")
        dummy_skills_for_file = ["Python", "JavaScript", "Cloud Computing", "React", "Node.js", "API Development"]
        with open(skills_file_path, 'w', encoding='utf-8') as f_dummy:
            json.dump(dummy_skills_for_file, f_dummy)
    else:
        print(f"INFO: '{skills_file_path}' already exists. Scenario 1 will attempt to use it.")

    print(f"\n--- SCENARIO 1: Attempting to use '{skills_file_path}' for PERSONALIZED GLOBAL job search (max {test_run_limit} jobs/source) ---")
    scraped_job_data_personalized = scrape_jobs(
        keywords=example_search_keywords, # These are fallback if skills_file_path fails
        location=None, # Global search
        max_jobs_per_source=test_run_limit,
        skills_json_path=skills_file_path # Path to the JSON file with skills
    )
    if scraped_job_data_personalized:
        print(f"\n--- SCENARIO 1 Results ---")
        print(f"Total unique jobs found: {len(scraped_job_data_personalized)}")
        # for job in scraped_job_data_personalized[:2]: # Print first few for brevity
        # print(json.dumps(job, indent=2))
    else:
        print(f"\nNo job data (personalized or fallback global) was successfully aggregated in Scenario 1.")

    # Verification step
    if os.path.exists(skills_file_path):
        print(f"VERIFICATION: '{skills_file_path}' still exists after Scenario 1 run, as expected (script does not delete it).")


    # --- SCENARIO 2: Fallback to 'example_search_keywords' for a US-based search ---
    # This scenario uses a non-existent JSON file path to force a fallback.
    # For USAJOBS, this will now trigger the extensive keyword search if skills_json_path fails.
    print(f"\n--- SCENARIO 2: Forcing fallback to 'example_search_keywords' for US job search (max {test_run_limit} jobs/source) ---")
    scraped_job_data_recommended_us = scrape_jobs(
        keywords=example_search_keywords, # These become primary if skills_json_path is invalid
        location="United States", # Specific US location
        max_jobs_per_source=test_run_limit,
        skills_json_path="non_existent_skills_file.json" # Force fallback
    )
    if scraped_job_data_recommended_us:
        print(f"\n--- SCENARIO 2 Results ---")
        print(f"Total unique jobs found: {len(scraped_job_data_recommended_us)}")
        # for job in scraped_job_data_recommended_us[:2]:
        # print(json.dumps(job, indent=2))
    else:
        print("\nNo recommended job data was successfully aggregated in Scenario 2 for US search.")

    # Clean up dummy file if it was created by this test script specifically for this run
    # Check if 'dummy_skills_for_file' was defined, indicating this script created the file.
    if os.path.exists(skills_file_path) and 'dummy_skills_for_file' in locals():
        user_choice = input(f"Do you want to delete the dummy '{skills_file_path}' that might have been created for this test run? (y/n): ").lower()
        if user_choice == 'y':
            try:
                os.remove(skills_file_path)
                print(f"Dummy '{skills_file_path}' deleted.")
            except OSError as e:
                print(f"Error deleting dummy file: {e}")