from flask import Flask
from flask import jsonify, request, session
import json
from flask import render_template
#from yahoo_finance import Share
from datetime import date, timedelta
import urllib2


app = Flask(__name__)
base_url = "http://download.finance.yahoo.com/d/quotes.csv?"
history_url = "http://ichart.finance.yahoo.com/table.csv?"

stock_map = {
    'ethical' : ['AAPL', 'GILD', 'GOOG', 'JCI',   'NOV'],
    'growth'  : ['QQQ',  'IWF',  'VUG',  'IVW',   'IWO'],
    'index'   : ['SPY',  'QQQ',  'IWM',  'DIA',   'VTI'],
    'quality' : ['JPM',  'RAI',  'PSA',  'RYAAY', 'PGR'],
    'value'   : ['AAL',  'GILD', 'WFC',  'PBR',   'BRFS']
}

avg_map={}

def get_200day_moving_percent(symbol):
    f="m6"
    query = base_url+"s="+symbol+"&f="+f+"&e=.csv"
    response = urllib2.urlopen(query)
    data = response.read()
    percent = data.replace('%','').strip()
    return float(percent)

def get_price(symbol):
    f="l1"
    query = base_url+"s="+symbol+"&f="+f+"&e=.csv"
    response = urllib2.urlopen(query)
    data = response.read()
    return float(data)


def get_startday():
    startday = date.today() - timedelta(7) 
    return (str(startday.month-1), str(startday.day),str(startday.year))

def get_endday():
    endday = date.today() - timedelta(1)
    return (str(endday.month-1), str(endday.day), str(endday.year))


def get_historical(symbol):
    startday = get_startday()
    endday = get_endday()
    query = history_url+"s="+symbol+"&a="+startday[0]+"&b="+startday[1]+"&c="+startday[2]+"&d="+endday[0]+"&e="+endday[1]+"&f="+endday[2]+"&g=d"
    response = urllib2.urlopen(query)
    data = response.read()
    data = data.split('\n')
    close_price_history = []
    for d in data:
        line = d.split(',')
        if len(line) != 1:
            if line[4] != "Close":
                close_price_history.append(float(line[4]))
    return close_price_history

# Divided by the maximum common divisor
def simplify_ratio(original_ratio_list) :
    original_ratio_list = map(abs, original_ratio_list)
    minEle = min(original_ratio_list)
    return [int(x / minEle) for x in original_ratio_list]

#Selecte 2 stock from one list
#input: list of stock symbol, and num of stock to select(either 2 or 4 in our case)
def select_top_ones(stock_list, num):
    temp_map = {}
    temp_map=dict.fromkeys(stock_list,0) # stock symbol from the stock_list : 200day_moving_avg
    for s in stock_list:
        temp_map[s] = get_200day_moving_percent(s)
    avg_map.update(temp_map)
    top_symbol_list = sorted(temp_map, key =lambda x: temp_map[x], reverse=True)[:num]
   
    return top_symbol_list

#input: top 4 stock symbol list
def processing(selected_list):
    ratio_list = []
    top4_past_info =[]
    for symbol in selected_list:
        ratio_list.append(avg_map[symbol])
        last_five_day_history = get_historical(symbol)
        top4_past_info.append(last_five_day_history)

    top4_avg_ratio = simplify_ratio(ratio_list)
    top4_stock_avgRatio_profolio_list = [selected_list, top4_avg_ratio]

    print top4_stock_avgRatio_profolio_list

    amount = float(request.form.get('Amount'))
    sum_ratio = float(sum(top4_avg_ratio))
    
    #line 99-112 was Laura's code, and I rewrite in loop format, but result is the same. 
    # (see console output and page load)
    top1_amount = amount * top4_avg_ratio[0] / sum_ratio
    top2_amount = amount * top4_avg_ratio[1] / sum_ratio
    top3_amount = amount * top4_avg_ratio[2] / sum_ratio
    top4_amount = amount * top4_avg_ratio[3] / sum_ratio


    top1_profolio = [round( top1_amount/get_price(selected_list[0]) * i, 2 ) for i in top4_past_info[0]]
    top2_profolio = [round( top2_amount/get_price(selected_list[1]) * i, 2 ) for i in top4_past_info[1]]
    top3_profolio = [round( top3_amount/get_price(selected_list[2]) * i, 2 ) for i in top4_past_info[2]]
    top4_profolio = [round( top4_amount/get_price(selected_list[3]) * i, 2 ) for i in top4_past_info[3]]
    top4_stocks_profolio = [x+y+z+w for x, y, z, w in zip(top1_profolio, top2_profolio, top3_profolio, top4_profolio)]

    top4_stock_avgRatio_profolio_list.append(top4_stocks_profolio)
    print top4_stock_avgRatio_profolio_list


    amount_distribute = []
    for r in top4_avg_ratio:
        amount_distribute.append(amount*r/sum_ratio)
    top_potfolio = []
    for i in range(len(selected_list)):
        stock_profolio= [round( amount_distribute[i]/get_price(selected_list[i]) * j, 2 ) for j in top4_past_info[i]]
        top_potfolio.append(stock_profolio)
    top4_stocks_potfolio = []
    for j in range(len(top4_past_info[0])):
        sum_profolio = 0
        for t in top_potfolio:
            sum_profolio+=t[j]
        top4_stocks_potfolio.append(sum_profolio)
    
    top4_stock_avgRatio_profolio_list.append(top4_stocks_potfolio)
    return top4_stock_avgRatio_profolio_list
    
@app.route('/')
def my_form():
    return render_template("index.html")

@app.route('/', methods=['POST'])
def my_form_post():

    amount = request.form['Amount']
    strategies_selected = request.form.getlist('strategies')
    #if one strategy picked, select top4; if two strategy picked, select top2 from each strategy.
    selected_list =[]
    avg_map.clear()
    if len(strategies_selected) == 1:
        selected_list = select_top_ones(stock_map.get(strategies_selected[0]), 4)
    else:
        for s in strategies_selected:
            top2_list = select_top_ones(stock_map.get(s), 2)
            for symbol in top2_list:
               selected_list.append(symbol)
    
    top4_stock_avgRatio_profolio_list = processing(selected_list)

    return render_template("calculateResult.html", var_investment_amount=amount, var_strategy=strategies_selected, 
        var_top3_stocks=top4_stock_avgRatio_profolio_list[0], var_ratio_list=top4_stock_avgRatio_profolio_list[1],
        var_stocks_profolio=top4_stock_avgRatio_profolio_list[2])
  
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



