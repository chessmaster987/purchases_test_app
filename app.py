from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

import psycopg2  # pip install psycopg2
import psycopg2.extras

#from dotenv import load_dotenv

# Завантажуємо змінні з .env
#load_dotenv()

app = Flask(__name__)
app.secret_key = "nasa"

# Налаштування Cloudinary (використовуємо ENV-перемінні у Render)
#cloudinary.config(
#    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
#    api_key=os.getenv("CLOUDINARY_API_KEY"),
#    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
#    secure=True
#)

# =======================
# Підключення до Neon через змінну середовища
# =======================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Не встановлено змінну середовища DATABASE_URL")

try:
    conn = psycopg2.connect(DATABASE_URL)
    print("Успішно підключено до бази даних!")
except psycopg2.Error as e:
    print("Не вдалось підключитися до бази даних:", e)
    conn = None  # conn = None, щоб не падало

# Головна
@app.route('/')
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
        m_name = request.form['market_name']
        p_desc = request.form['purchase_description']
        suma = request.form['amount']

        try:
            with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
                cur.execute(
                    "INSERT INTO enter_purchase (date_of_purchase, market_name, purchase_description, suma) VALUES (%s,%s,%s,%s)", (date, m_name, p_desc, suma)
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
            """

    return render_template('add.html')

# Статистика
@app.route('/stats')
def stats():
    #purchases = Purchase.query.all()
    
    # сума по магазинах
    """
    shops = {}
    for p in purchases:
        shops[p.shop] = shops.get(p.shop, 0) + p.amount

    return render_template('stats.html', purchases=purchases, total=total, shops=shops)"""

if __name__ == '__main__':
    app.run(debug=True)
