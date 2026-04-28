from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db=SQLAlchemy(app)

BASE_DIR= os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER= os.path.join(BASE_DIR,'static','uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = 'nexora_hayday_key_2008'

# Bazanı başlanğıcda yaratmaq üçün funksiya
def init_db():
    if not os.path.exists('static/uploads'):
        os.makedirs('static/uploads')
    conn = sqlite3.connect('database.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS products 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     name TEXT, price REAL, category TEXT, image TEXT)''')
    conn.close()

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    
    temp_cart = session['cart']
    temp_cart.append(product_id)
    session['cart'] = temp_cart
    
    # Sessiyanın dəyişdiyini Flask-a bildiririk
    session.modified = True 
    
    return redirect(url_for('index'))




@app.route('/')
def index():
    # Brauzer linkindən kateqoriyanı oxuyuruq (məs: /?category=depo)
    # Əgər kateqoriya seçilməyibsə, default olaraq 'tüm' qəbul edilir
    cat = request.args.get('category', 'tüm')
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if cat == 'tüm' or not cat:
        # 'tüm' seçilibsə və ya heç bir filtr yoxdursa, bütün məhsulları gətir
        cursor.execute("SELECT * FROM products")
    else:
        # Konkret kateqoriya seçilibsə, bazada həmin kateqoriyaya aid olanları gətir
        cursor.execute("SELECT * FROM products WHERE category=?", (cat,))
        
    products = cursor.fetchall()
    conn.close()
    
    # Səbətdəki məhsul sayını tapırıq (Səhifənin yuxarısındakı düymə üçün)
    cart_count = len(session.get('cart', []))
    
    # Məlumatları HTML-ə göndəririk
    return render_template('index.html', 
                           products=products, 
                           cart_items_count=cart_count, 
                           current_category=cat)
    

    # --- QOVLUQ VƏ BAZA YOLLARINI TƏYİN EDİRİK ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


# --- ADMİN GİRİŞ (LOGIN) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        # Şifrən: HayDayLuks2026! (İstəsən dəyişə bilərsən)
        if password == '@Nİhad_Nexora!': 
            session['is_admin'] = True
            return redirect(url_for('admin'))
        else:
            return "Şifrə səhvdir! <a href='/login'>Yenidən yoxla</a>"
    
    return '''
        <div style="text-align:center; margin-top:100px; font-family:sans-serif;">
            <h2>HAYDAYLÜKS Admin Girişi</h2>
            <form method="post">
                <input type="password" name="password" placeholder="Şifrəni daxil edin" style="padding:10px; width:250px;" required><br><br>
                <button type="submit" style="padding:10px 20px; cursor:pointer; background: #2ecc71; color:white; border:none; border-radius:5px;">Giriş Et</button>
            </form>
        </div>
    '''

# --- ADMİN PANEL (ƏSAS) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category'] # Seçilən kateqoriya
        file = request.files['image']

        if file:
            filename = file.filename
            file.save(os.path.join('static/uploads', filename))
            cursor.execute("INSERT INTO products (name, price, category, image) VALUES (?, ?, ?, ?)",
                           (name, price, category, filename))
            conn.commit()
            return redirect(url_for('admin'))

    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    conn.close()
    return render_template('admin.html', products=products)

# --- MƏHSULU REDAKTƏ ET (EDIT) ---
@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        category = request.form['category']
        
        cursor.execute("UPDATE products SET name=?, price=?, category=? WHERE id=?", 
                       (name, price, category, id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))

    cursor.execute("SELECT * FROM products WHERE id=?", (id,))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        return "Məhsul tapılmadı", 404
        
    return render_template('edit_product.html', product=product)

# --- MƏHSUL SİLMƏ ---
@app.route('/delete_product/<int:id>')
def delete_product(id):
    if not session.get('is_admin'):
        return redirect(url_for('login'))

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT image FROM products WHERE id = ?", (id,))
    product = cursor.fetchone()
    if product:
        img_path = os.path.join('static/uploads', product[0])
        if os.path.exists(img_path):
            os.remove(img_path)
            
        cursor.execute("DELETE FROM products WHERE id = ?", (id,))
        conn.commit()
    
    conn.close()
    return redirect(url_for('admin'))

# --- ÇIXIŞ ---
@app.route('/logout')
def logout():
    session.pop('is_admin', None)
    return redirect(url_for('index'))




@app.route('/clear_cart')
def clear_cart():
    session.pop('cart', None)  # Səbəti sessiyadan silirik
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart = session.get('cart', [])
    cart_details = []
    total_price = 0
    
    if cart:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        for product_id in cart:
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            if product:
                total_price += float(product[2])
                cart_details.append(product)
        conn.close()
    
    return render_template('cart.html', cart_details=cart_details, total_price=total_price)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)