print("Starting Flask application...")
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_session import Session 
from auth import User, authenticate_user
from db import execute_query, fetch_query_results, get_db_connection
from query_processor import process_natural_language_query
import hashlib

app = Flask(__name__)
print("Flask app initialized.")
app.secret_key = "your_secret_key"
app.config["SECRET_KEY"] = "your_secret_key_here"  # ✅ Required for sessions
app.config["SESSION_TYPE"] = "filesystem"  # ✅ Ensures sessions persist
Session(app)  # ✅ Initialize Flask-Session
#from flask_session import Session

# Flask session configuration
'''app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False  # Prevents automatic logout issues
app.config["SESSION_USE_SIGNER"] = True  # Secures sessions
app.config["SESSION_KEY_PREFIX"] = "sqlingual_"  # Helps avoid conflicts
Session(app)'''


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(email):
    print("DEBUG: Loading User - Email:", email)  # Debugging
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    query = "SELECT email, login_type FROM auth WHERE user_id = %s"
    cursor.execute(query, (email,))

    user_data = cursor.fetchone()
    cursor.close()
    conn.close()

    if user_data:
        print(f"DEBUG: Loaded user {user_data['email']} with role {user_data['login_type']}")  # Debugging
        return User(user_data["email"], user_data["login_type"])

    print("DEBUG: not loaded user")

    return None


@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    data = request.get_json() if request.content_type == "application/json" else request.form
    email = data.get("email")
    password = data.get("password")
    
    user = authenticate_user(email, password)
    
    if user:
        login_user(user, remember=True)
        print(f"DEBUG: Logged in as {user.email} with role {user.role}")
        return jsonify({"success": True, "redirect": url_for(f"{user.role}_dashboard")})
    else:
        return jsonify({"success": False, "message": "Invalid email or password."})


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/admin")
@login_required
def admin_dashboard():
    return render_template("admin.html")

@app.route("/faculty")
@login_required
def faculty_dashboard():
    return render_template("faculty.html")

@app.route("/student")
@login_required
def student_dashboard():
    return render_template("student.html")

@app.route("/query", methods=["POST"])
@login_required
def process_query():
    try:
        data = request.get_json() if request.content_type == "application/json" else request.form
        natural_language_query = data.get("query")

        user_role = current_user.role  # Ensure 'role' exists in User class
        user_email = current_user.email

        
        print("Received query:", natural_language_query)  # Debug log
        
        sql_query = process_natural_language_query(natural_language_query, user_role, user_email)
        print("Generated SQL:", sql_query)  # Debug log

        if sql_query == "Unauthorized":
            return jsonify({"success": False, "error": "Unauthorized query. You do not have permission to access this data."})
        
        results = fetch_query_results(sql_query)
        print("Query results:", results)  # Debug log
        
        return jsonify({"success": True, "query": natural_language_query, "results": results})

    
    except Exception as e:
        print("Error processing query:", str(e))  # Debug log
        return jsonify({"success": False, "message": "Query processing failed."}), 500


@app.route("/add-faculty", methods=["POST"])
@login_required
def add_faculty():
    data = request.get_json() if request.content_type == "application/json" else request.form

    try:
        # Insert into faculty_details
        faculty_query = "INSERT INTO faculty_details (name, department, email) VALUES (%s, %s, %s)"
        execute_query(faculty_query, (data["faculty-name"], data["faculty-department"], data["faculty-email"]))
        print("Faculty inserted successfully.")

        # Insert into auth table
        auth_query = "INSERT INTO auth (email, password, login_type) VALUES (%s, %s, 'faculty')"
        execute_query(auth_query, (data["faculty-email"], data["faculty-password"]))
        print("Auth table updated successfully.")

        return jsonify({"success": True, "message": "Faculty added successfully!"})
    except Exception as e:
        print("Error inserting into auth table:", str(e))
        return jsonify({"success": False, "message": "Error updating auth table."})


@app.route("/add-student", methods=["POST"])
@login_required
def add_student():
    data = request.get_json() if request.content_type == "application/json" else request.form
    
    student_query = "INSERT INTO student_details (name, email, department, year) VALUES (%s, %s, %s, %s)"
    execute_query(student_query, (data["student-name"], data["student-email"], data["student-department"], data["student-year"]))
    
    auth_query = "INSERT INTO auth (email, password, login_type) VALUES (%s, %s, 'student')"
    execute_query(auth_query, (data["student-email"], data["student-password"]))
    
    return jsonify({"success": True, "message": "Student added successfully!"})

@app.route("/add-marks", methods=["POST"])
@login_required
def add_marks():
    print("DEBUG: Current User Role ->", current_user.role)  # Debugging

    if current_user.role != "faculty":  # Ensure it matches database role
        return jsonify({"success": False, "message": "Unauthorized access"}), 403

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Invalid input data"}), 400

    # Get faculty ID from the logged-in user's email
    faculty_query = "SELECT faculty_id FROM faculty_details WHERE email = %s"
    faculty_result = fetch_query_results(faculty_query, (current_user.email,))

    if not faculty_result:
        return jsonify({"success": False, "message": "Faculty ID not found"}), 404

    faculty_id = faculty_result[0]["faculty_id"]

    # Insert marks along with the faculty_id
    query = "INSERT INTO marks (student_id, course_id, marks_obtained, faculty_id) VALUES (%s, %s, %s, %s)"
    execute_query(query, (data.get("student-id"), data.get("course-id"), data.get("marks"), faculty_id))

    return jsonify({"success": True, "message": "Marks added successfully!"})

if __name__ == "__main__":
    print("Running Flask now...")
    app.run(debug=True)


'''
import sys
import traceback

print("Starting Flask application...")

try:
    from flask import Flask
    print("Flask module imported successfully.")

    app = Flask(__name__)

    print("Flask app initialized.")

    if __name__ == "__main__":
        print("Running Flask now...")
        app.run(debug=True)
except Exception as e:
    print("Flask failed to start!")
    traceback.print_exc()  # Prints the full error traceback
    print(f"Error Details: {e}", file=sys.stderr)
'''
