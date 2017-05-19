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
google_url="http://www.google.com/finance/historical?"

stock_map = {
    'Ethical Investing' : ['AAPL', 'GOOG', 'JCI',   'NOV',  'NSRGY'],
    'Growth Investing'  : ['QQQ',  'IWF',  'VUG',  'IVW',   'IWO'],
    'Index Investing'   : ['SPY',  'IWM',  'DIA',   'VTI',  'MDY'],
    'Quality Investing' : ['JPM',  'RAI',  'PSA',  'RYAAY', 'PGR'],
    'Value Investing'   : ['AAL',  'GILD', 'WFC',  'PBR',   'BRFS']
}

avg_map={}

def get_200day_moving_percent(symbol):
    f="m6"
    query = base_url+"s="+symbol+"&f="+f+"&e=.csv"
    response = urllib2.urlopen(query)
    data = response.read()
    percent = data.replace('%','').strip()
    print(percent)
    return float(percent)

def get_price(symbol):
    f="l1"
    query = base_url+"s="+symbol+"&f="+f+"&e=.csv"
    response = urllib2.urlopen(query)
    data = response.read()
    return float(data)

def get_company_name(selected_list):
    f = "n"
    company_names = []
    for symbol in selected_list:
        query = base_url+"s="+symbol+"&f="+f+"&e=.csv"
        response = urllib2.urlopen(query)
        data = response.read()
        data = data.replace('\n','').strip()
        company_names.append(data)
    return company_names
    

def get_startday():
    startday = date.today() - timedelta(7) 
    return (str(startday.month-1), str(startday.day),str(startday.year))

def get_endday():
    endday = date.today() - timedelta(1)
    return (str(endday.month-1), str(endday.day), str(endday.year))

def get_startday_google() :
    startday = date.today() - timedelta(7) 
    return (str(startday.month), str(startday.day),str(startday.year))

def get_endday_google() :
    endday = date.today() - timedelta(1)
    return (str(endday.month), str(endday.day), str(endday.year))

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

def get_historical_google(symbol):
    startday = get_startday_google()
    endday = get_endday_google()
    query = google_url+"q="+symbol+"&histperiod=daily&startdate="+startday[0]+"+"+startday[1]+"+"+startday[2]+"&enddate="+endday[0]+"+"+endday[1]+"+"+endday[2]+"&output=csv"
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
    sumEle = sum(original_ratio_list)
    return [round((x / sumEle * 100),1) for x in original_ratio_list]

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
def processing(selected_list, amnt):
    ratio_list = []
    top4_past_info =[]
    for symbol in selected_list:
        ratio_list.append(avg_map[symbol])
        last_five_day_history = get_historical_google(symbol)
        top4_past_info.append(last_five_day_history)

    top4_avg_ratio = simplify_ratio(ratio_list)
    top4_stock_avgRatio_profolio_list = [top4_avg_ratio]

    amount = float(amnt)
    sum_ratio = float(sum(top4_avg_ratio))

    amount_distribute = []
    for r in top4_avg_ratio:
        amount_distribute.append(amount*r/sum_ratio)
    top_potfolio = []
    top4_stock_num =[]
    for i in range(len(selected_list)):
        stock_num = float(amount_distribute[i]/get_price(selected_list[i]))
        top4_stock_num.append(stock_num)
        stock_profolio= [stock_num * j for j in top4_past_info[i]]
        top_potfolio.append(stock_profolio)
        
    session['stock_num'] = top4_stock_num
    session['selected_list'] = selected_list
    
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
    strategies=[]
    #if one strategy picked, select top4; if two strategy picked, select top2 from each strategy.
    selected_list =[]
    avg_map.clear()
    if len(strategies_selected) == 1:
        selected_list = select_top_ones(stock_map.get(strategies_selected[0]), 4)
        strategies.append(str(strategies_selected[0]))
    else:
        for s in strategies_selected:
            strategies.append(str(s))
            top2_list = select_top_ones(stock_map.get(s), 2)
            for symbol in top2_list:
               selected_list.append(symbol)
    
    company_names = get_company_name(selected_list)

    top4_stock_avgRatio_profolio_list = processing(selected_list, amount)

    return render_template("calculateResult.html", var_investment_amount=amount, var_strategy=strategies, var_companies = company_names,
        var_top3_stocks=selected_list, var_ratio_list=top4_stock_avgRatio_profolio_list[0],
        var_stocks_profolio=top4_stock_avgRatio_profolio_list[1])
 

@app.route('/charts',  methods=['POST'])
def charts():
    amount = request.form['Amount']
    strategies_selected = request.form.getlist('strategies')
    strategies=[]
    #if one strategy picked, select top4; if two strategy picked, select top2 from each strategy.
    selected_list =[]
    avg_map.clear()
    if len(strategies_selected) == 1:
        selected_list = select_top_ones(stock_map.get(strategies_selected[0]), 4)
        strategies.append(str(strategies_selected[0]))
    else:
        for s in strategies_selected:
            strategies.append(str(s))
            top2_list = select_top_ones(stock_map.get(s), 2)
            for symbol in top2_list:
               selected_list.append(symbol)

    company_names = get_company_name(selected_list)

    top4_stock_avgRatio_profolio_list = processing(selected_list, amount)
    
    if len(strategies) == 1:
        strategies.append(strategies[0]);

    return render_template("charts.html", var_investment_amount=amount, var_strategy=strategies, var_companies = company_names,
        var_top3_stocks=selected_list, var_ratio_list=top4_stock_avgRatio_profolio_list[0],
        var_stocks_profolio=top4_stock_avgRatio_profolio_list[1])


@app.route('/getLatest', methods =['POST'])
def current_value():
    stock_num = session['stock_num']
    selected_stock_symbol = session['selected_list']
    current_value = 0
    for i in range(len(stock_num)):
        current_value += float(stock_num[i])*get_price(selected_stock_symbol[i])
   #current_value = round(current_value, 2)
    send_value_in_str = "$"+ str(current_value)
    print ("sssssss" + send_value_in_str)
    return send_value_in_str



finalResult = {}    
@app.route('/result',methods = ['POST'])
def displayCharts():
   input= json.dumps(request.json)
   data = input
   print(data)
   amount = request.json['amount']
   strategies_selected = []
   finalResult["errMsg"] = "None"
   finalResult["Strategy"] = []

   # Currently, only support checking only one of the checkbox 
   if 'ethical_chosen' in input:
        finalResult["Strategy"].append("Ethical Investing")
        strategies_selected.append("Ethical Investing")
   if 'growth_chosen' in input:
        finalResult["Strategy"].append("Growth Investing")
        strategies_selected.append("Growth Investing")
   if 'index_chosen' in input:
        finalResult["Strategy"].append("Index Investing")
        strategies_selected.append("Index Investing")
   if 'quality_chosen' in input:
        finalResult["Strategy"].append("Quality Investing")
        strategies_selected.append("Quality Investing")
   if 'value_chosen' in input:
        finalResult["Strategy"].append("Value Investing")
        strategies_selected.append("Value Investing")
   
   #if one strategy picked, select top4; if two strategy picked, select top2 from each strategy.
   selected_list = []
   avg_map.clear()
   if len(strategies_selected) == 1:
        print(strategies_selected[0])
        selected_list = select_top_ones(stock_map.get(strategies_selected[0]), 4)
   else:
        for s in strategies_selected:
            print(s)
            top2_list = select_top_ones(stock_map.get(s), 2)
            for symbol in top2_list:
               selected_list.append(symbol)
               
   company_names = get_company_name(selected_list)               
    
   top4_stock_avgRatio_profolio_list = processing(selected_list, amount)

   if len(strategies_selected) == 1:
        strategies_selected.append(strategies_selected[0]);
   finalResult["Top3"] = selected_list;
   finalResult["RatioList"] = top4_stock_avgRatio_profolio_list[0];
   finalResult["PastInfo"] = top4_stock_avgRatio_profolio_list[1]; 
   finalResult["Strategy"] = strategies_selected;
   finalResult["Company"] = company_names;
   jsonResult = json.dumps(finalResult)
   return jsonResult

if __name__ == '__main__':
    #app.run()
    app.secret_key = 'ABDCEES@$#FAAS'
    app.run( host='0.0.0.0',port = 5000, debug = True) # run app in debug mode



