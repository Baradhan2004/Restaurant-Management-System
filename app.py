"""Small restaurant ordering API backed by SQLite."""
from flask import Flask, jsonify, request
from pathlib import Path
import os, sqlite3
BASE=Path(__file__).resolve().parent
DB_PATH=Path(os.getenv('RESTAURANT_DB', BASE/'restaurant.db'))
app=Flask(__name__)

def connect():
    con=sqlite3.connect(DB_PATH); con.row_factory=sqlite3.Row; con.execute('PRAGMA foreign_keys=ON'); return con

def init_db():
    schema=(BASE/'sql'/'schema.sql').read_text(encoding='utf-8')
    with connect() as con: con.executescript(schema)

@app.get('/health')
def health(): return jsonify(status='ok')

@app.get('/menu')
def menu():
    with connect() as con: rows=con.execute('SELECT item_id,name,category,price,available FROM menu_items WHERE available=1 ORDER BY category,name').fetchall()
    return jsonify([dict(r) for r in rows])

@app.post('/orders')
def create_order():
    body=request.get_json(silent=True) or {}; customer_id=body.get('customer_id'); items=body.get('items')
    if not isinstance(customer_id,int) or not isinstance(items,list) or not items:
        return jsonify(error='customer_id (integer) and a non-empty items list are required'),400
    try:
        with connect() as con:
            if not con.execute('SELECT 1 FROM customers WHERE customer_id=?',(customer_id,)).fetchone(): return jsonify(error='Customer not found'),404
            normalized=[]
            submitted_ids=[item.get('item_id') for item in items if isinstance(item,dict)]
            if len(submitted_ids) != len(set(submitted_ids)):
                return jsonify(error='Submit each menu item once and increase its quantity instead'),400
            for item in items:
                if not isinstance(item,dict) or not isinstance(item.get('item_id'),int) or not isinstance(item.get('quantity'),int) or item['quantity']<1 or item['quantity']>50:
                    return jsonify(error='Each item needs integer item_id and quantity from 1 to 50'),400
                row=con.execute('SELECT item_id,name,price FROM menu_items WHERE item_id=? AND available=1',(item['item_id'],)).fetchone()
                if not row: return jsonify(error=f"Menu item {item['item_id']} not found or unavailable"),400
                normalized.append((row,item['quantity']))
            total=sum(float(row['price'])*qty for row,qty in normalized)
            cur=con.execute("INSERT INTO orders(customer_id,status,total_amount) VALUES(?, 'PLACED', ?)",(customer_id,round(total,2)))
            order_id=cur.lastrowid
            for row,qty in normalized: con.execute('INSERT INTO order_items(order_id,item_id,quantity,unit_price) VALUES(?,?,?,?)',(order_id,row['item_id'],qty,row['price']))
            return jsonify(order_id=order_id,status='PLACED',total_amount=round(total,2),items=[{'item_id':r['item_id'],'name':r['name'],'quantity':q,'unit_price':r['price']} for r,q in normalized]),201
    except sqlite3.IntegrityError:
        return jsonify(error='Order could not be saved because of a data constraint'),400

@app.get('/orders/<int:order_id>')
def get_order(order_id):
    with connect() as con:
        order=con.execute('SELECT order_id,customer_id,status,total_amount,created_at FROM orders WHERE order_id=?',(order_id,)).fetchone()
        if not order: return jsonify(error='Order not found'),404
        items=con.execute('SELECT mi.name,oi.item_id,oi.quantity,oi.unit_price FROM order_items oi JOIN menu_items mi ON mi.item_id=oi.item_id WHERE oi.order_id=?',(order_id,)).fetchall()
    result=dict(order); result['items']=[dict(r) for r in items]; return jsonify(result)

if __name__=='__main__':
    init_db(); app.run(host='127.0.0.1',port=int(os.getenv('PORT','5000')),debug=False)
