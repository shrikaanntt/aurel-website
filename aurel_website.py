import os
import re
import textwrap
from datetime import datetime
import streamlit as st
from google import genai
from google.genai import types

st.set_page_config(page_title="AUREL — Carry Better", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")

def html(x):
    st.html(textwrap.dedent(x).strip())

# ---------- AI ----------
key = os.getenv("GEMINI_API_KEY")
if not key:
    try: key = st.secrets["GEMINI_API_KEY"]
    except Exception: key = None
ai = genai.Client(api_key=key) if key else None

SYSTEM = """You are AUREL Concierge, the premium shopping assistant for AUREL,
a fictional modern everyday-carry and travel brand. Recommend only catalogue
products supplied in the prompt. Be concise, polished and helpful. Help with
shopping, comparisons, gifts, travel kits and packing lists. Never invent specs."""

# ---------- DATA ----------
P = [
{"id":"p1","name":"Atlas Carry-On","cat":"Travel","price":14999,"old":17999,"rating":4.9,"reviews":328,"badge":"BESTSELLER","img":"https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=1200&q=88","desc":"A compact premium carry-on for short trips and fast airport movement.","features":["Cabin-friendly profile","Organized interior","Laptop compartment","Reinforced handles"]},
{"id":"p2","name":"Nomad Sling","cat":"Bags","price":4999,"old":5999,"rating":4.8,"reviews":214,"badge":"POPULAR","img":"https://images.unsplash.com/photo-1556306535-38febf6782e7?auto=format&fit=crop&w=1200&q=88","desc":"A lightweight crossbody for phone, passport, wallet and daily essentials.","features":["Quick-access pocket","Adjustable strap","Soft-touch lining","Hidden passport pocket"]},
{"id":"p3","name":"Transit Pack 24","cat":"Bags","price":8999,"old":9999,"rating":4.7,"reviews":167,"badge":"NEW","img":"https://images.unsplash.com/photo-1553062407-98eeb64c6a62?auto=format&fit=crop&w=1200&q=88","desc":"A structured daypack for work, travel and everything between.","features":["24L capacity","Padded laptop sleeve","Luggage pass-through","Water-resistant shell"]},
{"id":"p4","name":"Field Wallet","cat":"Accessories","price":2499,"old":2999,"rating":4.8,"reviews":492,"badge":"EVERYDAY","img":"https://images.unsplash.com/photo-1627123424574-724758594e93?auto=format&fit=crop&w=1200&q=88","desc":"A slim wallet designed to carry the essentials without bulk.","features":["Slim profile","Multiple card slots","Cash sleeve","RFID-aware design"]},
{"id":"p5","name":"Weekender 38","cat":"Travel","price":10999,"old":12999,"rating":4.9,"reviews":119,"badge":"LIMITED","img":"https://images.unsplash.com/photo-1552919387-2b5a2a0b8a3e?auto=format&fit=crop&w=1200&q=88","desc":"A spacious weekend bag with a structured base and understated silhouette.","features":["Structured base","Shoe compartment","Interior zip pocket","Shoulder strap"]},
{"id":"p6","name":"Aero Tech Organizer","cat":"Tech","price":3299,"old":3999,"rating":4.7,"reviews":276,"badge":"SMART PICK","img":"https://images.unsplash.com/photo-1612815154858-60aa4c59eaa6?auto=format&fit=crop&w=1200&q=88","desc":"A compact organizer for chargers, cables, adapters and small tech.","features":["Cable loops","Mesh pocket","Flat-open design","Compact footprint"]},
{"id":"p7","name":"Terra Bottle","cat":"Lifestyle","price":2199,"old":2499,"rating":4.6,"reviews":183,"badge":"DAILY","img":"https://images.unsplash.com/photo-1602143407151-7111542de6e8?auto=format&fit=crop&w=1200&q=88","desc":"A reusable bottle designed for desks, commutes and long days.","features":["Leak-resistant lid","Carry loop","Minimal silhouette","Reusable design"]},
{"id":"p8","name":"Daily Carry Set","cat":"Sets","price":12999,"old":15999,"rating":4.9,"reviews":88,"badge":"SET","img":"https://images.unsplash.com/photo-1553531889-56a4c4e9c9b8?auto=format&fit=crop&w=1200&q=88","desc":"A curated trio of sling, wallet and tech organizer.","features":["3-piece bundle","Coordinated design","Gift-ready","Bundle savings"]}
]

# ---------- STATE ----------
for k,v in {"page":"Home","cart":{},"wish":[],"selected":None,"chat":[],"newsletter":False}.items():
    if k not in st.session_state: st.session_state[k]=v

def money(x): return f"₹{x:,.0f}"
def get(pid): return next((x for x in P if x["id"]==pid),None)
def add(pid,n=1): st.session_state.cart[pid]=st.session_state.cart.get(pid,0)+n
def count(): return sum(st.session_state.cart.values())
def items(): return [(get(k),v) for k,v in st.session_state.cart.items() if get(k)]
def subtotal(): return sum(x["price"]*q for x,q in items())
def shipping(): return 0 if subtotal()==0 or subtotal()>=5000 else 199
def discount(): return round(subtotal()*.1) if subtotal()>=10000 else 0
def total(): return subtotal()+shipping()-discount()
def valid_email(x): return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$",x))

# ---------- STYLE ----------
html("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');
:root{--ink:#171716;--paper:#f5f1e9;--white:#fffdf8;--accent:#b56b45;--muted:#77736b;--line:#ddd7ca}
html,body,[data-testid="stAppViewContainer"],.stApp{background:#f5f1e9!important;color:var(--ink)!important}
header[data-testid="stHeader"]{display:none!important}
[data-testid="stAppViewContainer"]>.main>div{padding-top:0!important}
.block-container{max-width:1500px;padding:0 3rem 4rem!important}
p,div,span,label,input,textarea,button{font-family:'DM Sans',sans-serif}
h1,h2,h3,h4{font-family:'Playfair Display',serif!important;color:var(--ink)!important}
.stButton>button{background:var(--ink)!important;color:white!important;border:1px solid var(--ink)!important;border-radius:5px!important;font-weight:600!important}
.stButton>button:hover{background:var(--accent)!important;border-color:var(--accent)!important}
div[data-testid="stTextInput"] input,div[data-baseweb="select"]>div,div[data-testid="stNumberInput"] input,div[data-testid="stTextArea"] textarea{background:#fffdf8!important;color:#171716!important;-webkit-text-fill-color:#171716!important;border:1px solid #d8d1c4!important}
div[data-baseweb="select"] span{color:#171716!important}
.top{padding:11px 0;border-bottom:1px solid var(--line);text-align:center;color:#777168;font-size:10px;letter-spacing:1.5px}
.brand{font:30px 'Playfair Display',serif;letter-spacing:5px}.navnote{text-align:center;color:#77736b;font-size:10px;letter-spacing:2px;padding-top:10px}
.hero{min-height:560px;border-radius:0 0 14px 14px;padding:70px;background:linear-gradient(90deg,rgba(20,21,19,.94),rgba(20,21,19,.60),rgba(20,21,19,.12)),url('https://images.unsplash.com/photo-1523779917675-b6ed3a42a561?auto=format&fit=crop&w=1900&q=90');background-size:cover;background-position:center;color:white;display:flex;align-items:center;margin-bottom:60px}
.kicker{font-size:10px;color:var(--accent);font-weight:700;letter-spacing:3px;text-transform:uppercase}.hero .kicker{color:#e6c9ad}
.hero-title{font:72px/1 'Playfair Display',serif;color:white;max-width:760px;margin:16px 0 20px}.hero-copy{color:#e6e0d6;max-width:570px;line-height:1.8}
.section-title{font:42px 'Playfair Display',serif;margin-top:5px}
.card{background:var(--white);border:1px solid #e0d9cc;border-radius:10px;overflow:hidden}.product-img{width:100%;height:310px;object-fit:cover}.product-name{font:21px 'Playfair Display',serif;margin-top:13px}.meta{color:#807a70;font-size:12px;margin:6px 0}.price{font-weight:700;margin-top:10px}.old{text-decoration:line-through;color:#aaa49a;font-weight:400;margin-left:5px}.badge{display:inline-block;padding:5px 8px;background:#20211f;color:white;border-radius:3px;font-size:9px;letter-spacing:1px;font-weight:700}
.feature{padding:25px;border-top:1px solid var(--line);border-bottom:1px solid var(--line);min-height:145px}.feature-title{font:20px 'Playfair Display',serif;margin:8px 0}.feature-text{color:#77736b;font-size:13px;line-height:1.7}
.news{margin-top:60px;padding:50px;border-radius:14px;background:#20211f;color:white}.news h2{color:white!important;font-size:40px}.news p{color:#c8c4ba;max-width:650px;line-height:1.7}
.detail-title{font:52px/1.05 'Playfair Display',serif}.detail{color:#6e6a62;line-height:1.8}.review{padding:22px;border:1px solid var(--line);background:var(--white);border-radius:8px;min-height:130px}
.cartrow{padding:18px 0;border-bottom:1px solid var(--line)}
.chat{background:var(--white);border:1px solid #ded7ca;border-radius:12px;padding:25px}
div[data-testid="stChatMessage"]{background:var(--white)!important;border:1px solid #e0d9cc;border-radius:10px;color:#171716!important}div[data-testid="stChatMessage"] *{color:#171716!important}
div[data-testid="stChatInput"]{background:var(--white)!important;border:1px solid #cfc7ba!important;border-radius:8px!important}
div[data-testid="stChatInput"] textarea{background:var(--white)!important;color:#171716!important;-webkit-text-fill-color:#171716!important}
div[data-testid="stChatInput"] button{background:#171716!important;color:#fff!important}
.footer{margin-top:85px;padding:45px 0;border-top:1px solid var(--line);color:#77736b;font-size:10px;letter-spacing:1px}
@media(max-width:800px){.block-container{padding:0 1rem 3rem!important}.hero{padding:30px 24px;min-height:500px}.hero-title{font-size:48px}.section-title{font-size:34px}.detail-title{font-size:40px}}
</style>
""")

# ---------- NAV ----------
html('<div class="top">COMPLIMENTARY SHIPPING OVER ₹5,000 · 30-DAY RETURNS · DESIGNED FOR EVERYDAY MOVEMENT</div>')
a,b,c=st.columns([2,6,2])
with a: html('<div class="brand">AUREL</div>')
with b: html('<div class="navnote">EVERYDAY CARRY · TRAVEL · OBJECTS FOR THE WAY YOU LIVE</div>')
with c:
    if st.button(f"Bag ({count()})",use_container_width=True): st.session_state.page="Cart"; st.rerun()
nav=st.columns(5)
for col,label,page in zip(nav,["SHOP","TRAVEL","OUR STORY","CONCIERGE","NEWSLETTER"],["Shop","Travel","Story","Concierge","Newsletter"]):
    with col:
        if st.button(label,use_container_width=True): st.session_state.page=page; st.rerun()

# ---------- HOME ----------
if st.session_state.page=="Home":
    html("""<div class="hero"><div><div class="kicker">THE AUREL EDIT · 2026</div><div class="hero-title">Carry less.<br>Live more.</div><div class="hero-copy">Thoughtful objects for people who move through cities, airports, workdays and weekends with intention. AUREL is everyday carry without the unnecessary noise.</div></div></div>""")
    html('<div class="kicker">THE NEW COLLECTION</div><div class="section-title">Objects made to go places.</div><p class="detail">From airport mornings to late-night city walks, every AUREL piece is designed around what you actually carry.</p><br>')
    cols=st.columns(4)
    for i,x in enumerate(P[:4]):
        with cols[i]:
            html(f'<div class="card"><img class="product-img" src="{x["img"]}"><div style="padding:17px"><span class="badge">{x["badge"]}</span><div class="product-name">{x["name"]}</div><div class="meta">{x["cat"]} · ★ {x["rating"]} ({x["reviews"]})</div><div class="price">{money(x["price"])} <span class="old">{money(x["old"])}</span></div></div></div>')
            if st.button("View piece →",key="hv"+x["id"],use_container_width=True): st.session_state.selected=x["id"];st.session_state.page="Product";st.rerun()
    st.markdown("<br><br>",unsafe_allow_html=True)
    cols=st.columns(4)
    for col,(ico,title,txt) in zip(cols,[("◈","Thoughtful design","Nothing added just to look busy."),("⌁","Built to move","Objects designed around real journeys."),("○","30-day returns","Take your time deciding."),("✦","Human support","AUREL Concierge is always here.")]):
        with col: html(f'<div class="feature"><div style="font-size:28px">{ico}</div><div class="feature-title">{title}</div><div class="feature-text">{txt}</div></div>')
    html('<div class="news"><div class="kicker" style="color:#e6c9ad">THE AUREL JOURNAL</div><h2>Travel notes. New objects. No noise.</h2><p>A monthly dispatch of useful travel ideas, product stories, city guides and occasional early access.</p></div>')
    e=st.text_input("Email",placeholder="you@example.com",label_visibility="collapsed",key="home_email")
    if st.button("SUBSCRIBE TO THE JOURNAL",use_container_width=True):
        if valid_email(e): st.session_state.newsletter=True;st.success("Welcome to The AUREL Journal.")
        else: st.error("Please enter a valid email.")

# ---------- SHOP ----------
elif st.session_state.page=="Shop":
    html('<div class="kicker">SHOP AUREL</div><div class="section-title">The complete collection.</div><br>')
    c1,c2,c3=st.columns([3,2,2])
    with c1: q=st.text_input("Search",placeholder="Search products...",label_visibility="collapsed").lower()
    with c2: cat=st.selectbox("Category",["All"]+sorted(set(x["cat"] for x in P)))
    with c3: order=st.selectbox("Sort",["Featured","Price: Low to High","Price: High to Low","Rating"])
    data=[x for x in P if (not q or q in x["name"].lower() or q in x["cat"].lower() or q in x["desc"].lower()) and (cat=="All" or x["cat"]==cat)]
    if order=="Price: Low to High": data=sorted(data,key=lambda x:x["price"])
    if order=="Price: High to Low": data=sorted(data,key=lambda x:x["price"],reverse=True)
    if order=="Rating": data=sorted(data,key=lambda x:x["rating"],reverse=True)
    cols=st.columns(4)
    for i,x in enumerate(data):
        with cols[i%4]:
            html(f'<div class="card"><img class="product-img" src="{x["img"]}"><div style="padding:17px"><span class="badge">{x["badge"]}</span><div class="product-name">{x["name"]}</div><div class="meta">{x["cat"]} · ★ {x["rating"]}</div><div class="price">{money(x["price"])} <span class="old">{money(x["old"])}</span></div></div></div>')
            a,b=st.columns(2)
            with a:
                if st.button("View",key="sv"+x["id"],use_container_width=True):st.session_state.selected=x["id"];st.session_state.page="Product";st.rerun()
            with b:
                if st.button("Add",key="sa"+x["id"],use_container_width=True):add(x["id"]);st.toast(f'{x["name"]} added to bag.')

# ---------- PRODUCT ----------
elif st.session_state.page=="Product":
    x=get(st.session_state.selected)
    if not x: st.session_state.page="Shop";st.rerun()
    l,r=st.columns([1.15,1])
    with l: html(f'<div class="card"><img src="{x["img"]}" style="width:100%;border-radius:8px"></div>')
    with r:
        html(f'<span class="badge">{x["badge"]}</span><div class="detail-title">{x["name"]}</div><div class="meta">★ {x["rating"]} · {x["reviews"]} reviews · {x["cat"]}</div><div class="price" style="font-size:28px">{money(x["price"])} <span class="old">{money(x["old"])}</span></div><p class="detail">{x["desc"]}</p>')
        qty=st.number_input("Quantity",1,5,1)
        a,b=st.columns(2)
        with a:
            if st.button("ADD TO BAG",use_container_width=True):add(x["id"],qty);st.toast("Added to bag.")
        with b:
            if st.button("♡ SAVE",use_container_width=True):
                if x["id"] not in st.session_state.wish:st.session_state.wish.append(x["id"])
                st.toast("Saved.")
    st.markdown("<br><br>",unsafe_allow_html=True)
    html('<div class="kicker">THE DETAILS</div><div class="section-title">Designed around the journey.</div><br>')
    cols=st.columns(len(x["features"]))
    for col,f in zip(cols,x["features"]):
        with col:html(f'<div class="feature"><div class="feature-title">{f}</div><div class="feature-text">Thoughtfully considered to keep the everyday experience simple.</div></div>')
    st.markdown("<br>",unsafe_allow_html=True)
    html('<div class="kicker">COMMUNITY</div><div class="section-title">A few words from customers.</div><br>')
    cols=st.columns(3)
    for col,q in zip(cols,["“The kind of product you stop thinking about because it just works.”","“Beautiful without feeling precious. I take mine everywhere.”","“The organization is exactly what I wanted for short trips.”"]):
        with col:html(f'<div class="review"><div style="font:18px Playfair Display">{q}</div><div class="meta">Verified buyer</div></div>')

# ---------- TRAVEL KIT ----------
elif st.session_state.page=="Travel":
    html('<div class="kicker">THE TRAVEL EDIT</div><div class="section-title">Build your ideal travel system.</div><p class="detail">Tell us what kind of trip you are taking and AUREL will build a practical carry recommendation.</p><br>')
    a,b,c=st.columns(3)
    with a:t=st.selectbox("Trip type",["Weekend escape","Business trip","International trip","Long weekend","Daily commute"])
    with b:d=st.selectbox("Duration",["1–2 days","3–4 days","5–7 days","7+ days"])
    with c:s=st.selectbox("Travel style",["Minimal","Balanced","Prepared for anything"])
    if st.button("BUILD MY TRAVEL KIT",use_container_width=True):
        kits={"Weekend escape":["Weekender 38","Field Wallet","Aero Tech Organizer"],"Business trip":["Atlas Carry-On","Transit Pack 24","Aero Tech Organizer"],"International trip":["Atlas Carry-On","Nomad Sling","Field Wallet","Aero Tech Organizer"],"Long weekend":["Weekender 38","Nomad Sling","Terra Bottle"],"Daily commute":["Transit Pack 24","Field Wallet","Terra Bottle"]}
        html(f'<div class="news"><div class="kicker" style="color:#e6c9ad">YOUR AUREL KIT</div><h2>{t} · {d} · {s}</h2><p>A considered starting point for the journey.</p></div>')
        for name in kits[t]:
            x=next(z for z in P if z["name"]==name)
            c1,c2,c3=st.columns([1,5,1])
            with c1:st.image(x["img"],width=90)
            with c2:st.markdown(f"### {x['name']}");st.caption(x["desc"])
            with c3:
                if st.button("ADD",key="tk"+x["id"]):add(x["id"]);st.toast("Added.")

# ---------- STORY ----------
elif st.session_state.page=="Story":
    html("""<div class="hero" style="min-height:430px;background:linear-gradient(90deg,rgba(20,21,19,.92),rgba(20,21,19,.35)),url('https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=1900&q=88');background-size:cover;background-position:center"><div><div class="kicker" style="color:#e6c9ad">OUR STORY</div><div class="hero-title" style="font-size:62px">Less, but better.</div><div class="hero-copy">AUREL began with a simple frustration: everyday products were either over-designed or under-considered.</div></div></div>""")
    a,b=st.columns(2)
    with a:html('<div class="kicker">THE IDEA</div><div class="section-title">Objects should disappear into your day.</div><p class="detail">We design around catching trains, working from cafés, walking through cities, packing at midnight and finding your passport five minutes before boarding.</p>')
    with b:html('<div class="kicker">OUR STANDARD</div><div class="section-title">Useful first. Beautiful second. Always both.</div><p class="detail">Every AUREL piece is considered around utility, organization, tactile experience and longevity.</p>')

# ---------- CONCIERGE ----------
elif st.session_state.page=="Concierge":
    html('<div class="kicker">AUREL CONCIERGE</div><div class="section-title">Shopping, without the scrolling.</div><p class="detail">Ask a question and let our AI concierge narrow the collection down.</p><br>')
    suggestions=["I need a carry-on for a 3-day business trip.","Build me a minimalist everyday carry.","Best gift under ₹5,000?","Compare Atlas Carry-On and Weekender 38.","What should I pack for an international trip?"]
    cols=st.columns(3)
    for i,s in enumerate(suggestions):
        with cols[i%3]:
            if st.button(s,key="cs"+str(i),use_container_width=True):st.session_state.chat.append({"role":"user","content":s});st.rerun()
    for m in st.session_state.chat:
        with st.chat_message(m["role"]):st.markdown(m["content"])
    q=st.chat_input("Ask AUREL Concierge anything...")
    if q:
        st.session_state.chat.append({"role":"user","content":q})
        with st.chat_message("user"):st.markdown(q)
        with st.chat_message("assistant"):
            catalogue="\n".join(f'- {x["name"]} | {x["cat"]} | {money(x["price"])} | {x["desc"]}' for x in P)
            if ai:
                try:
                    r=ai.models.generate_content(model="gemini-3.1-flash-lite",contents=f"REQUEST:\n{q}\nCATALOGUE:\n{catalogue}",config=types.GenerateContentConfig(temperature=.55,system_instruction=SYSTEM))
                    ans=r.text
                except Exception as e:ans=f"Concierge is temporarily unavailable: {e}"
            else:ans="Add `GEMINI_API_KEY` to enable the live AI concierge."
            st.markdown(ans);st.session_state.chat.append({"role":"assistant","content":ans})

# ---------- NEWSLETTER ----------
elif st.session_state.page=="Newsletter":
    html('<div class="news"><div class="kicker" style="color:#e6c9ad">THE AUREL JOURNAL</div><h2>The useful kind of newsletter.</h2><p>One thoughtful dispatch each month: new objects, travel systems, city notes, packing ideas and early access.</p></div><br>')
    first=st.text_input("First name",placeholder="Your name")
    email=st.text_input("Email",placeholder="you@example.com")
    interest=st.selectbox("What interests you most?",["Travel","Everyday carry","Product launches","City guides","All of it"])
    if st.button("JOIN THE JOURNAL",use_container_width=True):
        if valid_email(email):st.session_state.newsletter=True;st.success(f"Welcome {first or 'there'} — your {interest.lower()} dispatch is coming.")
        else:st.error("Please enter a valid email.")
    html('<br><div class="kicker">WHAT YOU GET</div><div class="section-title">A small letter worth opening.</div><br>')
    cols=st.columns(3)
    for col,(n,t,txt) in zip(cols,[("01","Field Notes","Useful travel systems and city observations."),("02","Object Stories","Why we made something and how to use it."),("03","Early Access","Occasional previews before everyone else.")]):
        with col:html(f'<div class="feature"><div class="kicker">{n}</div><div class="feature-title">{t}</div><div class="feature-text">{txt}</div></div>')

# ---------- CART ----------
elif st.session_state.page=="Cart":
    html('<div class="kicker">YOUR BAG</div><div class="section-title">Things you are taking with you.</div><br>')
    if not items(): html('<div class="news"><div class="kicker" style="color:#e6c9ad">EMPTY FOR NOW</div><h2>Your bag is waiting.</h2><p>Start with one useful object.</p></div>')
    else:
        for x,q in items():
            st.markdown(f"**{x['name']}** × {q} — {money(x['price']*q)}")
            a,b=st.columns([1,6])
            with a:
                if st.button("Remove",key="rm"+x["id"]):st.session_state.cart.pop(x["id"],None);st.rerun()
        html(f'<div class="feature" style="margin-top:25px"><div class="meta">SUBTOTAL</div><div style="font:34px Playfair Display">{money(subtotal())}</div><div class="feature-text">Shipping: {money(shipping())} · Discount: -{money(discount())}</div><hr><div style="font:34px Playfair Display">{money(total())}</div></div>')
        if st.button("PROCEED TO CHECKOUT →",use_container_width=True):st.session_state.page="Checkout";st.rerun()

# ---------- CHECKOUT ----------
elif st.session_state.page=="Checkout":
    html('<div class="kicker">CHECKOUT</div><div class="section-title">Almost yours.</div><br>')
    if not items():st.info("Your bag is empty.")
    else:
        a,b=st.columns([1.4,1])
        with a:
            name=st.text_input("Full name");email=st.text_input("Email");phone=st.text_input("Phone");address=st.text_area("Address");city=st.text_input("City");pin=st.text_input("PIN code")
            payment=st.radio("Payment",["UPI","Credit / Debit Card","Cash on Delivery"])
            if st.button("PLACE DEMO ORDER",use_container_width=True):
                if not name or not email or not address or not city or not valid_email(email):st.error("Complete the required fields with a valid email.")
                else:
                    oid="AUR-"+datetime.now().strftime("%Y%m%d%H%M%S");st.session_state.cart={}
                    html(f'<div class="news"><div class="kicker" style="color:#e6c9ad">ORDER CONFIRMED</div><h2>Thank you, {name.split()[0]}.</h2><p>Your demo order <b>{oid}</b> has been created. No real payment was processed.</p></div>')
        with b:
            html(f'<div class="feature"><div class="kicker">ORDER SUMMARY</div><br><b>{money(total())}</b></div>')

# ---------- FOOTER ----------
html('<div class="footer"><div style="font:28px Playfair Display;letter-spacing:4px;color:#25241f">AUREL</div><br>EVERYDAY CARRY · TRAVEL · OBJECTS FOR THE WAY YOU LIVE<br><br>© 2026 AUREL · PRIVACY · RETURNS · SHIPPING · CONTACT</div>')
