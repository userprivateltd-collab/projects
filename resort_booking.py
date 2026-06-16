#!/usr/bin/env python3
"""
AquaLux Resort — Full booking website in a single Python file.
Run:  python3 resort_booking.py
Then open:  http://localhost:8080
No external dependencies required.
"""

import http.server
import json
import sqlite3
import urllib.parse
import os
import sys
from datetime import datetime, date

# ──────────────────────────────────────────────
# DATABASE
# ──────────────────────────────────────────────
DB_PATH = "resort_bookings.db"

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT NOT NULL,
            phone       TEXT NOT NULL,
            room_type   TEXT NOT NULL,
            check_in    TEXT NOT NULL,
            check_out   TEXT NOT NULL,
            guests      INTEGER NOT NULL,
            nights      INTEGER NOT NULL,
            total_price REAL NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)
    con.commit()
    con.close()

def save_booking(data):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("""
        INSERT INTO bookings
            (name, email, phone, room_type, check_in, check_out,
             guests, nights, total_price, created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
    """, (
        data["name"], data["email"], data["phone"],
        data["room_type"], data["check_in"], data["check_out"],
        int(data["guests"]), int(data["nights"]),
        float(data["total_price"]),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    booking_id = cur.lastrowid
    con.commit()
    con.close()
    return booking_id

def get_all_bookings():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM bookings ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows

# ──────────────────────────────────────────────
# HTML PAGE
# ──────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>AquaLux Resort &amp; Spa</title>
<link rel="preconnect" href="https://fonts.googleapis.com"/>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;600;700&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
/* ── RESET & BASE ── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{
  --ocean:#0a4d6e;--ocean-light:#1a7fa0;--sand:#f0ebe0;
  --gold:#c9a96e;--gold-light:#e8d5a3;--white:#fff;
  --text:#1a1a2e;--muted:#6b7280;--surface:#f8f6f1;
  --radius:12px;--shadow:0 8px 32px rgba(10,77,110,.12);
}
html{scroll-behavior:smooth}
body{font-family:'Jost',sans-serif;color:var(--text);background:var(--white);overflow-x:hidden}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}
h1,h2,h3,h4{font-family:'Cormorant Garamond',serif;font-weight:600}

/* ── NAV ── */
nav{
  position:fixed;top:0;left:0;right:0;z-index:999;
  display:flex;align-items:center;justify-content:space-between;
  padding:1.2rem 5%;
  transition:all .4s ease;
}
nav.scrolled{background:rgba(10,77,110,.96);backdrop-filter:blur(8px);padding:.9rem 5%;box-shadow:0 2px 20px rgba(0,0,0,.2)}
.nav-logo{font-family:'Cormorant Garamond',serif;font-size:1.6rem;font-weight:700;color:var(--white);letter-spacing:.04em}
.nav-logo span{color:var(--gold)}
.nav-links{display:flex;gap:2rem;list-style:none}
.nav-links a{color:rgba(255,255,255,.88);font-size:.88rem;letter-spacing:.08em;text-transform:uppercase;font-weight:500;transition:color .2s}
.nav-links a:hover{color:var(--gold)}
.nav-cta{background:var(--gold);color:var(--white)!important;padding:.5rem 1.2rem;border-radius:50px;transition:background .2s!important}
.nav-cta:hover{background:#b8894e!important}
.hamburger{display:none;flex-direction:column;gap:5px;cursor:pointer}
.hamburger span{width:24px;height:2px;background:var(--white);border-radius:2px;transition:.3s}

/* ── HERO ── */
#hero{
  height:100vh;min-height:600px;position:relative;display:flex;align-items:center;
  background:linear-gradient(135deg,#041e2e 0%,#0a4d6e 45%,#0d6a8a 70%,#1a9ab5 100%);
  overflow:hidden;
}
.hero-waves{position:absolute;bottom:0;left:0;right:0;opacity:.18}
.hero-circles{position:absolute;top:-80px;right:-80px;width:500px;height:500px;
  border-radius:50%;background:radial-gradient(circle,rgba(201,169,110,.25),transparent 70%)}
.hero-circles2{position:absolute;bottom:-120px;left:-60px;width:400px;height:400px;
  border-radius:50%;background:radial-gradient(circle,rgba(26,127,160,.3),transparent 70%)}
.hero-content{position:relative;z-index:2;max-width:1200px;margin:0 auto;padding:0 5%;width:100%}
.hero-eyebrow{display:inline-flex;align-items:center;gap:.5rem;color:var(--gold-light);
  font-size:.78rem;letter-spacing:.25em;text-transform:uppercase;font-weight:500;margin-bottom:1.2rem}
.hero-eyebrow::before{content:'';width:30px;height:1px;background:var(--gold)}
.hero-title{font-size:clamp(3rem,7vw,5.5rem);color:var(--white);line-height:1.08;
  font-weight:300;margin-bottom:1.5rem}
.hero-title strong{font-weight:700;display:block;color:var(--gold-light)}
.hero-sub{color:rgba(255,255,255,.72);font-size:1.05rem;max-width:480px;line-height:1.7;margin-bottom:2.5rem}
.hero-btns{display:flex;gap:1rem;flex-wrap:wrap}
.btn-primary{background:var(--gold);color:var(--white);padding:.9rem 2.2rem;
  border-radius:50px;font-weight:600;font-size:.9rem;letter-spacing:.06em;
  transition:all .25s;border:2px solid var(--gold);display:inline-block}
.btn-primary:hover{background:transparent;color:var(--gold)}
.btn-outline{border:2px solid rgba(255,255,255,.5);color:var(--white);
  padding:.9rem 2.2rem;border-radius:50px;font-weight:500;font-size:.9rem;
  letter-spacing:.06em;transition:all .25s;display:inline-block}
.btn-outline:hover{border-color:var(--white);background:rgba(255,255,255,.1)}
.hero-stats{display:flex;gap:3rem;margin-top:3.5rem;padding-top:2rem;border-top:1px solid rgba(255,255,255,.12)}
.stat-item .num{font-family:'Cormorant Garamond',serif;font-size:2.4rem;color:var(--gold-light);font-weight:700;line-height:1}
.stat-item .lbl{font-size:.75rem;color:rgba(255,255,255,.6);letter-spacing:.1em;text-transform:uppercase;margin-top:.25rem}

/* ── SEARCH BAR ── */
#search-bar{
  background:var(--white);border-radius:var(--radius);
  box-shadow:0 20px 60px rgba(10,77,110,.18);
  padding:2rem 2.5rem;max-width:1000px;margin:-60px auto 0;
  position:relative;z-index:10;
}
.search-grid{display:grid;grid-template-columns:repeat(4,1fr) auto;gap:1rem;align-items:end}
.search-group label{font-size:.72rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--ocean);font-weight:600;display:block;margin-bottom:.4rem}
.search-group input,.search-group select{
  width:100%;border:1.5px solid #e5e0d5;border-radius:8px;
  padding:.65rem .9rem;font-family:'Jost',sans-serif;font-size:.92rem;
  color:var(--text);background:var(--surface);transition:border-color .2s;outline:none
}
.search-group input:focus,.search-group select:focus{border-color:var(--ocean)}
.search-btn{
  background:var(--ocean);color:var(--white);border:none;
  border-radius:8px;padding:.7rem 1.6rem;font-family:'Jost',sans-serif;
  font-size:.9rem;font-weight:600;cursor:pointer;white-space:nowrap;
  transition:background .2s;letter-spacing:.04em
}
.search-btn:hover{background:var(--ocean-light)}

/* ── SECTIONS ── */
.section{padding:6rem 5%}
.section-inner{max-width:1200px;margin:0 auto}
.section-label{font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;
  color:var(--gold);font-weight:600;margin-bottom:.75rem;display:flex;align-items:center;gap:.6rem}
.section-label::after{content:'';flex:1;max-width:40px;height:1px;background:var(--gold)}
.section-title{font-size:clamp(2rem,4vw,3rem);margin-bottom:1.2rem;line-height:1.15}
.section-sub{color:var(--muted);max-width:520px;line-height:1.75;font-size:.97rem}

/* ── ROOMS ── */
#rooms{background:var(--surface)}
.rooms-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:1.8rem;margin-top:3rem}
.room-card{
  background:var(--white);border-radius:var(--radius);overflow:hidden;
  box-shadow:var(--shadow);transition:transform .3s,box-shadow .3s;cursor:pointer
}
.room-card:hover{transform:translateY(-6px);box-shadow:0 20px 50px rgba(10,77,110,.18)}
.room-img{height:220px;position:relative;overflow:hidden}
.room-img-bg{width:100%;height:100%;transition:transform .4s}
.room-card:hover .room-img-bg{transform:scale(1.06)}
.room-badge{
  position:absolute;top:1rem;right:1rem;background:var(--gold);color:var(--white);
  font-size:.7rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  padding:.3rem .8rem;border-radius:50px
}
.room-body{padding:1.5rem}
.room-name{font-size:1.4rem;margin-bottom:.3rem}
.room-desc{color:var(--muted);font-size:.88rem;line-height:1.65;margin-bottom:1rem}
.room-features{display:flex;gap:1rem;flex-wrap:wrap;margin-bottom:1.2rem}
.room-feature{font-size:.75rem;color:var(--ocean);background:rgba(10,77,110,.07);
  padding:.25rem .7rem;border-radius:50px;font-weight:500}
.room-footer{display:flex;align-items:center;justify-content:space-between;
  padding-top:1rem;border-top:1px solid #f0ebe0}
.room-price .amt{font-family:'Cormorant Garamond',serif;font-size:1.8rem;font-weight:700;color:var(--ocean)}
.room-price .per{font-size:.75rem;color:var(--muted)}
.btn-book{background:var(--ocean);color:var(--white);border:none;
  padding:.55rem 1.3rem;border-radius:50px;font-family:'Jost',sans-serif;
  font-size:.82rem;font-weight:600;cursor:pointer;transition:background .2s;letter-spacing:.04em}
.btn-book:hover{background:var(--ocean-light)}

/* Room visual backgrounds */
.bg-ocean{background:linear-gradient(160deg,#041e2e,#0a4d6e,#1a9ab5)}
.bg-jungle{background:linear-gradient(160deg,#1a3a1a,#2d6a2d,#4a9a4a)}
.bg-sunset{background:linear-gradient(160deg,#4a1a1a,#8a3a1a,#c97a2a)}
.bg-sky{background:linear-gradient(160deg,#1a2a4a,#2a4a8a,#4a7abf)}
.bg-villa{background:linear-gradient(160deg,#3a2a1a,#7a5a2a,#b08030)}
.bg-beach{background:linear-gradient(160deg,#0a3a3a,#1a6a6a,#2a9a8a)}
.room-img-dec{width:100%;height:100%;display:flex;align-items:center;justify-content:center;
  font-size:4rem;opacity:.35;user-select:none}

/* ── AMENITIES ── */
#amenities{background:var(--white)}
.amenities-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1.5rem;margin-top:3rem}
.amenity-card{text-align:center;padding:2rem 1rem}
.amenity-icon{width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,rgba(10,77,110,.1),rgba(26,127,160,.15));
  display:flex;align-items:center;justify-content:center;margin:0 auto 1rem;font-size:1.6rem}
.amenity-name{font-size:1rem;font-family:'Cormorant Garamond',serif;font-weight:600;margin-bottom:.3rem}
.amenity-desc{font-size:.8rem;color:var(--muted);line-height:1.5}

/* ── GALLERY ── */
#gallery{background:var(--ocean);padding:5rem 5%}
.gallery-title{color:var(--white);font-size:clamp(2rem,4vw,3rem);text-align:center;margin-bottom:.5rem}
.gallery-sub{color:rgba(255,255,255,.6);text-align:center;margin-bottom:2.5rem;font-size:.95rem}
.gallery-grid{display:grid;grid-template-columns:repeat(4,1fr);grid-template-rows:200px 200px;gap:1rem;max-width:1200px;margin:0 auto}
.g-item{border-radius:var(--radius);overflow:hidden;position:relative}
.g-item:first-child{grid-column:span 2;grid-row:span 2}
.g-item:nth-child(4){grid-column:span 2}
.g-img{width:100%;height:100%;transition:transform .4s}
.g-item:hover .g-img{transform:scale(1.07)}
.bg-g1{background:linear-gradient(135deg,#041e2e,#1a7fa0)}
.bg-g2{background:linear-gradient(135deg,#0d3d1a,#2a8a4a)}
.bg-g3{background:linear-gradient(135deg,#3a1a05,#c97a2a)}
.bg-g4{background:linear-gradient(135deg,#1a0a3a,#5a2a9a)}
.bg-g5{background:linear-gradient(135deg,#3a2a0a,#b08030)}
.g-dec{width:100%;height:100%;display:flex;align-items:center;justify-content:center;font-size:3.5rem;opacity:.3}

/* ── BOOKING FORM ── */
#booking{background:var(--surface);padding:6rem 5%}
.booking-inner{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:4rem;align-items:start}
.booking-info h2{font-size:clamp(2rem,3.5vw,2.8rem);margin-bottom:1rem}
.booking-info p{color:var(--muted);line-height:1.75;margin-bottom:1.5rem}
.booking-highlights{display:flex;flex-direction:column;gap:.8rem;margin-top:1.5rem}
.b-highlight{display:flex;align-items:center;gap:.75rem;font-size:.9rem;color:var(--muted)}
.b-highlight::before{content:'✓';width:24px;height:24px;background:var(--gold);color:var(--white);
  border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.7rem;
  font-weight:700;flex-shrink:0;line-height:24px;text-align:center}
.booking-form{background:var(--white);border-radius:var(--radius);
  padding:2.5rem;box-shadow:var(--shadow)}
.booking-form h3{font-size:1.6rem;margin-bottom:1.5rem;color:var(--ocean)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:1rem}
.form-group{margin-bottom:1rem}
.form-group label{font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;
  color:var(--ocean);font-weight:600;display:block;margin-bottom:.4rem}
.form-group input,.form-group select,.form-group textarea{
  width:100%;border:1.5px solid #e5e0d5;border-radius:8px;
  padding:.7rem 1rem;font-family:'Jost',sans-serif;font-size:.92rem;
  color:var(--text);background:var(--surface);transition:border-color .2s;outline:none
}
.form-group input:focus,.form-group select:focus,.form-group textarea:focus{border-color:var(--ocean)}
.form-group textarea{resize:vertical;min-height:80px}
.price-summary{background:linear-gradient(135deg,var(--ocean),var(--ocean-light));
  border-radius:8px;padding:1.2rem;margin:1.2rem 0;color:var(--white)}
.price-row{display:flex;justify-content:space-between;font-size:.88rem;margin-bottom:.4rem;opacity:.85}
.price-total{display:flex;justify-content:space-between;font-size:1.1rem;
  font-weight:700;border-top:1px solid rgba(255,255,255,.25);padding-top:.7rem;margin-top:.4rem}
.submit-btn{width:100%;background:var(--gold);color:var(--white);border:none;
  border-radius:50px;padding:1rem;font-family:'Jost',sans-serif;font-size:1rem;
  font-weight:700;cursor:pointer;transition:background .25s,transform .15s;letter-spacing:.06em}
.submit-btn:hover{background:#b8894e;transform:translateY(-2px)}
.submit-btn:active{transform:translateY(0)}
#form-msg{display:none;padding:.9rem;border-radius:8px;margin-top:.8rem;font-size:.9rem;text-align:center}
#form-msg.success{background:#d1fae5;color:#065f46;display:block}
#form-msg.error{background:#fee2e2;color:#991b1b;display:block}

/* ── TESTIMONIALS ── */
#testimonials{background:var(--white);padding:6rem 5%}
.testimonials-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.8rem;margin-top:3rem}
.t-card{background:var(--surface);border-radius:var(--radius);padding:2rem;
  border-left:3px solid var(--gold)}
.t-stars{color:var(--gold);font-size:1rem;margin-bottom:.8rem;letter-spacing:.1em}
.t-text{color:var(--muted);font-size:.92rem;line-height:1.75;margin-bottom:1.2rem;font-style:italic}
.t-author{display:flex;align-items:center;gap:.75rem}
.t-avatar{width:40px;height:40px;border-radius:50%;display:flex;align-items:center;
  justify-content:center;font-size:1.1rem;font-weight:700;color:var(--white);flex-shrink:0}
.t-name{font-weight:600;font-size:.9rem}
.t-loc{font-size:.78rem;color:var(--muted)}

/* ── CONTACT ── */
#contact{background:linear-gradient(160deg,#041e2e,#0a4d6e);padding:5rem 5%}
.contact-inner{max-width:1100px;margin:0 auto;display:grid;grid-template-columns:1fr 1fr;gap:4rem;align-items:center}
.contact-left h2{color:var(--white);font-size:clamp(1.8rem,3.5vw,2.8rem);margin-bottom:1rem}
.contact-left p{color:rgba(255,255,255,.65);line-height:1.75;margin-bottom:2rem}
.contact-details{display:flex;flex-direction:column;gap:1rem}
.c-detail{display:flex;align-items:center;gap:.75rem;color:rgba(255,255,255,.8);font-size:.9rem}
.c-icon{font-size:1.1rem;color:var(--gold)}
.contact-map{border-radius:var(--radius);overflow:hidden;height:300px;
  background:linear-gradient(135deg,rgba(255,255,255,.05),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.1);display:flex;align-items:center;justify-content:center;
  color:rgba(255,255,255,.3);font-size:.9rem;flex-direction:column;gap:.5rem}
.map-pin{font-size:3rem;opacity:.4}

/* ── ADMIN ── */
#admin{display:none;padding:6rem 5%;background:var(--surface)}
.admin-inner{max-width:1200px;margin:0 auto}
.admin-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:2rem}
.admin-header h2{font-size:2rem}
.admin-close{background:var(--ocean);color:var(--white);border:none;padding:.5rem 1.2rem;
  border-radius:50px;cursor:pointer;font-family:'Jost',sans-serif;font-size:.85rem;font-weight:600}
.bookings-table{width:100%;border-collapse:collapse;background:var(--white);
  border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow)}
.bookings-table th{background:var(--ocean);color:var(--white);padding:1rem .8rem;
  text-align:left;font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;font-weight:600}
.bookings-table td{padding:.9rem .8rem;border-bottom:1px solid #f0ebe0;font-size:.88rem;color:var(--text)}
.bookings-table tr:last-child td{border-bottom:none}
.bookings-table tr:hover td{background:var(--surface)}
.status-badge{background:rgba(10,77,110,.1);color:var(--ocean);font-size:.7rem;
  font-weight:700;padding:.25rem .65rem;border-radius:50px;text-transform:uppercase;letter-spacing:.08em}
.empty-state{text-align:center;color:var(--muted);padding:3rem;font-size:.95rem}

/* ── FOOTER ── */
footer{background:#020d14;color:rgba(255,255,255,.55);padding:4rem 5% 2rem}
.footer-inner{max-width:1200px;margin:0 auto}
.footer-grid{display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:3rem;margin-bottom:3rem}
.footer-brand .nav-logo{font-size:1.8rem;margin-bottom:1rem}
.footer-brand p{font-size:.85rem;line-height:1.75;max-width:260px}
.footer-col h4{color:var(--white);font-size:.8rem;letter-spacing:.14em;text-transform:uppercase;
  font-weight:600;margin-bottom:1.2rem}
.footer-col ul{list-style:none;display:flex;flex-direction:column;gap:.6rem}
.footer-col ul a{font-size:.85rem;transition:color .2s}
.footer-col ul a:hover{color:var(--gold)}
.footer-bottom{border-top:1px solid rgba(255,255,255,.07);padding-top:1.5rem;
  display:flex;justify-content:space-between;align-items:center;font-size:.8rem;flex-wrap:wrap;gap:.5rem}
.footer-legal{display:flex;gap:1.5rem}
.footer-legal a{transition:color .2s}
.footer-legal a:hover{color:var(--gold)}

/* ── MODAL ── */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:1000;
  display:flex;align-items:center;justify-content:center;opacity:0;pointer-events:none;transition:opacity .3s}
.modal-overlay.open{opacity:1;pointer-events:all}
.modal{background:var(--white);border-radius:var(--radius);padding:2.5rem;
  max-width:520px;width:90%;transform:translateY(20px);transition:transform .3s}
.modal-overlay.open .modal{transform:translateY(0)}
.modal h3{font-size:1.8rem;margin-bottom:.5rem;color:var(--ocean)}
.modal p{color:var(--muted);margin-bottom:1.5rem;line-height:1.65}
.booking-ref{font-size:2rem;font-weight:700;color:var(--gold);text-align:center;
  background:var(--surface);border-radius:8px;padding:1rem;margin-bottom:1.5rem;
  font-family:'Cormorant Garamond',serif;letter-spacing:.05em}
.modal-close{width:100%;background:var(--ocean);color:var(--white);border:none;
  border-radius:50px;padding:.8rem;font-family:'Jost',sans-serif;
  font-size:.9rem;font-weight:600;cursor:pointer;transition:background .2s}
.modal-close:hover{background:var(--ocean-light)}

/* ── SCROLL TO TOP ── */
#top-btn{position:fixed;bottom:2rem;right:2rem;width:48px;height:48px;
  background:var(--ocean);color:var(--white);border:none;border-radius:50%;
  font-size:1.2rem;cursor:pointer;box-shadow:0 4px 15px rgba(10,77,110,.35);
  transition:all .25s;opacity:0;pointer-events:none;z-index:500}
#top-btn.visible{opacity:1;pointer-events:all}
#top-btn:hover{background:var(--ocean-light);transform:translateY(-3px)}

/* ── RESPONSIVE ── */
@media(max-width:900px){
  .search-grid{grid-template-columns:1fr 1fr}
  .booking-inner,.contact-inner,.footer-grid{grid-template-columns:1fr}
  .gallery-grid{grid-template-columns:1fr 1fr;grid-template-rows:auto}
  .g-item:first-child{grid-column:span 1;grid-row:span 1}
  .g-item:nth-child(4){grid-column:span 1}
}
@media(max-width:640px){
  .nav-links{display:none;flex-direction:column;position:absolute;top:100%;left:0;right:0;
    background:rgba(10,77,110,.97);padding:1.5rem 5%;gap:1rem}
  .nav-links.open{display:flex}
  .hamburger{display:flex}
  .search-grid{grid-template-columns:1fr}
  .form-row{grid-template-columns:1fr}
  .gallery-grid{grid-template-columns:1fr}
  .hero-stats{gap:1.5rem}
  .footer-grid{grid-template-columns:1fr 1fr}
}
</style>
</head>
<body>

<!-- NAV -->
<nav id="navbar">
  <a href="#hero" class="nav-logo">Aqua<span>Lux</span></a>
  <ul class="nav-links" id="nav-links">
    <li><a href="#rooms">Rooms</a></li>
    <li><a href="#amenities">Amenities</a></li>
    <li><a href="#gallery">Gallery</a></li>
    <li><a href="#testimonials">Reviews</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#booking" class="nav-cta">Book Now</a></li>
  </ul>
  <div class="hamburger" id="hamburger" onclick="toggleMenu()">
    <span></span><span></span><span></span>
  </div>
</nav>

<!-- HERO -->
<section id="hero">
  <div class="hero-circles"></div>
  <div class="hero-circles2"></div>
  <div class="hero-content">
    <div class="hero-eyebrow">Maldives &middot; Since 1998</div>
    <h1 class="hero-title">Where the Ocean<strong>Meets Luxury</strong></h1>
    <p class="hero-sub">Discover paradise at AquaLux — overwater villas, private beaches, and world-class spa retreats await you.</p>
    <div class="hero-btns">
      <a href="#booking" class="btn-primary">Reserve Your Stay</a>
      <a href="#rooms" class="btn-outline">Explore Rooms</a>
    </div>
    <div class="hero-stats">
      <div class="stat-item"><div class="num">48+</div><div class="lbl">Luxury Villas</div></div>
      <div class="stat-item"><div class="num">4.9</div><div class="lbl">Guest Rating</div></div>
      <div class="stat-item"><div class="num">12k</div><div class="lbl">Happy Guests</div></div>
      <div class="stat-item"><div class="num">25yr</div><div class="lbl">Of Excellence</div></div>
    </div>
  </div>
  <svg class="hero-waves" viewBox="0 0 1440 100" xmlns="http://www.w3.org/2000/svg">
    <path d="M0,50 C240,100 480,0 720,50 C960,100 1200,0 1440,50 L1440,100 L0,100 Z" fill="rgba(255,255,255,0.06)"/>
    <path d="M0,70 C360,20 720,90 1080,40 C1260,15 1380,60 1440,70 L1440,100 L0,100 Z" fill="rgba(255,255,255,0.04)"/>
  </svg>
</section>

<!-- SEARCH BAR -->
<div style="padding:0 5%;background:var(--white)">
  <div id="search-bar">
    <div class="search-grid">
      <div class="search-group">
        <label>Check-In</label>
        <input type="date" id="s-checkin"/>
      </div>
      <div class="search-group">
        <label>Check-Out</label>
        <input type="date" id="s-checkout"/>
      </div>
      <div class="search-group">
        <label>Guests</label>
        <select id="s-guests">
          <option>1 Guest</option><option selected>2 Guests</option>
          <option>3 Guests</option><option>4 Guests</option>
          <option>5+ Guests</option>
        </select>
      </div>
      <div class="search-group">
        <label>Room Type</label>
        <select id="s-room">
          <option value="">Any Room</option>
          <option>Ocean View Suite</option><option>Jungle Retreat</option>
          <option>Sunset Overwater Villa</option><option>Sky Penthouse</option>
          <option>Royal Beach Villa</option><option>Coral Lagoon Bungalow</option>
        </select>
      </div>
      <button class="search-btn" onclick="quickSearch()">Search</button>
    </div>
  </div>
</div>

<!-- ROOMS -->
<section id="rooms" class="section">
  <div class="section-inner">
    <div class="section-label">Accommodation</div>
    <h2 class="section-title">Our Signature Rooms &amp; Villas</h2>
    <p class="section-sub">Each space is a private sanctuary, designed to connect you with the natural beauty of the ocean and tropical landscape.</p>
    <div class="rooms-grid" id="rooms-grid"></div>
  </div>
</section>

<!-- AMENITIES -->
<section id="amenities" class="section">
  <div class="section-inner">
    <div style="text-align:center">
      <div class="section-label" style="justify-content:center">Resort Facilities</div>
      <h2 class="section-title">World-Class Amenities</h2>
      <p class="section-sub" style="margin:0 auto">Every detail of your stay is curated for total relaxation, adventure, and indulgence.</p>
    </div>
    <div class="amenities-grid">
      <div class="amenity-card">
        <div class="amenity-icon">🏊</div>
        <div class="amenity-name">Infinity Pools</div>
        <div class="amenity-desc">Three oceanfront infinity pools with swim-up bars and private cabanas</div>
      </div>
      <div class="amenity-card">
        <div class="amenity-icon">🧖</div>
        <div class="amenity-name">Luxury Spa</div>
        <div class="amenity-desc">Award-winning treatments using local botanicals and ancient techniques</div>
      </div>
      <div class="amenity-card">
        <div class="amenity-icon">🍽️</div>
        <div class="amenity-name">Fine Dining</div>
        <div class="amenity-desc">Five restaurants from beach-side casual to Michelin-starred fine dining</div>
      </div>
      <div class="amenity-card">
        <div class="amenity-icon">🤿</div>
        <div class="amenity-name">Water Sports</div>
        <div class="amenity-desc">Scuba diving, snorkelling, kayaking and private submarine tours</div>
      </div>
      <div class="amenity-card">
        <div class="amenity-icon">🛥️</div>
        <div class="amenity-name">Private Yacht</div>
        <div class="amenity-desc">Sunset cruises and private island transfers on our luxury fleet</div>
      </div>
      <div class="amenity-card">
        <div class="amenity-icon">🎾</div>
        <div class="amenity-name">Sports Club</div>
        <div class="amenity-desc">Tennis, beach volleyball, a fully-equipped gym and yoga pavilion</div>
      </div>
      <div class="amenity-card">
        <div class="amenity-icon">🧒</div>
        <div class="amenity-name">Kids Club</div>
        <div class="amenity-desc">Supervised activities, creative workshops and marine education</div>
      </div>
      <div class="amenity-card">
        <div class="amenity-icon">✈️</div>
        <div class="amenity-name">Seaplane Transfer</div>
        <div class="amenity-desc">Scenic seaplane arrivals from Malé International Airport</div>
      </div>
    </div>
  </div>
</section>

<!-- GALLERY -->
<section id="gallery">
  <div style="max-width:1200px;margin:0 auto;padding:0 0 2rem">
    <div class="section-label" style="color:rgba(255,255,255,.5);justify-content:center">Visual Journey</div>
    <h2 class="gallery-title">A Glimpse of Paradise</h2>
    <p class="gallery-sub">Every corner of AquaLux is a frame-worthy moment</p>
  </div>
  <div class="gallery-grid" style="max-width:1200px;margin:0 auto">
    <div class="g-item"><div class="g-img bg-g1"><div class="g-dec">🌊</div></div></div>
    <div class="g-item"><div class="g-img bg-g2"><div class="g-dec">🌴</div></div></div>
    <div class="g-item"><div class="g-img bg-g3"><div class="g-dec">🌅</div></div></div>
    <div class="g-item"><div class="g-img bg-g4"><div class="g-dec">⭐</div></div></div>
    <div class="g-item"><div class="g-img bg-g5"><div class="g-dec">🏖️</div></div></div>
  </div>
</section>

<!-- BOOKING -->
<section id="booking">
  <div class="booking-inner">
    <div class="booking-info">
      <div class="section-label">Reserve Now</div>
      <h2>Plan Your Perfect Escape</h2>
      <p>Experience unparalleled luxury with our seamless booking process. Your dream vacation is just a few clicks away.</p>
      <div class="booking-highlights">
        <div class="b-highlight">Complimentary airport seaplane transfer</div>
        <div class="b-highlight">Free breakfast for two daily</div>
        <div class="b-highlight">Flexible cancellation up to 48 hours</div>
        <div class="b-highlight">Private butler service on request</div>
        <div class="b-highlight">Best rate guarantee</div>
        <div class="b-highlight">Instant booking confirmation</div>
      </div>
    </div>
    <div class="booking-form">
      <h3>Book Your Stay</h3>
      <div class="form-row">
        <div class="form-group">
          <label>First Name</label>
          <input type="text" id="f-fname" placeholder="John"/>
        </div>
        <div class="form-group">
          <label>Last Name</label>
          <input type="text" id="f-lname" placeholder="Smith"/>
        </div>
      </div>
      <div class="form-group">
        <label>Email Address</label>
        <input type="email" id="f-email" placeholder="john@example.com"/>
      </div>
      <div class="form-group">
        <label>Phone Number</label>
        <input type="tel" id="f-phone" placeholder="+1 234 567 8900"/>
      </div>
      <div class="form-group">
        <label>Room Type</label>
        <select id="f-room" onchange="updatePrice()">
          <option value="">-- Select a Room --</option>
          <option value="Ocean View Suite|350">Ocean View Suite — $350/night</option>
          <option value="Jungle Retreat|220">Jungle Retreat — $220/night</option>
          <option value="Sunset Overwater Villa|680">Sunset Overwater Villa — $680/night</option>
          <option value="Sky Penthouse|950">Sky Penthouse — $950/night</option>
          <option value="Royal Beach Villa|1200">Royal Beach Villa — $1,200/night</option>
          <option value="Coral Lagoon Bungalow|480">Coral Lagoon Bungalow — $480/night</option>
        </select>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Check-In</label>
          <input type="date" id="f-checkin" onchange="updatePrice()"/>
        </div>
        <div class="form-group">
          <label>Check-Out</label>
          <input type="date" id="f-checkout" onchange="updatePrice()"/>
        </div>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>Guests</label>
          <select id="f-guests">
            <option>1</option><option selected>2</option>
            <option>3</option><option>4</option><option>5</option>
          </select>
        </div>
        <div class="form-group">
          <label>Special Requests</label>
          <input type="text" id="f-special" placeholder="Honeymoon setup, etc."/>
        </div>
      </div>
      <div class="price-summary" id="price-summary" style="display:none">
        <div class="price-row"><span>Room rate</span><span id="ps-rate">—</span></div>
        <div class="price-row"><span>Nights</span><span id="ps-nights">—</span></div>
        <div class="price-row"><span>Taxes &amp; fees (15%)</span><span id="ps-tax">—</span></div>
        <div class="price-total"><span>Total</span><span id="ps-total">—</span></div>
      </div>
      <button class="submit-btn" onclick="submitBooking()">Confirm Reservation</button>
      <div id="form-msg"></div>
    </div>
  </div>
</section>

<!-- TESTIMONIALS -->
<section id="testimonials" class="section">
  <div class="section-inner">
    <div style="text-align:center">
      <div class="section-label" style="justify-content:center">Guest Reviews</div>
      <h2 class="section-title">What Our Guests Say</h2>
    </div>
    <div class="testimonials-grid">
      <div class="t-card">
        <div class="t-stars">★★★★★</div>
        <p class="t-text">"Absolutely magical. The overwater villa exceeded every expectation. Waking up to the sound of the ocean with the most stunning sunrise — I never wanted to leave."</p>
        <div class="t-author">
          <div class="t-avatar" style="background:var(--ocean)">S</div>
          <div><div class="t-name">Sarah Mitchell</div><div class="t-loc">New York, USA</div></div>
        </div>
      </div>
      <div class="t-card">
        <div class="t-stars">★★★★★</div>
        <p class="t-text">"The spa treatments were beyond incredible. The staff remembered our names from day one. AquaLux has permanently ruined all other resorts for us — in the best way."</p>
        <div class="t-author">
          <div class="t-avatar" style="background:var(--gold)">J</div>
          <div><div class="t-name">James &amp; Claire</div><div class="t-loc">London, UK</div></div>
        </div>
      </div>
      <div class="t-card">
        <div class="t-stars">★★★★★</div>
        <p class="t-text">"We celebrated our anniversary here and it was perfect in every way. The private sunset cruise was a highlight. Booking the Royal Beach Villa for our return trip already!"</p>
        <div class="t-author">
          <div class="t-avatar" style="background:#4a7a3a">A</div>
          <div><div class="t-name">Aiko Tanaka</div><div class="t-loc">Tokyo, Japan</div></div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- CONTACT -->
<section id="contact">
  <div class="contact-inner">
    <div class="contact-left">
      <div class="section-label" style="color:rgba(255,255,255,.45)">Get In Touch</div>
      <h2>We'd Love to Hear From You</h2>
      <p>Our concierge team is available 24/7 to assist with reservations, special requests, or any questions about your stay.</p>
      <div class="contact-details">
        <div class="c-detail"><span class="c-icon">📞</span> +960 800-AQUALUX (2782589)</div>
        <div class="c-detail"><span class="c-icon">✉️</span> reservations@aqualuxresort.com</div>
        <div class="c-detail"><span class="c-icon">📍</span> North Malé Atoll, Republic of Maldives</div>
        <div class="c-detail"><span class="c-icon">🕐</span> Concierge: 24 hours · 7 days a week</div>
      </div>
    </div>
    <div class="contact-map">
      <div class="map-pin">🗺️</div>
      <span>North Malé Atoll, Maldives</span>
      <span style="font-size:.75rem;margin-top:.25rem">4°10′N 73°30′E</span>
    </div>
  </div>
</section>

<!-- ADMIN PANEL -->
<section id="admin">
  <div class="admin-inner">
    <div class="admin-header">
      <h2>📋 Booking Management</h2>
      <button class="admin-close" onclick="toggleAdmin()">✕ Close</button>
    </div>
    <div id="admin-content"></div>
  </div>
</section>

<!-- FOOTER -->
<footer>
  <div class="footer-inner">
    <div class="footer-grid">
      <div class="footer-brand">
        <div class="nav-logo">Aqua<span>Lux</span></div>
        <p>A private paradise in the heart of the Maldives. Where luxury meets nature in perfect harmony.</p>
      </div>
      <div class="footer-col">
        <h4>Rooms</h4>
        <ul>
          <li><a href="#rooms">Ocean View Suite</a></li>
          <li><a href="#rooms">Jungle Retreat</a></li>
          <li><a href="#rooms">Overwater Villa</a></li>
          <li><a href="#rooms">Sky Penthouse</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Resort</h4>
        <ul>
          <li><a href="#amenities">Spa &amp; Wellness</a></li>
          <li><a href="#amenities">Dining</a></li>
          <li><a href="#amenities">Water Sports</a></li>
          <li><a href="#amenities">Kids Club</a></li>
        </ul>
      </div>
      <div class="footer-col">
        <h4>Quick Links</h4>
        <ul>
          <li><a href="#booking">Book Now</a></li>
          <li><a href="#contact">Contact</a></li>
          <li><a href="#" onclick="toggleAdmin();return false">Admin Panel</a></li>
        </ul>
      </div>
    </div>
    <div class="footer-bottom">
      <span>© 2025 AquaLux Resort &amp; Spa. All rights reserved.</span>
      <div class="footer-legal">
        <a href="#">Privacy Policy</a>
        <a href="#">Terms &amp; Conditions</a>
        <a href="#">Cookie Policy</a>
      </div>
    </div>
  </div>
</footer>

<!-- SUCCESS MODAL -->
<div class="modal-overlay" id="modal">
  <div class="modal">
    <h3>🎉 Booking Confirmed!</h3>
    <p>Thank you for choosing AquaLux. Your reservation is confirmed. A confirmation email will be sent to you shortly.</p>
    <div class="booking-ref" id="booking-ref">AQL-000000</div>
    <p style="text-align:center;font-size:.88rem;color:var(--muted);margin-bottom:1.5rem">Please save your reference number for check-in.</p>
    <button class="modal-close" onclick="closeModal()">Close</button>
  </div>
</div>

<button id="top-btn" onclick="window.scrollTo({top:0,behavior:'smooth'})">↑</button>

<script>
// ── ROOMS DATA ──
const ROOMS = [
  {name:"Ocean View Suite",price:350,icon:"🌊",bg:"bg-ocean",desc:"Perched above the turquoise lagoon with floor-to-ceiling windows and a private infinity plunge pool.",features:["King Bed","Ocean View","Plunge Pool","85 m²"],badge:"Popular"},
  {name:"Jungle Retreat",price:220,icon:"🌴",bg:"bg-jungle",desc:"Nestled in lush tropical gardens with an open-air bathroom and hammock deck for ultimate seclusion.",features:["Queen Bed","Garden View","Rain Shower","65 m²"],badge:null},
  {name:"Sunset Overwater Villa",price:680,icon:"🌅",bg:"bg-sunset",desc:"Iconic overwater bungalow with glass floor panels, direct ocean access, and 360° sunset panoramas.",features:["King Bed","Overwater","Glass Floor","110 m²"],badge:"Best View"},
  {name:"Sky Penthouse",price:950,icon:"🏙️",bg:"bg-sky",desc:"Two-story penthouse with a rooftop terrace, private heated pool, and dedicated butler service.",features:["Master Suite","Rooftop Pool","Butler","180 m²"],badge:"Premium"},
  {name:"Royal Beach Villa",price:1200,icon:"🏖️",bg:"bg-villa",desc:"Exclusive beachfront villa with a private beach, outdoor dining pavilion, and full resort privileges.",features:["3 Bedrooms","Private Beach","Chef","320 m²"],badge:"Exclusive"},
  {name:"Coral Lagoon Bungalow",price:480,icon:"🪸",bg:"bg-beach",desc:"Intimate bungalow steps from the reef, perfect for snorkellers with direct lagoon access.",features:["King Bed","Lagoon Access","Deck","75 m²"],badge:null}
];

function renderRooms(){
  const g = document.getElementById("rooms-grid");
  g.innerHTML = ROOMS.map(r=>`
    <div class="room-card" onclick="selectRoom('${r.name}|${r.price}')">
      <div class="room-img">
        <div class="room-img-bg ${r.bg}"><div class="room-img-dec">${r.icon}</div></div>
        ${r.badge?`<span class="room-badge">${r.badge}</span>`:''}
      </div>
      <div class="room-body">
        <h3 class="room-name">${r.name}</h3>
        <p class="room-desc">${r.desc}</p>
        <div class="room-features">${r.features.map(f=>`<span class="room-feature">${f}</span>`).join('')}</div>
        <div class="room-footer">
          <div class="room-price"><span class="amt">$${r.price}</span><span class="per"> / night</span></div>
          <button class="btn-book">Book Now</button>
        </div>
      </div>
    </div>`).join('');
}

function selectRoom(val){
  document.getElementById("f-room").value=val;
  updatePrice();
  document.getElementById("booking").scrollIntoView({behavior:"smooth"});
}

// ── PRICE CALCULATOR ──
function updatePrice(){
  const rv=document.getElementById("f-room").value;
  const ci=document.getElementById("f-checkin").value;
  const co=document.getElementById("f-checkout").value;
  const ps=document.getElementById("price-summary");
  if(!rv||!ci||!co){ps.style.display="none";return}
  const rate=parseInt(rv.split("|")[1]);
  const d1=new Date(ci),d2=new Date(co);
  const nights=Math.round((d2-d1)/(1000*60*60*24));
  if(nights<=0){ps.style.display="none";return}
  const sub=rate*nights,tax=Math.round(sub*.15),total=sub+tax;
  document.getElementById("ps-rate").textContent=`$${rate}/night`;
  document.getElementById("ps-nights").textContent=nights;
  document.getElementById("ps-tax").textContent=`$${tax}`;
  document.getElementById("ps-total").textContent=`$${total}`;
  ps.style.display="block";
}

// ── BOOKING SUBMIT ──
async function submitBooking(){
  const fname=document.getElementById("f-fname").value.trim();
  const lname=document.getElementById("f-lname").value.trim();
  const email=document.getElementById("f-email").value.trim();
  const phone=document.getElementById("f-phone").value.trim();
  const room=document.getElementById("f-room").value;
  const ci=document.getElementById("f-checkin").value;
  const co=document.getElementById("f-checkout").value;
  const guests=document.getElementById("f-guests").value;
  const msg=document.getElementById("form-msg");
  msg.className="";msg.style.display="none";

  if(!fname||!lname||!email||!room||!ci||!co){
    msg.textContent="Please fill in all required fields.";
    msg.className="error";return;
  }
  const d1=new Date(ci),d2=new Date(co);
  const nights=Math.round((d2-d1)/(1000*60*60*24));
  if(nights<=0){msg.textContent="Check-out must be after check-in.";msg.className="error";return;}

  const rate=parseInt(room.split("|")[1]);
  const sub=rate*nights,tax=Math.round(sub*.15),total=sub+tax;
  const payload={
    name:`${fname} ${lname}`,email,phone,
    room_type:room.split("|")[0],
    check_in:ci,check_out:co,guests,
    nights,total_price:total
  };

  try{
    const res=await fetch("/api/booking",{
      method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify(payload)
    });
    const data=await res.json();
    if(data.success){
      document.getElementById("booking-ref").textContent=`AQL-${String(data.id).padStart(6,"0")}`;
      document.getElementById("modal").classList.add("open");
      clearForm();
    } else {
      msg.textContent="Booking failed: "+(data.error||"Unknown error");msg.className="error";
    }
  }catch(e){
    msg.textContent="Network error. Please try again.";msg.className="error";
  }
}

function clearForm(){
  ["f-fname","f-lname","f-email","f-phone","f-checkin","f-checkout","f-special"].forEach(id=>document.getElementById(id).value="");
  document.getElementById("f-room").value="";
  document.getElementById("f-guests").value="2";
  document.getElementById("price-summary").style.display="none";
}
function closeModal(){document.getElementById("modal").classList.remove("open");}

// ── ADMIN ──
async function toggleAdmin(){
  const sec=document.getElementById("admin");
  if(sec.style.display==="block"){sec.style.display="none";return;}
  sec.style.display="block";sec.scrollIntoView({behavior:"smooth"});
  const res=await fetch("/api/bookings");
  const data=await res.json();
  const cont=document.getElementById("admin-content");
  if(!data.length){cont.innerHTML='<div class="empty-state">No bookings yet.</div>';return;}
  cont.innerHTML=`<table class="bookings-table">
    <thead><tr>
      <th>#</th><th>Guest</th><th>Email</th><th>Room</th>
      <th>Check-In</th><th>Check-Out</th><th>Nights</th><th>Guests</th><th>Total</th><th>Status</th>
    </tr></thead>
    <tbody>${data.map(b=>`<tr>
      <td>AQL-${String(b.id).padStart(6,"0")}</td>
      <td>${b.name}</td><td>${b.email}</td><td>${b.room_type}</td>
      <td>${b.check_in}</td><td>${b.check_out}</td>
      <td>${b.nights}</td><td>${b.guests}</td>
      <td>$${b.total_price.toLocaleString()}</td>
      <td><span class="status-badge">Confirmed</span></td>
    </tr>`).join("")}</tbody>
  </table>`;
}

// ── QUICK SEARCH ──
function quickSearch(){
  const room=document.getElementById("s-room").value;
  const ci=document.getElementById("s-checkin").value;
  const co=document.getElementById("s-checkout").value;
  if(room) document.getElementById("f-room").value=ROOMS.find(r=>r.name===room)?`${room}|${ROOMS.find(r=>r.name===room).price}`:"";
  if(ci) document.getElementById("f-checkin").value=ci;
  if(co) document.getElementById("f-checkout").value=co;
  updatePrice();
  document.getElementById("booking").scrollIntoView({behavior:"smooth"});
}

// ── NAV ──
window.addEventListener("scroll",()=>{
  document.getElementById("navbar").classList.toggle("scrolled",window.scrollY>80);
  document.getElementById("top-btn").classList.toggle("visible",window.scrollY>400);
});
function toggleMenu(){document.getElementById("nav-links").classList.toggle("open");}

// ── INIT ──
renderRooms();
const today=new Date().toISOString().split("T")[0];
document.getElementById("s-checkin").min=today;
document.getElementById("s-checkout").min=today;
document.getElementById("f-checkin").min=today;
document.getElementById("f-checkout").min=today;
</script>
</body>
</html>"""

# ──────────────────────────────────────────────
# HTTP SERVER
# ──────────────────────────────────────────────
class ResortHandler(http.server.BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] {fmt % args}")

    # ── ROUTING ──
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path.rstrip("/") or "/"

        if path == "/":
            self._send_html(HTML)
        elif path == "/api/bookings":
            self._send_json(get_all_bookings())
        else:
            self._send_404()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path

        if path == "/api/booking":
            length  = int(self.headers.get("Content-Length", 0))
            raw     = self.rfile.read(length)
            try:
                data = json.loads(raw)
                # Basic validation
                required = ["name","email","phone","room_type",
                            "check_in","check_out","guests","nights","total_price"]
                for field in required:
                    if field not in data or str(data[field]).strip() == "":
                        raise ValueError(f"Missing field: {field}")
                booking_id = save_booking(data)
                print(f"  ✅  New booking #{booking_id}: {data['name']} — {data['room_type']}")
                self._send_json({"success": True, "id": booking_id})
            except Exception as exc:
                self._send_json({"success": False, "error": str(exc)}, status=400)
        else:
            self._send_404()

    # ── HELPERS ──
    def _send_html(self, html):
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_404(self):
        body = b"Not found"
        self.send_response(404)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 8080))
    init_db()
    server = http.server.HTTPServer(("0.0.0.0", PORT), ResortHandler)
    print(f"""
╔══════════════════════════════════════════╗
║       🌊  AquaLux Resort Booking         ║
╠══════════════════════════════════════════╣
║  Server  : http://localhost:{PORT:<13}   ║
║  Admin   : scroll to footer → Admin      ║
║  Database: {DB_PATH:<30} ║
║  Stop    : Ctrl + C                      ║
╚══════════════════════════════════════════╝
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋  Server stopped.")
        sys.exit(0)