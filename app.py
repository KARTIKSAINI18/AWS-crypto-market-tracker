from flask import Flask, render_template, request, redirect, url_for, session
import requests
from datetime import datetime
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

users = {}
price_history = {}

def get_crypto_prices():
    url ="https://api.coingecko.com/api/v3/simple/price"
    params = {
        "ids" : "bitcoin,ethereum",
        "vs_currencies" : "usd"
    }
    response = requests.get(url, params=params)
    data = response.json()
    prices = {
        "Bitcoin": data["bitcoin"]["usd"],
        "Ethereum": data["ethereum"]["usd"]
    }
    timestamp =datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for coin,price in prices.items():
        price_history.setdefault(coin, []).append({
            "price" : price,
            "time" : timestamp
        })
        price_history[coin]= price_history[coin][-10:]
    return prices
watchlists= {}
alerts = {}

@app.route("/")
def index():
    return render_template("index.html")




@app.route( "/signup" , methods = ["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users:
            return "User already exists! "

        users[username] = password
        watchlists[username] = []
        alerts[username] = {}
        return redirect(url_for("login"))

    return render_template("signup.html")

@app.route("/login",methods = [ "GET"  , "POST"])
def login():
    if request.method == "POST":
        username =request.form["username"]
        password =request.form["password"]

        if username in users and users[username] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        return "Invalid credentials!"
    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    prices = get_crypto_prices()

    triggered_alerts = []
    for coin, alert_price in alerts.get(user, {}).items():
        if prices.get(coin) <= alert_price:
            triggered_alerts.append(
                f"{coin} dropped to ${prices[coin]} (Alert: ${alert_price})"
            )
    return render_template(
        "dashboard.html",
        user=user,
        prices=prices,
        watchlist=watchlists.get(user, []),
        triggered_alerts=triggered_alerts,
        history=price_history
    )

@app.route("/add_to_watchlist", methods=["POST"])
def add_to_watchlist():
    watchlists[session["user"]].append(request.form["coin"])
    return redirect(url_for("dashboard"))




@app.route("/set_alert", methods=["POST"])
def set_alert():
    alerts[session["user"]][request.form["coin"]] = float(request.form["price"])
    return redirect(url_for("dashboard"))
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
