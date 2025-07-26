from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config import MONGO_DB_URI, DB_NAME, DEFAULT_USER_PLAN
import datetime

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        self.users_collection = None
        self._connect()

    def _connect(self):
        """Establishes connection to MongoDB."""
        try:
            self.client = MongoClient(MONGO_DB_URI)
            self.client.admin.command('ismaster')
            self.db = self.client[DB_NAME]
            self.users_collection = self.db["users"]
            print("MongoDB connected successfully!")
        except ConnectionFailure as e:
            print(f"MongoDB connection failed: {e}")
            self.client = None
            self.db = None
            self.users_collection = None
        except Exception as e:
            print(f"An unexpected error occurred during MongoDB connection: {e}")
            self.client = None
            self.db = None
            self.users_collection = None

    def get_user(self, user_id: int):
        """Fetches user data from the database. Creates a new entry if user doesn't exist."""
        if not self.users_collection: return None
        user = self.users_collection.find_one({"_id": user_id})
        if not user:
            # Create a new user with default plan
            new_user_data = DEFAULT_USER_PLAN.copy()
            new_user_data["_id"] = user_id
            self.users_collection.insert_one(new_user_data)
            return new_user_data

        # --- Migration/Update for existing users to new fields ---
        # Add any missing fields from DEFAULT_USER_PLAN to existing user documents
        updated = False
        for key, default_value in DEFAULT_USER_PLAN.items():
            if key not in user:
                user[key] = default_value
                self.users_collection.update_one({"_id": user_id}, {"$set": {key: default_value}})
                updated = True
        # --- End Migration ---

        # Check and reset daily upload if new day
        today = datetime.date.today()
        if user.get("last_upload_date") and user["last_upload_date"].date() < today:
            self.users_collection.update_one(
                {"_id": user_id},
                {"$set": {"daily_uploaded_gb": 0, "last_upload_date": datetime.datetime.now()}}
            )
            user["daily_uploaded_gb"] = 0
            user["last_upload_date"] = datetime.datetime.now()

        return user

    def update_user_field(self, user_id: int, field_name: str, value):
        """Updates a specific field for a user."""
        if not self.users_collection: return False
        try:
            self.users_collection.update_one(
                {"_id": user_id},
                {"$set": {field_name: value}}
            )
            return True
        except Exception as e:
            print(f"Error updating user {user_id} field {field_name}: {e}")
            return False

    def increment_daily_upload(self, user_id: int, size_bytes: int):
        """Increments daily uploaded GB for a user."""
        if not self.users_collection: return False
        gb_uploaded = size_bytes / (1024**3) # Convert bytes to GB
        try:
            self.users_collection.update_one(
                {"_id": user_id},
                {"$inc": {"daily_uploaded_gb": gb_uploaded},
                 "$set": {"last_upload_date": datetime.datetime.now()}}
            )
            return True
        except Exception as e:
            print(f"Error incrementing daily upload for user {user_id}: {e}")
            return False

    def set_active_operation(self, user_id: int, file_data: dict):
        """Stores the active file operation context for a user."""
        return self.update_user_field(user_id, "active_file_operation", file_data)

    def get_active_operation(self, user_id: int):
        """Retrieves the active file operation context for a user."""
        user = self.get_user(user_id)
        return user.get("active_file_operation") if user else None

    def clear_active_operation(self, user_id: int):
        """Clears the active file operation context for a user."""
        return self.update_user_field(user_id, "active_file_operation", None)

    def close(self):
        """Closes the MongoDB connection."""
        if self.client:
            self.client.close()
            print("MongoDB connection closed.")

# Instantiate the database class
db = Database()
