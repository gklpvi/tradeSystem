from flask import Flask, request, render_template
import requests
from werkzeug.exceptions import HTTPException, NotFound
from functions import *

app = Flask(__name__)
app.config["REQUEST_URL_TEMPLATE"] = "http://ftx.com/api/markets/%s/%s/orderbook?depth=%d"
app.config["JSON_SORT_KEYS"] = False

@app.route("/", methods = ['GET'])
def home():
    return render_template("home.html")


@app.route("/quote", methods = ['POST'])
def quote():        
    requestData = request.get_json()    # receiving the post request as json

    # fetching the data from the api according to the request daya
    depth = 100
    orderBookData = get_order_book(requestData, depth)
    if orderBookData["type"] == "error":
        return render_template(orderBookData["result"]["errorHTML"]), orderBookData["result"]["errorCode"]
    
    orderBook, reversed = orderBookData["result"]["orderBook"], orderBookData["result"]["reversed"]
        
    if reversed:    # if the pair is reversed, fetched data has to be modified accordingly
        modResult = modify_reversed_data(requestData, orderBook, depth)
        if type(modResult) == tuple:
            return modResult
        
    return trade(requestData, orderBook, depth)    # function will do the requested operations and return a json file

@app.errorhandler(HTTPException) # for any other http exceptions 
def handle_exception(e):
    return render_template('error.html'), 400

if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True) # debug is True only for development purposes