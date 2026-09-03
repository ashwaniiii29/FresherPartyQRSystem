"""
Fresher Party QR Registration System
"""

import os
import sqlite3
import uuid
import shutil
import csv
import io

from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

import qrcode

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_from_directory,
    flash,
    send_file
)


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = "fresher-party-2026-secret-key-change-me"


# =========================================================
# PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_PATH = os.path.join(
    BASE_DIR,
    "participants.db"
)

QR_FOLDER = os.path.join(
    BASE_DIR,
    "qr_codes"
)

os.makedirs(
    QR_FOLDER,
    exist_ok=True
)


# =========================================================
# EVENT SETTINGS
# =========================================================

EVENT_NAME = "Fresher Party 2026"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# DATABASE INITIALIZATION
# =========================================================

def init_db():

    conn = get_db_connection()

    table_exists = conn.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name='participants'
        """
    ).fetchone()

    # -----------------------------------------------------
    # NEW DATABASE
    # -----------------------------------------------------

    if table_exists is None:

        conn.execute(
            """
            CREATE TABLE participants (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                registration_id TEXT UNIQUE NOT NULL,

                name TEXT NOT NULL,

                mobile TEXT UNIQUE NOT NULL,

                course TEXT NOT NULL,

                year TEXT NOT NULL,

                gender TEXT NOT NULL,

                enrollment_number TEXT UNIQUE NOT NULL,

                qr_filename TEXT NOT NULL,

                registration_date TEXT NOT NULL,

                checked_in INTEGER DEFAULT 0,

                checkin_time TEXT

            )
            """
        )

        conn.commit()
        conn.close()

        return

    # -----------------------------------------------------
    # CHECK EXISTING DATABASE COLUMNS
    # -----------------------------------------------------

    columns = [
        row["name"]
        for row in conn.execute(
            "PRAGMA table_info(participants)"
        ).fetchall()
    ]

    # -----------------------------------------------------
    # OLD DATABASE MIGRATION
    # -----------------------------------------------------

    if "enrollment_number" not in columns:

        print(
            "Old database detected."
        )

        print(
            "Starting database migration..."
        )

        backup_folder = os.path.join(
            BASE_DIR,
            "backups"
        )

        os.makedirs(
            backup_folder,
            exist_ok=True
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        backup_path = os.path.join(
            backup_folder,
            f"before_migration_{timestamp}.db"
        )

        conn.commit()

        shutil.copy2(
            DB_PATH,
            backup_path
        )

        print(
            f"Database backup created: {backup_path}"
        )

        # Rename old table

        conn.execute(
            """
            ALTER TABLE participants
            RENAME TO participants_old
            """
        )

        # Create new table

        conn.execute(
            """
            CREATE TABLE participants (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                registration_id TEXT UNIQUE NOT NULL,

                name TEXT NOT NULL,

                mobile TEXT UNIQUE NOT NULL,

                course TEXT NOT NULL,

                year TEXT NOT NULL,

                gender TEXT NOT NULL,

                enrollment_number TEXT UNIQUE NOT NULL,

                qr_filename TEXT NOT NULL,

                registration_date TEXT NOT NULL,

                checked_in INTEGER DEFAULT 0,

                checkin_time TEXT

            )
            """
        )

        # Copy old registrations
        # student_id → enrollment_number
        # email is removed

        conn.execute(
            """
            INSERT INTO participants
            (
                id,
                registration_id,
                name,
                mobile,
                course,
                year,
                gender,
                enrollment_number,
                qr_filename,
                registration_date,
                checked_in,
                checkin_time
            )

            SELECT
                id,
                registration_id,
                name,
                mobile,
                course,
                year,
                gender,
                student_id,
                qr_filename,
                registration_date,
                checked_in,
                checkin_time

            FROM participants_old
            """
        )

        # Remove old table

        conn.execute(
            """
            DROP TABLE participants_old
            """
        )

        conn.commit()

        print(
            "Database migration completed successfully."
        )

    conn.close()


# =========================================================
# DATABASE BACKUP
# =========================================================

def backup_database():

    if not os.path.exists(DB_PATH):
        return

    backup_folder = os.path.join(
        BASE_DIR,
        "backups"
    )

    os.makedirs(
        backup_folder,
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    backup_path = os.path.join(
        backup_folder,
        f"participants_backup_{timestamp}.db"
    )

    shutil.copy2(
        DB_PATH,
        backup_path
    )
    # =========================================================
# FORM VALIDATION
# =========================================================

def validate_registration_form(form):

    errors = []

    name = form.get(
        "name",
        ""
    ).strip()

    mobile = form.get(
        "mobile",
        ""
    ).strip()

    course = form.get(
        "course",
        ""
    ).strip()

    year = form.get(
        "year",
        ""
    ).strip()

    gender = form.get(
        "gender",
        ""
    ).strip()

    enrollment_number = form.get(
        "enrollment_number",
        ""
    ).strip()

    # Name validation

    if not name:

        errors.append(
            "Name is required."
        )

    elif len(name) < 2:

        errors.append(
            "Name must be at least 2 characters long."
        )

    # Mobile validation

    if not mobile:

        errors.append(
            "Mobile number is required."
        )

    elif not (
        mobile.isdigit()
        and len(mobile) == 10
    ):

        errors.append(
            "Mobile number must contain exactly 10 digits."
        )

    # Course validation

    if not course:

        errors.append(
            "Course is required."
        )

    # Year / Semester validation

    if not year:

        errors.append(
            "Year/Semester is required."
        )

    # Gender validation

    if not gender:

        errors.append(
            "Gender is required."
        )

    # Enrollment Number validation

    if not enrollment_number:

        errors.append(
            "Enrollment Number is required."
        )

    return errors


# =========================================================
# DUPLICATE CHECK
# =========================================================

def is_duplicate(
    mobile,
    enrollment_number
):

    conn = get_db_connection()

    row = conn.execute(
        """
        SELECT *
        FROM participants

        WHERE mobile = ?
        OR enrollment_number = ?

        """,
        (
            mobile,
            enrollment_number
        )
    ).fetchone()

    conn.close()

    return row is not None


# =========================================================
# QR CODE GENERATION
# =========================================================

def generate_qr_code(
    registration_id
):

    # QR contains only Registration ID

    qr_data = registration_id

    qr_img = qrcode.make(
        qr_data
    )

    filename = (
        f"{registration_id}.png"
    )

    filepath = os.path.join(
        QR_FOLDER,
        filename
    )

    qr_img.save(
        filepath
    )

    return filename


# =========================================================
# REGISTRATION ID GENERATION
# =========================================================

def generate_registration_id():

    conn = get_db_connection()

    row = conn.execute(
        """
        SELECT MAX(
            CAST(
                SUBSTR(
                    registration_id,
                    5
                ) AS INTEGER
            )
        ) AS last_number

        FROM participants

        WHERE registration_id LIKE 'FP26-%'
        """
    ).fetchone()

    conn.close()

    last_number = (
        row["last_number"]
        or 0
    )

    next_number = (
        last_number + 1
    )

    return (
        f"FP26-{next_number:04d}"
    )


# =========================================================
# STUDENT REGISTRATION
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def index():

    if request.method == "POST":

        # Validate form

        errors = validate_registration_form(
            request.form
        )

        # Get form data

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        course = request.form.get(
            "course",
            ""
        ).strip()

        year = request.form.get(
            "year",
            ""
        ).strip()

        gender = request.form.get(
            "gender",
            ""
        ).strip()

        enrollment_number = request.form.get(
            "enrollment_number",
            ""
        ).strip()

        # Duplicate check

        if not errors and is_duplicate(
            mobile,
            enrollment_number
        ):

            errors.append(
                "A participant with this mobile number "
                "or enrollment number has already registered."
            )

        # Show errors

        if errors:

            return render_template(
                "index.html",
                event_name=EVENT_NAME,
                errors=errors,
                form_data=request.form
            )

        # Generate registration ID

        registration_id = (
            generate_registration_id()
        )

        # Generate QR

        qr_filename = generate_qr_code(
            registration_id
        )

        # Registration date

        registration_date = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        # Save participant

        conn = get_db_connection()

        conn.execute(
            """
            INSERT INTO participants
            (
                registration_id,
                name,
                mobile,
                course,
                year,
                gender,
                enrollment_number,
                qr_filename,
                registration_date
            )

            VALUES
            (
                ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                registration_id,
                name,
                mobile,
                course,
                year,
                gender,
                enrollment_number,
                qr_filename,
                registration_date
            )
        )

        conn.commit()

        conn.close()

        # Backup database

        backup_database()

        # Redirect to success page

        return redirect(
            url_for(
                "success",
                registration_id=registration_id
            )
        )

    # GET request

    return render_template(
        "index.html",
        event_name=EVENT_NAME,
        errors=[],
        form_data={}
    )


# =========================================================
# SUCCESS PAGE
# =========================================================

@app.route(
    "/success/<registration_id>"
)
def success(
    registration_id
):

    conn = get_db_connection()

    participant = conn.execute(
        """
        SELECT *
        FROM participants

        WHERE registration_id = ?

        """,
        (
            registration_id,
        )
    ).fetchone()

    conn.close()

    if participant is None:

        flash(
            "Registration not found."
        )

        return redirect(
            url_for("index")
        )

    return render_template(
        "success.html",
        participant=participant,
        event_name=EVENT_NAME
    )


# =========================================================
# QR IMAGE
# =========================================================

@app.route(
    "/qr_codes/<filename>"
)
def qr_image(
    filename
):

    return send_from_directory(
        QR_FOLDER,
        filename
    )


# =========================================================
# DOWNLOAD DIGITAL PASS
# =========================================================

@app.route(
    "/download_pass/<registration_id>"
)
def download_pass(
    registration_id
):

    conn = get_db_connection()

    participant = conn.execute(
        """
        SELECT *
        FROM participants

        WHERE registration_id = ?

        """,
        (
            registration_id,
        )
    ).fetchone()

    conn.close()

    if participant is None:

        flash(
            "Registration not found."
        )

        return redirect(
            url_for("index")
        )

    # QR path

    qr_path = os.path.join(
        QR_FOLDER,
        participant["qr_filename"]
    )

    qr_img = Image.open(
        qr_path
    ).convert(
        "RGB"
    )

    width = qr_img.width
    height = qr_img.height

    pass_height = (
        height + 180
    )

    # Create pass image

    pass_img = Image.new(
        "RGB",
        (
            width,
            pass_height
        ),
        "white"
    )

    pass_img.paste(
        qr_img,
        (
            0,
            20
        )
    )

    draw = ImageDraw.Draw(
        pass_img
    )

    # Fonts

    try:

        font = ImageFont.truetype(
            "arial.ttf",
            32
        )

        small_font = ImageFont.truetype(
            "arial.ttf",
            24
        )

    except:

        font = ImageFont.load_default()

        small_font = ImageFont.load_default()

    # Name

    name = participant["name"]

    registration_id = (
        participant["registration_id"]
    )

    name_box = draw.textbbox(
        (
            0,
            0
        ),
        name,
        font=font
    )

    name_width = (
        name_box[2]
        - name_box[0]
    )

    draw.text(
        (
            (width - name_width) // 2,
            height + 35
        ),
        name,
        fill="black",
        font=font
    )

    # Registration ID

    reg_text = (
        f"Registration ID: "
        f"{registration_id}"
    )

    reg_box = draw.textbbox(
        (
            0,
            0
        ),
        reg_text,
        font=small_font
    )

    reg_width = (
        reg_box[2]
        - reg_box[0]
    )

    draw.text(
        (
            (width - reg_width) // 2,
            height + 90
        ),
        reg_text,
        fill="black",
        font=small_font
    )

    # Save pass

    filename = (
        f"{registration_id}_pass.png"
    )

    filepath = os.path.join(
        QR_FOLDER,
        filename
    )

    pass_img.save(
        filepath
    )

    return send_from_directory(
        QR_FOLDER,
        filename,
        as_attachment=True
    )
    # =========================================================
# ADMIN LOGIN CHECK
# =========================================================

def admin_logged_in():

    return session.get(
        "is_admin",
        False
    )


# =========================================================
# ADMIN LOGIN
# =========================================================

@app.route(
    "/admin/login",
    methods=["GET", "POST"]
)
def admin_login():

    error = None

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        ).strip()

        if (
            username == ADMIN_USERNAME
            and password == ADMIN_PASSWORD
        ):

            session["is_admin"] = True

            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )

        else:

            error = (
                "Invalid username or password."
            )

    return render_template(
        "admin_login.html",
        error=error,
        event_name=EVENT_NAME
    )


# =========================================================
# ADMIN LOGOUT
# =========================================================

@app.route(
    "/admin/logout"
)
def admin_logout():

    session.pop(
        "is_admin",
        None
    )

    return redirect(
        url_for("admin_login")
    )


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route(
    "/admin"
)
def admin_dashboard():

    if not admin_logged_in():

        return redirect(
            url_for("admin_login")
        )

    search = request.args.get(
        "search",
        ""
    ).strip()

    conn = get_db_connection()

    # -----------------------------------------------------
    # SEARCH PARTICIPANTS
    # -----------------------------------------------------

    if search:

        like = (
            f"%{search}%"
        )

        participants = conn.execute(
            """
            SELECT *
            FROM participants

            WHERE name LIKE ?
               OR registration_id LIKE ?
               OR mobile LIKE ?
               OR enrollment_number LIKE ?

            ORDER BY id DESC
            """,
            (
                like,
                like,
                like,
                like
            )
        ).fetchall()

    else:

        participants = conn.execute(
            """
            SELECT *
            FROM participants

            ORDER BY id DESC
            """
        ).fetchall()

    # -----------------------------------------------------
    # TOTAL REGISTRATIONS
    # -----------------------------------------------------

    total = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM participants
        """
    ).fetchone()["c"]

    # -----------------------------------------------------
    # CHECKED-IN COUNT
    # -----------------------------------------------------

    checked_in_count = conn.execute(
        """
        SELECT COUNT(*) AS c
        FROM participants

        WHERE checked_in = 1
        """
    ).fetchone()["c"]

    conn.close()

    return render_template(
        "admin.html",
        participants=participants,
        total=total,
        checked_in_count=checked_in_count,
        search=search,
        event_name=EVENT_NAME
    )


# =========================================================
# DOWNLOAD ALL STUDENT DETAILS AS CSV
# =========================================================

@app.route(
    "/admin/download-students"
)
def download_students():

    if not admin_logged_in():

        return redirect(
            url_for("admin_login")
        )

    conn = get_db_connection()

    participants = conn.execute(
        """
        SELECT

            registration_id,
            name,
            mobile,
            course,
            year,
            gender,
            enrollment_number,
            registration_date,
            checked_in,
            checkin_time

        FROM participants

        ORDER BY id DESC
        """
    ).fetchall()

    conn.close()

    # -----------------------------------------------------
    # CREATE CSV
    # -----------------------------------------------------

    output = io.StringIO()

    writer = csv.writer(
        output
    )

    writer.writerow(
        [
            "Registration ID",
            "Name",
            "Mobile",
            "Course",
            "Year / Semester",
            "Gender",
            "Enrollment Number",
            "Registration Date",
            "Check-in Status",
            "Check-in Time"
        ]
    )

    # -----------------------------------------------------
    # ADD STUDENT DATA
    # -----------------------------------------------------

    for student in participants:

        writer.writerow(
            [
                student["registration_id"],
                student["name"],
                student["mobile"],
                student["course"],
                student["year"],
                student["gender"],
                student["enrollment_number"],
                student["registration_date"],

                "Checked In"
                if student["checked_in"]
                else "Not Checked In",

                student["checkin_time"]
                or ""
            ]
        )

    output.seek(0)

    csv_data = (
        output.getvalue()
    )

    # -----------------------------------------------------
    # DOWNLOAD CSV FILE
    # -----------------------------------------------------

    return send_file(
        io.BytesIO(
            csv_data.encode(
                "utf-8-sig"
            )
        ),

        mimetype="text/csv",

        as_attachment=True,

        download_name="student_details.csv"
    )


# =========================================================
# ADMIN CHECK-IN / QR SCANNER
# =========================================================

@app.route(
    "/admin/checkin",
    methods=["GET", "POST"]
)
def checkin():

    if not admin_logged_in():

        return redirect(
            url_for("admin_login")
        )

    participant = None

    message = None

    message_type = None

    # -----------------------------------------------------
    # POST REQUEST
    # -----------------------------------------------------

    if request.method == "POST":

        registration_id = request.form.get(
            "registration_id",
            ""
        ).strip().upper()

        conn = get_db_connection()

        participant = conn.execute(
            """
            SELECT *
            FROM participants

            WHERE registration_id = ?

            """,
            (
                registration_id,
            )
        ).fetchone()

        # -------------------------------------------------
        # PARTICIPANT NOT FOUND
        # -------------------------------------------------

        if participant is None:

            message = (
                f"No participant found with "
                f"Registration ID "
                f"'{registration_id}'."
            )

            message_type = "error"

        else:

            action = request.form.get(
                "action"
            )

            # ---------------------------------------------
            # MARK CHECKED IN
            # ---------------------------------------------

            if action == "mark_checked_in":

                # Already checked in

                if participant["checked_in"]:

                    message = (
                        f"{participant['name']} "
                        f"is already checked in."
                    )

                    message_type = "info"

                # First-time check-in

                else:

                    checkin_time = (
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )

                    conn.execute(
                        """
                        UPDATE participants

                        SET checked_in = 1,
                            checkin_time = ?

                        WHERE registration_id = ?

                        """,
                        (
                            checkin_time,
                            registration_id
                        )
                    )

                    conn.commit()

                    # Get updated participant

                    participant = conn.execute(
                        """
                        SELECT *
                        FROM participants

                        WHERE registration_id = ?

                        """,
                        (
                            registration_id,
                        )
                    ).fetchone()

                    message = (
                        f"{participant['name']} "
                        f"has been checked in successfully!"
                    )

                    message_type = "success"

        conn.close()

    # -----------------------------------------------------
    # SHOW CHECK-IN PAGE
    # -----------------------------------------------------

    return render_template(
        "checkin.html",
        participant=participant,
        message=message,
        message_type=message_type,
        event_name=EVENT_NAME
    )


# =========================================================
# INITIALIZE DATABASE
# =========================================================

init_db()


# =========================================================
# RUN LOCAL SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )