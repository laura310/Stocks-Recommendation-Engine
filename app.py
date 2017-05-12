from flask import Flask
from flask import jsonify, request, session
import json
from flask import render_template
from yahoo_finance import Share
from datetime import date, timedelta


app = Flask(__name__)


stock_map = {
    'ethical' : ['AAPL', 'GILD', 'GOOG', 'JCI',   'NOV'],
    'growth'  : ['QQQ',  'IWF',  'VUG',  'IVW',   'IWO'],
    'index'   : ['SPY',  'QQQ',  'IWM',  'DIA',   'VTI'],
    'quality' : ['JPM',  'RAI',  'PSA',  'RYAAY', 'PGR'],
    'value'   : ['AAL',  'GILD', 'WFC',  'PBR',   'BRFS']
}


def get_startday() :
    startday = date.today() - timedelta(7)   
    return startday

def get_endday() :
    endday = date.today() - timedelta(1)
    return endday

def get_stock_historical_info(stock_sym) :
    startday = get_startday()
    endday = get_endday()
    stock = Share(stock_sym)
    closes = [c['Close'] for c in stock.get_historical(str(startday), str(endday))]
    floatCloses = [round(float(i), 2) for i in closes]
    return floatCloses

# Divided by the maximum common divisor
def simplify_ratio(original_ratio_list) :
    minEle = min(original_ratio_list)
    return [int(x / minEle) for x in original_ratio_list]

# input: a list of selected stock symbols
# output: a list of two lists: top3 stock symbol list and ratio of 3 symbols
def select_top3(stock_list):
    avg_map=dict.fromkeys(stock_list,0) # stock symbol from the stock_list : 200day_moving_avg
    for s in stock_list:
        avg_map[s] = float(Share(s).get_200day_moving_avg())   
    top3_symbol_list = sorted(avg_map, key = lambda x:avg_map[x], reverse=True)[:3]

    ratio_list = []
    for symbol in top3_symbol_list:
        ratio_list.append(avg_map[symbol])
    top3_avg_ratio = simplify_ratio(ratio_list)
    
    return [top3_symbol_list, top3_avg_ratio]


def processing(stock_list):
    top3_stock_avgRatio_profolio_list = select_top3(stock_list)
    top3_stocks = top3_stock_avgRatio_profolio_list[0]
    top3_avg_ratio = top3_stock_avgRatio_profolio_list[1]


    amount = float(request.form.get('Amount'))
    top1_amount = amount * top3_avg_ratio[0] / sum(top3_avg_ratio)
    top2_amount = amount * top3_avg_ratio[1] / sum(top3_avg_ratio)
    top3_amount = amount * top3_avg_ratio[2] / sum(top3_avg_ratio)
    top3_past_info = [get_stock_historical_info(top3_stocks[0]), get_stock_historical_info(top3_stocks[1]), get_stock_historical_info(top3_stocks[2])]
    top1_profolio = [round( top1_amount/float(Share(top3_stocks[0]).get_price()) * i, 2 ) for i in top3_past_info[0]]
    top2_profolio = [round( top2_amount/float(Share(top3_stocks[1]).get_price()) * i, 2 ) for i in top3_past_info[1]]
    top3_profolio = [round( top3_amount/float(Share(top3_stocks[2]).get_price()) * i, 2 ) for i in top3_past_info[2]]
    top3_stocks_profolio = [x+y+z for x, y, z in zip(top1_profolio, top2_profolio, top3_profolio)]

    top3_stock_avgRatio_profolio_list.append(top3_stocks_profolio)
    return top3_stock_avgRatio_profolio_list



@app.route('/')
def my_form():
    return render_template("index.html")

@app.route('/', methods=['POST'])
def my_form_post():

    amount = request.form['Amount']

    strategies_selected = request.form.getlist('strategies')

    #obtain stock symbol from stock_map using strategy as key 
    stock_list =[]
    for s in strategies_selected:
        for symbol in stock_map.get(s):
            stock_list.append(symbol)

    print stock_list
    top3_stock_avgRatio_profolio_list = processing(stock_list)

    return render_template("calculateResult.html", var_investment_amount=amount, var_strategy=strategies_selected, 
        var_top3_stocks=top3_stock_avgRatio_profolio_list[0], var_ratio_list=top3_stock_avgRatio_profolio_list[1],
        var_stocks_profolio=top3_stock_avgRatio_profolio_list[2])
  
@app.route('/charts')
def charts():
   return render_template('charts.html')
  
finalResult = {}    
@app.route('/result',methods = ['POST'])
def displayCharts():
   input= json.dumps(request.json)
   data = input
   print(data)
   amount = request.json['amount']
   finalResult["errMsg"] = "None"

   # Currently, only support checking only one of the checkbox 
   if 'ethical_chosen' in input:
        top3_stock_avgRatio_profolio_list = ethical_processing()
        finalResult["Strategy"] = "Ethical Investing"
   if 'growth_chosen' in input:
        top3_stock_avgRatio_profolio_list = growth_processing()
        finalResult["Strategy"] = "Growth Investing"
   if 'index_chosen' in input:
        top3_stock_avgRatio_profolio_list = index_processing()
        finalResult["Strategy"] = "Index Investing"
   if 'quality_chosen' in input:
        top3_stock_avgRatio_profolio_list = quality_processing()
        finalResult["Strategy"] = "Quality Investing"
   if 'value_chosen' in input:
        top3_stock_avgRatio_profolio_list = value_processing()
        finalResult["Strategy"] = "Value Investing"
   
   finalResult["Top3"] = top3_stock_avgRatio_profolio_list[0];
   finalResult["RatioList"] = top3_stock_avgRatio_profolio_list[1];
   finalResult["PastInfo"] = top3_stock_avgRatio_profolio_list[2];
   
   jsonResult = json.dumps(finalResult)
   return jsonResult

if __name__ == '__main__':
    #app.run()
    app.run( host='0.0.0.0',port = 5000, debug = True) # run app in debug mode



