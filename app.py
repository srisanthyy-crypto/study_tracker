# ============================================================
# app.py - Main Flask Application
# AI-Based Study Progress Tracker & Student Assistant
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime, date, timedelta
from functools import wraps

# ── App Setup ──────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "study_tracker_secret_key_2024"   # Change in production
DATABASE = "study_tracker.db"


# ── DB Helper ──────────────────────────────────────────────
def get_db():
    """Open a database connection and return it."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row          # Access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all tables if they don't exist and add sample data."""
    conn = get_db()
    c = conn.cursor()

    # Users table
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    UNIQUE NOT NULL,
            email       TEXT    UNIQUE NOT NULL,
            password    TEXT    NOT NULL,
            created_at  TEXT    DEFAULT (datetime('now'))
        )
    """)

    # Subjects table
    c.execute("""
        CREATE TABLE IF NOT EXISTS subjects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            name        TEXT    NOT NULL,
            color       TEXT    DEFAULT '#6366f1',
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Tasks table
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            subject_id  INTEGER,
            title       TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            deadline    TEXT,
            completed   INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)    REFERENCES users(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    """)

    # Notes table
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            title       TEXT    NOT NULL,
            content     TEXT    DEFAULT '',
            subject_id  INTEGER,
            created_at  TEXT    DEFAULT (datetime('now')),
            FOREIGN KEY (user_id)    REFERENCES users(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    """)

    # Study logs (for streak tracking)
    c.execute("""
        CREATE TABLE IF NOT EXISTS study_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            log_date    TEXT    NOT NULL,
            minutes     INTEGER DEFAULT 0,
            UNIQUE(user_id, log_date),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# ── Login Decorator ────────────────────────────────────────
def login_required(f):
    """Redirect to login if user is not in session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# ── Auth Routes ────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        email    = request.form["email"].strip()
        password = request.form["password"]

        if not username or not email or not password:
            error = "All fields are required."
        elif len(password) < 6:
            error = "Password must be at least 6 characters."
        else:
            conn = get_db()
            try:
                conn.execute(
                    "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                    (username, email, generate_password_hash(password))
                )
                conn.commit()
                # Add sample data for new user
                user = conn.execute(
                    "SELECT id FROM users WHERE username = ?", (username,)
                ).fetchone()
                _add_sample_data(conn, user["id"])
                conn.commit()
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                error = "Username or email already exists."
            finally:
                conn.close()

    return render_template("signup.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"]  = user["id"]
            session["username"] = user["username"]
            # Log today as a study day
            _log_study_day(user["id"])
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ── Dashboard ──────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    uid  = session["user_id"]
    conn = get_db()

    # Summary counts
    total_tasks     = conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (uid,)).fetchone()[0]
    completed_tasks = conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND completed=1", (uid,)).fetchone()[0]
    total_subjects  = conn.execute("SELECT COUNT(*) FROM subjects WHERE user_id=?", (uid,)).fetchone()[0]
    total_notes     = conn.execute("SELECT COUNT(*) FROM notes WHERE user_id=?", (uid,)).fetchone()[0]

    progress = int((completed_tasks / total_tasks * 100) if total_tasks > 0 else 0)

    # Per-subject progress for chart
    subjects = conn.execute(
        "SELECT id, name, color FROM subjects WHERE user_id=?", (uid,)
    ).fetchall()

    subject_data = []
    for s in subjects:
        tot  = conn.execute("SELECT COUNT(*) FROM tasks WHERE subject_id=?", (s["id"],)).fetchone()[0]
        done = conn.execute("SELECT COUNT(*) FROM tasks WHERE subject_id=? AND completed=1", (s["id"],)).fetchone()[0]
        subject_data.append({
            "name":     s["name"],
            "color":    s["color"],
            "total":    tot,
            "done":     done,
            "progress": int((done / tot * 100) if tot > 0 else 0)
        })

    # Upcoming deadlines (next 7 days)
    today   = date.today().isoformat()
    week    = (date.today() + timedelta(days=7)).isoformat()
    upcoming = conn.execute("""
        SELECT t.title, t.deadline, s.name as subject_name, s.color
        FROM tasks t
        LEFT JOIN subjects s ON t.subject_id = s.id
        WHERE t.user_id=? AND t.completed=0
          AND t.deadline BETWEEN ? AND ?
        ORDER BY t.deadline
        LIMIT 5
    """, (uid, today, week)).fetchall()

    # Streak
    streak = _calculate_streak(uid, conn)

    # Study log (last 7 days) for activity chart
    logs = conn.execute("""
        SELECT log_date, minutes FROM study_logs
        WHERE user_id=? ORDER BY log_date DESC LIMIT 7
    """, (uid,)).fetchall()
    log_dates   = [l["log_date"]  for l in reversed(logs)]
    log_minutes = [l["minutes"]   for l in reversed(logs)]

    conn.close()
    return render_template("dashboard.html",
        total_tasks=total_tasks, completed_tasks=completed_tasks,
        total_subjects=total_subjects, total_notes=total_notes,
        progress=progress, subject_data=subject_data,
        upcoming=upcoming, streak=streak,
        log_dates=log_dates, log_minutes=log_minutes
    )


# ── Subjects ───────────────────────────────────────────────
@app.route("/subjects")
@login_required
def subjects():
    uid  = session["user_id"]
    conn = get_db()
    subs = conn.execute(
        "SELECT * FROM subjects WHERE user_id=? ORDER BY created_at DESC", (uid,)
    ).fetchall()

    # Attach task counts
    result = []
    for s in subs:
        tot  = conn.execute("SELECT COUNT(*) FROM tasks WHERE subject_id=?", (s["id"],)).fetchone()[0]
        done = conn.execute("SELECT COUNT(*) FROM tasks WHERE subject_id=? AND completed=1", (s["id"],)).fetchone()[0]
        result.append({**dict(s), "total": tot, "done": done,
                        "progress": int((done/tot*100) if tot > 0 else 0)})
    conn.close()
    return render_template("subjects.html", subjects=result)


@app.route("/subjects/add", methods=["POST"])
@login_required
def add_subject():
    uid   = session["user_id"]
    name  = request.form["name"].strip()
    color = request.form.get("color", "#6366f1")
    if name:
        conn = get_db()
        conn.execute("INSERT INTO subjects (user_id, name, color) VALUES (?, ?, ?)",
                     (uid, name, color))
        conn.commit()
        conn.close()
    return redirect(url_for("subjects"))


@app.route("/subjects/delete/<int:sid>", methods=["POST"])
@login_required
def delete_subject(sid):
    uid  = session["user_id"]
    conn = get_db()
    conn.execute("DELETE FROM tasks    WHERE subject_id=? AND user_id=?", (sid, uid))
    conn.execute("DELETE FROM notes    WHERE subject_id=? AND user_id=?", (sid, uid))
    conn.execute("DELETE FROM subjects WHERE id=?         AND user_id=?", (sid, uid))
    conn.commit()
    conn.close()
    return redirect(url_for("subjects"))


# ── Tasks ──────────────────────────────────────────────────
@app.route("/tasks")
@login_required
def tasks():
    uid  = session["user_id"]
    filter_status = request.args.get("filter", "all")
    conn = get_db()

    query = """
        SELECT t.*, s.name as subject_name, s.color as subject_color
        FROM tasks t
        LEFT JOIN subjects s ON t.subject_id = s.id
        WHERE t.user_id = ?
    """
    params = [uid]
    if filter_status == "pending":
        query += " AND t.completed = 0"
    elif filter_status == "done":
        query += " AND t.completed = 1"

    query += " ORDER BY t.deadline ASC, t.created_at DESC"
    all_tasks = conn.execute(query, params).fetchall()
    subs      = conn.execute("SELECT id, name FROM subjects WHERE user_id=?", (uid,)).fetchall()
    conn.close()
    return render_template("tasks.html", tasks=all_tasks, subjects=subs,
                           filter_status=filter_status,
                           today=date.today().isoformat())


@app.route("/tasks/add", methods=["POST"])
@login_required
def add_task():
    uid         = session["user_id"]
    title       = request.form["title"].strip()
    description = request.form.get("description", "").strip()
    deadline    = request.form.get("deadline", "")
    subject_id  = request.form.get("subject_id") or None
    if title:
        conn = get_db()
        conn.execute("""
            INSERT INTO tasks (user_id, subject_id, title, description, deadline)
            VALUES (?, ?, ?, ?, ?)
        """, (uid, subject_id, title, description, deadline))
        conn.commit()
        conn.close()
    return redirect(url_for("tasks"))


@app.route("/tasks/toggle/<int:tid>", methods=["POST"])
@login_required
def toggle_task(tid):
    uid  = session["user_id"]
    conn = get_db()
    task = conn.execute("SELECT completed FROM tasks WHERE id=? AND user_id=?",
                        (tid, uid)).fetchone()
    if task:
        new_status = 0 if task["completed"] else 1
        conn.execute("UPDATE tasks SET completed=? WHERE id=? AND user_id=?",
                     (new_status, tid, uid))
        conn.commit()
    conn.close()
    return redirect(url_for("tasks"))


@app.route("/tasks/delete/<int:tid>", methods=["POST"])
@login_required
def delete_task(tid):
    uid  = session["user_id"]
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id=? AND user_id=?", (tid, uid))
    conn.commit()
    conn.close()
    return redirect(url_for("tasks"))


@app.route("/tasks/edit/<int:tid>", methods=["POST"])
@login_required
def edit_task(tid):
    uid         = session["user_id"]
    title       = request.form["title"].strip()
    description = request.form.get("description", "").strip()
    deadline    = request.form.get("deadline", "")
    subject_id  = request.form.get("subject_id") or None
    conn = get_db()
    conn.execute("""
        UPDATE tasks SET title=?, description=?, deadline=?, subject_id=?
        WHERE id=? AND user_id=?
    """, (title, description, deadline, subject_id, tid, uid))
    conn.commit()
    conn.close()
    return redirect(url_for("tasks"))


# ── Notes ──────────────────────────────────────────────────
@app.route("/notes")
@login_required
def notes():
    uid  = session["user_id"]
    conn = get_db()
    all_notes = conn.execute("""
        SELECT n.*, s.name as subject_name
        FROM notes n
        LEFT JOIN subjects s ON n.subject_id = s.id
        WHERE n.user_id=?
        ORDER BY n.created_at DESC
    """, (uid,)).fetchall()
    subs = conn.execute("SELECT id, name FROM subjects WHERE user_id=?", (uid,)).fetchall()
    conn.close()
    return render_template("notes.html", notes=all_notes, subjects=subs)


@app.route("/notes/add", methods=["POST"])
@login_required
def add_note():
    uid        = session["user_id"]
    title      = request.form["title"].strip()
    content    = request.form.get("content", "").strip()
    subject_id = request.form.get("subject_id") or None
    if title:
        conn = get_db()
        conn.execute("INSERT INTO notes (user_id, title, content, subject_id) VALUES (?,?,?,?)",
                     (uid, title, content, subject_id))
        conn.commit()
        conn.close()
    return redirect(url_for("notes"))


@app.route("/notes/delete/<int:nid>", methods=["POST"])
@login_required
def delete_note(nid):
    uid  = session["user_id"]
    conn = get_db()
    conn.execute("DELETE FROM notes WHERE id=? AND user_id=?", (nid, uid))
    conn.commit()
    conn.close()
    return redirect(url_for("notes"))


@app.route("/notes/edit/<int:nid>", methods=["POST"])
@login_required
def edit_note(nid):
    uid        = session["user_id"]
    title      = request.form["title"].strip()
    content    = request.form.get("content", "").strip()
    subject_id = request.form.get("subject_id") or None
    conn = get_db()
    conn.execute("UPDATE notes SET title=?, content=?, subject_id=? WHERE id=? AND user_id=?",
                 (title, content, subject_id, nid, uid))
    conn.commit()
    conn.close()
    return redirect(url_for("notes"))


# ── AI Chatbot (API) ───────────────────────────────────────
@app.route("/chatbot")
@login_required
def chatbot():
    return render_template("chatbot.html")


@app.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    """Rule-based AI chatbot endpoint. Returns JSON response."""
    data    = request.get_json()
    message = data.get("message", "").lower().strip()
    uid     = session["user_id"]
    conn    = get_db()

    reply = _chatbot_response(message, uid, conn)
    conn.close()
    return jsonify({"reply": reply})


# ── Study Log API ──────────────────────────────────────────
@app.route("/api/log_study", methods=["POST"])
@login_required
def log_study():
    """Log study minutes for today."""
    data    = request.get_json()
    minutes = int(data.get("minutes", 30))
    uid     = session["user_id"]
    today   = date.today().isoformat()
    conn    = get_db()
    conn.execute("""
        INSERT INTO study_logs (user_id, log_date, minutes)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, log_date) DO UPDATE SET minutes = minutes + ?
    """, (uid, today, minutes, minutes))
    conn.commit()
    streak = _calculate_streak(uid, conn)
    conn.close()
    return jsonify({"success": True, "streak": streak})


# ── Helper Functions ───────────────────────────────────────
def _log_study_day(user_id):
    """Mark today as a study day (login = studying)."""
    today = date.today().isoformat()
    conn  = get_db()
    conn.execute("""
        INSERT OR IGNORE INTO study_logs (user_id, log_date, minutes)
        VALUES (?, ?, 1)
    """, (user_id, today))
    conn.commit()
    conn.close()


def _calculate_streak(user_id, conn):
    """Calculate the current consecutive study day streak."""
    logs = conn.execute("""
        SELECT DISTINCT log_date FROM study_logs
        WHERE user_id=? ORDER BY log_date DESC
    """, (user_id,)).fetchall()

    if not logs:
        return 0

    streak    = 0
    check_day = date.today()

    for row in logs:
        log_day = date.fromisoformat(row["log_date"])
        if log_day == check_day:
            streak    += 1
            check_day -= timedelta(days=1)
        else:
            break

    return streak


def _chatbot_response(message, user_id, conn):
    """Rule-based chatbot — returns appropriate response string."""

    # ── Greetings
    if any(w in message for w in ["hello", "hi", "hey", "hola", "namaste"]):
        name = session.get("username", "Student")
        return f"Hello {name}! 👋 I'm your Study Assistant. Ask me about your tasks, progress, notes, or study tips!"

    # ── Progress query
    if any(w in message for w in ["progress", "how am i doing", "my stats", "performance"]):
        total = conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id=?", (user_id,)).fetchone()[0]
        done  = conn.execute("SELECT COUNT(*) FROM tasks WHERE user_id=? AND completed=1", (user_id,)).fetchone()[0]
        pct   = int((done/total*100) if total > 0 else 0)
        return f"📊 You've completed **{done}/{total}** tasks — that's **{pct}%** overall progress! {'Great work! 🔥' if pct >= 70 else 'Keep pushing! 💪'}"

    # ── Pending tasks
    if any(w in message for w in ["pending", "remaining", "incomplete", "what tasks", "todo"]):
        pending = conn.execute("""
            SELECT title, deadline FROM tasks
            WHERE user_id=? AND completed=0
            ORDER BY deadline LIMIT 5
        """, (user_id,)).fetchall()
        if not pending:
            return "🎉 You have no pending tasks! Great work!"
        lines = "\n".join([f"• {t['title']}" + (f" (due {t['deadline']})" if t['deadline'] else "") for t in pending])
        return f"📋 Your pending tasks:\n{lines}"

    # ── Subjects
    if any(w in message for w in ["subject", "course", "my subjects"]):
        subs = conn.execute("SELECT name FROM subjects WHERE user_id=?", (user_id,)).fetchall()
        if not subs:
            return "You haven't added any subjects yet. Go to the Subjects page to add some!"
        names = ", ".join([s["name"] for s in subs])
        return f"📚 Your subjects: {names}"

    # ── Study tips
    if any(w in message for w in ["tip", "advice", "how to study", "study tips", "improve"]):
        tips = [
            "🎯 Use the **Pomodoro Technique** — 25 min focus, 5 min break.",
            "📖 Review your notes **within 24 hours** of class to boost retention.",
            "🧠 Teach concepts to someone else — it's the best way to learn.",
            "😴 Never skip sleep before exams — memory consolidates during sleep!",
            "🗓️ Break big topics into small daily tasks — avoid cramming.",
            "📝 Use active recall — test yourself instead of just re-reading.",
        ]
        import random
        return random.choice(tips)

    # ── Streak query
    if any(w in message for w in ["streak", "days", "consistent"]):
        streak = _calculate_streak(user_id, conn)
        if streak >= 7:
            return f"🔥 Amazing! You're on a **{streak}-day streak!** Keep it up!"
        elif streak > 0:
            return f"⚡ You're on a **{streak}-day streak!** Stay consistent!"
        else:
            return "You don't have an active streak yet. Start studying today to build one! 🚀"

    # ── Motivation
    if any(w in message for w in ["motivat", "inspire", "sad", "stressed", "tired", "help"]):
        quotes = [
            "💡 *'Success is the sum of small efforts repeated day in and day out.'* — R. Collier",
            "🚀 *'The expert in anything was once a beginner.'* Keep going!",
            "🌟 *'Don't watch the clock; do what it does. Keep going.'* — Sam Levenson",
            "🏆 You've got this! Every line of code and every page read brings you closer to your goal.",
        ]
        import random
        return random.choice(quotes)

    # ── Notes query
    if any(w in message for w in ["note", "notes"]):
        count = conn.execute("SELECT COUNT(*) FROM notes WHERE user_id=?", (user_id,)).fetchone()[0]
        return f"📝 You have **{count} notes** saved. Head to the Notes section to view or add more!"

    # ── Deadline reminder
    if any(w in message for w in ["deadline", "due", "upcoming", "soon"]):
        today = date.today().isoformat()
        week  = (date.today() + timedelta(days=7)).isoformat()
        tasks = conn.execute("""
            SELECT title, deadline FROM tasks
            WHERE user_id=? AND completed=0 AND deadline BETWEEN ? AND ?
            ORDER BY deadline LIMIT 5
        """, (user_id, today, week)).fetchall()
        if not tasks:
            return "✅ No tasks due in the next 7 days. You're all clear!"
        lines = "\n".join([f"• {t['title']} — due {t['deadline']}" for t in tasks])
        return f"⏰ Upcoming deadlines:\n{lines}"

    # ── Goodbye
    if any(w in message for w in ["bye", "goodbye", "exit", "quit"]):
        return "Goodbye! 📚 Study hard and take breaks. See you soon! 👋"

    # ── Default fallback
    return ("🤖 I can help you with:\n"
            "• Your **progress** and stats\n"
            "• **Pending tasks** and deadlines\n"
            "• Your **subjects** and **notes**\n"
            "• **Study tips** and motivation\n"
            "• Your **streak** info\n\n"
            "Try asking: *'What are my pending tasks?'* or *'Give me a study tip!'*")


def _add_sample_data(conn, user_id):
    """Insert demo subjects, tasks, and notes for a new user."""
    subjects = [
        ("Data Structures",  "#6366f1"),
        ("Operating Systems","#ec4899"),
        ("DBMS",             "#f59e0b"),
        ("Web Development",  "#10b981"),
    ]
    sub_ids = []
    for name, color in subjects:
        cur = conn.execute(
            "INSERT INTO subjects (user_id, name, color) VALUES (?, ?, ?)",
            (user_id, name, color)
        )
        sub_ids.append(cur.lastrowid)

    today = date.today()
    tasks = [
        (sub_ids[0], "Study Binary Trees",   "Read Chapter 5",  (today + timedelta(2)).isoformat(),  0),
        (sub_ids[0], "Practice Sorting",     "Bubble, Merge",   (today + timedelta(5)).isoformat(),  1),
        (sub_ids[1], "Process Scheduling",   "FCFS, SJF, RR",   (today + timedelta(3)).isoformat(),  0),
        (sub_ids[2], "ER Diagrams",           "Design a schema", (today + timedelta(6)).isoformat(),  1),
        (sub_ids[3], "Build Flask App",       "This project!",   (today + timedelta(1)).isoformat(),  0),
        (sub_ids[3], "Learn Chart.js",        "Dashboard charts",(today + timedelta(4)).isoformat(),  1),
    ]
    for s_id, title, desc, deadline, done in tasks:
        conn.execute("""
            INSERT INTO tasks (user_id, subject_id, title, description, deadline, completed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, s_id, title, desc, deadline, done))

    notes = [
        (sub_ids[0], "DSA Quick Reference",
         "Time Complexities:\n- Binary Search: O(log n)\n- BFS/DFS: O(V+E)\n- Merge Sort: O(n log n)"),
        (sub_ids[2], "SQL Joins Cheatsheet",
         "INNER JOIN — matching rows\nLEFT JOIN — all left + matching right\nFULL OUTER JOIN — all rows from both"),
    ]
    for s_id, title, content in notes:
        conn.execute(
            "INSERT INTO notes (user_id, subject_id, title, content) VALUES (?, ?, ?, ?)",
            (user_id, s_id, title, content)
        )

    # Sample study logs (last 5 days)
    for i in range(5):
        day = (today - timedelta(days=i)).isoformat()
        conn.execute("""
            INSERT OR IGNORE INTO study_logs (user_id, log_date, minutes)
            VALUES (?, ?, ?)
        """, (user_id, day, 45 + i*10))


# ── Main ───────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("=" * 50)
    print("  Study Tracker is running!")
    print("  Open http://127.0.0.1:5000 in your browser")
    print("=" * 50)
    app.run(debug=True, host="0.0.0.0", port=5000)
