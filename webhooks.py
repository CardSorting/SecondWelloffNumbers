import sqlite3
import json
from flask import Flask, request, jsonify
from config import config
import requests
import hmac
import hashlib
import base64

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

SHOPIFY_CLIENT_ID = config.SHOPIFY_CLIENT_ID
SHOPIFY_CLIENT_SECRET = config.SHOPIFY_CLIENT_SECRET
USAGE_CHARGE_LIMIT = 100  # Number of orders included in the subscription plan
USAGE_CHARGE_COST = 0.25  # Cost per additional order beyond the limit

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def verify_webhook(data, hmac_header):
    digest = hmac.new(SHOPIFY_CLIENT_SECRET.encode('utf-8'), data, hashlib.sha256).digest()
    computed_hmac = base64.b64encode(digest)
    return hmac.compare_digest(computed_hmac, hmac_header.encode('utf-8'))

def save_order(order, shop):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO orders (shopify_order_id, shopify_shop, status, details, updated_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (order['id'], shop, order.get('financial_status', 'pending'), str(order), order['updated_at']))
    c.execute('''
        UPDATE users SET order_count = order_count + 1 WHERE shopify_shop = ?
    ''', (shop,))
    conn.commit()

    # Check for usage charges
    c.execute('SELECT order_count FROM users WHERE shopify_shop = ?', (shop,))
    order_count = c.fetchone()['order_count']
    if order_count > USAGE_CHARGE_LIMIT:
        create_usage_charge(shop, order_count - USAGE_CHARGE_LIMIT)
    conn.close()

def save_notification(message, timestamp, shop):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO notifications (shopify_shop, message, created_at)
        VALUES (?, ?, ?)
    ''', (shop, message, timestamp))
    conn.commit()
    conn.close()

def create_usage_charge(shop, excess_orders):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT access_token, charge_id FROM users WHERE shopify_shop = ?', (shop,))
    user = c.fetchone()
    conn.close()

    access_token = user['access_token']
    charge_id = user['charge_id']
    usage_charge_url = f"https://{shop}/admin/api/2023-01/recurring_application_charges/{charge_id}/usage_charges.json"
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    payload = {
        "usage_charge": {
            "description": "Additional orders",
            "price": excess_orders * USAGE_CHARGE_COST
        }
    }
    response = requests.post(usage_charge_url, json=payload, headers=headers)
    return response.json()

@app.route('/webhook/orders/create', methods=['POST'])
def orders_create():
    data = request.get_data()
    hmac_header = request.headers.get('X-Shopify-Hmac-Sha256')

    if not verify_webhook(data, hmac_header):
        return "Webhook verification failed", 400

    order = request.json
    shop = request.headers.get('X-Shopify-Shop-Domain')
    save_order(order, shop)
    save_notification('New order received', order['created_at'], shop)
    return jsonify({'status': 'success'})

@app.route('/webhook/orders/paid', methods=['POST'])
def orders_paid():
    data = request.get_data()
    hmac_header = request.headers.get('X-Shopify-Hmac-Sha256')

    if not verify_webhook(data, hmac_header):
        return "Webhook verification failed", 400

    order = request.json
    shop = request.headers.get('X-Shopify-Shop-Domain')
    save_order(order, shop)
    save_notification('Order payment received', order['updated_at'], shop)
    return jsonify({'status': 'success'})

@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    conn = get_db_connection()
    project = conn.execute('SELECT * FROM projects WHERE id = ?', (project_id,)).fetchone()
    conn.close()
    if project is None:
        return jsonify({'error': 'Project not found'}), 404
    return jsonify(dict(project))

@app.route('/api/projects/<int:project_id>', methods=['POST'])
def update_project(project_id):
    data = request.json
    conn = get_db_connection()
    conn.execute('''
        UPDATE projects SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
    ''', (json.dumps(data), project_id))
    conn.commit()
    conn.close()
    return jsonify({'status': 'success'})

def register_webhook(shop, access_token, topic, address):
    headers = {
        "X-Shopify-Access-Token": access_token,
        "Content-Type": "application/json"
    }
    webhook_payload = {
        "webhook": {
            "topic": topic,
            "address": address,
            "format": "json"
        }
    }
    response = requests.post(f"https://{shop}/admin/api/2023-01/webhooks.json", json=webhook_payload, headers=headers)
    return response.json()

if __name__ == '__main__':
    app.run(debug=True)