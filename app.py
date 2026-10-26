import os
from flask import Flask, render_template, request, redirect, url_for
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# قراءة رابط قاعدة البيانات من إعدادات السحابة، ولو مش موجود ياخد الرابط المحلي كاحتياطي
DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://postgres:Eemmaadd132%40@aws-0-eu-central-1.pooler.supabase.co:6543/postgres"
)

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

@app.route('/')
def index():
    search_query = request.args.get('q', '')
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # جلب الإحصائيات الشاملة
        cur.execute("SELECT COUNT(*) as cnt FROM items WHERE status='متوفر'")
        available_count = cur.fetchone()['cnt']
        
        cur.execute("SELECT COUNT(*) as cnt FROM items")
        total_count = cur.fetchone()['cnt']

        cur.execute("SELECT COUNT(*) as cnt FROM items WHERE status='محجوز'")
        reserved_count = cur.fetchone()['cnt']

        cur.execute("SELECT COUNT(*) as cnt FROM items WHERE status='مباع'")
        sold_count = cur.fetchone()['cnt']

        # جلب القطع مع دعم البحث لو تم البحث عن شيء
        if search_query:
            query = "SELECT * FROM items WHERE model ILIKE %s OR part_type ILIKE %s OR color ILIKE %s ORDER BY id DESC"
            val = (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%")
            cur.execute(query, val)
        else:
            cur.execute("SELECT * FROM items ORDER BY id DESC")
            
        items = cur.fetchall()

        cur.close()
        conn.close()
    except Exception as e:
        available_count = 0
        total_count = 0
        reserved_count = 0
        sold_count = 0
        items = []
        
    return render_template(
        'index.html', 
        available_count=available_count, 
        total_count=total_count, 
        reserved_count=reserved_count,
        sold_count=sold_count,
        items=items
    )

@app.route('/add', methods=('GET', 'POST'))
def add_item():
    if request.method == 'POST':
        model = request.form['model']
        part_type = request.form['part_type']
        color = request.form['color']
        target_price = request.form['target_price']
        min_price = request.form['min_price']
        status = request.form.get('status', 'متوفر')
        seller_name = request.form.get('seller_name', 'أمجد')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO items (model, part_type, color, target_price, min_price, status, seller_name) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (model, part_type, color, target_price, min_price, status, seller_name)
        )
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('index'))
        
    return render_template('add.html')

@app.route('/update_status/<int:id>/<string:new_status>')
def update_status(id, new_status):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE items SET status = %s WHERE id = %s", (new_status, id))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error updating status:", e)
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_item(id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM items WHERE id = %s", (id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print("Error deleting item:", e)
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)