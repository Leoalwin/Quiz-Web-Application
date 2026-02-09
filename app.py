from flask import Flask, render_template, request,redirect,url_for
import psycopg2
import os


app = Flask(__name__)
DATABASE_URL = os.getenv("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL, sslmode="require")



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        cur = conn.cursor()
        cur.execute("SELECT id, username, password FROM users WHERE username=%s", (username,))
        user = cur.fetchone()

        if user and user[2] == password:
            return redirect(url_for('admin'))
        else:
            return "Invalid Username or Password"


    return render_template("login.html")



@app.route('/addtopic', methods=['GET', 'POST'])
def add_topic():
    if request.method == "POST":
        topic_name = request.form.get("topic_name")

        if topic_name:
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO topics (name) VALUES (%s)",
                (topic_name,)
            )
            conn.commit()
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

        cur.execute("""INSERT INTO questions (topic_id, question, option1, option2, option3, option4, correct_option)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""", (topic_id, question, option1, option2, option3, option4, correct_option))

        conn.commit()
        return redirect(url_for('home'))

    return render_template("add_question.html", topics=topics)

@app.route('/admin')
def admin():
    return render_template("admin.html")

@app.route('/')
def home():
    cur = conn.cursor()
    cur.execute("SELECT * FROM topics")
    topics = cur.fetchall()
    return render_template("home.html",topics=topics)


@app.route('/quiz/<int:topic_id>', methods=['GET'])
def quiz_get(topic_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions WHERE topic_id=%s LIMIT 5", (topic_id,))
    questions = cur.fetchall()
    question = questions[0]
    total = len(questions)
    return render_template("quiz.html",question=question,topic_id=topic_id,index=0,score=0,total=total)

@app.route('/quiz/<int:topic_id>', methods=['POST'])
def quiz_post(topic_id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM questions WHERE topic_id=%s LIMIT 5", (topic_id,))
    questions = cur.fetchall()
    total = len(questions)
    index = int(request.form.get("index"))
    score = int(request.form.get("score"))
    selected = request.form.get("answer")

    correct_option = questions[index][7]

    if selected and int(selected) == correct_option:
        score += 1
    index += 1
    
    if index >= len(questions):
        return render_template("result.html", score=score)
    question = questions[index]

    return render_template("quiz.html",question=question,topic_id=topic_id,index=index,score=score,total = total)

if __name__ == "__main__":
    app.run(debug=True)     

