import sqlite3
import os
from datetime import datetime
from flask import Flask, request, render_template_string, session, redirect, url_for, flash

app = Flask(__name__)
# Secret key is required for session management and flashing messages
app.secret_key = "tamilnadu_heritage_super_secret_key"

# --- 1. Database Initialization ---
DB_FILE = 'resort_tamilnadu.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS rooms 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price INTEGER, desc TEXT, capacity INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookings 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, room_id INTEGER, guest_name TEXT, 
                  guest_email TEXT, checkin TEXT, checkout TEXT, total_price INTEGER, nights INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS subscribers 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE)''')
    
    # Seed the database with Tamil Nadu rooms if empty
    c.execute("SELECT COUNT(*) FROM rooms")
    if c.fetchone()[0] == 0:
        rooms_data = [
            ("Chola Imperial Suite", 30000, "Spacious suite with a private temple-style courtyard, antique teakwood furniture, and panoramic views of the Bay of Bengal.", 4),
            ("Nayakar Royal Deluxe", 15000, "Elegant room featuring authentic Chettinad pillars, woven silk drapery, and a private balcony overlooking the palm groves.", 2),
            ("Coromandel Heritage Room", 8500, "Classic comfort infused with local art, featuring a modern en-suite and easy access to the Ayurvedic spa.", 2),
            ("Pallava Family Villa", 25000, "A secluded two-bedroom villa with a private plunge pool, perfect for families seeking a serene coastal retreat.", 6)
        ]
        c.executemany("INSERT INTO rooms (name, price, desc, capacity) VALUES (?, ?, ?, ?)", rooms_data)
        conn.commit()
    conn.close()

# Initialize DB on startup
init_db()

# --- 2. Master HTML Template ---
# This template uses conditional rendering ({% if page == '...' %}) to serve different pages
MASTER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Bay Retreat | Tamil Nadu</title>
    <style>
        :root {
            --primary: #00334e;      /* Deep Ocean Blue */
            --accent: #d4af37;       /* Temple Gold */
            --bg-light: #faf9f6;     /* Sand Cream */
            --text-dark: #222;
            --text-light: #fff;
        }
        body { font-family: 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 0; background-color: var(--bg-light); color: var(--text-dark); line-height: 1.6; }
        
        /* Navigation & Header */
        header { background: var(--primary); color: var(--text-light); padding: 1.5rem 2rem; display: flex; justify-content: space-between; align-items: center; }
        header h1 { margin: 0; font-size: 1.8rem; font-weight: 300; letter-spacing: 2px; }
        .nav-links a { color: var(--text-light); text-decoration: none; margin-left: 20px; font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }
        
        /* Hero Section */
        .hero { background: linear-gradient(rgba(0,51,78,0.7), rgba(0,51,78,0.7)), url('https://images.unsplash.com/photo-1585501869372-df7eb58dbdb9?auto=format&fit=crop&w=1920&q=80') center/cover; color: white; padding: 100px 20px; text-align: center; }
        .hero h2 { font-size: 3.5rem; margin-bottom: 10px; font-family: 'Georgia', serif; font-weight: normal; }
        .hero p { font-size: 1.2rem; letter-spacing: 2px; margin-bottom: 40px; }
        
        /* Search Bar */
        .search-bar { background: white; padding: 20px; border-radius: 4px; display: inline-flex; gap: 15px; flex-wrap: wrap; justify-content: center; align-items: center; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .search-bar input, .search-bar select { padding: 15px; border: 1px solid #ddd; border-radius: 2px; font-size: 1rem; outline: none; }
        .btn { background: var(--accent); color: var(--primary); border: none; padding: 15px 30px; font-size: 1rem; font-weight: bold; text-transform: uppercase; cursor: pointer; transition: 0.3s; text-decoration: none; display: inline-block; }
        .btn:hover { background: #b5952f; color: white; }
        
        /* Alerts / Flashes */
        .flashes { max-width: 800px; margin: 20px auto; list-style: none; padding: 0; }
        .flashes li { padding: 15px; background: #d4edda; color: #155724; border: 1px solid #c3e6cb; border-radius: 4px; text-align: center; margin-bottom: 10px; font-weight: bold; }
        .flashes li.error { background: #f8d7da; color: #721c24; border-color: #f5c6cb; }

        /* Container & Grids */
        .container { max-width: 1200px; margin: 40px auto; padding: 0 20px; }
        .section-title { text-align: center; font-family: 'Georgia', serif; color: var(--primary); font-size: 2.5rem; margin-bottom: 40px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 30px; }
        
        /* Cards */
        .card { background: white; padding: 30px; border-radius: 4px; box-shadow: 0 5px 15px rgba(0,0,0,0.05); text-align: center; border-bottom: 3px solid var(--accent); transition: transform 0.3s; }
        .card:hover { transform: translateY(-5px); }
        .card h3 { color: var(--primary); font-family: 'Georgia', serif; font-size: 1.5rem; margin-top: 0; }
        .price { font-size: 1.8rem; font-weight: bold; color: var(--primary); margin: 15px 0; }
        .price span { font-size: 0.9rem; color: #777; font-weight: normal; }
        
        /* Stats Section */
        .stats { display: flex; justify-content: space-around; background: white; padding: 40px 20px; border-top: 1px solid #eee; border-bottom: 1px solid #eee; flex-wrap: wrap; text-align: center; }
        .stat-item h4 { font-size: 2.5rem; color: var(--primary); margin: 0; font-family: 'Georgia', serif; }
        .stat-item p { text-transform: uppercase; letter-spacing: 1px; font-size: 0.8rem; color: #666; margin-top: 5px; }

        /* Forms */
        .booking-form { max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 4px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 20px; text-align: left; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: bold; color: var(--primary); }
        .form-group input { width: 100%; padding: 12px; border: 1px solid #ccc; box-sizing: border-box; }
        .summary-box { background: var(--bg-light); padding: 20px; border-left: 4px solid var(--accent); margin-bottom: 20px; }

        /* Footer */
        footer { background: var(--primary); color: white; padding: 60px 20px 20px; text-align: center; margin-top: 60px; }
        .footer-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 40px; max-width: 1200px; margin: 0 auto; text-align: left; }
        .footer-col h4 { color: var(--accent); font-family: 'Georgia', serif; font-size: 1.2rem; }
        .footer-col input[type="email"] { padding: 12px; width: calc(100% - 110px); border: none; }
        .footer-col button { padding: 12px 20px; background: var(--accent); border: none; color: var(--primary); font-weight: bold; cursor: pointer; }
        .copyright { text-align: center; border-top: 1px solid rgba(255,255,255,0.1); margin-top: 40px; padding-top: 20px; font-size: 0.9rem; color: #aaa; }
    </style>
</head>
<body>

    <header>
        <h1>THE BAY RETREAT</h1>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="/#accommodations">Resorts</a>
            <a href="#">Ayurveda</a>
            <a href="#">Dining</a>
        </div>
    </header>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <ul class="flashes">
        {% for category, message in messages %}
          <li class="{{ category }}">{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}

    <!-- PAGE: HOME -->
    {% if page == 'home' %}
    <div class="hero">
        <h2>Let's Relax & Unwind By The Sea</h2>
        <p>DISCOVER THE SOUL OF TAMIL NADU</p>
        
        <form class="search-bar" action="/search" method="POST">
            <select name="location" required>
                <option value="" disabled selected>Select Location in Tamil Nadu</option>
                <option value="Chennai">Chennai Azure</option>
                <option value="Mahabalipuram">Mahabalipuram Sands</option>
                <option value="Kanyakumari">Kanyakumari Cape</option>
            </select>
            <input type="date" name="checkin" required title="Check-in">
            <input type="date" name="checkout" required title="Check-out">
            <button type="submit" class="btn">Search</button>
        </form>
    </div>

    <div class="stats">
        <div class="stat-item"><h4>12M+</h4><p>Happy Guests</p></div>
        <div class="stat-item"><h4>22</h4><p>Heritage Experiences</p></div>
        <div class="stat-item"><h4>14</h4><p>Culinary Awards</p></div>
        <div class="stat-item"><h4>17</h4><p>Service Awards</p></div>
    </div>

    <div class="container" id="accommodations">
        <h2 class="section-title">Experience Elegant Rooms & Culinary Delights</h2>
        <p style="text-align: center; max-width: 700px; margin: 0 auto 40px; color: #666;">
            Immerse yourself in authentic South Indian hospitality. Our spaces are designed with ancient Chettinad architecture principles to let hospitality embrace you.
        </p>
        
        <div class="grid">
            {% for room in rooms %}
            <div class="card">
                <h3>{{ room.name }}</h3>
                <p>{{ room.desc }}</p>
                <p><strong>Capacity:</strong> Up to {{ room.capacity }} guests</p>
                <div class="price">₹{{ "{:,}".format(room.price) }} <span>/ night</span></div>
                <!-- Redirects to search to force date selection first -->
                <a href="#accommodations" onclick="alert('Please select your dates in the search bar above to book.'); window.scrollTo(0,0);" class="btn" style="padding: 10px 20px; font-size: 0.9rem;">Check Availability</a>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- PAGE: RESULTS -->
    {% elif page == 'results' %}
    <div class="container">
        <div class="summary-box">
            <h2 style="margin-top:0; color: var(--primary);">Availability for {{ session['location'] }}</h2>
            <p><strong>Check-in:</strong> {{ session['checkin'] }} &nbsp;&nbsp;|&nbsp;&nbsp; <strong>Check-out:</strong> {{ session['checkout'] }}</p>
            <p><strong>Duration of stay:</strong> {{ session['nights'] }} night(s)</p>
            <a href="/" style="color: var(--primary); font-weight: bold;">← Change Search</a>
        </div>

        <h2 class="section-title">Select Your Heritage Stay</h2>
        <div class="grid">
            {% for room in rooms %}
            <div class="card">
                <h3>{{ room.name }}</h3>
                <p>{{ room.desc }}</p>
                <div class="price">
                    ₹{{ "{:,}".format(room.price) }} <span>/ night</span><br>
                    <span style="color: var(--primary); font-size: 1.1rem; font-weight: bold;">Total: ₹{{ "{:,}".format(room.price * session['nights']) }}</span>
                </div>
                <a href="/checkout/{{ room.id }}" class="btn">Select Room</a>
            </div>
            {% endfor %}
        </div>
    </div>

    <!-- PAGE: CHECKOUT -->
    {% elif page == 'checkout' %}
    <div class="container">
        <h2 class="section-title">Complete Your Booking</h2>
        <div class="booking-form">
            <div class="summary-box">
                <h3 style="margin-top:0; color: var(--primary);">{{ room.name }}</h3>
                <p><strong>Location:</strong> {{ session['location'] }}</p>
                <p><strong>Dates:</strong> {{ session['checkin'] }} to {{ session['checkout'] }} ({{ session['nights'] }} nights)</p>
                <h2 style="color: var(--primary); border-top: 1px solid #ddd; padding-top: 15px; margin-bottom: 0;">Total Amount: ₹{{ "{:,}".format(total_price) }}</h2>
            </div>

            <form action="/confirm/{{ room.id }}" method="POST">
                <div class="form-group">
                    <label>Full Name</label>
                    <input type="text" name="guest_name" required placeholder="E.g. Vikram Sharma">
                </div>
                <div class="form-group">
                    <label>Email Address</label>
                    <input type="email" name="guest_email" required placeholder="vikram@example.com">
                </div>
                <button type="submit" class="btn" style="width: 100%;">Confirm Booking & Pay at Resort</button>
            </form>
        </div>
    </div>
    {% endif %}

    <footer>
        <div class="footer-grid">
            <div class="footer-col">
                <h4>About Us</h4>
                <p>Rooted in the rich cultural tapestry of Tamil Nadu, we offer unparalleled luxury intertwined with ancient heritage.</p>
            </div>
            <div class="footer-col">
                <h4>Contact</h4>
                <p>East Coast Road, Chennai<br>Tamil Nadu, India 600119<br>+91 44 2345 6789</p>
            </div>
            <div class="footer-col">
                <h4>Newsletter Sign Up</h4>
                <p>Exclusive offers on Ayurveda & stays.</p>
                <form action="/subscribe" method="POST" style="display: flex;">
                    <input type="email" name="email" placeholder="Email Address" required>
                    <button type="submit">→</button>
                </form>
            </div>
        </div>
        <div class="copyright">
            &copy; 2024 The Bay Retreat Tamil Nadu. All rights reserved. Code written by NIRANJAN.
        </div>
    </footer>
</body>
</html>
"""

# --- 3. Routing and Application Logic ---

@app.route("/")
def index():
    # Fetch all rooms from DB to display on home page
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    conn.close()
    return render_template_string(MASTER_TEMPLATE, page='home', rooms=rooms)

@app.route("/search", methods=["POST"])
def search():
    location = request.form.get("location")
    checkin_str = request.form.get("checkin")
    checkout_str = request.form.get("checkout")

    # Date Validation and Night Calculation
    try:
        checkin_date = datetime.strptime(checkin_str, "%Y-%m-%d")
        checkout_date = datetime.strptime(checkout_str, "%Y-%m-%d")
        
        nights = (checkout_date - checkin_date).days
        if nights <= 0:
            flash("Check-out date must be after check-in date.", "error")
            return redirect(url_for('index'))
            
        # Store search parameters in the user's session
        session['location'] = location
        session['checkin'] = checkin_str
        session['checkout'] = checkout_str
        session['nights'] = nights
        
        return redirect(url_for('results'))
    except ValueError:
        flash("Invalid dates selected.", "error")
        return redirect(url_for('index'))

@app.route("/results")
def results():
    # Ensure user has searched first
    if 'nights' not in session:
        return redirect(url_for('index'))
        
    conn = get_db_connection()
    rooms = conn.execute('SELECT * FROM rooms').fetchall()
    conn.close()
    return render_template_string(MASTER_TEMPLATE, page='results', rooms=rooms)

@app.route("/checkout/<int:room_id>")
def checkout(room_id):
    if 'nights' not in session:
        return redirect(url_for('index'))

    conn = get_db_connection()
    room = conn.execute('SELECT * FROM rooms WHERE id = ?', (room_id,)).fetchone()
    conn.close()

    if room is None:
        flash("Room not found.", "error")
        return redirect(url_for('results'))

    total_price = room['price'] * session['nights']
    return render_template_string(MASTER_TEMPLATE, page='checkout', room=room, total_price=total_price)

@app.route("/confirm/<int:room_id>", methods=["POST"])
def confirm(room_id):
    if 'nights' not in session:
        return redirect(url_for('index'))

    guest_name = request.form.get("guest_name")
    guest_email = request.form.get("guest_email")
    
    conn = get_db_connection()
    room = conn.execute('SELECT * FROM rooms WHERE id = ?', (room_id,)).fetchone()
    
    if room:
        total_price = room['price'] * session['nights']
        
        # Insert booking into database
        conn.execute('''INSERT INTO bookings (room_id, guest_name, guest_email, checkin, checkout, total_price, nights) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)''',
                     (room_id, guest_name, guest_email, session['checkin'], session['checkout'], total_price, session['nights']))
        conn.commit()
        conn.close()
        
        # Clear session after successful booking
        session.clear()
        
        flash(f"Booking Confirmed! Thank you, {guest_name}. Your reservation for the {room['name']} is secure. Total payable at resort: ₹{total_price:,}.", "success")
        return redirect(url_for('index'))
    else:
        conn.close()
        flash("An error occurred processing your booking.", "error")
        return redirect(url_for('index'))

@app.route("/subscribe", methods=["POST"])
def subscribe():
    email = request.form.get("email")
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
        conn.commit()
        flash(f"Success! {email} has been subscribed to our Tamil Nadu heritage newsletter.", "success")
    except sqlite3.IntegrityError:
        flash(f"The email {email} is already subscribed.", "error")
    finally:
        conn.close()
        
    return redirect(url_for('index'))

# --- 4. Run Application ---
if __name__ == "__main__":
    print("Database connected. Server starting...")
    print("Open http://127.0.0.1:5000 in your web browser to test.")
    app.run(debug=True)