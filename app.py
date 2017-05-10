from flask import Flask
from flask import request
from flask import render_template
from yahoo_finance import Share
from datetime import date, timedelta


app = Flask(__name__)


def get_startday() :
    startday = date.today() - timedelta(5)   
    return startday

def get_endday() :
    endday = date.today() - timedelta(1)
    return endday

def get_stock_historical_info(stock_sym) :
    startday = get_startday()
    endday = get_endday()
    stock = Share(stock_sym)
    closes = [c['Close'] for c in stock.get_historical(str(startday), str(endday))]
    floatCloses = [float(i) for i in closes]

    return floatCloses


def processing(stocks_list):
    info0 = get_stock_historical_info(stocks_list[0])
    info1 = get_stock_historical_info(stocks_list[1])
    info2 = get_stock_historical_info(stocks_list[2])
    info3 = get_stock_historical_info(stocks_list[3])
    info4 = get_stock_historical_info(stocks_list[4])
    info_list = [info0, info1, info2, info3, info4]

    avg0 = round(sum(info0)/len(info0), 2)
    avg1 = round(sum(info1)/len(info1), 2)
    avg2 = round(sum(info2)/len(info2), 2)
    avg3 = round(sum(info3)/len(info3), 2)
    avg4 = round(sum(info4)/len(info4), 2)
    avg_list = [avg0, avg1, avg2, avg3, avg4]

    top3_index_list = sorted(range(len(avg_list)), key=lambda i: avg_list[i], reverse=True)[:3]
    top1Index = top3_index_list[0]
    top2Index = top3_index_list[1]
    top3Index = top3_index_list[2]
    top3_stocks = [stocks_list[top1Index], stocks_list[top2Index], stocks_list[top3Index]]

    top3_avg = [avg_list[top1Index], avg_list[top2Index], avg_list[top3Index]]
    top3_stock_and_avg_list = [top3_stocks, top3_avg]
    return top3_stock_and_avg_list


# AAPL  GILD    GOOG   JCI  NOV
def ethical_processing() :
    stocks_list = ['AAPL', 'GILD', 'GOOG', 'JCI', 'NOV']
    top3_stock_and_avg_list = processing(stocks_list)
    return top3_stock_and_avg_list


# # QQQ   IWF VUG IVW IWO
def growth_processing():
    stocks_list = ['QQQ', 'IWF', 'VUG', 'IVW', 'IWO']
    top3_stock_and_avg_list = processing(stocks_list)
    return top3_stock_and_avg_list


# # SPY   QQQ     IWM     DIA     VTI
def index_processing():
    stocks_list = ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI']
    top3_stock_and_avg_list = processing(stocks_list)
    return top3_stock_and_avg_list


# # JPM   RAI   PSA   RYAAY   PGR
def quality_processing():
    stocks_list = ['JPM', 'RAI', 'PSA', 'RYAAY', 'PGR']
    top3_stock_and_avg_list = processing(stocks_list)
    return top3_stock_and_avg_list


# # AAL   GILD    WFC    PBR    BRFS
def value_processing():
    stocks_list = ['AAL', 'GILD', 'WFC', 'PBR', 'BRFS']
    top3_stock_and_avg_list = processing(stocks_list)
    return top3_stock_and_avg_list



@app.route('/')
def my_form():
    return render_template("index.html")

@app.route('/', methods=['POST'])
def my_form_post():

    amount = request.form['Amount']
    # Currently, only support checking only one of the checkbox 
    if request.form.get('ethical_chosen'):
        top3_stock_and_avg_list = ethical_processing()
        strategy = request.form.get('ethical_chosen')
    if request.form.get('growth_chosen'):
        top3_stock_and_avg_list = growth_processing()
        strategy = request.form.get('growth_chosen')
    if request.form.get('index_chosen'):
        top3_stock_and_avg_list = index_processing()
        strategy = request.form.get('index_chosen')
    if request.form.get('quality_chosen'):
        top3_stock_and_avg_list = quality_processing()
        strategy = request.form.get('quality_chosen')
    if request.form.get('value_chosen'):
        top3_stock_and_avg_list = value_processing()
        strategy = request.form.get('value_chosen')


    return render_template("calculateResult.html", var_investment_amount=float(amount), var_strategy=strategy, 
        var_top3_stocks=top3_stock_and_avg_list[0], var_top3_avg=top3_stock_and_avg_list[1])

if __name__ == '__main__':
    app.run()



