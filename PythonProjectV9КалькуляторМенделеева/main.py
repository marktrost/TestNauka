
from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'gmaMob8989bl'  # ⚠️ ВАЖНО: добавь этот ключ!
DB_NAME = "ent.db"

# Остальной код остается без изменений...
# --- Регистрация ---
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        # Валидация имени пользователя
        if not username:
            flash("Имя пользователя не может быть пустым", "error")
            return render_template("register.html")

        if len(username) < 5:
            flash("Имя пользователя должно быть не менее 5 символов", "error")
            return render_template("register.html")

        if len(username) > 20:
            flash("Имя пользователя не должно превышать 20 символов", "error")
            return render_template("register.html")

        if not username.isalnum():
            flash("Имя пользователя должно содержать только буквы и цифры", "error")
            return render_template("register.html")

        # Проверка запрещенных слов в username
        forbidden_words = ['admin', 'administrator', 'moderator', 'support', 'system', 'root', 'test']
        if any(word in username.lower() for word in forbidden_words):
            flash("Это имя пользователя запрещено", "error")
            return render_template("register.html")

        # Валидация пароля
        if not password:
            flash("Пароль не может быть пустым", "error")
            return render_template("register.html")

        if len(password) < 8:
            flash("Пароль должен быть не менее 8 символов", "error")
            return render_template("register.html")

        if len(password) > 50:
            flash("Пароль не должен превышать 50 символов", "error")
            return render_template("register.html")

        # Проверка сложности пароля
        if not any(char.isdigit() for char in password):
            flash("Пароль должен содержать хотя бы одну цифру", "error")
            return render_template("register.html")

        if not any(char.isalpha() for char in password):
            flash("Пароль должен содержать хотя бы одну букву", "error")
            return render_template("register.html")

        if password.isnumeric():
            flash("Пароль не должен состоять только из цифр", "error")
            return render_template("register.html")

        if password.lower() == username.lower():
            flash("Пароль не должен совпадать с именем пользователя", "error")
            return render_template("register.html")

        # Проверка на простые пароли
        weak_passwords = ['password', '12345678', 'qwertyui', 'asdfghjk', 'zxcvbnm', 'abcdefgh']
        if password.lower() in weak_passwords:
            flash("Пароль слишком простой", "error")
            return render_template("register.html")

        # Проверка на повторяющиеся символы
        if len(set(password)) < 4:
            flash("Пароль содержит слишком много повторяющихся символов", "error")
            return render_template("register.html")

        conn = get_db()
        try:
            password_hash = generate_password_hash(password)
            conn.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            conn.commit()
            flash("Регистрация успешна! Теперь войдите.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Пользователь с таким именем уже существует", "error")
        except Exception as e:
            flash("Произошла ошибка при регистрации", "error")
            print(f"Ошибка регистрации: {e}")
        finally:
            conn.close()

    return render_template("register.html")

# --- Вход ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Добро пожаловать, {user['username']}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Неверное имя пользователя или пароль", "error")

    return render_template("login.html")

# --- Выход ---
@app.route("/logout")
def logout():
    session.clear()
    flash("Вы вышли из системы", "info")
    return redirect(url_for("index"))

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # ВКЛЮЧАЕМ поддержку внешних ключей для каждого соединения
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
# Добавляем в main.py основные маршруты для студентов

# --- Главная страница для студентов ---
@app.route("/")
def index():
    conn = get_db()
    blocks = conn.execute("SELECT * FROM blocks ORDER BY name").fetchall()
    conn.close()
    return render_template("index.html", blocks=blocks)

# --- Выбор варианта в блоке ---
@app.route("/block/<int:block_id>")
def block_variants(block_id):
    conn = get_db()
    block = conn.execute("SELECT * FROM blocks WHERE id=?", (block_id,)).fetchone()
    variants = conn.execute("SELECT * FROM variants WHERE block_id=? ORDER BY name", (block_id,)).fetchall()
    conn.close()
    return render_template("block_variants.html", block=block, variants=variants)


# --- Страница тестирования ---
@app.route("/test/<int:variant_id>")
def take_test(variant_id):
    conn = get_db()

    variant = conn.execute("""
                           SELECT v.*, b.has_calculator, b.has_periodic_table
                           FROM variants v
                                    JOIN blocks b ON v.block_id = b.id
                           WHERE v.id = ?
                           """, (variant_id,)).fetchone()

    if not variant:
        conn.close()
        flash("Вариант не найден.", "error")
        return redirect(url_for('index'))

    # Получаем вопросы с группировкой по предметам
    questions = conn.execute("""
        SELECT q.id as question_id, q.text, s.name as subject_name
        FROM questions q
        JOIN subjects s ON q.subject_id = s.id
        WHERE s.variant_id = ?
        ORDER BY s.name, q.id
    """, (variant_id,)).fetchall()

    if not questions:
        conn.close()
        flash("В этом варианте пока нет вопросов. Администратор должен добавить вопросы.", "warning")
        return redirect(url_for('block_variants', block_id=variant['block_id']))

    # Группируем вопросы по предметам
    questions_by_subject = {}
    for question in questions:
        subject_name = question['subject_name']
        if subject_name not in questions_by_subject:
            questions_by_subject[subject_name] = []
        questions_by_subject[subject_name].append(question)

    # Получаем ответы отдельно
    answers_dict = {}
    for question in questions:
        answers = conn.execute("SELECT * FROM answers WHERE question_id=?", (question['question_id'],)).fetchall()
        answers_dict[question['question_id']] = answers

        if not answers:
            conn.close()
            flash(f"У вопроса '{question['text'][:50]}...' нет ответов. Обратитесь к администратору.", "error")
            return redirect(url_for('block_variants', block_id=variant['block_id']))

    conn.close()

    return render_template("test.html",
                           variant=variant,
                           questions_by_subject=questions_by_subject,
                           answers_dict=answers_dict)

# --- Обработка результатов теста ---
# --- Обработка результатов теста ---
@app.route("/submit_test/<int:variant_id>", methods=["POST"])
def submit_test(variant_id):
    conn = get_db()

    # Получаем вариант и вопросы
    variant = conn.execute("""
                           SELECT v.*, b.has_calculator, b.has_periodic_table
                           FROM variants v
                                    JOIN blocks b ON v.block_id = b.id
                           WHERE v.id = ?
                           """, (variant_id,)).fetchone()
    questions = conn.execute("""
                             SELECT q.id, q.text, s.name as subject_name
                             FROM questions q
                                      JOIN subjects s ON q.subject_id = s.id
                             WHERE s.variant_id = ?
                             ORDER BY s.name, q.id
                             """, (variant_id,)).fetchall()

    # Собираем правильные ответы
    correct_answers = {}
    subject_correct = {}
    subject_total = {}

    for question in questions:
        correct_answer = conn.execute(
            "SELECT id FROM answers WHERE question_id = ? AND is_correct = 1",
            (question['id'],)
        ).fetchone()
        if correct_answer:
            correct_answers[question['id']] = correct_answer['id']

        # Инициализируем счетчики для предметов
        subject_name = question['subject_name']
        if subject_name not in subject_total:
            subject_total[subject_name] = 0
            subject_correct[subject_name] = 0
        subject_total[subject_name] += 1

    # Проверяем ответы пользователя
    user_answers = request.form.to_dict()
    results = []
    total_questions = len(questions)
    correct_count = 0
    time_left_str = request.form.get('time_left', '0')
    time_left = int(time_left_str) if time_left_str and time_left_str.isdigit() else 0
    time_spent = 240 * 60 - time_left

    for question in questions:
        question_id = question['id']
        user_answer_id = user_answers.get(f'question_{question_id}')
        correct_answer_id = correct_answers.get(question_id)

        is_correct = user_answer_id and int(user_answer_id) == correct_answer_id
        if is_correct:
            correct_count += 1
            subject_correct[question['subject_name']] += 1

        results.append({
            'question': question['text'],
            'user_answer': user_answer_id,
            'correct_answer': correct_answer_id,
            'is_correct': is_correct,
            'subject': question['subject_name']
        })

    # Считаем процент
    percentage = (correct_count / total_questions * 100) if total_questions > 0 else 0

    # Сохраняем результат в базу (если пользователь авторизован)
    if 'user_id' in session:
        try:
            conn.execute("""
                         INSERT INTO test_results
                             (user_id, variant_id, score, total_questions, percentage, time_spent)
                         VALUES (?, ?, ?, ?, ?, ?)
                         """, (session['user_id'], variant_id, correct_count, total_questions, percentage, time_spent))

            # Обновляем прогресс по предметам
            for subject_name in subject_total.keys():
                conn.execute("""
                    INSERT OR REPLACE INTO subject_progress 
                    (user_id, subject_name, total_answered, correct_answered)
                    VALUES (?, ?, COALESCE((SELECT total_answered FROM subject_progress 
                                           WHERE user_id = ? AND subject_name = ?), 0) + ?,
                                           COALESCE((SELECT correct_answered FROM subject_progress 
                                           WHERE user_id = ? AND subject_name = ?), 0) + ?)
                """, (session['user_id'], subject_name,
                      session['user_id'], subject_name, subject_total[subject_name],
                      session['user_id'], subject_name, subject_correct[subject_name]))

            # ✅✅✅ ВОТ ТУТ ВЫЗЫВАЕМ ОБНОВЛЕНИЕ РЕЙТИНГА ✅✅✅
            update_user_ranking(session['user_id'])

            conn.commit()
        except Exception as e:
            print(f"Ошибка сохранения результатов: {e}")

    conn.close()

    return render_template("results.html",
                           results=results,
                           total_questions=total_questions,
                           correct_count=correct_count,
                           percentage=percentage,
                           time_spent=time_spent,
                           variant=variant)

# --- Личный кабинет ---
@app.route("/profile")
def user_profile():
    if 'user_id' not in session:
        flash("Для доступа к профилю需要 авторизация", "warning")
        return redirect(url_for('login'))

    conn = get_db()

    # Данные пользователя
    user_data = conn.execute(
        "SELECT * FROM users WHERE id = ?", (session['user_id'],)
    ).fetchone()

    # Общая статистика
    total_tests = conn.execute(
        "SELECT COUNT(*) as count FROM test_results WHERE user_id = ?", (session['user_id'],)
    ).fetchone()['count'] or 0

    average_result = conn.execute(
        "SELECT AVG(percentage) as avg FROM test_results WHERE user_id = ?", (session['user_id'],)
    ).fetchone()['avg'] or 0

    total_time = conn.execute(
        "SELECT SUM(time_spent) as total FROM test_results WHERE user_id = ?", (session['user_id'],)
    ).fetchone()['total'] or 0
    total_time = total_time / 3600  # Convert to hours

    total_correct = conn.execute(
        "SELECT SUM(score) as total FROM test_results WHERE user_id = ?", (session['user_id'],)
    ).fetchone()['total'] or 0

    best_score = conn.execute(
        "SELECT MAX(percentage) as best FROM test_results WHERE user_id = ?", (session['user_id'],)
    ).fetchone()['best'] or 0

    # Прогресс по предметам
    subject_progress = conn.execute("""
                                    SELECT *
                                    FROM subject_progress
                                    WHERE user_id = ?
                                    ORDER BY correct_answered DESC
                                    """, (session['user_id'],)).fetchall()

    # История тестов
    test_results = conn.execute("""
                                SELECT tr.*, v.name as variant_name
                                FROM test_results tr
                                         JOIN variants v ON tr.variant_id = v.id
                                WHERE tr.user_id = ?
                                ORDER BY tr.completed_at DESC LIMIT 10
                                """, (session['user_id'],)).fetchall()

    conn.close()

    return render_template("profile.html",
                           user_data=user_data,
                           total_tests=total_tests,
                           average_percentage=average_result,
                           total_time=total_time,
                           total_correct=total_correct,
                           best_score=best_score,
                           subject_progress=subject_progress,
                           test_results=test_results)

# --- Главная страница админки ---
@app.route("/admin")
def admin_index():
    return render_template("admin_index.html")

# --- 1. Страница со всеми блоками ---
@app.route("/admin/blocks")
def admin_blocks():
    conn = get_db()
    blocks = conn.execute("SELECT * FROM blocks ORDER BY name").fetchall()
    conn.close()
    return render_template("admin_blocks.html", blocks=blocks)

# --- 2. Добавить блок ---
@app.route("/admin/add_block", methods=["POST"])
def add_block():
    name = request.form["name"].strip()
    if not name:
        flash("Название блока не может быть пустым.", "error")
        return redirect(url_for("admin_blocks"))

    conn = get_db()
    try:
        conn.execute("INSERT INTO blocks (name) VALUES (?)", (name,))
        conn.commit()
        flash(f"Блок '{name}' успешно добавлен!", "success")
    except sqlite3.IntegrityError:
        flash(f"Блок с названием '{name}' уже существует.", "error")
    finally:
        conn.close()
    return redirect(url_for("admin_blocks"))

# --- 2.1 Удалить блок ---
@app.route("/admin/delete_block/<int:block_id>", methods=["POST"])
def delete_block(block_id):
    conn = get_db()
    # Сначала узнаем имя блока для сообщения
    block = conn.execute("SELECT name FROM blocks WHERE id=?", (block_id,)).fetchone()
    if block:
        conn.execute("DELETE FROM blocks WHERE id=?", (block_id,))
        conn.commit()
        flash(f"Блок '{block['name']}' и все связанные данные удалены.", "success")
    conn.close()
    return redirect(url_for("admin_blocks"))

# --- 3. Список вариантов внутри блока ---
@app.route("/admin/variants/<int:block_id>")
def admin_variants(block_id):
    conn = get_db()
    block = conn.execute("SELECT * FROM blocks WHERE id=?", (block_id,)).fetchone()
    variants = conn.execute("SELECT * FROM variants WHERE block_id=? ORDER BY name", (block_id,)).fetchall()
    conn.close()
    if not block:
        flash("Блок не найден.", "error")
        return redirect(url_for("admin_blocks"))
    return render_template("admin_variants.html", block=block, variants=variants)

# --- 4. Добавить вариант ---
@app.route("/admin/add_variant/<int:block_id>", methods=["POST"])
def add_variant(block_id):
    name = request.form["name"].strip()
    if not name:
        flash("Название варианта не может быть пустым.", "error")
        return redirect(url_for("admin_variants", block_id=block_id))

    conn = get_db()
    try:
        conn.execute("INSERT INTO variants (block_id, name) VALUES (?, ?)", (block_id, name))
        conn.commit()
        flash(f"Вариант '{name}' успешно добавлен!", "success")
    except sqlite3.IntegrityError:
        flash("Ошибка при добавлении варианта.", "error")
    finally:
        conn.close()
    return redirect(url_for("admin_variants", block_id=block_id))

# --- 4.1 Удалить вариант ---
@app.route("/admin/delete_variant/<int:variant_id>", methods=["POST"])
def delete_variant(variant_id):
    conn = get_db()
    # Чтобы сделать redirect назад, нужно знать block_id
    variant = conn.execute("SELECT block_id, name FROM variants WHERE id=?", (variant_id,)).fetchone()
    if variant:
        conn.execute("DELETE FROM variants WHERE id=?", (variant_id,))
        conn.commit()
        flash(f"Вариант '{variant['name']}' удален.", "success")
        block_id = variant['block_id']
    else:
        flash("Вариант не найден.", "error")
        block_id = request.form.get('block_id')  # Резервный вариант, если variant уже удален
    conn.close()
    return redirect(url_for("admin_variants", block_id=block_id))

# --- 5. Список предметов в варианте ---
@app.route("/admin/subjects/<int:variant_id>")
def admin_subjects(variant_id):
    conn = get_db()
    variant = conn.execute("SELECT v.*, b.name as block_name FROM variants v JOIN blocks b ON v.block_id = b.id WHERE v.id=?", (variant_id,)).fetchone()
    subjects = conn.execute("SELECT * FROM subjects WHERE variant_id=? ORDER BY name", (variant_id,)).fetchall()
    conn.close()
    if not variant:
        flash("Вариант не найден.", "error")
        return redirect(url_for("admin_blocks"))
    return render_template("admin_subjects.html", variant=variant, subjects=subjects)

# --- 6. Добавить предмет ---
@app.route("/admin/add_subject/<int:variant_id>", methods=["POST"])
def add_subject(variant_id):
    name = request.form["name"].strip()
    if not name:
        flash("Название предмета не может быть пустым.", "error")
        return redirect(url_for("admin_subjects", variant_id=variant_id))

    conn = get_db()
    try:
        conn.execute("INSERT INTO subjects (variant_id, name) VALUES (?, ?)", (variant_id, name))
        conn.commit()
        flash(f"Предмет '{name}' добавлен!", "success")
    except sqlite3.IntegrityError:
        flash("Ошибка при добавлении предмета.", "error")
    finally:
        conn.close()
    return redirect(url_for("admin_subjects", variant_id=variant_id))

# --- 6.1 Удалить предмет ---
@app.route("/admin/delete_subject/<int:subject_id>", methods=["POST"])
def delete_subject(subject_id):
    conn = get_db()
    subject = conn.execute("SELECT variant_id, name FROM subjects WHERE id=?", (subject_id,)).fetchone()
    if subject:
        conn.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
        conn.commit()
        flash(f"Предмет '{subject['name']}' удален.", "success")
        variant_id = subject['variant_id']
    else:
        flash("Предмет не найден.", "error")
        variant_id = request.form.get('variant_id')
    conn.close()
    return redirect(url_for("admin_subjects", variant_id=variant_id))

# --- 7. Список вопросов в предмете ---
@app.route("/admin/questions/<int:subject_id>")
def admin_questions(subject_id):
    conn = get_db()
    # Добавляем JOIN чтобы получить название варианта
    subject = conn.execute("""
        SELECT s.*, v.name as variant_name 
        FROM subjects s 
        JOIN variants v ON s.variant_id = v.id 
        WHERE s.id=?
    """, (subject_id,)).fetchone()

    questions = conn.execute("SELECT * FROM questions WHERE subject_id=?", (subject_id,)).fetchall()
    conn.close()

    if not subject:
        flash("Предмет не найден.", "error")
        return redirect(url_for("admin_blocks"))

    return render_template("admin_questions.html", subject=subject, questions=questions)

# --- 8. Добавить вопрос ---
@app.route("/admin/add_question/<int:subject_id>", methods=["POST"])
def add_question(subject_id):
    text = request.form["text"].strip()
    if not text:
        flash("Текст вопроса не может быть пустым.", "error")
        return redirect(url_for("admin_questions", subject_id=subject_id))

    conn = get_db()
    try:
        conn.execute("INSERT INTO questions (subject_id, text) VALUES (?, ?)", (subject_id, text))
        conn.commit()
        flash("Вопрос добавлен!", "success")
    except sqlite3.IntegrityError:
        flash("Ошибка при добавлении вопроса.", "error")
    finally:
        conn.close()
    return redirect(url_for("admin_questions", subject_id=subject_id))

# --- 8.1 Удалить вопрос ---
@app.route("/admin/delete_question/<int:question_id>", methods=["POST"])
def delete_question(question_id):
    conn = get_db()
    question = conn.execute("SELECT subject_id FROM questions WHERE id=?", (question_id,)).fetchone()
    if question:
        conn.execute("DELETE FROM questions WHERE id=?", (question_id,))
        conn.commit()
        flash("Вопрос удален.", "success")
        subject_id = question['subject_id']
    else:
        flash("Вопрос не найден.", "error")
        subject_id = request.form.get('subject_id')
    conn.close()
    return redirect(url_for("admin_questions", subject_id=subject_id))


# --- 9. Список ответов ---
@app.route("/admin/answers/<int:question_id>")
def admin_answers(question_id):
    conn = get_db()
    # ИСПРАВЛЕННЫЙ ЗАПРОС: Добавляем JOIN чтобы получить всю нужную информацию
    question = conn.execute("""
        SELECT q.*, s.name as subject_name, s.variant_id, v.block_id, v.name as variant_name, b.name as block_name
        FROM questions q
        JOIN subjects s ON q.subject_id = s.id
        JOIN variants v ON s.variant_id = v.id
        JOIN blocks b ON v.block_id = b.id
        WHERE q.id=?
    """, (question_id,)).fetchone()

    answers = conn.execute("SELECT * FROM answers WHERE question_id=?", (question_id,)).fetchall()
    conn.close()

    if not question:
        flash("Вопрос не найден.", "error")
        return redirect(url_for("admin_blocks"))

    return render_template("admin_answers.html", question=question, answers=answers)

# --- 10. Добавить ответ ---
@app.route("/admin/add_answer/<int:question_id>", methods=["POST"])
def add_answer(question_id):
    text = request.form["text"].strip()
    if not text:
        flash("Текст ответа не может быть пустым.", "error")
        return redirect(url_for("admin_answers", question_id=question_id))

    is_correct = 1 if "is_correct" in request.form else 0
    conn = get_db()
    try:
        conn.execute("INSERT INTO answers (question_id, text, is_correct) VALUES (?, ?, ?)",
                     (question_id, text, is_correct))
        conn.commit()
        flash("Ответ добавлен!", "success")
    except sqlite3.IntegrityError:
        flash("Ошибка при добавлении ответа.", "error")
    finally:
        conn.close()
    return redirect(url_for("admin_answers", question_id=question_id))

# --- 10.1 Удалить ответ ---
@app.route("/admin/delete_answer/<int:answer_id>", methods=["POST"])
def delete_answer(answer_id):
    conn = get_db()
    answer = conn.execute("SELECT question_id FROM answers WHERE id=?", (answer_id,)).fetchone()
    if answer:
        conn.execute("DELETE FROM answers WHERE id=?", (answer_id,))
        conn.commit()
        flash("Ответ удален.", "success")
        question_id = answer['question_id']
    else:
        flash("Ответ не найден.", "error")
        question_id = request.form.get('question_id')
    conn.close()
    return redirect(url_for("admin_answers", question_id=question_id))


# --- 10.2 Отметить правильный ответ ---
@app.route("/admin/toggle_answer/<int:answer_id>")
def toggle_answer(answer_id):
    conn = get_db()
    answer = conn.execute("SELECT question_id, is_correct FROM answers WHERE id=?", (answer_id,)).fetchone()
    if answer:
        new_value = 0 if answer['is_correct'] else 1
        conn.execute("UPDATE answers SET is_correct=? WHERE id=?", (new_value, answer_id))
        conn.commit()
        question_id = answer['question_id']
    else:
        # Если ответ не найден, берем question_id из параметра URL
        question_id = request.args.get('question_id')
    conn.close()
    return redirect(url_for("admin_answers", question_id=question_id))


# --- Редактировать блок ---
@app.route("/admin/edit_block/<int:block_id>", methods=["GET", "POST"])
def edit_block(block_id):
    conn = get_db()
    block = conn.execute("SELECT * FROM blocks WHERE id=?", (block_id,)).fetchone()

    if request.method == "POST":
        new_name = request.form["name"].strip()
        if new_name:
            conn.execute("UPDATE blocks SET name=? WHERE id=?", (new_name, block_id))
            conn.commit()
            flash("Блок успешно обновлен!", "success")
            return redirect(url_for("admin_blocks"))

    conn.close()
    return render_template("edit_block.html", block=block)


# --- Редактировать вариант ---
@app.route("/admin/edit_variant/<int:variant_id>", methods=["GET", "POST"])
def edit_variant(variant_id):
    conn = get_db()
    variant = conn.execute("SELECT * FROM variants WHERE id=?", (variant_id,)).fetchone()

    if request.method == "POST":
        new_name = request.form["name"].strip()
        if new_name:
            conn.execute("UPDATE variants SET name=? WHERE id=?", (new_name, variant_id))
            conn.commit()
            flash("Вариант успешно обновлен!", "success")
            return redirect(url_for("admin_variants", block_id=variant['block_id']))

    conn.close()
    return render_template("edit_variant.html", variant=variant)


# --- Редактировать предмет ---
@app.route("/admin/edit_subject/<int:subject_id>", methods=["GET", "POST"])
def edit_subject(subject_id):
    conn = get_db()
    subject = conn.execute("SELECT * FROM subjects WHERE id=?", (subject_id,)).fetchone()

    if request.method == "POST":
        new_name = request.form["name"].strip()
        if new_name:
            conn.execute("UPDATE subjects SET name=? WHERE id=?", (new_name, subject_id))
            conn.commit()
            flash("Предмет успешно обновлен!", "success")
            return redirect(url_for("admin_subjects", variant_id=subject['variant_id']))

    conn.close()
    return render_template("edit_subject.html", subject=subject)


# --- Редактировать вопрос ---
@app.route("/admin/edit_question/<int:question_id>", methods=["GET", "POST"])
def edit_question(question_id):
    conn = get_db()
    question = conn.execute("SELECT * FROM questions WHERE id=?", (question_id,)).fetchone()

    if request.method == "POST":
        new_text = request.form["text"].strip()
        if new_text:
            conn.execute("UPDATE questions SET text=? WHERE id=?", (new_text, question_id))
            conn.commit()
            flash("Вопрос успешно обновлен!", "success")
            return redirect(url_for("admin_questions", subject_id=question['subject_id']))

    conn.close()
    return render_template("edit_question.html", question=question)


# --- Редактировать ответ ---
@app.route("/admin/edit_answer/<int:answer_id>", methods=["GET", "POST"])
def edit_answer(answer_id):
    conn = get_db()
    answer = conn.execute("SELECT * FROM answers WHERE id=?", (answer_id,)).fetchone()

    if request.method == "POST":
        new_text = request.form["text"].strip()
        is_correct = 1 if "is_correct" in request.form else 0

        if new_text:
            conn.execute(
                "UPDATE answers SET text=?, is_correct=? WHERE id=?",
                (new_text, is_correct, answer_id)
            )
            conn.commit()
            flash("Ответ успешно обновлен!", "success")
            return redirect(url_for("admin_answers", question_id=answer['question_id']))

    conn.close()
    return render_template("edit_answer.html", answer=answer)


def update_user_ranking(user_id):
    """Обновляет рейтинг пользователя после каждого теста"""
    conn = get_db()

    # Считаем статистику пользователя
    stats = conn.execute("""
                         SELECT COUNT(*)        as tests_completed,
                                SUM(score)      as total_score,
                                AVG(percentage) as average_percentage
                         FROM test_results
                         WHERE user_id = ?
                         """, (user_id,)).fetchone()

    # Обновляем или создаем запись в рейтинге
    conn.execute("""
        INSERT OR REPLACE INTO user_rankings 
        (user_id, total_score, tests_completed, average_percentage)
        VALUES (?, ?, ?, ?)
    """, (user_id, stats['total_score'] or 0, stats['tests_completed'] or 0, stats['average_percentage'] or 0))

    conn.commit()
    conn.close()

# --- Топ пользователей ---
@app.route("/leaderboard")
def leaderboard():
    conn = get_db()

    top_users = conn.execute("""
                             SELECT u.username, r.total_score, r.tests_completed, r.average_percentage
                             FROM user_rankings r
                                      JOIN users u ON r.user_id = u.id
                             ORDER BY r.average_percentage DESC, r.total_score DESC LIMIT 20
                             """).fetchall()

    conn.close()

    return render_template("leaderboard.html", top_users=top_users)

# Добавь в main.py для проверки
@app.route("/admin/debug")
def debug_foreign_keys():
    conn = get_db()
    result = conn.execute("PRAGMA foreign_keys").fetchone()
    conn.close()
    return f"Foreign keys enabled: {result[0] == 1}"

if __name__ == "__main__":
    app.run(debug=True)