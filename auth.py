import mysql.connector
from db import get_db_connection
import hashlib
from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, email, role):
        self.email = email
        self.role = role

    def get_id(self):
        return self.email

def authenticate_user(email, password):
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)

    query = "SELECT user_id, email, login_type FROM auth WHERE email = %s AND password = %s"
    cursor.execute(query, (email, password))

    user_data = cursor.fetchone()

    cursor.close()
    conn.close()

    if user_data:
        user_id = user_data["user_id"]  # Fetch user_id
        role = user_data["login_type"]  # Fetch role (admin, faculty, student)
        print(f"DEBUG: Logging in user {email} with role {role}")  # Debugging

        return User(user_id, role)  # Replace "admin" with actual role lookup ✅

    return None
