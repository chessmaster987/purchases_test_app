from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

import psycopg2  # pip install psycopg2
import psycopg2.extras

from dotenv import load_dotenv

import cloudinary
import cloudinary.uploader

# Завантажуємо змінні з .env
load_dotenv()

app = Flask(__name__)
app.secret_key = "nasa"

# Налаштування Cloudinary (використовуємо ENV-перемінні у Render)
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# =======================
# Підключення до Neon через змінну середовища
# =======================
DATABASE_URL = os.getenv("DATABASE_URL_TEST")
if not DATABASE_URL:
    raise ValueError("Не встановлено змінну середовища DATABASE_URL")

PASSWORD = os.getenv("SITE_PASSWORD")

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("Успішно підключено до бази даних!")
except psycopg2.Error as e:
    print("Не вдалось підключитися до бази даних:", e)
    conn = None  # conn = None, щоб не падало

# ===== Авторизація =====####################################################
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash("Неправильний пароль!")
    return render_template('login.html')

def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
                                                                ##################################################
# Головна
@app.route('/')
@login_required                                 #####################
def index():
    return render_template('index.html')

# Додавання покупки
@app.route('/add', methods=['GET', 'POST'])
def add():
    conn = psycopg2.connect(DATABASE_URL)
    if not conn:
        return "Помилка: база даних недоступна"

    if request.method == 'POST':
        date = request.form['date_of_purchase']
        m_name = request.form['market_id']
        p_desc = request.form['purchase_description']
        suma = request.form['amount']

        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(
                    "INSERT INTO enter_purchase (date_of_purchase, market_id, purchase_description, suma) VALUES (%s,%s,%s,%s)", (date, m_name, p_desc, suma)
                )
                conn.commit()
        except psycopg2.Error as e:
            conn.rollback()
            return f"Помилка при додаванні покупки: {e}"

        """
        file = request.files['receipt']
        receipt_url = None
        if file:
            upload_result = cloudinary.uploader.upload(file)
            receipt_url = upload_result['secure_url']
            print(receipt_url)
        """

    # --- дістаємо список магазинів для select ---
    markets = []
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT id_market, name_of_market, logo_market FROM Markets")
        markets = cur.fetchall()

    return render_template('add.html', markets=markets)

# Додавання магазинів
@app.route('/markets', methods=['GET', 'POST'])
def markets():
    conn = psycopg2.connect(DATABASE_URL)
    if not conn:
        return "Помилка: база даних недоступна"

    if request.method == 'POST':
        name = request.form['name_of_market']
        file = request.files['logo_market']
        logo_url = None

        if file:
            upload_result = cloudinary.uploader.upload(file)
            logo_url = upload_result['secure_url']

        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO Markets (name_of_market, logo_market) VALUES (%s, %s)",
                    (name, logo_url)
                )
                conn.commit()
        except Exception as e:
            conn.rollback()
            return f"Помилка при додаванні магазину: {e}"

    markets_data = []
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT id_market, name_of_market, logo_market FROM Markets")
        markets_data = cur.fetchall()

    conn.close()
    return render_template('markets.html', markets=markets_data)

# Статистика
@app.route('/stats')
def stats():
    conn = psycopg2.connect(DATABASE_URL)
    purchases = []
    shops = {}
    total = 0

    try:
        with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            # Всі покупки
            cur.execute("""SELECT id_purchase, date_of_purchase, markets.name_of_market, purchase_description, suma
                        FROM enter_purchase
                        INNER JOIN markets on enter_purchase.market_id = markets.id_market
                        ORDER BY date_of_purchase DESC
                        LIMIT 20""")
            rows = cur.fetchall()

            for row in rows:
                purchases.append({
                    "id": row["id_purchase"],
                    "date": row["date_of_purchase"].strftime("%d-%m-%Y"),
                    "shop": row["name_of_market"],
                    "desc": row["purchase_description"],
                    "amount": float(row["suma"]),
                    #"receipt": None -- if Cloudinary
                })

                # Загальна сума
                total += float(row["suma"])

                # По магазинах
                shop = row["name_of_market"]
                shops[shop] = shops.get(shop, 0) + float(row["suma"])

    except psycopg2.Error as e:
        return f"Помилка при отриманні статистики: {e}"

    return render_template("stats.html", purchases=purchases, total=total, shops=shops)

##
####
####
####
####
####
####
####
##


# ===== Вихід =====
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
