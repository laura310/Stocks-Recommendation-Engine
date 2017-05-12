from flask import Flask
from flask import jsonify, request, session
import json
from flask import render_template
from yahoo_finance import Share
from datetime import date, timedelta
import yahoo_finance

app = Flask(__name__)

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

def simplify_ratio(original_ratio_list) :
    minEle = min(original_ratio_list)
    return [int(x / minEle) for x in original_ratio_list]


def processing(stocks_list):
    avg0 = float( Share(stocks_list[0]).get_200day_moving_avg() )
    avg1 = float( Share(stocks_list[1]).get_200day_moving_avg() )
    avg2 = float( Share(stocks_list[2]).get_200day_moving_avg() )
    avg3 = float( Share(stocks_list[3]).get_200day_moving_avg() )
    avg4 = float( Share(stocks_list[4]).get_200day_moving_avg() )
    avg_list = [avg0, avg1, avg2, avg3, avg4]


    top3_index_list = sorted(range(len(avg_list)), key=lambda i: avg_list[i], reverse=True)[:3]
    top1Index = top3_index_list[0]
    top2Index = top3_index_list[1]
    top3Index = top3_index_list[2]
    top3_stocks = [stocks_list[top1Index], stocks_list[top2Index], stocks_list[top3Index]]


    top3_avg_ratio_original = [avg_list[top1Index], avg_list[top2Index], avg_list[top3Index]]
    top3_avg_ratio = simplify_ratio(top3_avg_ratio_original)


    amount = float(request.form.get('Amount'))
    top3_past_info = [get_stock_historical_info(top3_stocks[0]), get_stock_historical_info(top3_stocks[1]), get_stock_historical_info(top3_stocks[2])]
    top1_profolio = [round( amount/float(Share(top3_stocks[0]).get_price()) * i, 2 ) for i in top3_past_info[0]]
    top2_profolio = [round( amount/float(Share(top3_stocks[1]).get_price()) * i, 2 ) for i in top3_past_info[1]]
    top3_profolio = [round( amount/float(Share(top3_stocks[2]).get_price()) * i, 2 ) for i in top3_past_info[2]]
    top3_stocks_profolio = [top1_profolio, top2_profolio, top3_profolio]


    top3_stock_avgRatio_profolio_list = [top3_stocks, top3_avg_ratio, top3_stocks_profolio]
    return top3_stock_avgRatio_profolio_list


# AAPL  GILD    GOOG   JCI  NOV
def ethical_processing() :
    stocks_list = ['AAPL', 'GILD', 'GOOG', 'JCI', 'NOV']
    top3_stock_avgRatio_profolio_list = processing(stocks_list)
    return top3_stock_avgRatio_profolio_list


# # QQQ   IWF VUG IVW IWO
def growth_processing():
    stocks_list = ['QQQ', 'IWF', 'VUG', 'IVW', 'IWO']
    top3_stock_avgRatio_profolio_list = processing(stocks_list)
    return top3_stock_avgRatio_profolio_list


# # SPY   QQQ     IWM     DIA     VTI
def index_processing():
    stocks_list = ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI']
    top3_stock_avgRatio_profolio_list = processing(stocks_list)
    return top3_stock_avgRatio_profolio_list


# # JPM   RAI   PSA   RYAAY   PGR
def quality_processing():
    stocks_list = ['JPM', 'RAI', 'PSA', 'RYAAY', 'PGR']
    top3_stock_avgRatio_profolio_list = processing(stocks_list)
    return top3_stock_avgRatio_profolio_list


# # AAL   GILD    WFC    PBR    BRFS
def value_processing():
    stocks_list = ['AAL', 'GILD', 'WFC', 'PBR', 'BRFS']
    top3_stock_avgRatio_profolio_list = processing(stocks_list)
    return top3_stock_avgRatio_profolio_list



@app.route('/')
def my_form():
    return render_template("index.html")

@app.route('/', methods=['POST'])
def my_form_post():

    amount = request.form['Amount']
    # Currently, only support checking only one of the checkbox 
    if request.form.get('ethical_chosen'):
        top3_stock_avgRatio_profolio_list = ethical_processing()
        strategy = request.form.get('ethical_chosen')
    if request.form.get('growth_chosen'):
        top3_stock_avgRatio_profolio_list = growth_processing()
        strategy = request.form.get('growth_chosen')
    if request.form.get('index_chosen'):
        top3_stock_avgRatio_profolio_list = index_processing()
        strategy = request.form.get('index_chosen')
    if request.form.get('quality_chosen'):
        top3_stock_avgRatio_profolio_list = quality_processing()
        strategy = request.form.get('quality_chosen')
    if request.form.get('value_chosen'):
        top3_stock_avgRatio_profolio_list = value_processing()
        strategy = request.form.get('value_chosen')


    return render_template("calculateResult.html", var_investment_amount=float(amount), var_strategy=strategy, 
        var_top3_stocks=top3_stock_avgRatio_profolio_list[0], var_ratio_list=top3_stock_avgRatio_profolio_list[1], 
        var_top3_pastInfo=top3_stock_avgRatio_profolio_list[2])

    
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



