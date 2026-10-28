from urllib.parse import quote_plus
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import os
import re
import sqlite3
import bcrypt

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "careerpilot_secret_2026")

DATABASE = "careerpilot.db"


# =========================================================
# DATABASE
# =========================================================

def get_db():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


def create_database():

    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL

        )
    """)
    connection.execute("""
        CREATE TABLE IF NOT EXISTS user_profile (
            user_id INTEGER PRIMARY KEY,
            education TEXT,
            branch TEXT,
            year_of_study TEXT,
            career_interest TEXT,
            programming_skills TEXT,
            about TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

    connection.execute("""
    CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        skill TEXT NOT NULL,
        completed INTEGER DEFAULT 0,
        UNIQUE(user_id, skill),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
""")

    connection.commit()
    connection.close()


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        if not name or not email or not password:

            return render_template(
                "register.html",
                error="Please fill all fields."
            )

        if len(password) < 6:

            return render_template(
                "register.html",
                error="Password must contain at least 6 characters."
            )

        hashed_password = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

        connection = get_db()

        try:

            connection.execute(
                """
                INSERT INTO users
                (name, email, password)
                VALUES (?, ?, ?)
                """,
                (
                    name,
                    email,
                    hashed_password
                )
            )

            connection.commit()
            connection.close()

            return redirect(
                url_for("login")
            )

        except sqlite3.IntegrityError:

            connection.close()

            return render_template(
                "register.html",
                error="Email already registered."
            )


    return render_template("register.html")


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email", ""
        ).strip().lower()

        password = request.form.get(
            "password", ""
        )

        if not email or not password:

            return render_template(
                "login.html",
                error="Please enter email and password."
            )

        connection = get_db()

        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE email = ?
            """,
            (email,)
        ).fetchone()

        connection.close()

        if user is None:

            return render_template(
                "login.html",
                error="Email not registered."
            )

        try:

            password_correct = bcrypt.checkpw(
                password.encode("utf-8"),
                user["password"].encode("utf-8")
            )

        except Exception:

            return render_template(
                "login.html",
                error="Password verification error."
            )

        if password_correct:

            session["user_id"] = user["id"]

            session["user_name"] = user["name"]

            session["user_email"] = user["email"]

            return redirect(
                url_for("dashboard")
            )

        return render_template(
            "login.html",
            error="Incorrect password."
        )


    return render_template("login.html")


# =========================================================
# DASHBOARD
# =========================================================
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    career = session.get(
        "recommended_career",
        "Not Assessed"
    )

    skill_map = {
        "Data Analyst": [
            "Python", "SQL", "Excel",
            "Power BI", "Statistics"
        ],

        "Software Developer": [
            "Programming", "Data Structures",
            "Git", "Problem Solving"
        ],

        "Data Scientist": [
            "Python", "SQL", "Statistics",
            "Pandas", "Machine Learning"
        ],

        "AI / ML Engineer": [
            "Python", "Mathematics",
            "Machine Learning", "Deep Learning",
            "TensorFlow"
        ],

        "Web Developer": [
            "HTML", "CSS", "JavaScript",
            "React", "Git"
        ]
    }

    skills = skill_map.get(career, [])

    connection = get_db()

    completed_count = connection.execute("""
        SELECT COUNT(*)
        FROM user_progress
        WHERE user_id = ?
        AND completed = 1
    """, (
        session["user_id"],
    )).fetchone()[0]

    connection.close()

    total_skills = len(skills)

    if total_skills > 0:
        progress = int(
            (completed_count / total_skills) * 100
        )
    else:
        progress = 0

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        email=session["user_email"],
        career=career,
        progress=progress,
        completed_count=completed_count,
        total_skills=total_skills
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    connection = get_db()
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        education = request.form.get("education", "").strip()
        branch = request.form.get("branch", "").strip()
        year_of_study = request.form.get("year_of_study", "").strip()
        career_interest = request.form.get("career_interest", "").strip()
        programming_skills = ", ".join(request.form.getlist("programming_skills"))
        about = request.form.get("about", "").strip()

        if not full_name or not education or not branch or not year_of_study or not career_interest:
            connection.close()
            return render_template("profile.html", name=session.get("user_name"), email=session.get("user_email"), error="Please fill all required fields.")

        connection.execute("UPDATE users SET name=? WHERE id=?", (full_name, session["user_id"]))
        connection.execute("""
            INSERT INTO user_profile(user_id, education, branch, year_of_study, career_interest, programming_skills, about)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                education=excluded.education, branch=excluded.branch, year_of_study=excluded.year_of_study,
                career_interest=excluded.career_interest, programming_skills=excluded.programming_skills, about=excluded.about
        """, (session["user_id"], education, branch, year_of_study, career_interest, programming_skills, about))
        connection.commit()
        connection.close()
        session["user_name"] = full_name
        return redirect(url_for("profile", saved=1))

    row = connection.execute("SELECT * FROM user_profile WHERE user_id=?", (session["user_id"],)).fetchone()
    connection.close()
    profile_data = dict(row) if row else {}
    return render_template("profile.html", name=session.get("user_name"), email=session.get("user_email"), profile=profile_data, saved=request.args.get("saved"))

# =========================================================
# CAREER ASSESSMENT
# =========================================================

@app.route("/assessment", methods=["GET", "POST"])
def assessment():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        session["education"] = request.form.get(
            "education", ""
        )

        session["skills"] = request.form.get(
            "skills", ""
        )

        session["interests"] = request.form.get(
            "interests", ""
        )

        session["strengths"] = request.form.get(
            "strengths", ""
        )

        session["career_goal"] = request.form.get(
            "career_goal", ""
        )

        return redirect(
            url_for("recommendation")
        )

    return render_template(
        "assessment.html"
    )


# =========================================================
# CAREER RECOMMENDATION
# =========================================================
CAREER_SKILLS = {
    "Software Developer": ["Programming", "Data Structures", "OOP", "DBMS", "Git", "Problem Solving"],
    "Web Developer": ["HTML", "CSS", "JavaScript", "React", "Git", "Web Development"],
    "Data Analyst": ["Excel", "SQL", "Statistics", "Power BI", "Python", "Data Visualization"],
    "Data Scientist": ["Python", "Statistics", "Machine Learning", "SQL", "Pandas", "Data Visualization"],
    "Data Engineer": ["Python", "SQL", "ETL", "Databases", "Cloud", "Apache Spark"],
    "AI/ML Engineer": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Mathematics"],
    "Cybersecurity Analyst": ["Networking", "Linux", "Cybersecurity", "Cryptography", "Ethical Hacking", "Security Tools"],
    "Cloud Engineer": ["Linux", "Networking", "AWS", "Azure", "Docker", "Cloud Computing"],
    "DevOps Engineer": ["Linux", "Git", "Docker", "Kubernetes", "CI/CD", "Cloud"],
    "Business Analyst": ["Excel", "SQL", "Business Analysis", "Communication", "Power BI", "Problem Solving"],
    "UI/UX Designer": ["Figma", "UI Design", "UX Research", "Prototyping", "Graphic Design", "Communication"],
    "Database Administrator": ["SQL", "DBMS", "Database Administration", "Linux", "Backup and Recovery", "Database Security"]
}

CAREER_ALIASES = {"AI / ML Engineer": "AI/ML Engineer"}

def canonical_career(value):
    return CAREER_ALIASES.get(value, value)

@app.route("/recommendation")
def recommendation():
    if "user_id" not in session:
        return redirect(url_for("login"))

    skills = session.get("skills", "").strip().lower()
    interests = session.get("interests", "").strip().lower()
    career_goal = canonical_career(session.get("career_goal", "").strip())

    # The user chooses the target career. CareerPilot analyzes ONLY that career.
    if not career_goal or career_goal not in CAREER_SKILLS:
        return redirect(url_for("assessment"))

    required = CAREER_SKILLS[career_goal]
    combined = f"{skills} {interests}"
    matched = [skill for skill in required if skill.lower() in combined]
    missing = [skill for skill in required if skill not in matched]
    percentage = round((len(matched) / len(required)) * 100) if required else 0

    session["recommended_career"] = career_goal
    session["match_percentage"] = percentage

    result = [{
        "career": career_goal,
        "score": len(matched),
        "percentage": percentage
    }]

    return render_template(
        "recommendation.html",
        results=result,
        recommended_career=career_goal,
        match_percentage=percentage,
        skills=skills,
        interests=interests,
        career_goal=career_goal,
        matched_skills=matched,
        missing_skills=missing
    )

# =========================================================
# SKILL GAP
# =========================================================


@app.route("/skill-gap")
def skill_gap():
    if "user_id" not in session:
        return redirect(url_for("login"))
    career = canonical_career(session.get("recommended_career", "Data Analyst"))
    user_skills = session.get("skills", "").lower()
    required = CAREER_SKILLS.get(career, CAREER_SKILLS["Data Analyst"])
    current = [skill for skill in required if skill.lower() in user_skills]
    missing = [skill for skill in required if skill not in current]
    percentage = round((len(current) / len(required)) * 100) if required else 0
    return render_template("skill_gap.html", career=career, current=current, missing=missing, percentage=percentage)

# =========================================================
# LEARNING ROADMAP
# =========================================================

ROADMAP_DESCRIPTIONS = {
    "Programming": ("Strengthen programming fundamentals and problem solving.", "3–4 Weeks"),
    "Data Structures": ("Learn arrays, linked lists, stacks, queues, trees and graphs.", "4–6 Weeks"),
    "OOP": ("Learn classes, objects, inheritance and polymorphism.", "2 Weeks"),
    "DBMS": ("Learn relational databases, SQL and normalization.", "2–3 Weeks"),
    "Git": ("Learn Git, GitHub and collaborative version control.", "1 Week"),
    "Problem Solving": ("Practice algorithms, logical reasoning and coding problems.", "4 Weeks"),
    "HTML": ("Learn semantic HTML and webpage structure.", "1 Week"),
    "CSS": ("Learn layouts, responsive design and styling.", "2 Weeks"),
    "JavaScript": ("Learn JavaScript fundamentals and browser interaction.", "3–4 Weeks"),
    "React": ("Build component-based interactive web applications.", "3–4 Weeks"),
    "Web Development": ("Build and deploy complete web applications.", "3–4 Weeks"),
    "Excel": ("Learn formulas, Pivot Tables and data cleaning.", "2 Weeks"),
    "SQL": ("Learn queries, joins, filtering and database operations.", "2–3 Weeks"),
    "Statistics": ("Learn descriptive statistics, probability and interpretation.", "2–3 Weeks"),
    "Power BI": ("Create dashboards and interactive reports.", "2–3 Weeks"),
    "Python": ("Learn Python programming and practical scripting.", "3–4 Weeks"),
    "Data Visualization": ("Create clear charts, dashboards and data stories.", "2 Weeks"),
    "Machine Learning": ("Learn supervised, unsupervised learning and evaluation.", "4–6 Weeks"),
    "Pandas": ("Learn data manipulation and analysis with Pandas.", "2 Weeks"),
    "ETL": ("Learn extract, transform and load data pipelines.", "2–3 Weeks"),
    "Databases": ("Learn database design, indexing and performance basics.", "2–3 Weeks"),
    "Cloud": ("Learn cloud concepts, services and deployment basics.", "2–3 Weeks"),
    "Apache Spark": ("Learn distributed data processing with Spark.", "3–4 Weeks"),
    "Deep Learning": ("Learn neural networks and deep learning workflows.", "4–6 Weeks"),
    "TensorFlow": ("Build and train machine learning models.", "3 Weeks"),
    "PyTorch": ("Build deep-learning models with PyTorch.", "3 Weeks"),
    "Mathematics": ("Learn linear algebra, probability and statistics for AI.", "3–4 Weeks"),
    "Networking": ("Learn networks, protocols and troubleshooting basics.", "3 Weeks"),
    "Linux": ("Learn Linux commands, permissions and administration.", "2 Weeks"),
    "Cybersecurity": ("Learn security concepts, threats and defenses.", "3–4 Weeks"),
    "Cryptography": ("Learn encryption, hashing and security fundamentals.", "2 Weeks"),
    "Ethical Hacking": ("Learn ethical security testing concepts.", "3–4 Weeks"),
    "Security Tools": ("Practice common security monitoring and testing tools.", "2–3 Weeks"),
    "AWS": ("Learn core AWS cloud services and deployment.", "3 Weeks"),
    "Azure": ("Learn Azure services and cloud deployment.", "3 Weeks"),
    "Docker": ("Learn containers, images and Docker workflows.", "2 Weeks"),
    "Cloud Computing": ("Learn cloud architecture and service models.", "3 Weeks"),
    "Kubernetes": ("Learn container orchestration and Kubernetes basics.", "3–4 Weeks"),
    "CI/CD": ("Learn automated build, test and deployment pipelines.", "2–3 Weeks"),
    "Business Analysis": ("Learn requirements, processes and business analysis techniques.", "2–3 Weeks"),
    "Communication": ("Improve professional communication and presentation skills.", "2 Weeks"),
    "Figma": ("Learn interface design and prototyping in Figma.", "2 Weeks"),
    "UI Design": ("Learn visual hierarchy, layouts and interface principles.", "2 Weeks"),
    "UX Research": ("Learn user research, personas and usability testing.", "2–3 Weeks"),
    "Prototyping": ("Create low- and high-fidelity interactive prototypes.", "2 Weeks"),
    "Graphic Design": ("Learn typography, composition and visual design basics.", "2–3 Weeks"),
    "Database Administration": ("Learn database setup, maintenance and monitoring.", "3 Weeks"),
    "Backup and Recovery": ("Learn backup strategies, recovery and disaster planning.", "2 Weeks"),
    "Database Security": ("Learn database access control and security practices.", "2 Weeks")
}

@app.route("/roadmap")
def roadmap():
    if "user_id" not in session:
        return redirect(url_for("login"))
    career = canonical_career(session.get("recommended_career", "Data Analyst"))
    user_skills = session.get("skills", "").lower()
    roadmap_items = []
    for skill in CAREER_SKILLS.get(career, CAREER_SKILLS["Data Analyst"]):
        desc, duration = ROADMAP_DESCRIPTIONS.get(skill, (f"Build practical skills in {skill}.", "2–3 Weeks"))
        roadmap_items.append((skill, desc, duration))
    completed = [skill for skill, _, _ in roadmap_items if skill.lower() in user_skills]
    return render_template("roadmap.html", career=career, roadmap=roadmap_items, completed=completed)

# =========================================================
# AI CAREER EXPLANATION
# =========================================================
@app.route("/career-insights")
def career_insights():
    if "user_id" not in session:
        return redirect(url_for("login"))
    career = canonical_career(session.get("recommended_career", "Data Analyst"))
    icons = {"Data Analyst":"📊","Software Developer":"💻","Web Developer":"🌐","Data Scientist":"🔬","Data Engineer":"🛠️","AI/ML Engineer":"🤖","Cybersecurity Analyst":"🔐","Cloud Engineer":"☁️","DevOps Engineer":"⚙️","Business Analyst":"📈","UI/UX Designer":"🎨","Database Administrator":"🗄️"}
    reason = f"Your assessment inputs are being matched against the skills and career profile for {career}."
    return render_template("career_insights.html", career=career, icon=icons.get(career,"🚀"), title=career,
                           reason=reason, required_skills=CAREER_SKILLS.get(career, CAREER_SKILLS["Data Analyst"]),
                           user_skills=session.get("skills",""), interests=session.get("interests",""), career_goal=session.get("career_goal",""))

@app.route("/learning-resources")
def learning_resources():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("learning_resources.html")

# =========================================================
# COURSES & RESOURCES
# =========================================================

@app.route("/projects")
def projects():

    if "user_id" not in session:
        return redirect(url_for("login"))

    career = session.get("recommended_career", "Data Analyst")

    project_data = {
        "Data Analyst": [
            ("Sales Dashboard", "Excel + Power BI", ["Collect a CSV dataset", "Clean missing values", "Create Pivot Tables", "Build charts in Power BI", "Add KPIs and filters", "Publish screenshots to GitHub"]),
            ("Student Performance Analyzer", "Python + Pandas", ["Create student dataset", "Load it with Pandas", "Clean the data", "Calculate average and pass percentage", "Create charts", "Write a README and upload the project"])
        ],
        "Data Scientist": [
            ("Student Score Predictor", "Python + Pandas + Scikit-learn", ["Collect a small student dataset", "Clean and explore the data", "Select useful features", "Train a regression model", "Evaluate the model", "Create a simple Flask interface and document it"]),
            ("Customer Churn Predictor", "Python + Machine Learning", ["Prepare customer data", "Perform EDA", "Encode categorical values", "Train a classification model", "Check accuracy and confusion matrix", "Build a prediction page"])
        ],
        "Software Developer": [
            ("Task Manager", "Python/Java + SQLite", ["Design the task fields", "Create the database", "Build add/edit/delete functions", "Add login", "Create a clean UI", "Test and upload to GitHub"]),
            ("Expense Tracker", "Python + SQLite", ["Create expense categories", "Store transactions", "Add monthly totals", "Create search and filters", "Add charts", "Write documentation and test cases"])
        ],
        "Web Developer": [
            ("Portfolio Website", "HTML + CSS + JavaScript", ["Plan sections", "Create responsive HTML", "Style with CSS", "Add JavaScript interactions", "Test on mobile", "Deploy and add the live link to GitHub"]),
            ("College Event Website", "HTML + CSS + JavaScript", ["Design home and event pages", "Add registration form", "Create responsive layout", "Add validation", "Test links and forms", "Deploy the website"])
        ],
        "AI / ML Engineer": [
            ("Image Classifier", "Python + TensorFlow", ["Choose a small image dataset", "Preprocess images", "Build a neural network", "Train and validate", "Test predictions", "Create a simple demo interface"]),
            ("AI Chatbot", "Python + NLP", ["Define intents", "Create training examples", "Preprocess text", "Build the response logic", "Add a web chat UI", "Test common user questions"])
        ]
    }

    default_projects = [
        (f"{career} Portfolio Project", "Python + Web", ["Choose a real problem", "Collect or create data", "Build the core feature", "Add a simple user interface", "Test the application", "Document it and upload to GitHub"])
    ]

    return render_template("projects.html", career=career, projects=project_data.get(career, default_projects))

@app.route("/courses")
def courses():

    if "user_id" not in session:
        return redirect(url_for("login"))

    career = session.get(
        "recommended_career",
        "Data Analyst"
    )

    resources = {

        "Python": {
            "description": "Learn Python programming from basics to practical projects.",
            "type": "Programming",
            "url": "https://www.python.org/about/gettingstarted/"
        },

        "SQL": {
            "description": "Learn SQL queries, databases, joins and data manipulation.",
            "type": "Database",
            "url": "https://www.w3schools.com/sql/"
        },

        "Excel": {
            "description": "Learn Excel formulas, Pivot Tables, charts and data analysis.",
            "type": "Data Analysis",
            "url": "https://support.microsoft.com/excel"
        },

        "Power BI": {
            "description": "Learn how to create interactive dashboards and reports.",
            "type": "Visualization",
            "url": "https://learn.microsoft.com/power-bi/"
        },

        "Statistics": {
            "description": "Build your foundation in statistics and probability.",
            "type": "Mathematics",
            "url": "https://www.khanacademy.org/math/statistics-probability"
        },

        "Machine Learning": {
            "description": "Learn machine learning concepts and practical algorithms.",
            "type": "AI",
            "url": "https://developers.google.com/machine-learning/crash-course"
        },

        "Deep Learning": {
            "description": "Learn neural networks and deep learning fundamentals.",
            "type": "AI",
            "url": "https://www.deeplearning.ai/"
        },

        "HTML": {
            "description": "Learn how to structure modern web pages.",
            "type": "Web Development",
            "url": "https://developer.mozilla.org/en-US/docs/Web/HTML"
        },

        "CSS": {
            "description": "Learn styling, layouts and responsive web design.",
            "type": "Web Development",
            "url": "https://developer.mozilla.org/en-US/docs/Web/CSS"
        },

        "JavaScript": {
            "description": "Learn JavaScript for interactive web applications.",
            "type": "Web Development",
            "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript"
        },

        "React": {
            "description": "Learn React for building modern user interfaces.",
            "type": "Web Development",
            "url": "https://react.dev/learn"
        },

        "Git": {
            "description": "Learn version control and GitHub workflows.",
            "type": "Development Tools",
            "url": "https://git-scm.com/doc"
        },

        "Data Structures": {
            "description": "Learn important data structures and algorithms.",
            "type": "Computer Science",
            "url": "https://www.freecodecamp.org/learn/javascript-algorithms-and-data-structures-v8/"
        },

        "Pandas": {
            "description": "Learn Python Pandas for data manipulation and analysis.",
            "type": "Data Science",
            "url": "https://pandas.pydata.org/docs/getting_started/"
        },

        "TensorFlow": {
            "description": "Learn how to build machine learning models using TensorFlow.",
            "type": "AI / ML",
            "url": "https://www.tensorflow.org/learn"
        },

        "Mathematics": {
            "description": "Build mathematics foundations useful for AI and machine learning.",
            "type": "Mathematics",
            "url": "https://www.khanacademy.org/math"
        },

        "Problem Solving": {
            "description": "Practice programming and logical problem solving.",
            "type": "Programming",
            "url": "https://www.hackerrank.com/domains/algorithms"
        },

        "Programming": {
            "description": "Strengthen your programming fundamentals.",
            "type": "Programming",
            "url": "https://www.freecodecamp.org/learn/"
        }

    }

    career_skills = {

        "Data Analyst": [
            "Python",
            "SQL",
            "Excel",
            "Power BI",
            "Statistics"
        ],

        "Software Developer": [
            "Programming",
            "Data Structures",
            "Git",
            "Problem Solving"
        ],

        "Data Scientist": [
            "Python",
            "SQL",
            "Statistics",
            "Pandas",
            "Machine Learning"
        ],

        "AI / ML Engineer": [
            "Python",
            "Mathematics",
            "Machine Learning",
            "Deep Learning",
            "TensorFlow"
        ],

        "Web Developer": [
            "HTML",
            "CSS",
            "JavaScript",
            "React",
            "Git"
        ]
    }

    skills = career_skills.get(
        career,
        career_skills["Data Analyst"]
    )

    recommended_resources = []

    for skill in skills:

        if skill in resources:

            item = resources[skill].copy()

            item["skill"] = skill
            item["youtube_url"] = "https://www.youtube.com/results?search_query=" + quote_plus(skill + " tutorial for beginners")

            recommended_resources.append(item)

    return render_template(
        "courses.html",
        career=career,
        resources=recommended_resources
    )
    # =========================================================
# PROGRESS
# =========================================================
@app.route("/progress")
def progress():

    if "user_id" not in session:
        return redirect(url_for("login"))

    career = session.get(
        "recommended_career",
        "Data Analyst"
    )

    skill_map = {

        "Data Analyst": [
            "Python",
            "SQL",
            "Excel",
            "Power BI",
            "Statistics"
        ],

        "Software Developer": [
            "Programming",
            "Data Structures",
            "Git",
            "Problem Solving"
        ],

        "Data Scientist": [
            "Python",
            "SQL",
            "Statistics",
            "Pandas",
            "Machine Learning"
        ],

        "AI / ML Engineer": [
            "Python",
            "Mathematics",
            "Machine Learning",
            "Deep Learning",
            "TensorFlow"
        ],

        "Web Developer": [
            "HTML",
            "CSS",
            "JavaScript",
            "React",
            "Git"
        ]
    }

    skills = skill_map.get(
        career,
        skill_map["Data Analyst"]
    )

    connection = get_db()

    rows = connection.execute("""
        SELECT skill
        FROM user_progress
        WHERE user_id = ?
        AND completed = 1
    """, (
        session["user_id"],
    )).fetchall()

    connection.close()

    completed_names = {
        row["skill"]
        for row in rows
    }

    completed = []

    pending = []

    for skill in skills:

        if skill in completed_names:
            completed.append(skill)

        else:
            pending.append(skill)

    total = len(skills)

    percentage = 0

    if total > 0:

        percentage = int(
            (len(completed) / total) * 100
        )

    return render_template(
        "progress.html",

        career=career,

        completed=completed,

        pending=pending,

        percentage=percentage,

        total=total
    )
# =========================================================
# UPDATE PROGRESS
# =========================================================

@app.route("/complete-skill", methods=["POST"])
def complete_skill():

    if "user_id" not in session:
        return redirect(url_for("login"))

    skill = request.form.get("skill")

    if not skill:
        return redirect(url_for("progress"))

    connection = get_db()

    connection.execute("""
        INSERT INTO user_progress
        (user_id, skill, completed)
        VALUES (?, ?, 1)

        ON CONFLICT(user_id, skill)
        DO UPDATE SET completed = 1
    """, (
        session["user_id"],
        skill
    ))

    connection.commit()
    connection.close()

    return redirect(url_for("progress"))
# =========================================================
# JOBS & INTERNSHIPS
# =========================================================

@app.route("/jobs")
def jobs():

    if "user_id" not in session:
        return redirect(url_for("login"))

    career = session.get(
        "recommended_career",
        "Data Analyst"
    )

    jobs_data = {

        "Data Analyst": [
            {
                "title": "Junior Data Analyst",
                "company": "Entry-Level Opportunity",
                "type": "Full Time",
                "level": "Fresher",
                "skills": "Python, SQL, Excel, Power BI"
            },
            {
                "title": "Data Analyst Intern",
                "company": "Internship Opportunity",
                "type": "Internship",
                "level": "Student",
                "skills": "Excel, SQL, Statistics"
            }
        ],

        "Software Developer": [
            {
                "title": "Software Developer",
                "company": "Entry-Level Opportunity",
                "type": "Full Time",
                "level": "Fresher",
                "skills": "Programming, Git, Data Structures"
            },
            {
                "title": "Software Development Intern",
                "company": "Internship Opportunity",
                "type": "Internship",
                "level": "Student",
                "skills": "Python / Java, Git"
            }
        ],

        "Data Scientist": [
            {
                "title": "Junior Data Scientist",
                "company": "Entry-Level Opportunity",
                "type": "Full Time",
                "level": "Fresher",
                "skills": "Python, SQL, Statistics, ML"
            },
            {
                "title": "Data Science Intern",
                "company": "Internship Opportunity",
                "type": "Internship",
                "level": "Student",
                "skills": "Python, Pandas, Statistics"
            }
        ],

        "AI / ML Engineer": [
            {
                "title": "AI / ML Engineer",
                "company": "Entry-Level Opportunity",
                "type": "Full Time",
                "level": "Fresher",
                "skills": "Python, ML, Deep Learning"
            },
            {
                "title": "AI / ML Intern",
                "company": "Internship Opportunity",
                "type": "Internship",
                "level": "Student",
                "skills": "Python, Machine Learning"
            }
        ],

        "Web Developer": [
            {
                "title": "Frontend Developer",
                "company": "Entry-Level Opportunity",
                "type": "Full Time",
                "level": "Fresher",
                "skills": "HTML, CSS, JavaScript, React"
            },
            {
                "title": "Web Development Intern",
                "company": "Internship Opportunity",
                "type": "Internship",
                "level": "Student",
                "skills": "HTML, CSS, JavaScript"
            }
        ]
    }

    available_jobs = jobs_data.get(
        career,
        jobs_data["Data Analyst"]
    )

    return render_template(
        "jobs.html",
        career=career,
        jobs=available_jobs
    )
    # =========================================================
# RESUME BUILDER
# =========================================================

@app.route("/resume")
def resume():

    if "user_id" not in session:
        return redirect(url_for("login"))

    name = session.get("user_name", "")
    email = session.get("user_email", "")

    career = session.get(
        "recommended_career",
        "Data Analyst"
    )

    skills = session.get(
        "skills",
        ""
    )

    interests = session.get(
        "interests",
        ""
    )

    career_goal = session.get(
        "career_goal",
        ""
    )

    return render_template(
        "resume.html",
        name=name,
        email=email,
        career=career,
        skills=skills,
        interests=interests,
        career_goal=career_goal
    )
    # =========================================================
# MOCK INTERVIEW
# =========================================================

@app.route("/interview", methods=["GET", "POST"])
def interview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    career = session.get(
        "recommended_career",
        "Data Analyst"
    )

    questions = {

        "Data Analyst": [
            "Tell me about yourself.",
            "Why do you want to become a Data Analyst?",
            "What is the difference between SQL and Excel?",
            "What is a primary key in SQL?",
            "Explain a data analysis project you have worked on."
        ],

        "Software Developer": [
            "Tell me about yourself.",
            "Why do you want to become a Software Developer?",
            "What is object-oriented programming?",
            "What is the difference between an array and a linked list?",
            "Explain one programming project you have completed."
        ],

        "Data Scientist": [
            "Tell me about yourself.",
            "Why do you want to become a Data Scientist?",
            "What is the difference between supervised and unsupervised learning?",
            "What is overfitting?",
            "Explain a machine learning project you have worked on."
        ],

        "AI / ML Engineer": [
            "Tell me about yourself.",
            "Why are you interested in AI and Machine Learning?",
            "What is machine learning?",
            "What is a neural network?",
            "Explain an AI or ML project you have completed."
        ],

        "Web Developer": [
            "Tell me about yourself.",
            "Why do you want to become a Web Developer?",
            "What is HTML?",
            "What is the difference between CSS and JavaScript?",
            "Explain a web project you have created."
        ]
    }

    interview_questions = questions.get(
        career,
        questions["Data Analyst"]
    )

    return render_template(
        "interview.html",
        career=career,
        questions=interview_questions
    )
    # =========================================================
# INTERVIEW EVALUATION
# =========================================================

@app.route("/interview/result", methods=["POST"])
def interview_result():

    if "user_id" not in session:
        return redirect(url_for("login"))

    career = session.get(
        "recommended_career",
        "Data Analyst"
    )

    answers = request.form.getlist("answers")

    questions = {

        "Data Analyst": [
            "Tell me about yourself.",
            "Why do you want to become a Data Analyst?",
            "What is the difference between SQL and Excel?",
            "What is a primary key in SQL?",
            "Explain a data analysis project you have worked on."
        ],

        "Software Developer": [
            "Tell me about yourself.",
            "Why do you want to become a Software Developer?",
            "What is object-oriented programming?",
            "What is the difference between an array and a linked list?",
            "Explain one programming project you have completed."
        ],

        "Data Scientist": [
            "Tell me about yourself.",
            "Why do you want to become a Data Scientist?",
            "What is the difference between supervised and unsupervised learning?",
            "What is overfitting?",
            "Explain a machine learning project you have worked on."
        ],

        "AI / ML Engineer": [
            "Tell me about yourself.",
            "Why are you interested in AI and Machine Learning?",
            "What is machine learning?",
            "What is a neural network?",
            "Explain an AI or ML project you have completed."
        ],

        "Web Developer": [
            "Tell me about yourself.",
            "Why do you want to become a Web Developer?",
            "What is HTML?",
            "What is the difference between CSS and JavaScript?",
            "Explain a web project you have created."
        ]
    }

    interview_questions = questions.get(
        career,
        questions["Data Analyst"]
    )

    total_questions = len(interview_questions)

    answered = 0

    total_words = 0

    for answer in answers:

        if answer.strip():

            answered += 1

            total_words += len(
                answer.split()
            )

    if total_questions > 0:

        completion_score = int(
            (answered / total_questions) * 100
        )

    else:

        completion_score = 0

    if answered > 0:

        average_words = (
            total_words / answered
        )

    else:

        average_words = 0

    if average_words >= 30:

        quality_score = 100

    elif average_words >= 20:

        quality_score = 85

    elif average_words >= 10:

        quality_score = 70

    elif average_words > 0:

        quality_score = 50

    else:

        quality_score = 0

    final_score = int(
        (completion_score + quality_score) / 2
    )

    if final_score >= 80:

        level = "Excellent"

        feedback = (
            "Your answers show good preparation. "
            "Continue practicing with real interview "
            "examples and project explanations."
        )

    elif final_score >= 60:

        level = "Good"

        feedback = (
            "You have a good foundation. "
            "Try giving more specific examples "
            "and structured answers."
        )

    elif final_score >= 40:

        level = "Needs Improvement"

        feedback = (
            "Practice answering every question "
            "and explain your ideas with examples."
        )

    else:

        level = "Beginner"

        feedback = (
            "Start by learning the fundamentals "
            "of your target career and practice "
            "short interview answers."
        )

    return render_template(
        "interview_result.html",

        career=career,

        score=final_score,

        level=level,

        answered=answered,

        total_questions=total_questions,

        feedback=feedback
        )
    
    # =========================================================
# AI CAREER CHATBOT
# =========================================================

@app.route("/chatbot", methods=["GET", "POST"])
def chatbot():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        # Accept JSON requests safely so a missing/invalid payload does not
        # crash the chatbot endpoint.
        data = request.get_json(silent=True) or {}
        message = str(data.get("message", "")).lower().strip()
        if not message:
            return jsonify({"reply": "Please type a question about skills, courses, your roadmap, interviews or jobs."}), 400

        career = session.get(
            "recommended_career",
            "your target career"
        )

        if "skill" in message:

            reply = (
                f"For {career}, focus on technical skills, "
                "communication, problem-solving and practical "
                "projects. Start with the skills listed in your "
                "Career Roadmap and practice them through projects."
            )

        elif "interview" in message:

            reply = (
                f"To prepare for a {career} interview, "
                "practice common technical questions, explain "
                "your projects clearly, revise important concepts "
                "and complete mock interviews regularly."
            )

        elif "course" in message:

            reply = (
                f"For {career}, choose courses that teach "
                "practical, job-relevant skills. Prefer courses "
                "with projects, exercises and certificates."
            )

        elif "job" in message:

            reply = (
                f"To get a {career} job, build a strong resume, "
                "complete 2–3 practical projects, improve your "
                "required skills and apply for internships and "
                "entry-level positions."
            )

        elif "roadmap" in message:

            reply = (
                f"Your roadmap for {career} should follow this "
                "order: fundamentals → core skills → projects → "
                "resume → interview preparation → job applications."
            )

        elif "hello" in message or "hi" in message:

            reply = (
                f"Hello! 👋 I'm your CareerPilot AI Assistant. "
                f"I can help you with your {career} career journey."
            )

        else:

            reply = (
                f"I can help you with your {career} career. "
                "Try asking about skills, courses, roadmap, "
                "interviews or jobs."
            )

        return {
            "reply": reply
        }

    return render_template(
        "chatbot.html",
        name=session.get("user_name", "User")
    )
    # ---------------- ENGLISH COACH ----------------

@app.route("/english-coach")
def english_coach():

    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("english_coach.html")


@app.route("/check-sentence", methods=["POST"])
def check_sentence():

    if "user_id" not in session:
        return jsonify({
            "error": "Please login first."
        }), 401

    data = request.get_json(silent=True) or {}

    sentence = data.get("sentence", "").strip()

    if not sentence:
        return jsonify({
            "error": "Please enter a sentence."
        }), 400

    corrections = {

        "he go to college every day": {
            "correct": "He goes to college every day.",
            "explanation": 'With "he", "she", or "it", use "goes" in the simple present tense.',
            "score": 6,
            "examples": [
                "She goes to college every day.",
                "He goes to work every morning.",
                "She goes to the library every evening."
            ]
        },

        "she don't like coding": {
            "correct": "She doesn't like coding.",
            "explanation": 'With "she", use "doesn\'t" instead of "don\'t".',
            "score": 5,
            "examples": [
                "She doesn't like coffee.",
                "He doesn't like programming.",
                "She doesn't watch television."
            ]
        },

        "i am interested to learn data analysis": {
            "correct": "I am interested in learning data analysis.",
            "explanation": 'Use "interested in" followed by a noun or verb ending in "-ing".',
            "score": 6,
            "examples": [
                "I am interested in learning Python.",
                "She is interested in studying AI.",
                "I am interested in developing software."
            ]
        },

        "i have completed my degree yesterday": {
            "correct": "I completed my degree yesterday.",
            "explanation": '"Yesterday" refers to a completed past time, so simple past is appropriate.',
            "score": 6,
            "examples": [
                "I completed the project yesterday.",
                "She visited Hyderabad yesterday.",
                "We finished the work yesterday."
            ]
        },

        "he have a car": {
            "correct": "He has a car.",
            "explanation": 'With "he", "she", or "it", use "has" instead of "have".',
            "score": 5,
            "examples": [
                "He has a new laptop.",
                "She has a beautiful house.",
                "He has an interesting idea."
            ]
        },

        "i did not went there": {
            "correct": "I did not go there.",
            "explanation": 'After "did not", use the base form of the verb: "go", not "went".',
            "score": 5,
            "examples": [
                "I did not go to college.",
                "She did not attend the meeting.",
                "He did not finish the work."
            ]
        }
    }

    key = sentence.lower().strip().rstrip(".!?")

    result = corrections.get(key)

    if result:

        return jsonify({
            "original": sentence,
            "correct": result["correct"],
            "explanation": result["explanation"],
            "score": result["score"],
            "examples": result["examples"]
        })

    return jsonify({
        "original": sentence,
        "correct": "No specific correction was found.",
        "explanation": "This basic version does not yet contain a rule for this sentence.",
        "score": 8,
        "examples": [
            "I practice English every day.",
            "I am improving my communication skills.",
            "I want to speak English confidently."
        ]
    })
    
    # ---------------- AI RESUME BUILDER ----------------

@app.route("/resume-builder", methods=["GET", "POST"])
def resume_builder():

    if "user_id" not in session:
        return redirect(url_for("login"))

    form_data = {}

    if request.method == "POST":

        form_data = {

            "full_name":
                request.form.get("full_name", "").strip(),

            "email":
                request.form.get("email", "").strip(),

            "phone":
                request.form.get("phone", "").strip(),

            "location":
                request.form.get("location", "").strip(),

            "linkedin":
                request.form.get("linkedin", "").strip(),

            "career":
                request.form.get("career", "").strip(),

            "career_level":
                request.form.get("career_level", "").strip(),

            "objective":
                request.form.get("objective", "").strip(),

            "degree":
                request.form.get("degree", "").strip(),

            "specialization":
                request.form.get("specialization", "").strip(),

            "college":
                request.form.get("college", "").strip(),

            "graduation_year":
                request.form.get("graduation_year", "").strip(),

            "percentage":
                request.form.get("percentage", "").strip(),

            "skills":
                request.form.get("skills", "").strip(),

            "projects":
                request.form.get("projects", "").strip(),

            "experience":
                request.form.get("experience", "").strip(),

            "certifications":
                request.form.get("certifications", "").strip(),

            "languages":
                request.form.get("languages", "").strip()
        }


        # Required fields

        if not form_data["full_name"]:

            return render_template(
                "resume_builder.html",
                error="Please enter your full name.",
                form_data=form_data
            )


        if not form_data["email"]:

            return render_template(
                "resume_builder.html",
                error="Please enter your email.",
                form_data=form_data
            )


        if not form_data["career"]:

            return render_template(
                "resume_builder.html",
                error="Please select your target career.",
                form_data=form_data
            )


        if not form_data["skills"]:

            return render_template(
                "resume_builder.html",
                error="Please enter at least your skills.",
                form_data=form_data
            )


        # Store resume information in session

        session["resume_data"] = form_data


        return redirect(
            url_for("resume_preview")
        )


    # GET request

    return render_template(
        "resume_builder.html",
        form_data={}
    )
    # ---------------- RESUME PREVIEW ----------------

@app.route("/resume-preview")
def resume_preview():

    if "user_id" not in session:
        return redirect(url_for("login"))

    resume_data = session.get(
        "resume_data"
    )

    if not resume_data:
        return redirect(
            url_for("resume_builder")
        )

    return render_template(
        "resume_preview.html",
        resume=resume_data
    )
@app.route("/resume-analyzer", methods=["GET", "POST"])
def resume_analyzer():
    if "user_id" not in session:
        return redirect(url_for("login"))
    analysis = None
    if request.method == "POST":
        text = request.form.get("resume_text", "").strip()
        if not text:
            analysis = {"error": "Please paste your resume text."}
        else:
            lowered = text.lower()
            found = [skill for skills in CAREER_SKILLS.values() for skill in skills if skill.lower() in lowered]
            unique_found = list(dict.fromkeys(found))
            missing = [skill for skill in CAREER_SKILLS.get(canonical_career(session.get("recommended_career", "Data Analyst")), CAREER_SKILLS["Data Analyst"]) if skill.lower() not in lowered]
            score = min(100, 40 + len(unique_found) * 4)
            analysis = {"score": score, "skills_found": unique_found, "missing_skills": missing}
    return render_template("resume_analyzer.html", analysis=analysis)

# =========================================================
# JOB PREPARATION
# =========================================================
@app.route("/preparation")
def preparation():

    if "user_id" not in session:
        return redirect(url_for("login"))

    career = session.get(
        "recommended_career",
        "Data Analyst"
    )

    preparation_data = {
        "Data Analyst": [
            "Tell me about yourself.",
            "What is SQL and why is it used?",
            "What is the difference between WHERE and HAVING?",
            "What is a Pivot Table in Excel?",
            "What is data cleaning?",
            "What is Power BI?",
            "Explain mean, median and mode."
        ],

        "Software Developer": [
            "Tell me about yourself.",
            "What is Object-Oriented Programming?",
            "What is inheritance?",
            "What is polymorphism?",
            "Explain arrays and linked lists.",
            "What is Git?",
            "Explain your programming project."
        ],

        "Data Scientist": [
            "Tell me about yourself.",
            "What is Machine Learning?",
            "What is supervised learning?",
            "What is overfitting?",
            "What is Pandas?",
            "Explain classification and regression.",
            "Explain one ML project."
        ],

        "AI / ML Engineer": [
            "What is Artificial Intelligence?",
            "What is Machine Learning?",
            "What is Deep Learning?",
            "What is a neural network?",
            "What is TensorFlow?",
            "Explain supervised and unsupervised learning.",
            "Explain an AI project."
        ],

        "Web Developer": [
            "What is HTML?",
            "What is CSS?",
            "What is JavaScript?",
            "What is responsive design?",
            "What is React?",
            "What is Git?",
            "Explain your web project."
        ]
    }

    default_questions = [
        "Tell me about yourself.",
        f"Why do you want to become a {career}?",
        f"What are the most important skills for a {career}?",
        "Describe a project you have worked on.",
        "How do you solve a difficult technical problem?",
        "How do you keep your technical skills updated?",
        "Why should we hire you for this role?"
    ]
    questions = preparation_data.get(career, default_questions)

    return render_template(
        "preparation.html",
        career=career,
        questions=questions
    )
    
# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    create_database()

    app.run(
        debug=True
    )