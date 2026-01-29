from flask import Flask, render_template, request, redirect, url_for, session
import requests
from datetime import datetime
import boto3
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
AWS_REGION =Config.AWS_REGION
dynamodb =  boto3.resource("dynamodb", region_name = AWS_REGION)
sns= boto3.client("sns",region_name = AWS_REGION)

users_table =  dynamodb.Table(Config.DYNAMODB_TABLE_USERS)
watchlist_table   = dynamodb.Table(Config.DYNAMODB_TABLE_WATCHLIST)


prices_table  = dynamodb.Table(Config.DYNAMODB_TABLE_PRICES)

SNS_TOPIC_ARN = Config.SNS_TOPIC_ARN


def get_crypto_prices():
    
    url ="https://api.coingecko.com/api/v3/simple/price"
    
    params ={"ids":"bitcoin,ethereum", "vs_currencies": "usd"}

    try:
        response =requests.get(url,params =params,timeout=5)
        response.raise_for_status()
        data = response.json()
        
    except Exception as e:
        print("API error:", e)
        return {}

    prices = {
        
        "Bitcoin":data.get("bitcoin",{}).get("usd"),
        "Ethereum": data.get("ethereum", {}).get("usd")
    }

    timestamp =datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for coin, price in prices.items():
        if isinstance( price,(int, float)):
            prices_table.put_item(
                Item={
                    "coin":coin,
                    "timestamp" : timestamp,
                    "price" : price
                    
                }
            )
    return prices

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/signup",methods = ["GET", "POST"])
def signup():
    if request.method == "POST":
        
        username =request.form["username"]
        password =  request.form["password"]
        existing = users_table.get_item(Key ={"username": username})
        if "Item" in existing:
            return "User already exists!"
            

        users_table.put_item(Item= {"username":username,"password":password})
        return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/login",methods=["GET", "POST"])
def login():
    if request.method =="POST":
        username =request.form["username"]
        password   = request.form["password"]


        
        res =users_table.get_item(Key={"username": username})
        if "Item" in res and res["Item"]["password"] == password:
            
            session["user"] = username
            
            return redirect(url_for("dashboard"))

        return "Invalid credentials!"
    return render_template("login.html")



@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    user  = session["user"]
    prices = get_crypto_prices()

    watchlist_res = watchlist_table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("username").eq(user)
    )
    watchlist = [item["coin"] for item in watchlist_res.get("Items", [])]

    alerts_res = dynamodb.Table("Alerts").query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("username").eq(user)
    )
    triggered_alerts = []

    
    for alert in alerts_res.get("Items", []):
        coin = alert["coin"]
        
        target_price = alert["target_price"]
        current_price = prices.get(coin)

        if isinstance(current_price, (int, float)) and current_price <= target_price:
            message = f"{coin} dropped to ${current_price} (Alert: ${target_price})"
            triggered_alerts.append(message)
            sns.publish(
                
                TopicArn=SNS_TOPIC_ARN,
                Subject="Crypto Price Alert",
                
                Message=message
            )
    return render_template(
        "dashboard.html",
        user= user,
        prices = prices,
        watchlist = watchlist,
        triggered_alerts = triggered_alerts,
        
        history= {}
    )

@app.route("/add_to_watchlist", methods=["POST"])
def add_to_watchlist():
    
    watchlist_table.put_item(
        Item={
            "username":session["user"],
            "coin": request.form["coin"]
        }
    )
    return redirect(url_for("dashboard"))
@app.route("/set_alert",methods =["POST"])
def set_alert():
    dynamodb.Table("Alerts").put_item(
        Item={
            "username":session["user"],
            "coin" : request.form["coin"],
            "target_price" : float(request.form["price"])
        }
    )
    return redirect(url_for("dashboard"))



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)



