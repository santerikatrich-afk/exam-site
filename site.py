from flask import Flask, request, redirect, session, render_template_string
import sqlite3

app = Flask(__name__)
app.secret_key = "secret123"

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS grades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        exam TEXT,
        grade TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------- HTML ----------------
login_page = """
<h2>Вход</h2>
<form method="post">
<input name="username" placeholder="Логин"><br>
<input name="password" type="password" placeholder="Пароль"><br>
<button type="submit">Войти</button>
</form>
<a href="/register">Регистрация</a>
<p>{{ error }}</p>
"""

register_page = """
<h2>Регистрация</h2>
<form method="post">
<input name="username" placeholder="Логин"><br>
<input name="password" type="password" placeholder="Пароль"><br>
<button type="submit">Создать</button>
</form>
<a href="/">Назад</a>
"""

dashboard_page = """
<h2>Мои экзамены</h2>

<table border="1" cellpadding="10">
<tr>
    <th>Экзамен</th>
    <th>Оценка</th>
    <th>Удалить</th>
    <th>Изменить</th>
</tr>

{% for g in grades %}
<tr>
<td>{{ g[2] }}</td>
<td>{{ g[3] }}</td>

<td><a href="/delete/{{ g[0] }}">🗑 удалить</a></td>
<td><a href="/edit/{{ g[0] }}">✏️ изменить</a></td>

</tr>
{% endfor %}
</table>

<h3>Добавить экзамен</h3>

<form method="post" action="/add">
<input name="exam" placeholder="Экзамен">
<input name="grade" placeholder="Оценка">
<button type="submit">Добавить</button>
</form>

<br>
<a href="/logout">Выйти</a>
"""

# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
        SELECT * FROM users WHERE username=? AND password=?
        """, (request.form["username"], request.form["password"]))

        user = cur.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")
        else:
            return render_template_string(login_page, error="Ошибка входа")

    return render_template_string(login_page)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute("""
        INSERT INTO users (username, password)
        VALUES (?, ?)
        """, (request.form["username"], request.form["password"]))

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template_string(register_page)

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT * FROM grades WHERE user_id=?
    """, (session["user_id"],))

    grades = cur.fetchall()
    conn.close()

    return render_template_string(dashboard_page, grades=grades)

# ---------------- ADD ----------------
@app.route("/add", methods=["POST"])
def add():
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO grades (user_id, exam, grade)
    VALUES (?, ?, ?)
    """, (session["user_id"], request.form["exam"], request.form["grade"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- DELETE ----------------
@app.route("/delete/<int:id>")
def delete(id):
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    DELETE FROM grades WHERE id=? AND user_id=?
    """, (id, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")

# ---------------- EDIT (ИСПРАВЛЕНО) ----------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    if "user_id" not in session:
        return redirect("/")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if request.method == "POST":
        new_grade = request.form["grade"]

        cur.execute("""
        UPDATE grades SET grade=?
        WHERE id=? AND user_id=?
        """, (new_grade, id, session["user_id"]))

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    cur.execute("""
    SELECT exam, grade FROM grades
    WHERE id=? AND user_id=?
    """, (id, session["user_id"]))

    row = cur.fetchone()
    conn.close()

    if not row:
        return "Не найдено"

    return f"""
    <h3>Изменить оценку: {row[0]}</h3>

    <form method="post">
        <input name="grade" value="{row[1]}">
        <button type="submit">Сохранить</button>
    </form>

    <a href="/dashboard">Назад</a>
    """

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ---------------- RUN -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)