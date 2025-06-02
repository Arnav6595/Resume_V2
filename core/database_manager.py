import os
from pymongo import MongoClient, UpdateOne, errors
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta # Added timedelta
from bson import ObjectId

# Load environment variables (e.g., for MONGO_URI)
load_dotenv()

# --- Configuration ---
MONGO_URI = os.environ.get("MONGO_ATLAS_URI") # Your MongoDB Atlas connection string
DB_NAME = "job_matching_app" # Or your preferred database name
PERSONALIZED_SEARCH_COLLECTION = "personalized_searches"
RECOMMENDED_JOBS_COLLECTION = "recommended_jobs_cache"
USER_COLLECTION = "users"

# Global client and db variables to reuse connection
client = None
db = None

def connect_db():
    """
    Establishes a connection to MongoDB Atlas.
    Returns the database object.
    """
    global client, db
    if db is not None:
        try:
            client.admin.command('ping')
            # print("DEBUG: Reusing existing MongoDB connection.")
            return db
        except (errors.ConnectionFailure, errors.ServerSelectionTimeoutError) as e:
            print(f"DEBUG: Existing MongoDB connection lost or timed out: {e}. Reconnecting...")
            client = None
            db = None

    if not MONGO_URI:
        print("ERROR: MONGO_ATLAS_URI environment variable not set.")
        raise ValueError("MONGO_ATLAS_URI not set")

    try:
        print("Attempting to connect to MongoDB Atlas...")
        client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
        client.admin.command('ping')
        print("Successfully connected to MongoDB Atlas!")
        db = client[DB_NAME]
        return db
    except errors.ConfigurationError as e_conf:
        print(f"MongoDB Configuration Error: {e_conf}")
        raise
    except errors.ConnectionFailure as e_conn:
        print(f"MongoDB Connection Failure: Could not connect to server: {e_conn}")
        raise
    except Exception as e:
        print(f"An unexpected error occurred during MongoDB connection: {e}")
        raise

# --- User Management Functions ---
def create_user(username, email, password_hash):
    """Creates a new user in the database."""
    if not username or not email or not password_hash:
        print("ERROR: Username, email, and password hash are required to create a user.")
        return None
    try:
        database = connect_db()
        collection = database[USER_COLLECTION]
        if collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            print(f"ERROR: User with username '{username}' or email '{email}' already exists.")
            return None # Indicates user already exists
        user_doc = {
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc)
        }
        result = collection.insert_one(user_doc)
        print(f"User '{username}' created successfully with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"Error creating user '{username}': {e}")
        return None

def get_user_by_username(username):
    """Retrieves a user by their username."""
    if not username: return None
    try:
        database = connect_db()
        collection = database[USER_COLLECTION]
        return collection.find_one({"username": username})
    except Exception as e:
        print(f"Error retrieving user by username '{username}': {e}")
        return None

def get_user_by_id(user_id):
    """Retrieves a user by their ID."""
    if not user_id: return None
    try:
        database = connect_db()
        collection = database[USER_COLLECTION]
        return collection.find_one({"_id": ObjectId(user_id)})
    except Exception as e:
        print(f"Error retrieving user by ID '{user_id}': {e}")
        return None

# --- Personalized Search Results (Session-Specific, now User-Specific) ---

def save_personalized_search_session(session_id: str, resume_score: float, extracted_skills: list,
                                   personalized_job_results: list, raw_resume_text: str = None, user_id: str = None):
    """
    Saves or updates a document containing resume data and personalized job results
    for a specific session, potentially linked to a user.
    """
    if not session_id:
        print("ERROR: session_id is required to save personalized search.")
        return None

    try:
        database = connect_db()
        collection = database[PERSONALIZED_SEARCH_COLLECTION]

        search_document = {
            "session_id": session_id, # This is the search_id from app.py
            "resume_data": {
                "score": resume_score, # Changed from "resume_score" to "score" to match get_personalized_search_session expectations if any
                "extracted_skills": extracted_skills,
                "raw_text": raw_resume_text
            },
            "personalized_jobs": personalized_job_results,
            "created_at": datetime.now(timezone.utc),
            # "recommended_jobs": [] # If you decide to store recommended jobs snapshot with the session
        }
        if user_id: # Link to user if user_id is provided
            search_document["user_id"] = ObjectId(user_id)

        # Using session_id as the primary key for these search session documents
        result = collection.update_one(
            {"session_id": session_id},
            {"$set": search_document},
            upsert=True
        )
        print(f"Personalized search session for '{session_id}' (User: {user_id}) saved. Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted ID: {result.upserted_id}")
        return result.upserted_id if result.upserted_id else session_id # Return the session_id or new upserted id
    except Exception as e:
        print(f"Error saving personalized search session for '{session_id}': {e}")
        return None

def get_personalized_search_session(session_id: str):
    """
    Retrieves the personalized search session data for a given session_id.
    """
    if not session_id:
        print("ERROR: session_id is required to retrieve personalized search.")
        return None
    try:
        database = connect_db()
        collection = database[PERSONALIZED_SEARCH_COLLECTION]
        document = collection.find_one({"session_id": session_id})
        if document:
            # Ensure resume_data structure is consistent for easier access in templates
            if 'resume_data' in document and 'score' not in document['resume_data'] and 'resume_score' in document['resume_data']:
                document['resume_data']['score'] = document['resume_data'].pop('resume_score')
            print(f"Personalized search session found for '{session_id}'.")
        else:
            print(f"No personalized search session found for '{session_id}'.")
        return document
    except Exception as e:
        print(f"Error retrieving personalized search session for '{session_id}': {e}")
        return None

def get_search_sessions_for_user(user_id: str, limit: int = 10):
    """Retrieves all personalized search sessions for a given user_id, sorted by creation date."""
    if not user_id:
        print("ERROR: user_id is required to retrieve user's search sessions.")
        return []
    try:
        database = connect_db()
        collection = database[PERSONALIZED_SEARCH_COLLECTION]
        # Sort by 'created_at' descending to get the latest sessions first
        user_sessions = list(collection.find({"user_id": ObjectId(user_id)}).sort("created_at", -1).limit(limit))
        print(f"Found {len(user_sessions)} search sessions for user_id '{user_id}'.")
        return user_sessions
    except Exception as e:
        print(f"Error retrieving search sessions for user_id '{user_id}': {e}")
        return []


def delete_personalized_search_session(session_id: str):
    """
    Deletes the personalized search session data for a given session_id,
    only if it's older than one year.
    Returns a status string: "deleted", "retained", "not_found", or "error".
    """
    if not session_id:
        print("ERROR: session_id is required to delete personalized search.")
        return "error" # Return error status
    try:
        database = connect_db()
        collection = database[PERSONALIZED_SEARCH_COLLECTION]
        
        # Fetch the document first to check its creation date
        document_to_delete = collection.find_one({"session_id": session_id})

        if not document_to_delete:
            print(f"No personalized search session found for '{session_id}' to delete.")
            return "not_found" # Return not_found status

        created_at_timestamp = document_to_delete.get("created_at")
        
        # Policy: If created_at is missing, do not delete to be safe.
        if not created_at_timestamp:
            print(f"CRITICAL: 'created_at' timestamp missing for session '{session_id}'. Retention policy cannot be applied. Record will be retained.")
            return "retained" # Retain if timestamp is missing for safety

        # Ensure created_at_timestamp is offset-aware (timezone.utc) for comparison
        if created_at_timestamp.tzinfo is None:
            created_at_timestamp = created_at_timestamp.replace(tzinfo=timezone.utc)

        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

        if created_at_timestamp > one_year_ago:
            # Document is newer than one year, so it should be retained
            print(f"Personalized search session for '{session_id}' is within the 1-year retention period (Created: {created_at_timestamp}). Not deleted.")
            return "retained" # Return retained status

        # If older than one year, proceed with deletion
        result = collection.delete_one({"session_id": session_id})
        if result.deleted_count > 0:
            print(f"Personalized search session for '{session_id}' (older than 1 year) deleted successfully.")
            return "deleted" # Return deleted status
        else:
            # This case might occur if the document was deleted between the find_one and delete_one calls (race condition)
            print(f"Warning: Document for session '{session_id}' found but not deleted by delete_one. It might have been already cleared.")
            return "not_found" # Or a more specific status like "concurrent_deletion"
            
    except Exception as e:
        print(f"Error during deletion process for personalized search session '{session_id}': {e}")
        return "error" # Return error status

# --- Recommended Job Results (More Persistent Cache) ---
def save_recommended_job(job_data: dict, source_keywords: list):
    """Saves or updates a recommended job in the cache."""
    if not job_data or not job_data.get('url'): # Assuming URL is a unique identifier for a job
        print("ERROR: Job data with a URL is required to save a recommended job.")
        return None
    try:
        database = connect_db()
        collection = database[RECOMMENDED_JOBS_COLLECTION]
        job_document = {
            "job_details": job_data,
            "source_keywords": source_keywords, # Keywords that led to this job recommendation
            "first_seen_at": datetime.now(timezone.utc),
            "last_updated_at": datetime.now(timezone.utc)
        }
        # Upsert based on the job URL
        result = collection.update_one(
            {"job_details.url": job_data['url']},
            {
                "$set": { # Update these fields if job already exists
                    "job_details": job_data,
                    "source_keywords": source_keywords, # Could also use $addToSet for keywords
                    "last_updated_at": datetime.now(timezone.utc)
                },
                "$setOnInsert": {"first_seen_at": datetime.now(timezone.utc)} # Set only on creation
            },
            upsert=True
        )
        if result.upserted_id:
            print(f"New recommended job added to cache: {job_data['url']}")
        else:
            print(f"Recommended job updated in cache: {job_data['url']}")
        return result.upserted_id if result.upserted_id else job_data['url'] # Return ID or URL
    except Exception as e:
        print(f"Error saving recommended job '{job_data.get('url')}': {e}")
        return None

def get_recommended_jobs_by_keywords(keywords: list, limit: int = 20):
    """Retrieves recommended jobs from cache that match any of the given keywords."""
    if not keywords:
        print("INFO: No keywords provided for fetching recommended jobs.")
        return []
    try:
        database = connect_db()
        collection = database[RECOMMENDED_JOBS_COLLECTION]
        # Find jobs where 'source_keywords' array contains any of the 'keywords'
        query = {"source_keywords": {"$in": keywords}}
        # Sort by last update time to get fresher results, or by relevance if available
        jobs_cursor = collection.find(query).sort("last_updated_at", -1).limit(limit)
        jobs = [job['job_details'] for job in jobs_cursor if 'job_details' in job] # Extract actual job data
        print(f"Found {len(jobs)} recommended jobs for keywords: {keywords}")
        return jobs
    except Exception as e:
        print(f"Error retrieving recommended jobs by keywords: {e}")
        return []

# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Database Manager - Direct Test Mode")

    if not MONGO_URI:
        print("Please set MONGO_ATLAS_URI in your .env file to run tests.")
    else:
        # Example Test: Connect to DB
        db_conn = connect_db()
        if db_conn:
            print(f"Successfully connected to DB: {db_conn.name}")

            # Test User Creation (Example)
            # test_user_id = create_user("testuser_dbm", "testdbm@example.com", "hashed_password_example")
            # if test_user_id:
            #     print(f"Test user created with ID: {test_user_id}")
            #     retrieved_user = get_user_by_id(str(test_user_id))
            #     print(f"Retrieved test user: {retrieved_user}")

            #     # Test Saving Personalized Search Session (Example)
            #     test_session_id = "dbm_test_session_123"
            #     save_personalized_search_session(
            #         session_id=test_session_id,
            #         resume_score=0.85,
            #         extracted_skills=["python", "flask", "mongodb"],
            #         personalized_job_results=[{"title": "Python Dev", "company": "TestCo"}],
            #         raw_resume_text="This is a test resume text.",
            #         user_id=str(test_user_id)
            #     )
            #     retrieved_session = get_personalized_search_session(test_session_id)
            #     print(f"Retrieved test session: {retrieved_session}")

            #     user_history = get_search_sessions_for_user(str(test_user_id))
            #     print(f"User history for {test_user_id}: {len(user_history)} items")

                # Test Deletion Logic
                # Create a dummy session ID for deletion testing
                # recent_session_id_del = "recent_session_to_delete_dbm"
                # save_personalized_search_session(recent_session_id_del, 0.5, ["test"], [], "recent text", user_id=str(test_user_id))
                # status_recent = delete_personalized_search_session(recent_session_id_del)
                # print(f"Deletion status for recent session '{recent_session_id_del}': {status_recent}") # Expected: retained

                # To test actual deletion of an old record:
                # 1. Manually insert a record into 'personalized_searches' collection
                #    with a 'session_id' (e.g., "old_session_dbm") and 'user_id',
                #    and set 'created_at' to a date older than one year.
                #    Example: datetime.now(timezone.utc) - timedelta(days=400)
                # 2. Then call:
                # old_session_id_del = "old_session_dbm" # The one you manually created/aged
                # status_old = delete_personalized_search_session(old_session_id_del)
                # print(f"Deletion status for old session '{old_session_id_del}': {status_old}") # Expected: deleted or not_found if not set up

        else:
            print("Failed to connect to DB for testing.")
        print("\n--- Database Manager Test Complete ---")