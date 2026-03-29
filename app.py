from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import time
import hmac

app = Flask(__name__)
app.secret_key = 'apex_ultra_secret_2024_change_in_prod'

# ─── Password Store (rotated every 2 minutes by ESP32) ───────────────────────
# Each user has a current password + last_updated timestamp
PASSWORD_STORE = {
    "john_doe": {"password": "INIT-0000", "last_updated": time.time()},
}

# Shared API key for ESP32 authentication (embed this in your ESP32 firmware)
ESP32_API_KEY = "ESP32-APEX-SECRET-KEY-abc123"

# ─── Mock Account Data ────────────────────────────────────────────────────────
MOCK_BANK_DATA = {
    "user": {
        "account_holder": "user",
        "account_number": "XXXX-XXXX-9876",
        "balance": 1200.50,
        "recent_transactions": [
            {"date": "2024-10-02", "desc": "Grocery Store",     "amount": -85.20},
            {"date": "2024-10-01", "desc": "Coffee Shop",       "amount": -12.50},
            {"date": "2024-09-29", "desc": "Salary Deposit",    "amount": 2400.00},
        ],
        "card_type": "Gold",
        "card_color": "#2d1b00"
    }
}

# ─── Routes ───────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_info = MOCK_BANK_DATA.get(session['user'])
    return render_template('dashboard.html', user=user_info)


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user_data = PASSWORD_STORE.get(username)
        if user_data and hmac.compare_digest(user_data['password'], password):
            session['user'] = username
            session.permanent = False
            return redirect(url_for('home'))
        else:
            error = 'Invalid credentials. Your token may have rotated — check your device.'

    # Pass password age info to the template so the UI can show a countdown
    password_age = {}
    for user, data in PASSWORD_STORE.items():
        age = int(time.time() - data['last_updated'])
        password_age[user] = age
                                                        
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


# ─── ESP32 API: Update password ───────────────────────────────────────────────
# ESP32 sends: POST /api/update-password
# Headers: X-API-Key: <ESP32_API_KEY>
# Body JSON: {"username": "admin", "password": "NEW-PASS-XYZ"}
#
# Example ESP32 Arduino code (WiFi):
#   HTTPClient http;
#   http.begin("http://<YOUR_SERVER_IP>:5000/api/update-password");
#   http.addHeader("Content-Type", "application/json");
#   http.addHeader("X-API-Key", "ESP32-APEX-SECRET-KEY-abc123");
#   String payload = "{\"username\":\"admin\",\"password\":\"" + newPass + "\"}";
#   int code = http.POST(payload);
#
@app.route('/api/update-password', methods=['POST'])
def update_password():
    api_key = request.headers.get('X-API-Key', '')
    if not hmac.compare_digest(api_key, ESP32_API_KEY):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    username = data.get('username')
    new_password = data.get('password')

    if not username or not new_password:
        return jsonify({"error": "username and password required"}), 400

    if username not in PASSWORD_STORE:
        return jsonify({"error": "Unknown user"}), 404

    PASSWORD_STORE[username]['password'] = new_password
    PASSWORD_STORE[username]['last_updated'] = time.time()

    print(f"[ESP32] Password updated for '{username}' at {time.strftime('%H:%M:%S')}")
    return jsonify({"status": "ok", "user": username, "updated_at": time.time()}), 200


# ─── Token Display Page (for presentation / demo) ────────────────────────────
# Open http://localhost:5000/token in a browser to see live passwords
# No authentication required — for demo use only
@app.route('/token')
def token_display():
    passwords = {
        user: data['password']
        for user, data in PASSWORD_STORE.items()
    }
    return render_template('token_display.html', passwords=passwords)


# ─── API: Live password poll (used by token display page) ────────────────────
@app.route('/api/passwords')
def api_passwords():
    return jsonify({
        user: data['password']
        for user, data in PASSWORD_STORE.items()
    })


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)