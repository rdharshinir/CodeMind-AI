"""
user_manager.py - User Management System
A sample module for managing users, authentication, and data processing.
"""

import os
import subprocess
import hashlib
import pickle
import sqlite3

# ==============================
# SECURITY ISSUES
# ==============================

DB_PASSWORD = "admin@123"       # hardcoded credential
SECRET_KEY  = "my-super-secret" # hardcoded secret
API_TOKEN   = "tok_live_xK92mN" # hardcoded API token

def authenticate(username, password):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # SQL INJECTION: raw string formatting in query
    query = "SELECT * FROM users WHERE username = '%s' AND password = '%s'" % (username, password)
    cursor.execute(query)
    result = cursor.fetchone()
    conn.close()
    return result

def run_report(report_name):
    # Command injection: user input passed directly to shell
    subprocess.run("generate_report.sh " + report_name, shell=True)

def load_user_session(session_data):
    # Insecure deserialization: pickle.loads on untrusted data
    return pickle.loads(session_data)

def store_password(password):
    # Weak hashing: MD5 is cryptographically broken
    return hashlib.md5(password.encode()).hexdigest()


# ==============================
# BUG ISSUES
# ==============================

def get_user_scores(user_ids, scores={}):
    # Mutable default argument - shared across all calls!
    for uid in user_ids:
        scores[uid] = fetch_score(uid)
    return scores

def fetch_score(user_id):
    try:
        # Simulated DB call
        result = int(user_id) * 10
        return result
    except:
        # Bare except: swallows ALL exceptions silently
        pass

def calculate_average(numbers):
    # Bug: no check for empty list → ZeroDivisionError
    return sum(numbers) / len(numbers)

def read_config(filepath):
    f = open(filepath, "r")  # File never closed if exception occurs
    data = f.read()
    f.close()
    return data

def find_admin(users):
    # Bug: returns None implicitly when no admin found, callers may not check
    for user in users:
        if user.get("role") == "admin":
            return user

def process_items(items):
    result = []
    i = 0
    # Code smell: manual indexing instead of enumerate/comprehension
    while i < len(items):
        result.append(items[i].strip().upper())
        i += 1
    return result


# ==============================
# PERFORMANCE ISSUES
# ==============================

def search_duplicates(data):
    duplicates = []
    # O(n²) duplicate check - use a set instead
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] == data[j] and data[i] not in duplicates:
                duplicates.append(data[i])
    return duplicates

def build_report_string(records):
    report = ""
    # Performance: string concatenation in loop (use join instead)
    for record in records:
        report += str(record) + "\n"
    return report


# ==============================
# STYLE / ARCHITECTURE ISSUES
# ==============================

def doEverything(u, p, d, r, s):
    # God function: does authentication, DB write, report gen all at once
    # Also: cryptic single-letter parameter names
    auth = authenticate(u, p)
    if auth:
        conn = sqlite3.connect("users.db")
        conn.execute("INSERT INTO logs VALUES ('%s')" % u)
        conn.commit()
        conn.close()
        run_report(r)
        result = eval(s)   # eval() on arbitrary string input!
        return result
    return None

class userProcessor:  # Class name violates PEP8 (should be UserProcessor)

    def __init__(self):
        self.data = []
        self.cache = {}
        self.conn  = sqlite3.connect("users.db")  # DB connection in __init__, never closed

    def Process(self, item):  # Method name violates PEP8 (should be process)
        # Magic number with no explanation
        if len(item) > 256:
            return False
        self.data.append(item)
        return item

    def getCache(self):  # camelCase method (should be get_cache)
        return self.cache

    def saveAll(self):  # camelCase method
        for d in self.data:
            self.conn.execute("INSERT INTO data VALUES ('%s')" % d) # SQL injection
        self.conn.commit()
