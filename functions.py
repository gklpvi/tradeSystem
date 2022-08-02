from flask import jsonify, render_template, current_app
import requests

def get_order_book(requestData, depth):
    """
     Description:
      * fetching the data from the API
     Inputs:
      -> requestData: requested data in JSON format
      -> depth: number of offers
     Outputs:
      -> result: returns the data and a flag indicating whether it is reversed or not
    """
    url = current_app.config["REQUEST_URL_TEMPLATE"] % (requestData["base_currency"], requestData["quote_currency"], depth)
    orderBook = requests.get(url).json()
    reversed = False
    if(not orderBook['success']):   # if the requested pair does not exist, its reverse should be checked
        reversedUrl = current_app.config["REQUEST_URL_TEMPLATE"] % (requestData["quote_currency"], requestData["base_currency"], depth)
        orderBook = requests.get(reversedUrl).json()
        reversed = True
        if(not orderBook["success"]):   # if its reverse also does not exist then request was incorrect
            # return render_template('no_such_pair.html'), 400    # requested pairs does not exist error
            return {"result": {"errorHTML": "no_such_pair.html", "errorCode": 400}, "type": "error"}
    
    return {"result": {"orderBook": orderBook, "reversed": reversed}, "type": "data"}


def modify_reversed_data(requestData, orderBook, depth):
    """
     Description:
      * reversing the fetched data 
     Inputs:
      -> requestData: requested data in JSON format
      -> orderBook: fetched data
      -> depth: number of offers
     Outputs:
      -> returns an error message if action type is unknown
    """
    if requestData["action"] == "buy":
        requestData["action"] = "sell"
        for i in range (depth):
            orderBook["result"]["asks"][i][1] *= orderBook["result"]["asks"][i][0]
            orderBook["result"]["asks"][i][0]  = 1 / orderBook["result"]["asks"][i][0]
    elif requestData["action"]  == "sell":
        requestData["action"] = "buy"
        for i in range (depth):
            orderBook["result"]["bids"][i][1] *= orderBook["result"]["bids"][i][0]
            orderBook["result"]["bids"][i][0]  = 1 / orderBook["result"]["bids"][i][0]
    else:
        return render_template('error.html'), 400  # unknown action type error


def trade(requestData, orderBook, depth):  
    """
     Description:
      * doing the trading operations 
     Inputs:
      -> requestData: requested data in JSON format
      -> orderBook: fetched data
      -> depth: number of offers
     Outputs:
      -> returns a JSON as the format asked
    """
    requestAmount = float(requestData["amount"])   # to keep track of how much is bought/sold
    if requestAmount == 0:
        return "requested amount must be greater than 0", 400  # incorrect amount error

    currentAmount = requestAmount
    totalWeight = currentOffer =  0  

    if requestData["action"] == "buy": 
        tradeType = "bids"
    else:
        tradeType = "asks"

    while(currentAmount > 0):  # matching the offers fit the most with the request
        if(currentAmount > orderBook["result"][tradeType][currentOffer][1]):    # getting the weighted price 
            currentAmount -= orderBook["result"][tradeType][currentOffer][1]
            totalWeight += orderBook["result"][tradeType][currentOffer][0] * orderBook["result"][tradeType][currentOffer][1] 
            currentOffer += 1
        elif(currentAmount <= orderBook["result"][tradeType][currentOffer][1]):
            totalWeight += orderBook["result"][tradeType][currentOffer][0] * currentAmount 
            currentAmount = 0
        if(currentOffer >= depth and currentAmount != 0): # if all the offers are traversed but could not meet the requested amount
            return render_template('not_enough_offer.html'), 400  # not enough offers

    return jsonify(total = str(totalWeight), price = str(totalWeight / requestAmount), currency = requestData["quote_currency"])