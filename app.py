from flask import Flask, request, jsonify, Response
import yfinance as yf
import requests
import ast
import operator

app = Flask(__name__)

def get_airport_temp(iata_code):
    url = f"http://www.airport-data.com/api/ap_info.json?iata={iata_code}"
    airport_response = requests.get(url)
    airport_data = airport_response.json()
    print("AirportRESPONSE:", airport_data)  # Debugging line
    
    if "status" not in airport_data or airport_data["status"] != 200:
        raise ValueError("Invalid airport code or data not found.")
    
    if "latitude" not in airport_data or "longitude" not in airport_data:
        raise ValueError("Invalid airport data received.")
    
    lat = float(airport_data["latitude"])
    lon = float(airport_data["longitude"])
    
    weather_api_key = "37b35a8aab9a4456b1b100104252804"
    weather_api_url = f"http://api.weatherapi.com/v1/current.json?key={weather_api_key}&q={lat},{lon}"
    print(f"Calling weather API: {weather_api_url}")

    weather_response = requests.get(weather_api_url)
    weather_data = weather_response.json()
    print("Weather API response:", weather_data)

    if "current" not in weather_data or "temp_c" not in weather_data["current"]:
        raise ValueError("Weather data not available.")

    return weather_data["current"]["temp_c"]

def eval_expression(expr):
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv
    }

    def eval_node(node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            op = operators[type(node.op)]
            return op(left, right)
        elif isinstance(node, ast.Expression):
            return eval_node(node.body)
        else:
            raise TypeError(f"Unsupported type: {type(node)}")

    try:
        tree = ast.parse(expr, mode='eval')
        return eval_node(tree.body)
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")

def get_stock_price(stock_code):
    stock = yf.Ticker(stock_code)
    todays_data = stock.history(period='1d')

    if todays_data.empty:
        raise ValueError("Invalid stock code or no data available.")
    
    return todays_data['Close'][0]


@app.route('/', methods=['GET'])
def index():
    query_airport = request.args.get('queryAirportTemp')
    query_stock = request.args.get('queryStockPrice')
    query_eval = request.args.get('queryEval')
    
    if query_eval:
        query_eval = query_eval.replace(' ', '+')
        
    params = [query_airport, query_stock, query_eval]
    provided_params = [param for param in params if param is not None]

    if len(provided_params) != 1:
        return "Error: Exactly one query parameter must be provided.", 400

    accept = request.headers.get('Accept', 'application/json')

    try:
        if query_airport:
            result = get_airport_temp(query_airport)
        elif query_stock:
            result = get_stock_price(query_stock)
        elif query_eval:
            result = eval_expression(query_eval)
        else:
            return "Error: No valid parameter provided.", 400
    except Exception as e:
        return f"Error: {str(e)}", 500

    if 'application/xml' in accept or 'text/xml' in accept:
        content = f"<result>{result}</result>"
        return Response(content, mimetype='application/xml')
    else:
        return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
