import mysql.connector

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="SQLingual"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def execute_query(query, params=None):
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor()
    cursor.execute(query, params or ())
    conn.commit()
    cursor.close()
    conn.close()

def fetch_query_results(query, params=None):
    conn = get_db_connection()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    
    try:
        print("Executing query:", query)  # Debug log
        cursor.execute(query, params or ())
        results = cursor.fetchall()
        print("Query results:", results)  # Debug log
        return results
    except Exception as e:
        print("Error executing query:", str(e))  # Debug log
        return None
    finally:
        cursor.close()
        conn.close()

    
    return results
