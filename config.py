import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
    DYNAMODB_TABLE_ALERTS = os.environ.get("DYNAMODB_TABLE_ALERTS", "Alerts")

    DYNAMODB_TABLE_USERS = os.environ.get("DYNAMODB_TABLE_USERS", "Users")
    
    DYNAMODB_TABLE_WATCHLIST = os.environ.get("DYNAMODB_TABLE_WATCHLIST", "Watchlist")
    DYNAMODB_TABLE_PRICES = os.environ.get("DYNAMODB_TABLE_PRICES", "MarketPrices")
