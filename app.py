from flask import Flask, render_template, request, redirect, url_for
import psycopg2
import psycopg2.extras
import os

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")

# Create DB connection
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True


# ------------------ CREATE TABLES ------------------

def create_tables():
    cur = conn.cursor()

    # Topics table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS topics (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL
    );
    """)

    # Questions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id SERIAL PRIMARY KEY,
        topic_id INTEGER REFERENCES topics(id),
        question TEXT NOT NULL,
        option1 TEXT NOT NULL,
        option2 TEXT NOT NULL,
        option3 TEXT NOT NULL,
        option4 TEXT NOT NULL,
        correct_option INTEGER NOT NULL
    );
    """)

    # Add column if old table exists without correct_option
    cur.execute("""
    ALTER TABLE questions
    ADD COLUMN IF NOT EXISTS correct_option INTEGER;
    """)

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE,
        password VARCHAR(100)
    );
    """)

    # Default admin
    cur.execute("""
    INSERT INTO users (username, password)
    VALUES (%s, %s)
    ON CONFLICT (username) DO NOTHING;
    """, ("admin", "admin123"))

    cur.close()


create_tables()

# ------------------ ROUTES ------------------

@app.route('/')
def home():
    cur = conn.cursor()
    cur.execute("SELECT * FROM topics")
    topics = cur.fetchall()
    cur.close()
    return render_template("home.html", topics=topics)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and user[2] == password:
            return redirect(url_for('admin'))
        else:
            return "Invalid Username or Password"

    return render_template("login.html")


@app.route('/admin')
def admin():
    return render_template("admin.html")


@app.route('/addtopic', methods=['GET', 'POST'])
def add_topic():
    if request.method == "POST":
        topic_name = request.form.get("topic_name")

        if topic_name:
            cur = conn.cursor()
            cur.execute("INSERT INTO topics (name) VALUES (%s)", (topic_name,))
            cur.close()
            return redirect(url_for('admin'))

    return render_template("add_topic.html")


@app.route('/addquestion', methods=['GET', 'POST'])
def add_question():
    cur = conn.cursor()
    cur.execute("SELECT * FROM topics")
    topics = cur.fetchall()

    if request.method == "POST":
        topic_id = request.form.get("topic_id")
        question = request.form.get("question")
        option1 = request.form.get("option1")
        option2 = request.form.get("option2")
        option3 = request.form.get("option3")
        option4 = request.form.get("option4")
        correct_option = request.form.get("correct_option")

        cur.execute("""
            INSERT INTO questions 
            (topic_id, question, option1, option2, option3, option4, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (topic_id, question, option1, option2, option3, option4, int(correct_option)))

        cur.close()
        return redirect(url_for('home'))

    cur.close()
    return render_template("add_question.html", topics=topics)


@app.route('/quiz/<int:topic_id>', methods=['GET'])
def quiz_get(topic_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions WHERE topic_id=%s LIMIT 5", (topic_id,))
    questions = cur.fetchall()
    cur.close()

    if not questions:
        return "No questions available"

    question = questions[0]
    total = len(questions)

    return render_template(
        "quiz.html",
        question=question,
        topic_id=topic_id,
        index=0,
        score=0,
        total=total
    )


@app.route('/quiz/<int:topic_id>', methods=['POST'])
def quiz_post(topic_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions WHERE topic_id=%s LIMIT 5", (topic_id,))
    questions = cur.fetchall()
    cur.close()

    total = len(questions)
    index = int(request.form.get("index"))
    score = int(request.form.get("score"))
    selected = request.form.get("answer")

    correct_option = questions[index][7]

    if selected and int(selected) == int(correct_option):
        score += 1

    index += 1

    if index >= total:
        return render_template("result.html", score=score, total=total)

    question = questions[index]

    return render_template(
        "quiz.html",
        question=question,
        topic_id=topic_id,
        index=index,
        score=score,
        total=total
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
