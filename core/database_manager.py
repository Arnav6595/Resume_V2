import os
from pymongo import MongoClient, UpdateOne, errors
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from bson import ObjectId

# Load environment variables (e.g., for MONGO_URI)
load_dotenv()

# --- Configuration ---
MONGO_URI = os.environ.get("MONGO_ATLAS_URI") # Your MongoDB Atlas connection string
DB_NAME = "job_matching_app" # Or your preferred database name
PERSONALIZED_SEARCH_COLLECTION = "personalized_searches"
RECOMMENDED_JOBS_COLLECTION = "recommended_jobs_cache"
USER_COLLECTION = "users"
# New collection for the Resume Builder
USER_RESUMES_COLLECTION = "user_resumes" # Added for resume builder

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
# (Existing functions: create_user, get_user_by_username, get_user_by_id - remain unchanged)
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


# --- Personalized Search Results ---
# (Existing functions: save_personalized_search_session, get_personalized_search_session,
#  get_search_sessions_for_user, delete_personalized_search_session - remain unchanged)
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
                "score": resume_score,
                "extracted_skills": extracted_skills,
                "raw_text": raw_resume_text
            },
            "personalized_jobs": personalized_job_results,
            "created_at": datetime.now(timezone.utc),
        }
        if user_id: # Link to user if user_id is provided
            search_document["user_id"] = ObjectId(user_id)

        result = collection.update_one(
            {"session_id": session_id},
            {"$set": search_document},
            upsert=True
        )
        print(f"Personalized search session for '{session_id}' (User: {user_id}) saved. Matched: {result.matched_count}, Modified: {result.modified_count}, Upserted ID: {result.upserted_id}")
        return result.upserted_id if result.upserted_id else session_id
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
        return "error"
    try:
        database = connect_db()
        collection = database[PERSONALIZED_SEARCH_COLLECTION]
        
        document_to_delete = collection.find_one({"session_id": session_id})

        if not document_to_delete:
            print(f"No personalized search session found for '{session_id}' to delete.")
            return "not_found"

        created_at_timestamp = document_to_delete.get("created_at")
        
        if not created_at_timestamp:
            print(f"CRITICAL: 'created_at' timestamp missing for session '{session_id}'. Record will be retained.")
            return "retained"

        if created_at_timestamp.tzinfo is None:
            created_at_timestamp = created_at_timestamp.replace(tzinfo=timezone.utc)

        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

        if created_at_timestamp > one_year_ago:
            print(f"Personalized search session for '{session_id}' is within the 1-year retention period. Not deleted.")
            return "retained"

        result = collection.delete_one({"session_id": session_id})
        if result.deleted_count > 0:
            print(f"Personalized search session for '{session_id}' (older than 1 year) deleted successfully.")
            return "deleted"
        else:
            print(f"Warning: Document for session '{session_id}' found but not deleted. It might have been already cleared.")
            return "not_found"
            
    except Exception as e:
        print(f"Error during deletion process for personalized search session '{session_id}': {e}")
        return "error"

# --- Recommended Job Results ---
# (Existing functions: save_recommended_job, get_recommended_jobs_by_keywords - remain unchanged)
def save_recommended_job(job_data: dict, source_keywords: list):
    """Saves or updates a recommended job in the cache."""
    if not job_data or not job_data.get('url'):
        print("ERROR: Job data with a URL is required to save a recommended job.")
        return None
    try:
        database = connect_db()
        collection = database[RECOMMENDED_JOBS_COLLECTION]
        job_document = {
            "job_details": job_data,
            "source_keywords": source_keywords,
            "first_seen_at": datetime.now(timezone.utc),
            "last_updated_at": datetime.now(timezone.utc)
        }
        result = collection.update_one(
            {"job_details.url": job_data['url']},
            {
                "$set": {
                    "job_details": job_data,
                    "source_keywords": source_keywords,
                    "last_updated_at": datetime.now(timezone.utc)
                },
                "$setOnInsert": {"first_seen_at": datetime.now(timezone.utc)}
            },
            upsert=True
        )
        if result.upserted_id:
            print(f"New recommended job added to cache: {job_data['url']}")
        else:
            print(f"Recommended job updated in cache: {job_data['url']}")
        return result.upserted_id if result.upserted_id else job_data['url']
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
        query = {"source_keywords": {"$in": keywords}}
        jobs_cursor = collection.find(query).sort("last_updated_at", -1).limit(limit)
        jobs = [job['job_details'] for job in jobs_cursor if 'job_details' in job]
        print(f"Found {len(jobs)} recommended jobs for keywords: {keywords}")
        return jobs
    except Exception as e:
        print(f"Error retrieving recommended jobs by keywords: {e}")
        return []

# --- Resume Builder Functions ---
# NEW FUNCTIONS START HERE

def create_user_resume(user_id: str, resume_name: str, resume_data: dict, template_id: str = "default"):
    """
    Creates a new resume document for a user.
    Args:
        user_id (str): The ID of the user.
        resume_name (str): A name for the resume (e.g., "Software Engineer Resume").
        resume_data (dict): The structured data for the resume sections.
                            Example: {"personal_info": {...}, "experience": [{...}], ...}
        template_id (str): Identifier for the resume template used (optional).
    Returns:
        The ObjectId of the newly created resume, or None if an error occurred.
    """
    if not user_id or not resume_name or not resume_data:
        print("ERROR: user_id, resume_name, and resume_data are required to create a user resume.")
        return None
    try:
        database = connect_db()
        collection = database[USER_RESUMES_COLLECTION]
        
        current_time = datetime.now(timezone.utc)
        resume_document = {
            "user_id": ObjectId(user_id),
            "resume_name": resume_name,
            "template_id": template_id,
            "sections": resume_data, # This will store the detailed resume content
            "created_at": current_time,
            "updated_at": current_time
        }
        result = collection.insert_one(resume_document)
        print(f"User resume '{resume_name}' for user '{user_id}' created successfully with ID: {result.inserted_id}")
        return result.inserted_id
    except Exception as e:
        print(f"Error creating user resume for user '{user_id}': {e}")
        return None

def get_user_resumes(user_id: str, limit: int = 20):
    """
    Retrieves all resumes created by a specific user.
    Args:
        user_id (str): The ID of the user.
        limit (int): Maximum number of resumes to return.
    Returns:
        A list of resume documents, or an empty list if none are found or an error occurs.
    """
    if not user_id:
        print("ERROR: user_id is required to retrieve user resumes.")
        return []
    try:
        database = connect_db()
        collection = database[USER_RESUMES_COLLECTION]
        resumes = list(collection.find({"user_id": ObjectId(user_id)})
                       .sort("updated_at", -1) # Sort by most recently updated
                       .limit(limit))
        print(f"Found {len(resumes)} resumes for user_id '{user_id}'.")
        return resumes
    except Exception as e:
        print(f"Error retrieving resumes for user_id '{user_id}': {e}")
        return []

def get_user_resume_by_id(resume_id: str, user_id: str):
    """
    Retrieves a specific resume by its ID, ensuring it belongs to the specified user.
    Args:
        resume_id (str): The ID of the resume.
        user_id (str): The ID of the user who should own the resume.
    Returns:
        The resume document if found and owned by the user, otherwise None.
    """
    if not resume_id or not user_id:
        print("ERROR: resume_id and user_id are required to retrieve a specific user resume.")
        return None
    try:
        database = connect_db()
        collection = database[USER_RESUMES_COLLECTION]
        # Ensure both resume_id and user_id match
        resume_document = collection.find_one({
            "_id": ObjectId(resume_id),
            "user_id": ObjectId(user_id)
        })
        if resume_document:
            print(f"Resume found with ID '{resume_id}' for user '{user_id}'.")
        else:
            print(f"No resume found with ID '{resume_id}' for user '{user_id}', or permission denied.")
        return resume_document
    except Exception as e:
        print(f"Error retrieving resume ID '{resume_id}' for user '{user_id}': {e}")
        return None

def update_user_resume(resume_id: str, user_id: str, updated_resume_data: dict = None, new_resume_name: str = None):
    """
    Updates an existing resume for a user.
    Only updates fields that are provided.
    Args:
        resume_id (str): The ID of the resume to update.
        user_id (str): The ID of the user who owns the resume.
        updated_resume_data (dict, optional): The new structured data for the resume sections.
        new_resume_name (str, optional): The new name for the resume.
    Returns:
        True if the update was successful, False otherwise.
    """
    if not resume_id or not user_id:
        print("ERROR: resume_id and user_id are required to update a user resume.")
        return False
    if not updated_resume_data and not new_resume_name:
        print("INFO: No data provided to update for resume.")
        return False # Or True, if no change means success

    try:
        database = connect_db()
        collection = database[USER_RESUMES_COLLECTION]
        
        update_fields = {"updated_at": datetime.now(timezone.utc)}
        if updated_resume_data:
            update_fields["sections"] = updated_resume_data
        if new_resume_name:
            update_fields["resume_name"] = new_resume_name

        result = collection.update_one(
            {"_id": ObjectId(resume_id), "user_id": ObjectId(user_id)},
            {"$set": update_fields}
        )
        if result.matched_count == 0:
            print(f"No resume found with ID '{resume_id}' for user '{user_id}' to update, or permission denied.")
            return False
        if result.modified_count > 0:
            print(f"Resume '{resume_id}' for user '{user_id}' updated successfully.")
            return True
        else:
            print(f"Resume '{resume_id}' for user '{user_id}' was matched but not modified (data might be the same).")
            return True # Consider this a success if no modification was needed
    except Exception as e:
        print(f"Error updating resume '{resume_id}' for user '{user_id}': {e}")
        return False

def delete_user_resume(resume_id: str, user_id: str):
    """
    Deletes a specific resume created by a user.
    Args:
        resume_id (str): The ID of the resume to delete.
        user_id (str): The ID of the user who owns the resume.
    Returns:
        True if the deletion was successful, False otherwise.
    """
    if not resume_id or not user_id:
        print("ERROR: resume_id and user_id are required to delete a user resume.")
        return False
    try:
        database = connect_db()
        collection = database[USER_RESUMES_COLLECTION]
        result = collection.delete_one({
            "_id": ObjectId(resume_id),
            "user_id": ObjectId(user_id)
        })
        if result.deleted_count > 0:
            print(f"Resume '{resume_id}' for user '{user_id}' deleted successfully.")
            return True
        else:
            print(f"No resume found with ID '{resume_id}' for user '{user_id}' to delete, or permission denied.")
            return False
    except Exception as e:
        print(f"Error deleting resume '{resume_id}' for user '{user_id}': {e}")
        return False

# NEW FUNCTIONS END HERE
# --- Example Usage (for testing this module directly) ---
if __name__ == "__main__":
    print("Database Manager - Direct Test Mode")

    if not MONGO_URI:
        print("Please set MONGO_ATLAS_URI in your .env file to run tests.")
    else:
        db_conn = connect_db()
        if db_conn:
            print(f"Successfully connected to DB: {db_conn.name}")

            # --- Test Resume Builder Functions ---
            # Ensure you have a test user ID for these tests.
            # You might need to create one manually or use an existing one from your DB.
            # Example: Find an existing user or create one.
            test_user_obj = get_user_by_username("testuser_dbm") # Assuming this user exists from previous tests
            if not test_user_obj:
                 created_id = create_user("testuser_builder", "builder@example.com", "dummyhash")
                 if created_id:
                     test_user_obj = get_user_by_id(str(created_id))

            if test_user_obj:
                test_user_id_str = str(test_user_obj['_id'])
                print(f"\n--- Testing Resume Builder Functions with User ID: {test_user_id_str} ---")

                # 1. Create a resume
                sample_resume_data = {
                    "personal_info": {"name": "Test Builder", "email": "test@builder.com", "phone": "1234567890"},
                    "summary": "A dedicated builder of tests.",
                    "experience": [
                        {"title": "Test Engineer", "company": "Test Corp", "years": "2022-Present", "description": "Built many tests."}
                    ],
                    "education": [
                        {"degree": "B.Sc. Testology", "institution": "Test University", "year": "2021"}
                    ],
                    "skills": ["testing", "building", "python"]
                }
                created_resume_id = create_user_resume(test_user_id_str, "My First Test Resume", sample_resume_data)
                if created_resume_id:
                    print(f"Successfully created resume with ID: {created_resume_id}")

                    # 2. Get all resumes for the user
                    user_resumes_list = get_user_resumes(test_user_id_str)
                    print(f"User has {len(user_resumes_list)} resumes. First one: {user_resumes_list[0]['resume_name'] if user_resumes_list else 'None'}")

                    # 3. Get the specific resume by ID
                    retrieved_resume = get_user_resume_by_id(str(created_resume_id), test_user_id_str)
                    if retrieved_resume:
                        print(f"Successfully retrieved resume: {retrieved_resume.get('resume_name')}")
                        assert retrieved_resume['sections']['summary'] == "A dedicated builder of tests."

                    # 4. Update the resume
                    updated_data_sections = retrieved_resume['sections'] # Get existing sections
                    updated_data_sections['summary'] = "An extremely dedicated builder of tests and other things." # Modify summary
                    update_success = update_user_resume(str(created_resume_id), test_user_id_str, updated_resume_data=updated_data_sections, new_resume_name="My Updated Test Resume")
                    if update_success:
                        print("Resume updated successfully.")
                        updated_retrieved_resume = get_user_resume_by_id(str(created_resume_id), test_user_id_str)
                        print(f"Updated resume name: {updated_retrieved_resume.get('resume_name')}")
                        print(f"Updated summary: {updated_retrieved_resume['sections']['summary']}")
                        assert updated_retrieved_resume['sections']['summary'] == "An extremely dedicated builder of tests and other things."
                        assert updated_retrieved_resume['resume_name'] == "My Updated Test Resume"


                    # 5. Delete the resume
                    # delete_success = delete_user_resume(str(created_resume_id), test_user_id_str)
                    # if delete_success:
                    #     print(f"Resume {created_resume_id} deleted successfully.")
                    #     deleted_check = get_user_resume_by_id(str(created_resume_id), test_user_id_str)
                    #     assert deleted_check is None, "Resume should be deleted."
                    # else:
                    #     print(f"Failed to delete resume {created_resume_id}")
                else:
                    print("Failed to create a test resume.")
            else:
                print("Could not find or create a test user for resume builder tests. Please ensure a user exists.")
            # (Keep existing test code for other functions if desired)

        else:
            print("Failed to connect to DB for testing.")
        print("\n--- Database Manager Test Complete ---")