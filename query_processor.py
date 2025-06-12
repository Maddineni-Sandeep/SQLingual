import openai
import os
from db import get_db_connection  # Import DB connection

# Set OpenAI API Key
OPENAI_API_KEY = "" # Add your openai api key here

def process_natural_language_query(nl_query, user_role, user_email):
    """Convert English query to SQL using OpenAI API with schema."""

    prompt = f"""
    You are an AI assistant that converts English queries into SQL queries.
    Use the following MySQL database schema to generate accurate SQL queries:

    Table: auth (user_id, email, password, login_type)
    Table: faculty_details (faculty_id, name, department, email)
    Table: marks (mark_id, student_id, course_id, faculty_id, marks_obtained)
    Table: student_details (student_id, name, email, department, year)

    Convert the following natural language query into an SQL query:
    "{nl_query}"

    Rules:
    - If the user is an 'admin', they can access all data.
    - If the user is a 'faculty', they can access all students' data and their own data in facutly_details.
    - If the user is a 'student', they can only access their own data.

    The current user has role: {user_role}
    The current user email is: {user_email}
    
    given just the sql query as reply no explanation, no nothing, just sql query

    if the query is violating access rules give me output as "Unauthorized" instead of generating SQL.

    SQL Query:
    """

    try:
        client = openai.OpenAI(api_key=OPENAI_API_KEY)  # ✅ Pass API key correctly
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an AI that converts English queries into MySQL queries."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1000
        )

        if "Unauthorized" in response or "Access Denied" in response:
            return "Unauthorized"

        sql_query = response.choices[0].message.content.strip()

        # Remove markdown formatting
        if sql_query.startswith("```sql"):
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        
        return sql_query

    except Exception as e:
        print("Error processing query:", e)
        return None
    

def execute_query(sql_query):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="SQLingualDB"
    )
    cursor = conn.cursor()
    cursor.execute(sql_query)
    results = cursor.fetchall()
    conn.close()
    return results
