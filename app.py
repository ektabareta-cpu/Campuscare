from flask import Flask, render_template, request, redirect, url_for, session, flash

from werkzeug.security import generate_password_hash, check_password_hash

from database import get_connection, initialize_database

from dsa import ComplaintPriorityQueue, ComplaintHashMap, merge_sort_complaints, ComplaintQueue


app = Flask(__name__)
def create_admin():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO users
        (name, email, password_hash, role)
        VALUES (?, ?, ?, ?)
    """, (
        "Campus Admin",
        "admin@campuscare.com",
        generate_password_hash("Admin@123"),
        "admin"
    ))

    connection.commit()
    connection.close()
# Secret key for session
app.secret_key = "campuscare_secret_key"


# Home page
@app.route("/")
def home():
    return render_template("index.html")


# Student and staff registration
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        role = request.form["role"]

        # Check empty fields
        if not name or not email or not password:
            flash("Please fill all the fields.")
            return redirect(url_for("register"))

        # Allow only student and staff registration
        if role not in ["student", "staff"]:
            flash("Invalid user role.")
            return redirect(url_for("register"))

        # Hash password
        hashed_password = generate_password_hash(password)

        connection = get_connection()
        cursor = connection.cursor()

        try:

            cursor.execute("""
                INSERT INTO users
                (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (name, email, hashed_password, role))

            connection.commit()
            flash("Registration successful! Please login.")

            return redirect(url_for("login"))

        except Exception:
            flash("This email is already registered or the details are invalid.")
            return redirect(url_for("register"))

        finally:
            connection.close()

    return render_template("register.html")


# User login
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT * FROM users WHERE email = ?
        """, (email,))

        user = cursor.fetchone()

        connection.close()

        # Check email and password
        if user and check_password_hash(user[3], password):

            session["user_id"] = user[0]
            session["user_name"] = user[1]
            session["user_role"] = user[4]

            return redirect("/dashboard")

        else:
            flash("Invalid email or password.")
            return redirect(url_for("login"))

    return render_template("login.html")


# Dashboard after login
# Dashboard after login
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    name = session["user_name"]
    role = session["user_role"]
    if role == "student":
        return render_template(
            "student_dashboard.html",
            name=name
        )

    elif role == "staff":

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                complaints.id,
                users.name,
                categories.category_name,
                complaints.location,
                complaints.description,
                complaints.priority,
                complaints.status,
                complaints.created_at
            FROM complaints
            JOIN users ON complaints.user_id = users.id
            JOIN categories ON complaints.category_id = categories.id
            WHERE complaints.assigned_staff = ?
            ORDER BY complaints.id DESC
        """, (session["user_id"],))

        complaints = cursor.fetchall()
       
        complaints = merge_sort_complaints(complaints)

        return render_template(
            "staff_dashboard.html",
            name=name,
            complaints=complaints
        )

    elif role == "admin":

      connection = get_connection()
    cursor = connection.cursor()

    # Get all complaints
    cursor.execute("""
        SELECT
            complaints.id,
            users.name,
            categories.category_name,
            complaints.location,
            complaints.description,
            complaints.priority,
            complaints.status,
            complaints.created_at,
            complaints.assigned_staff
        FROM complaints
        JOIN users
        ON complaints.user_id = users.id
        JOIN categories
        ON complaints.category_id = categories.id
        ORDER BY complaints.id DESC
    """)

    complaints = cursor.fetchall()
    # FIFO Queue
    complaint_queue = ComplaintQueue()

    for complaint in complaints:
      complaint_queue.add_complaint(complaint)

    complaints = complaint_queue.show_queue()
    # Apply Priority Queue
    priority_queue = ComplaintPriorityQueue()

    for complaint in complaints:
      priority_queue.add_complaint(complaint)
   
    complaints = priority_queue.show_complaints()

    # Get all staff members
    cursor.execute("""
        SELECT id, name
        FROM users
        WHERE role = 'staff'
    """)

    staff_members = cursor.fetchall()

    # Category-wise complaint count
    cursor.execute("""
        SELECT categories.category_name, COUNT(complaints.id)
        FROM categories
        LEFT JOIN complaints
        ON categories.id = complaints.category_id
        GROUP BY categories.id, categories.category_name
        ORDER BY COUNT(complaints.id) DESC
    """)

    category_stats = cursor.fetchall()

    # Average resolution time in hours
    cursor.execute("""
        SELECT AVG(
            (julianday(history.updated_at) -
             julianday(complaints.created_at)) * 24
        )
        FROM complaints
        JOIN complaint_history AS history
        ON complaints.id = history.complaint_id
        WHERE history.new_status = 'Resolved'
    """)

    average_resolution_time = cursor.fetchone()[0]

    if average_resolution_time is None:
        average_resolution_time = 0
    else:
        average_resolution_time = round(average_resolution_time, 2)

    connection.close()

    # Dashboard statistics
    total_complaints = len(complaints)

    pending_complaints = sum(
        1 for c in complaints if c[6] == "Pending"
    )

    in_progress_complaints = sum(
        1 for c in complaints if c[6] == "In Progress"
    )

    resolved_complaints = sum(
        1 for c in complaints if c[6] == "Resolved"
    )

    return render_template(
        "admin_dashboard.html",
        name=name,
        complaints=complaints,
        staff_members=staff_members,
        total_complaints=total_complaints,
        pending_complaints=pending_complaints,
        in_progress_complaints=in_progress_complaints,
        resolved_complaints=resolved_complaints,
        category_stats=category_stats,
        average_resolution_time=average_resolution_time
    )



    return render_template(
        "admin_dashboard.html",
        name=name,
        complaints=complaints,
        staff_members=staff_members,
        total_complaints=total_complaints,
        pending_complaints=pending_complaints,
        in_progress_complaints=in_progress_complaints,
        resolved_complaints=resolved_complaints
    )
        

    return "Invalid user role."
# Student My Profile
@app.route("/my_profile")
def my_profile():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session.get("user_role") != "student":
        return redirect(url_for("dashboard"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name, email, role
        FROM users
        WHERE id = ?
    """, (session["user_id"],))

    user = cursor.fetchone()
    connection.close()

    return render_template("my_profile.html", user=user)
# Update complaint status by staff
@app.route("/update_complaint/<int:complaint_id>", methods=["POST"])
def update_complaint(complaint_id):

    if "user_id" not in session or session.get("user_role") != "staff":
        return redirect(url_for("login"))

    new_status = request.form.get("status")

    allowed_status = ["Pending", "In Progress", "Resolved"]

    if new_status not in allowed_status:
        flash("Invalid complaint status.")
        return redirect(url_for("dashboard"))

    connection = get_connection()
    cursor = connection.cursor()

    # Get previous status
    cursor.execute("""
        SELECT status FROM complaints
        WHERE id = ? AND assigned_staff = ?
    """, (complaint_id, session["user_id"]))

    complaint = cursor.fetchone()

    if complaint is None:
        connection.close()
        flash("Complaint not found.")
        return redirect(url_for("dashboard"))

    old_status = complaint[0]

    # Update status
    cursor.execute("""
        UPDATE complaints
        SET status = ?
        WHERE id = ? AND assigned_staff = ?
    """, (new_status, complaint_id, session["user_id"]))

    # Save status history
    if old_status != new_status:
        cursor.execute("""
            INSERT INTO complaint_history
            (complaint_id, old_status, new_status, note)
            VALUES (?, ?, ?, ?)
        """, (
            complaint_id,
            old_status,
            new_status,
            "Status updated by staff"
        ))

    connection.commit()
    connection.close()

    flash("Complaint status updated successfully!")

    return redirect(url_for("dashboard"))




  

# Submit new complaint
@app.route("/submit_complaint", methods=["GET", "POST"])
def submit_complaint():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        category = request.form["category"]
        location = request.form["location"]
        description = request.form["description"].strip()
        priority = request.form["priority"]

        connection = get_connection()
        cursor = connection.cursor()

        try:
            # Find category ID
            cursor.execute(
                "SELECT id FROM categories WHERE category_name = ?",
                (category,)
            )

            category_data = cursor.fetchone()

            if category_data is None:
                flash("Invalid complaint category.")
                return redirect("/submit_complaint")

            category_id = category_data[0]

            # Save complaint
            cursor.execute("""
                INSERT INTO complaints
                (user_id, category_id, location, description, priority)
                VALUES (?, ?, ?, ?, ?)
            """, (
                session["user_id"],
                category_id,
                location,
                description,
                priority
            ))

            connection.commit()

            flash("Complaint submitted successfully!")

            return redirect("/dashboard")

        except Exception as error:
            connection.rollback()
            flash("Unable to submit complaint. Please try again.")
            print("Complaint Error:", error)

        finally:
            connection.close()

    return render_template("submit_complaint.html")
# View student's complaints
@app.route("/my_complaints")
def my_complaints():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT complaints.id,
               categories.category_name,
               complaints.location,
               complaints.description,
               complaints.priority,
               complaints.status,
               complaints.created_at
        FROM complaints
        JOIN categories
        ON complaints.category_id = categories.id
        WHERE complaints.user_id = ?
        ORDER BY complaints.id DESC
    """, (session["user_id"],))

    complaints = cursor.fetchall()
    connection.close()

    return render_template(
        "my_complaints.html",
        complaints=complaints
    )
@app.route("/track_complaint")
def track_complaint():

    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    # Get all complaints submitted by current student
    cursor.execute("""
        SELECT complaints.id,
               categories.category_name,
               complaints.location,
               complaints.description,
               complaints.priority,
               complaints.status,
               complaints.created_at
        FROM complaints
        JOIN categories
        ON complaints.category_id = categories.id
        WHERE complaints.user_id = ?
        ORDER BY complaints.created_at DESC
    """, (session["user_id"],))

    complaints = cursor.fetchall()

    # Get status history of each complaint
    history_by_complaint = {}

    for complaint in complaints:

        complaint_id = complaint[0]

        cursor.execute("""
            SELECT old_status, new_status, note, updated_at
            FROM complaint_history
            WHERE complaint_id = ?
            ORDER BY updated_at ASC, id ASC
        """, (complaint_id,))

        history_by_complaint[complaint_id] = cursor.fetchall()

    connection.close()

    return render_template(
        "track_complaint.html",
        complaints=complaints,
        history_by_complaint=history_by_complaint
    )

        

    # Assign complaint to staff
@app.route("/assign_staff/<int:complaint_id>", methods=["POST"])
def assign_staff(complaint_id):

    if "user_id" not in session or session.get("user_role") != "admin":
        return redirect(url_for("login"))

    staff_id = request.form.get("staff_id")

    connection = get_connection()
    cursor = connection.cursor()

    # Check whether selected user is staff
    cursor.execute(
        "SELECT id FROM users WHERE id = ? AND role = 'staff'",
        (staff_id,)
    )

    staff = cursor.fetchone()

    if staff:
        cursor.execute("""
            UPDATE complaints
            SET assigned_staff = ?
            WHERE id = ?
        """, (staff_id, complaint_id))

        connection.commit()
        flash("Complaint assigned successfully!")

    else:
        flash("Please select a valid staff member.")

    connection.close()

    return redirect(url_for("dashboard"))

# Logout
@app.route("/logout")
def logout():

    session.clear()

    flash("You have logged out successfully.")

    return redirect(url_for("login"))

# Search complaint using Hash Map

@app.route("/search_complaint", methods=["GET", "POST"])
def search_complaint():

    if "user_id" not in session or session.get("user_role") != "admin":
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            complaints.id,
            users.name,
            categories.category_name,
            complaints.location,
            complaints.description,
            complaints.priority,
            complaints.status,
            complaints.created_at
        FROM complaints
        JOIN users ON complaints.user_id = users.id
        JOIN categories ON complaints.category_id = categories.id
    """)

    all_complaints = cursor.fetchall()
    connection.close()

    complaint_map = ComplaintHashMap()

    for complaint in all_complaints:
        complaint_map.add_complaint(complaint)

    result = None

    if request.method == "POST":
        complaint_id = request.form.get("complaint_id")

        if complaint_id.isdigit():
            result = complaint_map.search_complaint(int(complaint_id))

        if result is None:
            flash("Complaint not found.")

    return render_template(
        "search_complaint.html",
        complaint=result
    )


# Run application
if __name__ == "__main__":

    initialize_database()
    create_admin()

    app.run(debug=True)