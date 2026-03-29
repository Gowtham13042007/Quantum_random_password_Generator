# 🏦 Apex Bank — Hardware Token Banking Demo

A full-stack mock banking application featuring **ESP32-based hardware security tokens** that generate cryptographically random, rotating passwords using analog noise. Built to demonstrate embedded systems integration with a web backend.

---

## 📌 Project Overview

Apex Bank simulates a real-world hardware token authentication system (like RSA SecurID). An ESP32 microcontroller continuously samples analog noise from an ADC pin, applies Von Neumann debiasing to produce unbiased random bits, and generates a new 16-character password every 2 minutes. This password is pushed over WiFi to a Flask server, which uses it as the login credential for a mock banking dashboard.

```
[ESP32 Hardware Token]
  → Samples ADC noise (PIN 34)
  → Von Neumann debiasing
  → Generates 16-char password
  → POST /api/update-password (every 2 min)

[Flask Server]
  → Stores rotating password
  → Validates login via HMAC compare
  → Serves banking dashboard
  → /token page shows live password (for demo)
```

---

## 🗂️ Project Structure

```
apex-bank/
├── app.py                  # Flask backend — routes, auth, ESP32 API
├── templates/
│   ├── login.html          # Login page with hardware token UI
│   ├── dashboard.html      # Banking dashboard (protected)
│   └── token_display.html  # Live token viewer (demo/presentation)
├── firmware/
│   └── apex_token.ino      # ESP32 Arduino firmware
└── README.md
```

---

## ⚙️ How It Works

### 1. ESP32 — True Random Password Generation

The firmware uses **analog noise** from an unconnected or floating ADC pin (GPIO 34) as an entropy source.

**Pipeline:**
1. Reads 8000 ADC samples over 2 seconds
2. Extracts LSB from each sample after XOR mixing (`adcVal ^ (adcVal >> 1)`)
3. Applies **Von Neumann debiasing** to eliminate bit-frequency bias
4. Converts every 8 debiased bits into a printable ASCII character
5. Produces a 16-character password (requires 128 debiased bits)

**Error conditions handled:**
- `ERR_STATIC_SIGNAL` — ADC reading stuck (>300 identical consecutive values)
- `ERR_LOW_ENTROPY` — Insufficient debiased bits collected after sampling

**Transmission:**
- Connects to WiFi and POSTs the password to the Flask server
- Authenticated via a shared API key in the HTTP header (`X-API-Key`)
- Repeats every **120 seconds**

---

### 2. Flask Server — Auth & Dashboard

**Key routes:**

| Route | Method | Description |
|---|---|---|
| `/` | GET | Dashboard (session-protected) |
| `/login` | GET, POST | Login with rotating token password |
| `/logout` | GET | Clears session |
| `/api/update-password` | POST | ESP32 endpoint — updates password store |
| `/token` | GET | Live token display page (demo use) |
| `/api/passwords` | GET | JSON endpoint polled by token display page |

**Authentication flow:**
- Login compares submitted password against stored token using `hmac.compare_digest()` (timing-safe)
- ESP32 API endpoint is protected by a shared `X-API-Key` header

---

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.8+
- Flask
- Arduino IDE with ESP32 board support
- ArduinoJson library (`v6+`)

### Server Setup

```bash
# Clone the repo
git clone https://github.com/yourname/apex-bank.git
cd apex-bank

# Install dependencies
pip install flask

# Run the server
python app.py
```

Server runs at `http://0.0.0.0:5000`

---

### ESP32 Firmware Setup

1. Open `firmware/apex_token.ino` in Arduino IDE
2. Update WiFi credentials and server IP:

```cpp
const char* ssid          = "YOUR_WIFI_SSID";
const char* wifi_password = "YOUR_WIFI_PASSWORD";
const char* serverUrl     = "http://<YOUR_SERVER_IP>:5000/api/update-password";
```

3. Install **ArduinoJson** via Library Manager
4. Select board: `ESP32 Dev Module`
5. Flash and open Serial Monitor at **115200 baud**

> ⚠️ GPIO 34 is input-only on most ESP32 boards. Leave it floating or connect it to a noise source for maximum entropy.

---

## 🔐 Security Design

| Component | Mechanism |
|---|---|
| Password generation | True random — ADC analog noise + Von Neumann debiasing |
| Password rotation | Every 2 minutes, pushed by hardware device |
| ESP32 → Server auth | Shared API key in HTTP header |
| Login validation | `hmac.compare_digest()` — timing-safe comparison |
| Session | Flask server-side session, non-permanent |

**Not for production use.** This is a portfolio/demo project. In a real deployment you would use HTTPS, store hashed secrets, and not expose `/token` or `/api/passwords` without authentication.

---

## 🖥️ Demo Pages

| URL | Description |
|---|---|
| `http://localhost:5000/login` | Login page — enter username + current token |
| `http://localhost:5000/` | Banking dashboard (after login) |
| `http://localhost:5000/token` | Live token display — open this on a second screen during demos |

**Default test credential:**
- Username: ``user
- Password: shown on `/token` page (updated by ESP32)

---

## 🧪 Testing Without ESP32

You can manually push a password to the server using `curl`:

```bash
curl -X POST http://localhost:5000/api/update-password \
  -H "Content-Type: application/json" \
  -H "X-API-Key: ESP32-APEX-SECRET-KEY-abc123" \
  -d '{"username": "user", "password": "TEST-PASSWORD-1234"}'
```

Then log in at `/login` with `user` / `TEST-PASSWORD-1234`.

---

## 📡 ESP32 Serial Output

```
[SYSTEM] Connecting to WiFi....
[SYSTEM] WiFi Connected.
[SYSTEM] Generated Password: N>5`H[P;7\fBqT#1
[HTTP] Response Code: 200
```

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| Microcontroller | ESP32 (Arduino framework) |
| Firmware language | C++ (Arduino) |
| Backend | Python / Flask |
| Frontend | HTML, CSS, Vanilla JS |
| Templating | Jinja2 |
| Fonts | DM Serif Display, DM Sans, JetBrains Mono |

---

## 💡 Key Concepts Demonstrated

- **True random number generation** from analog hardware noise
- **Von Neumann debiasing** for unbiased bit extraction
- **ESP32 WiFi HTTP client** — POSTing JSON to a REST API
- **HMAC-safe password comparison** to prevent timing attacks
- **Hardware-software co-design** — embedded device drives web auth state
- **Flask session management** and protected routes

---

## 📄 License

MIT License — free to use for learning and portfolio purposes.

---

*Built as a portfolio project demonstrating ESP32 embedded systems integration with a web backend.*
