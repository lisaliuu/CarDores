from flask_pymongo import PyMongo
from flask import Flask


app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://admin:underthesea@cluster0.hp1znhg.mongodb.net/cardores?retryWrites=true&w=majority" 
mongo = PyMongo(app) #sets database to cardores