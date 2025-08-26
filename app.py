import cloudinary
import cloudinary.uploader
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime

app = Flask(__name__)

# Конфіг
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///purchases.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# Налаштування Cloudinary (використовуємо ENV-перемінні у Render)
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Модель бази
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    shop = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    receipt = db.Column(db.String(200))  # шлях до файлу

# Головна
@app.route('/')
def index():
    return render_template('index.html')

# Додавання покупки
@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        date_str = request.form['date']
        shop = request.form['shop']
        amount = float(request.form['amount'])

        file = request.files['receipt']
        receipt_url = None
        if file:
            upload_result = cloudinary.uploader.upload(file)
            receipt_url = upload_result['secure_url']

        # Збереження в БД
        purchase = Purchase(
            date=datetime.strptime(date_str, '%Y-%m-%d'),
            shop=shop,
            amount=amount,
            receipt=receipt_url
        )
        db.session.add(purchase)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add.html')

# Статистика
@app.route('/stats')
def stats():
    purchases = Purchase.query.all()
    total = sum(p.amount for p in purchases)
    
    # сума по магазинах
    shops = {}
    for p in purchases:
        shops[p.shop] = shops.get(p.shop, 0) + p.amount

    return render_template('stats.html', purchases=purchases, total=total, shops=shops)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
