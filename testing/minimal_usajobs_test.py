import requests
import os
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

USAJOBS_API_KEY = os.getenv("USAJOBS_API_KEY")
USAJOBS_USER_AGENT = os.getenv("USAJOBS_USER_AGENT")

# Keywords list (as provided in your previous request)
keywords_list = [
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

print(f"--- USAJOBS API Job Search ---")
print(f"Loaded API Key: {USAJOBS_API_KEY[:5]}..." if USAJOBS_API_KEY else "API Key NOT FOUND")
print(f"Loaded User Agent: {USAJOBS_USER_AGENT}" if USAJOBS_USER_AGENT else "User Agent NOT FOUND")

if not USAJOBS_API_KEY or not USAJOBS_USER_AGENT:
    print("Error: API Key or User Agent not found in .env file. Please check.")
else:
    url = "https://data.usajobs.gov/api/Search"

    headers = {
        'User-Agent': USAJOBS_USER_AGENT,
        'Authorization-Key': USAJOBS_API_KEY,
        'Host': 'data.usajobs.gov'
    }

    found_jobs_count = 0
    displayed_jobs_details = [] # To store details of jobs to avoid re-printing if IDs overlap from keywords
    job_ids_displayed = set()

    # Iterate through keywords. This is a simple approach.
    # A more sophisticated approach might try broader queries first or combine keywords.
    for keyword_to_search in keywords_list:
        if found_jobs_count >= 15:
            break # Stop if we have already found 15 jobs

        print(f"\nSearching for keyword: '{keyword_to_search}'...")
        params = {
            "Keyword": keyword_to_search,
            "ResultsPerPage": 25 # Fetch a bit more to allow for filtering or if some are already seen
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status() # Raise an exception for bad status codes

            data = response.json()
            search_result = data.get('SearchResult', {})
            search_items = search_result.get('SearchResultItems', [])

            if not search_items:
                print(f"No jobs found for keyword: '{keyword_to_search}'")
                continue

            for job_data in search_items:
                if found_jobs_count >= 15:
                    break

                job_id = job_data['MatchedObjectId'] # Assuming 'MatchedObjectId' is a unique identifier
                if job_id not in job_ids_displayed:
                    title = job_data['MatchedObjectDescriptor']['PositionTitle']
                    department = job_data['MatchedObjectDescriptor']['DepartmentName']
                    organization = job_data['MatchedObjectDescriptor']['OrganizationName']
                    # Location can be a list of dicts, so handle it carefully
                    locations = job_data['MatchedObjectDescriptor'].get('PositionLocation', [])
                    location_display = ", ".join([loc.get('LocationName', 'N/A') for loc in locations if loc.get('LocationName')])
                    if not location_display: # Fallback if PositionLocation is empty or malformed
                        location_display = job_data['MatchedObjectDescriptor'].get('PositionLocationDisplay', 'N/A')

                    job_url = job_data['MatchedObjectDescriptor']['PositionURI']

                    job_detail = {
                        "Title": title,
                        "Department": department,
                        "Organization": organization,
                        "Location": location_display,
                        "URL": job_url,
                        "ID": job_id
                    }
                    displayed_jobs_details.append(job_detail)
                    job_ids_displayed.add(job_id)
                    found_jobs_count += 1

                    print(f"\n--- Job #{found_jobs_count} (Found with '{keyword_to_search}') ---")
                    print(f"  Title: {title}")
                    print(f"  Department: {department}")
                    print(f"  Organization: {organization}")
                    print(f"  Location: {location_display}")
                    print(f"  URL: {job_url}")

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred for keyword '{keyword_to_search}': {http_err}")
            # print(f"Response content: {response.text if response else 'No response object'}")
        except requests.exceptions.RequestException as e:
            print(f"An error occurred for keyword '{keyword_to_search}': {e}")
        except json.JSONDecodeError:
            print(f"Error decoding JSON for keyword '{keyword_to_search}'.")
            # print(f"Response content that caused JSON error: {response.text if response else 'No response object'}")
        except Exception as e:
            print(f"An unexpected error occurred for keyword '{keyword_to_search}': {e}")


    print(f"\n--- Search Complete ---")
    if not displayed_jobs_details:
        print("No jobs found across all keywords.")
    else:
        print(f"Displayed a total of {len(displayed_jobs_details)} unique job(s).")
        if len(displayed_jobs_details) < 15:
            print(f"Could not find 15 unique jobs with the provided keywords.")