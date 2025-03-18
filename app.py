from config import Config
from functools import wraps

from six.moves.urllib.request import urlopen
from typing import Dict
from flask_cors import cross_origin
from jose import jwt

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email.mime.base import MIMEBase
from email import encoders

from unidecode import unidecode
from enum import Enum
import datetime
import os

#languages management
from flask_babel import Babel, gettext, refresh, _

#I use Polib to read babel files
import polib
# I need to update translations files after adding new words to pot 
import subprocess

from unicodedata import decimal
#from urllib import request
from flask import Flask, jsonify, request_started, request_tearing_down, send_file, session, flash
from flask import render_template, g, Response, _request_ctx_stack
from flask import request, url_for,redirect
from flask_mysql_connector import MySQL
#import simplejson as js
import json as json
import magic
import decimal
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
#import geopy
#from geopy import distance
#from geopy.geocoders import Nominatim
import csv


os.path.abspath(os.path.dirname(__file__))
#Detect langage in the request
def get_locale():
    return session.get('lang', 'fr')   


""" 
Just mysql connector worked this time. So... 
We need to add websocket too
In Normal way, json inital class doesnt parse decimals. Then we used simplejson
"""
app = Flask(__name__)

app.config.from_object(Config)
mysql = MySQL(app)
babel = Babel(app, locale_selector=get_locale)

#AUTH0
# This is the AUTH0 CODE

#Format error response and append status code
class AuthError(Exception):
    """
    An authError is raised whenever the authentification failed.
    """
    def __init__(self, error:Dict[str, str], status_code:int):
        super().__init__()
        self.error = error
        self.status_code = status_code

#AuthError handler
@app.errorhandler(AuthError)
def handle_auth_error(ex:AuthError) -> Response:
    """
    serializes the given AuthError as Json as sets the response status code accordingly
    :param ex: an auth error
    :return: a json serialized ex response
    """
    response = jsonify(ex.error)
    response.status_code = ex.status_code
    return response

def get_token_auth_header() -> str :
    """
    Obtains the access token  from the Authorization Header
    """
    auth = request.headers.get("Authorization", None)
    if not auth: 
        raise AuthError({"code":"authorization_header_missing", "description":"Authorization header is expected"}, 401)
    
    parts = auth.split()

    if parts[0].lower() != 'bearer':
        raise AuthError({"code":"invalid_header", "description":"Authorization header must start with Bearer"}, 401)
    
    elif len(parts) == 1:
        raise AuthError({"code":"invalid_header", "description":"Token not found"}, 401)
    
    elif len(parts) > 2:
        raise AuthError({"code":"invalid_header", "description":"Authorization header must be Bearer token"}, 401)
    
    token = parts[1]
    return token

def requires_scope(required_scope:str) -> bool:
    """
    Determines if the required scope is present in the access token 
    Args:
        required_scope(str): The scope required to acess ressource
    """
    token = get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)
    if unverified_claims.get("scope"):
        token_scopes = unverified_claims["scope"].split()
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return True
    return False



#JWT
JWKS_URL = f"https://{app.config['AUTH0_DOMAIN']}/.well-known/jwks.json"

#Create a JWT require decorator
def requires_auth(func):
    """
    Determines if the access token is valid
    """
    @wraps(func)
    def decorated(*args, **kwargs):
        token = get_token_auth_header()
        jsonurl = urlopen(JWKS_URL)
        jwks = json.loads(jsonurl.read())
        try:
            unverified_header = jwt.get_unverified_header(token)
        except jwt.JWTError as jwt_error:
            raise AuthError({"code":"invalid_header", "description":
                             "Invalid Header."
                             "Use an REMOVED signed JWT Access Token"}, 401) from jwt_error
        
        if unverified_header["alg"] != "REMOVED":
            raise AuthError({"code":"invalid_header", "description":
                             "Invalid Header."
                             "Use an REMOVED signed JWT Access Token"}, 401)
        
        rsa_key = {}
        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }
        
        if rsa_key:
            try: 
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=app.config['ALGORITHMS'],
                    audience=app.config['AUTH0_AUDIENCE'],
                    issuer=f"https://{app.config['AUTH0_DOMAIN']}/"
                )
            except jwt.ExpiredSignatureError as expired_error:
                raise AuthError({"code":"token_expired", "description":"Token is expired"}, 401) from expired_error
            
            except jwt.JWTClaimsError as jwt_claims_error:
                raise AuthError({"code":"invalid_claims", "description":
                                 "incorrect claims,"
                                 "please check the audience and issuer whixh was"
                                 f" audience: {app.config['AUTH0_AUDIENCE']} and "
                                 f"Issuer : https://{app.config['AUTH0_DOMAIN']}/"}, 401) from jwt_claims_error

            except Exception as exc:
                raise AuthError({"code":"invalid_header",
                                 "description":
                                 "Unable to parse authentification"
                                 "token."}, 401) from exc
            
            _request_ctx_stack.top.current_user = payload
            return func(*args, **kwargs)
        raise AuthError({"code":"invalid_header", "description":"Unable to find appropriate key"}, 401)
    return decorated


# Auth Controllers test
@app.route('/api/public')
@cross_origin(headers=['Content-Type', 'Authorization'])
def public():
    """
    A public endpoint that doesn't require authentification
    """
    response = "Hello from a public endpoint! You don't need to be authenticated to see this."
    return jsonify(message=response)

@app.route('/api/private')
@cross_origin(headers=['Content-Type', 'Authorization'])
@requires_auth
def private():
    """
    A private endpoint that requires a valid access token
    """
    response = "Hello from a private endpoint! You need to be authenticated to see this."
    return jsonify(message=response)

class fakefloat(float):
    def __init__(self, value):
        self._value = value
    def __repr__(self):
        return str(self._value)

class Address:
    def __init__(self, adress, longitude, latitude):
        self.adress = adress
        self.longitude = longitude
        self.latitude = latitude

settingPath = os.path.abspath('/var/www/express/static')
settingPath = os.path.abspath('./static')
#Set EXPRESS ADRESS
"""
geolocator = Nominatim(user_agent="express_dry_clean")
express_adress = geolocator.geocode("rue des allies 93 1190 Forest")
start_point = (express_adress.latitude, express_adress.longitude)   
"""

#To Convert DateTime
def defaultconverter(o):
    if isinstance(o, datetime.datetime):
      return o.__str__()
    if isinstance(o, decimal.Decimal):
      return fakefloat(o)

#====================================== Mail management =====================================
#Function to send mail
def send_email(to_addr, subject, content:str, attachement_path : str = None, name:str = None):
    #Signature as image
    html_text3 = f'<p>Cordialement,</p><img src="http://express.REMOVED/getimage?name=signature" alt="" style="margin:0px; padding:0px; border-radius:0rem 0rem 2rem 2rem;"/>'

    header = MIMEText(content, 'html', 'utf-8')
    msg = MIMEMultipart('alternative')
    msg['Subject'] = Header(subject, 'utf-8')
    msg['From'] = app.config['NOREPLY_EMAIL']
    msg['To'] = to_addr
    msg.attach(header)
    # add attahement if exists
    if attachement_path:
        with open(attachement_path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachement_path)}')
        msg.attach(part)
    #Send mail
    smtp_server = app.config['MAIL_SERVER']
    smtp_port = app.config['MAIL_PORT']
    smtp_user = app.config['SMTP_USER']
    smtp_pass = app.config['SMTP_PASSWORD']
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.ehlo()
    server.starttls()
    server.login(smtp_user, smtp_pass)
    server.sendmail(app.config["NOREPLY_EMAIL"], to_addr, msg.as_string())
    server.quit()
    #Add mail to CSV file
    with open(f'{settingPath}/mails.csv', 'a') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now().strftime("%d/%m/%Y - %H:%M:%S"), to_addr, subject, name, content])
        f.close()

"""
with open(f'{settingPath}/address.csv', 'r', encoding="latin-1") as address:
        reader = csv.DictReader(address)
        for row in reader:
            all_address.append(Address(adress=f'{row["address"]}', latitude=row["latitude"], longitude=row["longitude"]))
        
        # close
        address.close()
"""
# send address array
@app.route('/getaddress', methods=['POST'])
def searchAddress():
    if request.method == 'POST':
        result = []
        a = request.json['adress']
        for df in read_csv(f"{settingPath}/address.csv"):
            #df = df[['address', 'longitude', 'latitude']]
            # Sort the dataframe by Name
            df = df[df['address'].str.contains(a, case=False)]
            for index, row in df.iterrows():
                result.append(Address(row['address'], row['longitude'], row['latitude']))
        
        return json.dumps(result[:5], indent=4, default=lambda o: o.__dict__, ensure_ascii=False)


#================================================================================================
#====================================== Days off management =====================================

daysOff = [] # Array of date which are days off

#Function which return true if a date is in the daysOff dict
def LookForDayOff(date):
    for i in range(len(daysOff)):
        if daysOff[i]['date'] == date:
            return True
    return False

#Function to get days off from database
def GetDaysOff():
    daysOff.clear()
    cur = mysql.new_cursor(dictionary = True)
    cur.execute(f"SELECT * FROM {app.config['MYSQL_DB']}.daysoff")
    a = cur.fetchall()
    for i in a:
        daysOff.append({"id":i["id"],"date":i["date"]})

#================================== Database entries ==========================================
#All entries in the database
db_entries = Enum('db_entries',['ads','category','store','user', 'service', 'command', 'params', 'settings', 'times', 'coupon', 'daysoff', 'command_service', 'store_has_service', 'command_has_user'])

command = Enum('command', [
        'id',
        'infos',
        'cost',
        'enter_date',
        'return_date',
        'discount',
        'date_',
        'status',
        'agent',
        'enter_time',
        'return_time',
        'sub_total', 
        'delivery',
        'user_name'
    ])

command_service = Enum('command_service',[
        'command_id',
        'command_user_name',
        'service_name',
        'quantity'
    ])

#==================================

def FormatTextToMysql(a,sep):
    # if a is a number value, return it as it is
    if type(a) == int or type(a) == float:
        return a
    else:
        return f"'{a}'"


#====================================== Routes =====================================
#Function to get datas. To fecth where, set where = attribute#value
@app.route('/getalldatas/<filetype>/<name>/')
@app.route('/getalldatas/<filetype>/<name>/<where>/')
@app.route('/getalldatas/<filetype>/<name>/<where>/<lang>/')
def GetData(filetype:str  ,name: str, where = None, lang = None):
    cur = mysql.new_cursor(dictionary = True)
    # My plan here is to use RegEx with the where here to easily fetch commands for a specific month for example
    if where:
        print(where)
        if '.' not in where:
            return []
        values = where.split(".")
        com = f'SELECT * FROM {app.config["MYSQL_DB"]}.{name} WHERE {values[0]} LIKE "{values[1]}"'
        cur.execute(com)

    else:
        translation_table = f"{name}_translation"
        cur.execute(f"SELECT * FROM {app.config['MYSQL_DB']}.{name}")
    a = cur.fetchall()
    if filetype == 'json':
        return json.dumps(a, indent=4, default=defaultconverter)
    else:
        return a


# Function to avoid SQL Injection 
def escape (value : str):
    return MySQL.escape_string(value)

# Function to aperate - Create:Done
@app.route('/api/<model>', methods=['POST','DELETE','PUT'])
def Operate(model:str):
    cursor = mysql.new_cursor(dictionary = True, buffered = True)
    # Get primary Key
    cursor.execute(f"SHOW KEYS FROM {app.config['MYSQL_DB']}.{model} WHERE Key_name = 'PRIMARY'")
    primary_key = cursor.fetchone()['Column_name']
    print(f"Primary key : {primary_key}")
    if not primary_key:
        return jsonify({"status": "error", "message": "No primary key found"}), 400
    

    result = ""
    if request.method == "POST":
        cursor.execute(f"SELECT * FROM {app.config['MYSQL_DB']}.{model}")
        attributes = list(cursor.column_names)
        values = list(request.json[str(att)] for att in attributes)
        ### Execute command
        cursor.close()
        cursor = mysql.new_cursor(dictionary = True, buffered = True)
        create = ", ".join([f"`{att}`" for att in request.json.keys()]) # Attributes here needs to be embeded in `` because they are reserved words in SQL
        query = f"INSERT INTO {app.config['MYSQL_DB']}.{model} ({create}) VALUES ({', '.join([f'{FormatTextToMysql(request.json[att],1)}' for att in request.json.keys()])})"
        #cursor.execute(f"INSERT INTO {app.config['MYSQL_DB']}.{model} ({','.join(list(FormatTextToMysql(att,1) for att in attributes))}) VALUES ({','.join(list(FormatTextToMysql(val,2) for val in values))})")
        
        print(query)
        cursor.execute(query)
        mysql.connection.commit()
        return str(cursor.lastrowid)
    if request.method == "DELETE":
        # Get the id of the element to delete
        cursor.execute(f"SELECT * FROM {app.config['MYSQL_DB']}.{model}")
        model_ID = list(cursor.column_names)[-1]
        cursor.close()
        cursor = mysql.new_cursor(dictionary = True, buffered = True)
        cursor.execute(f"DELETE FROM {app.config['MYSQL_DB']}.{model} WHERE {primary_key} = {FormatTextToMysql(request.json[primary_key], 1)}")
        mysql.connection.commit()
        return "True"
    if request.method == "PUT":
        # SQL UPDATE REQUEST 
        
        if model == "params":
            updates = ", ".join([f"{att} = {request.json[att]}" for att in request.json.keys() if att != primary_key])
            query = f"UPDATE {app.config['MYSQL_DB']}.{model} SET {updates} WHERE {primary_key} = {request.json[primary_key]}"
        else:
            updates = ", ".join([f"{att} = {FormatTextToMysql(request.json[att],1)}" for att in request.json.keys() if att != primary_key])
            query = f"UPDATE {app.config['MYSQL_DB']}.{model} SET {updates} WHERE {primary_key} = {FormatTextToMysql(request.json[primary_key],2)}"
        print(updates)
        print(query)
        
        cursor.execute(query)
        mysql.connection.commit()
        cursor.close()
        return jsonify({"status": "success", "message": "Element updated"}), 200
       

    return "True"

# Function to test the connection
@app.route('/test')
def test():
    cursor = mysql.new_cursor(dictionary = True)
    cursor.execute(f"SELECT * FROM {app.config['MYSQL_DB']}.user")
    attributes = list(cursor.column_names)

    print (attributes)
    return json.dumps(cursor.fetchall(), indent=4, default=defaultconverter)

#Function to add a day off
@app.route('/adddayoff', methods=['POST'])
def AddDayOff():
    if request.method == 'POST':
        date = request.json['date']
        cur = mysql.new_cursor(dictionary = True)
        print(date)
        cur.execute(f"INSERT INTO `appexpress`.`daysoff` (`date`) VALUES ('{date}')")
        mysql.connection.commit()
        #GetDaysOff()
        return json.dumps("ok")

#Function to remove a day off
@app.route('/removedayoff', methods=['POST'])
def RemoveDayOff():
    if request.method == 'POST':
        date = request.json['date']
        cur = mysql.new_cursor(dictionary = True)
        cur.execute(f"DELETE FROM appexpress.daysoff WHERE date = '{date}'")
        mysql.connection.commit()
        GetDaysOff()
        return "ok"

#Function to get days off
@app.route('/getdaysoff', methods=['GET'])
def GetDaysOffRoute():
    if request.method == 'GET':
        GetDaysOff()
        return json.dumps(daysOff, indent=4, default=defaultconverter)

#Function to add multiple days off
@app.route('/addmultipledaysoff', methods=['POST'])
def AddMultipleDaysOff():
    if request.method == 'POST':
        dates = request.json['dates']
        cur = mysql.new_cursor(dictionary = True)
        for date in dates:
            cur.execute(f"INSERT INTO appexpress.daysoff (date) VALUES ('{date}')")
        GetDaysOff()
        return "ok"

#================================================================================================
#========================================Functions===============================================

#Function which take a datetime and return availables hours to pass a command
def GetAvailableHours(date):
    #If date is in the daysoff dictionary, just return empty
    if LookForDayOff(date):
        return []
    
    workingHours = [9,10,11,12,13,14,15,16,17]
    cur = mysql.new_cursor(dictionary = True)
    cur.execute(f"SELECT enter_time,return_time FROM {app.config['MYSQL_DB']}.command WHERE enter_date = '{date}'")
    a = cur.fetchall()
    #create a list of hours which are already booked
    bookedHours = []
    for i in a:
        bookedHours.append(int(i["enter_time"]))
        bookedHours.append(int(i["return_time"]))
    #remove booked hours from working hours
    for i in bookedHours:
        if i in workingHours and bookedHours.count(i) >= 2:
            workingHours.remove(i)
    #remoce value in workingHours if it appear two times in a
    return workingHours



# Read delivery prices from CSV file
deliveryPrices = []
"""
with open(f'{settingPath}/deliveryPrices.csv', 'w', newline='') as f:
    fieldnames = ['ZIPCODE', 'PRICE']

    reader = csv.reader(f)
    
    f.close()
"""
# add delivery price to csv
"""
with open(f'{settingPath}/deliveryPrices.csv', 'a') as f:
    writer = csv.writer(f)
    writer.writerow(['1410', '9.00'])
    writer.writerow(['1560', '9.00'])
    writer.writerow(['1000', '3.99'])
    writer.writerow(['1190', '3.99'])
    writer.writerow(['1200', '3.99'])
    writer.writerow(['1050', '3.99'])
    f.close()
"""
#Price by Km
price_by_km = float(0.30)
#Function to calculate the cost according to the distance between to ZIPCODES
"""
def GetDistanceToGo(adress):
    end_point = geolocator.geocode(adress)
    end_point = (end_point.latitude, end_point.longitude)
    return round(distance.distance(start_point, end_point).km, 2)
"""

#Function to calculate cost delevery according the ZIP CODE
def GetCostDelevery(code):
    
    # Look for code in deliveryPrices
    with open(f'{settingPath}/deliveryPrices.csv', 'r') as f:
        reader = csv.reader(f)
        deliveryPrices = list(reader)
        f.close()
    for i in deliveryPrices:
        if i[0] == code:
            return i[1]
        
    # If code not found, return default price
    return 0.00
    #return decimal.Decimal(GetDistanceToGo(adress)*price_by_km).quantize(decimal.Decimal('.01'))

#function to check a coupon and return the value
@app.route('/checkcoupon', methods=['POST'])
def Check_Coupon():
    if request.method == 'POST':
        cost = 0.00
        cursor = mysql.new_cursor(dictionary = True)
        code = request.json['code']
        cursor.execute(f"SELECT * FROM appexpress.coupon WHERE code = '{code}'")
        a = cursor.fetchall()
        return json.dumps(a, indent=4, default=defaultconverter)

@app.route('/getdeliveryprice', methods=['POST'])
def GetdeliveryPrice():
    if request.method == 'POST':
        
        return json.dumps(4151, indent=4, default=defaultconverter)


@app.route('/getavailablehours')
def GetAvailableHoursRoute():
    date = request.args.get('date')
    return (json.dumps(GetAvailableHours(date), indent=4))

@app.route('/reset')
def ResetPassword():
    mail = request.args.get('mail')
    print("Voici le mail client = " + mail)
    cursor = mysql.new_cursor(dictionary = True)
    cursor.execute(f"SELECT * FROM appexpress.user WHERE mail = '"+ mail +"'")
    response = cursor.fetchone()
    print("La réponse est" + str(response["name"] + str(response["password"])))
    #send_email(to_addr=mail, subject="Mot de passe Ex-press Dry Clean", user_name=(response["name"]), email_type="passwordReset", user_recap=response["password"])
    return "Mot de passe envoyé"


@app.route('/')
def index():
    return redirect(url_for('home', lang = 'fr'))

# Error handler
@app.errorhandler(404)
@app.errorhandler(500)
def page_not_found(e):
    print(f"Error 404 : Page not found {e}")
    session['lang'] = 'fr' if not session.get('lang') else session['lang']
    return render_template('error.html', lang = session['lang'], current_page = 'home')

@app.route('/<lang>/home/')
@app.route('/<lang>/home/<subpage>')
@app.route('/<lang>/home/<subpage>/<store>')
def home(lang = 'fr', subpage = None, store = None):
    #fill_database()
    #set language
    session['lang'] = lang
    user = getattr(g, 'user', None)
    
    print(getattr(g, 'user', None))
    #return str((GetCostDelevery("Rue Saint-germain 92 1410 Waterloo")*price_by_km).quantize(decimal.Decimal('.01')))
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])
    stores = GetData('full','store')
    services = GetData('full','service')
    return render_template('index.html', dictionary = dictionary[lang] , services = services, categories=categories, stores=stores, lang = session['lang'], current_page = 'home')

@app.route('/<lang>/policy/')
def policy(lang = 'fr'):
    #set language
    session['lang'] = lang
    #Usefull for the header, since Flask ask fot it
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])
    stores = GetData('full','store')
    services = GetData('full','service')
    return render_template('policy.html', lang = session['lang'], categories = categories, stores = stores, services = services, current_page = 'policy')

@app.route('/<lang>/terms/')
def terms(lang = 'fr'):
    #set language
    session['lang'] = lang
    #Usefull for the header, since Flask ask fot it
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])
    stores = GetData('full','store')
    services = GetData('full','service')
    return render_template('terms.html', lang = session['lang'], categories = categories, stores = stores, services = services, current_page = 'terms')

@app.route('/<lang>/pricing/')
@app.route('/<lang>/pricing/<subpage>')
@app.route('/<lang>/pricing/<subpage>/<store>')
def pricing(lang = 'fr', subpage = None, store = None):
    #set language
    session['lang'] = lang
    services = GetData('full','service') # Get all services
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])# Get just the categories 
    services_in_store = GetData('full','store_has_service') # Get all services associates to all stores

    others_categories = [ x for x in categories if x['name'] != subpage]
    available_services = [ x for x in services if x['category_name'] == subpage]

    selected_category = [ x for x in categories if x['name'] == subpage][0] if subpage else None
    #if selected_category:
    #   selected_category = { k.encode('utf-8'): v.encode('utf-8') for k, v in selected_category.items()}
    # Convert all informations in selectedCategory to utf-8

    stores = GetData('full','store')
    selected_store = [ x for x in stores if x['name'] == store][-1] if store else None
    return render_template('pricing.html', lang = session['lang'], categories = categories, services_in_store = services_in_store, dictionary = dictionary[lang], category = subpage, other_categories = others_categories, services = None if len(available_services) <= 0 else available_services, selected_category = selected_category, stores = stores, selected_store = selected_store, current_page = 'pricing')
    
@app.route('/<lang>/about/')
@app.route('/<lang>/about/<subpage>')
def about(lang = 'fr', subpage = None):
    #set language
    session['lang'] = lang
    stores = GetData('full','store')
    services = GetData('full','service')
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])# Get just the categories 
    return render_template('about.html', lang = session['lang'], dictionary = dictionary[lang], current_page = 'about', stores = stores, services = services, categories = categories)

@app.route('/<lang>/collaborations/')
@app.route('/<lang>/collaborations/<subpage>')
def collaborations(lang = 'fr', subpage = None, message = None):
    #set language
    session['lang'] = lang
    stores = GetData('full','store')
    services = GetData('full','service')
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])
    return render_template('collaborations.html', lang = session['lang'], dictionary = dictionary[lang], current_page = 'collaborations', stores = stores, services = services, categories = categories, message = message)

@app.route('/submit_collaboration', methods=['POST'])
def submit_collaboration():
    data = request.form
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])
    availablesCategoriesNames = [ x['name'] for x in categories]
    #send mail to admin to inform him about the message
    print(data)
    company = data['company_name']
    industry = data['industry']
    contact_name = data["contact_name"]
    phone = data['phone']
    email = data['email']
    try:
        all_services_check = data['all_services']
    except:
        all_services_check = False


    selected_services = [ x for x in data if x in  availablesCategoriesNames] if all_services_check == False else availablesCategoriesNames
    #send mail to admin to inform him about the Collaboration
    send_email(
        to_addr=app.config["NOREPLY_EMAIL"],
        subject=f"🤝 Nouvelle demande de collaboration de {company}",
        content=f"""
        <p><strong>Entreprise :</strong> {company}</p>
        <p><strong>Secteur d’activité :</strong> {industry}</p>
        <p><strong>Contact :</strong> {contact_name}</p>
        <p><strong>Email :</strong> {email}</p>
        <p><strong>Téléphone :</strong> {phone}</p>
        
        <p><strong>Services demandés :</strong></p>
        <ul>
            {"".join(f"<li>{service}</li>" for service in selected_services)}
        </ul>
        
        <p>{'✅ Demande de tous les services' if all_services_check else '📌 Sélection partielle des services'}</p>

        <p>📅 Cette demande a été envoyée via le formulaire de collaboration.</p>
        """
    )

    # send mail to the user to confirm the message
    send_email(
        to_addr=email,
        subject="📨 Confirmation de votre demande de collaboration",
        content=f"""
        <p>Bonjour {contact_name},</p>

        <p>Nous avons bien reçu votre demande de collaboration et nous vous remercions pour votre intérêt envers Ex-Press Dry Clean.</p>

        <p><strong>Entreprise :</strong> {company}</p>
        <p><strong>Secteur d’activité :</strong> {industry}</p>
        
        <p><strong>Services demandés :</strong></p>
        <ul>
            {"".join(f"<li>{service}</li>" for service in selected_services)}
        </ul>
        
        <p>{'✅ Vous avez demandé l’ensemble de nos services.' if all_services_check else '📌 Vous avez sélectionné certains services uniquement.'}</p>

        <p>Notre équipe va analyser votre demande et reviendra vers vous dans les plus brefs délais.</p>

        <p>Merci de votre confiance,</p>
        <p><strong>L’équipe Ex-Press Dry Clean</strong></p>
        """
    )   
    return redirect(url_for('collaborations', lang = session['lang'], message = "Message envoyé"))

@app.route('/<lang>/career/')
@app.route('/<lang>/career/<subpage>')
def career(lang = 'fr', subpage = None, message = None):
    #set language
    session['lang'] = lang
    stores = GetData('full','store')
    services = GetData('full','service')
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])
    return render_template('career.html', lang = session['lang'], dictionary = dictionary[lang], current_page = 'career', stores = stores, services = services, categories = categories, message = message)

@app.route('/submit_career', methods=['POST'])
def submit_career():
    data = request.form
    print(data)
    name = data["full_name"]
    email = data["email"]
    phone = data["phone"]
    message = data["message"]
    #Check the cv file and save it
    if 'cv_file' not in request.files or request.files['cv_file'].filename == '':
        return redirect(url_for('career', lang = session['lang'], message = "Veuillez joindre un fichier"))
    
    #Here we assume that the file is a pdf file
    cv_file = request.files['cv_file']
    if cv_file and allowed_file(cv_file.filename):
        #Remove spaces 
        filename = secure_filename(cv_file.filename)
        cv_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        #send mail to admin to inform him about the message
        send_email(
            to_addr=app.config["NOREPLY_EMAIL"],
            subject=f"📩 Nouvelle candidature reçue de {name}",
            content=f"""
            <p><strong>Nom :</strong> {name}</p>
            <p><strong>Email :</strong> {email}</p>
            <p><strong>Téléphone :</strong> {phone}</p>
            <p><strong>Message du candidat :</strong></p>
            <blockquote>{message}</blockquote>
            <p>📎 <strong>CV en pièce jointe</strong></p>
            <p>📅 Cette candidature a été envoyée depuis le formulaire en ligne.</p>
            """,
            attachment_path=os.path.join(app.config['UPLOAD_FOLDER'], filename),  # ✅ Ajoute le CV en pièce jointe
            name=name
        )
        # send mail to the user to confirm reception
        send_email(
    to_addr=email,
    subject="📨 Confirmation de réception de votre candidature",
    content=f"""
        <p>Bonjour {name},</p>

        <p>Nous avons bien reçu votre candidature et nous vous remercions de l'intérêt que vous portez à Express Dry Clean.</p>

        <p><strong>📩 Votre message :</strong></p>
        <blockquote>{message}</blockquote>

        <p>📎 <strong>Votre CV a bien été reçu.</strong></p>

        <p>Notre équipe de recrutement analysera votre profil et vous contactera si votre candidature correspond à nos besoins.</p>

        <p>Merci de votre confiance,</p>
        <p><strong>L’équipe Express Dry Clean</strong></p>
        """
    )
        return redirect(url_for('career', lang = session['lang'], message = "CV envoyé"))
    else:
        return redirect(url_for('career', lang = session['lang'], message = "Fichier non autorisé"))


@app.route('/<lang>/contact/')
@app.route('/<lang>/contact/<subpage>')
def contact(lang = 'fr', subpage = None, message = None):
    greatings = _("Bonjour")
    #set language
    session['lang'] = lang
    stores = GetData('full','store')
    services = GetData('full','service')
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])# Get just the categories 
    return render_template('contact.html', lang = session['lang'], dictionary = dictionary[lang], message = message, current_page = 'contact', stores = stores, services = services, categories = categories)


@app.route('/<lang>/delivery/')
@app.route('/<lang>/delivery/<subpage>')
def delivery(lang = 'fr', subpage = None , message = None):
    session['lang'] = lang
    params = GetData('full','params')[-1]
    print(params)
    stores = GetData('full','store')
    services = GetData('full','service')
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])# Get just the categories 
    return render_template('delivery.html', params = params, lang = session['lang'], dictionary = dictionary[lang], current_page = 'delivery', stores = stores, services = services, categories = categories)   

@app.route('/<lang>/localization/')
@app.route('/<lang>/localization/<subpage>')
def localization(lang = 'fr', subpage = None ):
    session['lang'] = lang
    stores = GetData('full','store')
    services = GetData('full','service')
    categories = sorted(GetData('full','category'), key=lambda x: x['index'])# Get just the categories 
    available_store = [ x for x in stores if x['name'] == subpage][-1] if subpage else None

    return render_template('localization.html', lang = session['lang'], dictionary = dictionary[lang], stores = stores, selected_store = available_store, current_page = 'localization', services = services, categories = categories)


@app.route('/chatwithus', methods=['POST'])
def chatwithus():
    data = request.form
    email = data['email']
    name = data['first_name'] + " " + data['last_name']
    phone = data['phone']
    message = data['subject']
    print(data)
    #send mail to admin to inform him about the message
    send_email(
    to_addr=app.config["NOREPLY_EMAIL"],    
    subject=f"📩 Nouveau message de {name}",
    content=f"""
    <p><strong>Nom :</strong> {name}</p>
    <p><strong>Email :</strong> {email}</p>
    <p><strong>Téléphone :</strong> {phone}</p>
    <p><strong>Message :</strong></p>
    <blockquote>{message}</blockquote>
    <p>📅 Ce message a été envoyé depuis le formulaire de contact.</p>
    """
)   
    #send mail to user to inform him that his message has been sent
    send_email(
    to_addr=email,
    subject="📨 Confirmation de réception de votre message",
    content=f"""
    <p>Bonjour {data['first_name']},</p>
    <p>Nous avons bien reçu votre message et nous vous répondrons dans les plus brefs délais.</p>
    <p>📩 <strong>Votre message :</strong></p>
    <blockquote>{message}</blockquote>
    <p>Notre équipe reviendra vers vous rapidement.</p>
    <p>Merci de votre confiance,</p>
    <p><strong>L’équipe Ex-Press Dry Clean</strong></p>
    """,
    name=name
    )
    return redirect(url_for('contact', lang = session['lang'], message = "Message envoyé"))


# Function to get the dictionary of a language
@app.route('/api/getdictionary', methods=['GET'])
def GetDictionary():
    lang = request.args.get('lang')
    #Get the babel .po
    po = polib.pofile(f"{app.config['BABEL_PO_FILES_PATH']}/{lang}/LC_MESSAGES/messages.po")
    dictionary  = { poEntry.msgid : poEntry.msgstr for poEntry in po }
    return json.dumps(dictionary, indent=4)

#Function to update a po file
@app.route('/api/updatebabelpo', methods=['POST'])
def updateBabelPo():
    print("Updating po file")
    lang = request.json['lang']
    translations = request.json['translations']
    #Get the babel .po
    po = polib.pofile(f"{app.config['BABEL_PO_FILES_PATH']}/{lang}/LC_MESSAGES/messages.po")
    for entry in po:
        if entry.msgid in translations:
            entry.fuzzy = False
            entry.msgstr = translations[entry.msgid]
    po.save(f"{app.config['BABEL_PO_FILES_PATH']}/{lang}/LC_MESSAGES/messages.po")
    
    return "True"

# Function to get server state (online or offline)
@app.route('/getserverstate')
def GetServerState():
    return "Connected"

import threading

# Function to restart the server
@app.route('/hotrestartserver', methods=['GET'])
@cross_origin(headers=['Content-Type', 'Authorization'])
@requires_auth
def RestartServer():
    def restart():
        result = subprocess.run(["sudo","systemctl", "restart", f"{app.config['SERVICE_NAME']}"], check=True, capture_output=True, text=True)
    
    thread = threading.Thread(target=restart, daemon=True)
    thread.start()

#Function to update mo files. Usefull for words in the website
@app.route('/api/updatewebsitedictionnary')
def updatewebsitedictionnary():
    # COmpile the .po into .mo 
    print("Compiling translations")
    subprocess.run(["pybabel", "compile", "-d", app.config['BABEL_PO_FILES_PATH']], check=True)
    print("Translation compiled")
                 
    refresh()
    return "True"


# function to update the flask babel dictionnary from the app
@app.route('/api/updatebabelpot', methods=['POST'])
def updateBabel():
    new_translations = request.json["translations"] # get new translations

    if not new_translations:
        return jsonify({"status": "error", "message": "No translations found"})
    # Update the pot file with the new translations
    pot = polib.pofile(f"{app.config['ROOT_FOLDER']}/messages.pot")
    for word in new_translations:
        #create a new entry
        word_entry = polib.POEntry(msgid=word, msgstr="")
        if word_entry not in pot:
            pot.append(word_entry)

    pot.save(f"{app.config['ROOT_FOLDER']}/messages.pot")
    # Update the translations files
    updating_process = subprocess.Popen(["pybabel", "update", "-i", "messages.pot", "-d", "translations"])
    print("Updating translations files")
    updating_process.wait()
    print("Translations updated")
    return jsonify({"status": "success", "message": "Translations updated"})

#Function to get all dictionnary words... the pot file
@app.route('/api/getpot')
def getPot():
    pot = polib.pofile(f"{app.config['ROOT_FOLDER']}/messages.pot")
    t = {entry.msgid: entry.msgstr for entry in pot}
    return jsonify(t)

@app.route('/babel_test')
def babel_test():
    pot = polib.pofile(f'./messages.pot')
    t = {entry.msgid: entry.msgstr for entry in pot}
    return t

@app.route('/getservices')
def show_sewing():
    cur = mysql.new_cursor(dictionary = True)
    cur.execute('SELECT * FROM appexpress.service')
    a = cur.fetchall()
    c = json.dumps(a, indent=4, default=defaultconverter)
    return (c)

#Get settings
@app.route('/getsettings')
def GetSettings():
    cur = mysql.new_cursor(dictionary = True)
    cur.execute("SELECT * FROM appexpress.settings")
    a = cur.fetchone()
    c = json.dumps(a,indent=4, default=defaultconverter)
    return (c)

#Get params {id, tarif_bruxelles, tarif_brabant, tarif_km}
@app.route('/getparams')
def GetParams():
    cur = mysql.new_cursor(dictionary = True)
    cur.execute("SELECT * FROM appexpress.params")
    a = cur.fetchone()
    c = json.dumps(a,indent=4, default=defaultconverter)
    return (c)

#Update Params
@app.route('/updateparams', methods=['POST'])
def UpdateParams():
    if request.method == 'POST':
        tarif_bruxelles = request.json['tarif_bruxelles']
        tarif_brabant = request.json['tarif_brabant']
        tarif_km = request.json['tarif_km']
        cursor = mysql.new_cursor()
        cursor.execute(f"UPDATE `appexpress`.`params` SET `tarif_bruxelles` = '{tarif_bruxelles}', `tarif_brabant` = '{tarif_brabant}', `tarif_km` = '{tarif_km}' WHERE (`id` = '1');")
        mysql.connection.commit()
        return "True"


#Get service by ID
@app.route('/getservicebyid')
def GetSewingByID():
    id_ = request.args.get("id")
    cur = mysql.new_cursor(dictionary = True)
    cur.execute("SELECT * FROM appexpress.service WHERE id = '"+ id_+"'")
    a = cur.fetchall()
    c = json.dumps(a,indent=4, default=defaultconverter)
    return (c)

#Get all commands from a user
@app.route('/getusercommands', methods=['POST'])
def GetUserCommands():
    if request.method == 'POST':
        id = request.json["id"]
        cur = mysql.new_cursor(dictionary = True)
        cur.execute(f"SELECT * FROM appexpress.command WHERE user = '{id}'")
        a = cur.fetchall()
        c = json.dumps(a, default=defaultconverter)
        mysql.connection.commit()
        return (c)

@app.route('/addservice', methods=['POST', 'GET'])
def AddService():
    if request.method == 'POST':
        id = request.json['id']
        name = request.json['name']
        cost = decimal.Decimal(str(request.json['cost'])).quantize(decimal.Decimal('.01'))
        category = request.json['categories']
        size = request.json['time']
        description = request.json['description']
        illustration = request.json['illustration']
        cursor = mysql.new_cursor()
        cursor.execute(f"INSERT INTO `appexpress`.`service` (`name`, `cost`, `categories`, `description`, `time`,`illustration`) VALUES ('{name}', '{cost}', '{category}', '{description}', '{size}', '{unidecode(illustration)}');")
        mysql.connection.commit()
        return "True"

#update service
@app.route('/updateservice', methods=['POST', 'GET'])
def Update_Service():
    if request.method == 'POST':
        id = request.json['id']
        name = request.json['name']
        cost = decimal.Decimal(str(request.json['cost'])).quantize(decimal.Decimal('.01'))
        category = request.json['categories']
        size = request.json['time']
        description = request.json['description']
        illustration = request.json['illustration']
        cursor = mysql.new_cursor()
        cursor.execute(f"UPDATE `appexpress`.`service` SET `name` = '{name}', `cost` = '{cost}', `categories` = '{category}', `time` = '{size}', `description` = '{description}', `illustration` = '{unidecode(illustration)}' WHERE (`id` = '{id}');")
        mysql.connection.commit()
        return "True"
    

#Connection Config
@app.route('/connect', methods = ['POST', 'GET'])
def secureConnection():
    if request.method == 'POST':
        username = request.json['name']
        password = request.json['password']
        email = request.json['mail']
        cur = mysql.new_cursor(dictionary=True)
        #Check if mail ou username can match depending on what user entered
        print(f"Connection for user {username} and password {password}")
        if username != "":
            cur.execute(f"SELECT * FROM {app.config['MYSQL_DB']}.user WHERE name = '{username}' and password = '{password}'")
        elif email != "":
            cur.execute(f"SELECT * FROM {app.config['MYSQL_DB']}.user WHERE mail = '{email}' and password = '{password}'")
        a = cur.fetchone()
        print(a)
        return json.dumps(a)

#Connection with the server. username exist ? return the password otherwise return nil      
@app.route('/checkuser', methods = ['POST', 'GET'])
def check_user():
    if request.method == 'POST':
        username = request.json['name']
        email = request.json['mail']
        cur =  mysql.new_cursor(dictionary=True)
        result = ""
        if username != "":
            #Get the password associate 
            cur.execute(f"SELECT password FROM appexpress.user WHERE name = '{username}'")
        elif email != "":
            cur.execute(f"SELECT password FROM appexpress.user WHERE mail = '{email}'")
        
        result = cur.fetchone()
        return result

#Get all users
@app.route('/getusers')
def GetUsers():
    cur = mysql.new_cursor(dictionary = True)
    cur.execute('SELECT * FROM appexpress.user')
    a = cur.fetchall()
    return json.dumps(a)

#Obtenir des informations sur un utilisateur à partir de son ID
@app.route('/getuserinfo')
def GetUserInfo():
    userID = request.args.get('id')
    cur = mysql.new_cursor(dictionary = True)
    cur.execute("SELECT * FROM appexpress.user WHERE id = '"+userID+"'")
    a = cur.fetchall()
    return json.dumps(a)

#Mettre à jour un utilisateur à partir de son ID
@app.route('/updateuser', methods = ['POST'])
def UpdateUser():
    id_ = request.json['id']
    username = request.json['name']
    mail = request.json['mail']
    adress = request.json['adress']
    phone = request.json['phone']
    password = request.json['password']
    account = request.json['type']
    loc_lat = request.json['loc_lat']
    loc_lon = request.json['loc_lon']
    province = request.json['province']
    cursor = mysql.new_cursor(dictionary = True)
    cursor.execute(f"UPDATE `appexpress`.`user` SET `name` = '{username}', `mail` = '{mail}', `adress` = '{adress}', `phone` = '{phone}', `password` = '{password}', `type` = '{account}', `loc_lat` = '{loc_lat}', `loc_lon` = '{loc_lon}', `province` = '{province}'  WHERE (`id` = '{id_}');")
    mysql.connection.commit()
    #Get user and send it back
    cursor.execute(f'SELECT * FROM appexpress.user WHERE id = {id_};')
    a = cursor.fetchone()
    print(a)
    return json.dumps(a)

#Register User
@app.route('/register', methods = ['POST', 'GET'])
def AddUser():
    if request.method == 'POST':
        cur = mysql.new_cursor()
        nameUser = request.json['name']
        email = request.json['mail']
        addressUser = request.json['adress']
        phoneUser = request.json['phone']
        passwordUser = request.json['password']
        typeUser = request.json['type']
        loc_lat = request.json['loc_lat']
        loc_lon = request.json['loc_lon']
        province = request.json['province']
        cur.execute(f"INSERT INTO `appexpress`.`user` (`name`, `mail`, `adress`, `phone`, `password`, `type`, `loc_lat`, `loc_lon`, `province`) VALUES ('{nameUser}', '{email}', '{addressUser}', '{phoneUser}', '{passwordUser}', '{typeUser}', '{loc_lat}', '{loc_lon}', '{province}')")
        mysql.connection.commit()
        id = cur.lastrowid
        #Create user recap in html array
        user_recap = f"<table><tr><td>Nom</td><td>{nameUser}</td></tr><tr><td>Adresse</td><td>{addressUser}</td></tr><tr><td>Mail</td><td>{email}</td></tr><tr><td>GSM</td><td>{phoneUser}</td></tr><tr><td>Mot de passe</td><td>{passwordUser}</td></tr></table> <i>Ceci est un mail factice pour tests alpha</i>"
        #Send mail to user
        #send_email(to_addr=email, subject="Inscription Ex-press Dry Clean", user_name=(nameUser), email_type="inscription", user_recap=user_recap)
        return json.dumps(id)
    
#Get all commands
@app.route('/getcommands')
def GetCommands():
    cur = mysql.new_cursor(dictionary = True)
    cur.execute('SELECT * FROM appexpress.command')
    a = cur.fetchall()
    return json.dumps(a, default=defaultconverter)

#Add command
@app.route('/addcommand', methods = ['POST', 'GET'])
def AddCommand():
    if request.method == 'POST':
        file = request.json
        id = request.json['id']
        user = request.json['user']
        status= request.json['infos']
        cost=  request.json['cost']
        enter_date =  request.json['enter_date']
        return_date =  request.json['return_date']
        discount =  request.json['discount']
        date = request.json['date_']
        #date =  request.json['enter_date']
        services_quantity =  request.json['services_quantity']
        #agent = request.json['agent']
        enter_time = request.json['enter_time']
        return_time = request.json['return_time']
        sub_total = request.json['sub_total']
        delivery = request.json['delivery']
        cur = mysql.new_cursor(dictionary = True)
        cur.execute(f"INSERT INTO `appexpress`.`command` (`id`, `infos`, `cost`, `enter_date`, `return_date`,`discount`, `services_quantity`, `user`, `enter_time`, `return_time`, `sub_total`, `delivery`) VALUES ('{id}', '{status}', '{cost}', '{enter_date}', '{return_date}', '{discount}', '{services_quantity}', '{user}', '{enter_time}', '{return_time}','{sub_total}','{delivery}')")
        #cur.execute("INSERT INTO `appexpress`.`command_has_user` (`command_id`, `user`) VALUES ('"+str(id)+"', '"+str(user)+"')")
        mysql.connection.commit()
        id = cur.lastrowid
        #Add services_quatity elements to command_service table
        for i in range(len(services_quantity.split(','))):
            cur.execute(f"INSERT INTO `appexpress`.`command_service` (`command_id`, `service_id`, `quantity`) VALUES ('{id}', '{services_quantity.split(',')[i].split(':')[0]}', '{services_quantity.split(',')[i].split(':')[1]}')")
            mysql.connection.commit()
        #Create command recap in html array
        command_recap = f"<table><tr><td>Numéro de commande</td><td>{id}</td></tr><tr><td>Prix</td><td>{cost}</td></tr><tr><td>Date de prise en charge</td><td>{enter_date}</td></tr><tr><td>Date de retour</td><td>{return_date}</td></tr><tr><td>Quantite de services</td><td>{services_quantity}</td></tr><tr><td>Heure de prise en charge</td><td>{enter_time}h-{int(enter_time) +1 }h</td></tr><tr><td>Heure de retour</td><td>{return_time}h-{int(return_time) +1 }h</td></tr><tr><td>Sous-total</td><td>{sub_total}</td></tr><tr><td>Livraison</td><td>{delivery}</td></tr></table> <i>Ceci est un mail factice pour tests de version alpha</i>"
        #Get user infos
        cur.execute(f"SELECT * FROM appexpress.user WHERE id = '{user}'")
        a = cur.fetchall()
        #Get services info
        #Write mail
        command_recap = f"<table><tr><td>Numéro de commande</td><td>{id}</td></tr><tr><td>Prix</td><td>{cost}€</td></tr><tr><td>Date de prise en charge</td><td>{enter_date}</td></tr><tr><td>Date de retour</td><td>{return_date}</td></tr><tr><td>Heure de prise en charge</td><td>{enter_time}h-{int(enter_time) +1 }h</td></tr><tr><td>Heure de retour</td><td>{return_time}h-{int(return_time) +1 }h</td></tr><tr><td>Sous-total</td><td>{sub_total}€</td></tr><tr><td>Livraison</td><td>{delivery}€</td></tr></table>"
        #Send mail to user
        #send_email(to_addr=a[0]["mail"], subject="Commande Ex-press Dry Clean", user_name=(a[0]["name"] +" "+ a[0]["surname"]), email_type="command_validation", command_recap=command_recap)


    return json.dumps(id)

@app.route('/getserviceandcommand')
def GetServiceAndCommand():
    cur = mysql.new_cursor(dictionary = True)
    cur.execute("SELECT * FROM appexpress.service_has_command")
    a = cur.fetchall()
    return json.dumps(a)

@app.route('/addservicehascommand', methods = ['POST', 'GET'])
def AddServiceHasCommand():
    if request.method =='GET':
        service = request.args.get('service')
        commandid = request.args.get('command')
        quantity = request.args.get('quantity')
        cur = mysql.new_cursor()
        cur.execute("INSERT INTO `appexpress`.`service_has_command` (`service_id`, `command_id`, `quantity`) VALUES ('"+str(service)+"', '"+str(commandid)+"', '"+str(quantity)+"');")
        mysql.connection.commit()
        return "True"

@app.route('/getuserandcommand')
def GetUserAndCommand():
    cur = mysql.new_cursor(dictionary = True)
    cur.execute("SELECT * FROM appexpress.command_has_user")
    a = cur.fetchall()
    return json.dumps(a)

#Fonction qu ajoute une commande à un utilisateur 
@app.route('/addcommandtouser', methods = ['POST','GET'])
def AddCommandToUser():
    user = request.json['user']
    command = request.json['command_id']
    cursor = mysql.new_cursor(dictionary = True)
    cursor.execute("INSERT INTO `appexpress`.`command_has_user` (`command_id`, `user`) VALUES ('"+str(command)+"', '"+str(user)+"')")
    mysql.connection.commit()
    return "True"

#Fonction qui recupère les horaires
@app.route('/gettimes')
def GetTimes():
    cursor = mysql.new_cursor(dictionary = True)
    cursor.execute("SELECT * FROM appexpress.times")
    a = cursor.fetchall()
    return json.dumps(a)



#Fonction qui met à jour un horaire
@app.route('/updatetime')
def UpdateTimes():
    id = request.json['id']
    state = request.json['state']
    day = request.json['day']
    cursor = mysql.new_cursor()
    cursor.execute("UPDATE `appexpress`.`times` SET `state` = '"+state+"' WHERE (`id` = '"+id+"');")
    mysql.connection.commit()
    return "True"

#Fonction qui ajoute un horaire
@app.route('/addtime', methods =['POST'])
def AddTime():
    if request.method == 'POST':
        creneau = request.json['creneau']
        state = request.json['state']
        day = request.json['day']
        program = request.json['program']
        cursor = mysql.new_cursor()
        cursor.execute("INSERT INTO `appexpress`.`times` (`creneau`, `state`,`day`) VALUES ('"+str(creneau)+"', '"+str(state)+"','"+str(day)+"')")
        mysql.connection.commit()
        return "True" 

 
#Fonction qui ajoute un Coupon
@app.route('/addcoupon', methods =['POST'])
def AddCoupon():
    if request.method == 'POST':
        codeCoupon = request.json['code']
        cost = request.json['discount']
        cursor = mysql.new_cursor()
        cursor.execute(f"INSERT INTO `appexpress`.`coupon` (`code`, `discount`) VALUES ('{codeCoupon}', '{cost}')")
        mysql.connection.commit()
        return "True"

#Fonction qui supprime un coupon
@app.route('/deletecoupon', methods =['POST'])
def DeleteCoupon():
    if request.method == 'POST':
        id = request.json['id']
        cursor = mysql.new_cursor()
        cursor.execute(f"DELETE FROM `appexpress`.`coupon` WHERE (`id` = '{id}')")
        mysql.connection.commit()
        return "True"
    

#Fonction qui recupère les coupons
@app.route('/getcoupons')
def GetCoupons():
    cursor = mysql.new_cursor(dictionary = True)
    cursor.execute("SELECT * FROM appexpress.coupon")
    a = cursor.fetchall()
    return json.dumps(a, default=defaultconverter)


#Fonction qui supprime un utilisateur 
@app.route('/deleteuser', methods = ['POST','GET'])
def DeleteUser():
    if request.method == 'POST':
        user = request.json['id']
        #Get user datas
        mail = request.json['mail']
        
        cursor = mysql.new_cursor(dictionary = True)
        cursor.execute("DELETE FROM `appexpress`.`user` WHERE (`id` = '"+str(user)+"')")
        mysql.connection.commit()
        #send mail that we are sorry
        #send_email(to_addr=mail, subject="Au revoir", user_name=(a[0]["name"]), email_type="command_validation", command_recap=command_recap)

    return "True"

#Fonction qui supprime un service 
@app.route('/deleteservice', methods = ['POST','GET'])
def DeleteService():
    if request.method == 'POST':
        service = request.json['id']
        cursor = mysql.new_cursor(dictionary = True)
        cursor.execute("DELETE FROM `appexpress`.`service` WHERE (`id` = '"+str(service)+"')")
        mysql.connection.commit()
    return "True"



#Fonction qui permet une connexion securisée 
@app.route('/secureconnection', methods = ['POST','GET'])
def SecureConnection():
    if request.method == 'POST':
        username = request.form['name']
        password = request.form['password']
        cursor = mysql.new_cursor(dictionary = True)
        cursor.execute("SELECT password FROM appexpress.user WHERE name = '"+username+"'")
        result = cursor.fetchall()
        if password == result[0]["password"]:     
            return "True"
        else: return "False"

#Fonction qui modifie une commande 
@app.route('/updatecommand', methods = ['POST'])
def UpdateCommand():
    Id = request.json['id']
    infos = request.json['infos']
    dateIn = request.json['enter_date']
    dateOut = request.json['return_date']
    cost = request.json['cost']
    discount = request.json['discount']
    services_quantity = request.json['services_quantity']
    date = request.json['date_']
    agent = request.json['agent']
    user = request.json['user']
    enter_time = request.json['enter_time']
    return_time = request.json['return_time']
    sub_total = request.json['sub_total']
    delivery = request.json['delivery']
    cursor = mysql.new_cursor()
    cursor.execute(f"UPDATE `appexpress`.`command` SET `cost` = '{cost}', `enter_date` = '{dateIn}', `return_date` = '{dateOut}', `services_quantity` = '{services_quantity}', `agent` = '{agent}', `enter_time` = '{enter_time}', `return_time` = '{return_time}', `sub_total` = '{sub_total}', `delivery` = '{delivery}' WHERE (`id` = '{Id}');")
    mysql.connection.commit()
    return "True"

#Fonction qui supprime une commande
@app.route('/deletecommand', methods = ['POST','GET'])
def DeleteCommand():
    if request.method == 'POST':
        command = request.json['id']
        cursor = mysql.new_cursor(dictionary = True)
        cursor.execute("DELETE FROM `appexpress`.`command` WHERE (`id` = '"+str(command)+"')")
        mysql.connection.commit()
    return "True"

#Return server time
@app.route('/time')
def get_current_time():
    now = datetime.datetime.now()
    return json.dumps({'time': now.strftime("%Y-%m-%d %H:%M:%S")})


# Function to convert a text to utf-8
def unidecode(text):
    return unidecode.unidecode(text)

"DELETE FROM `appexpress`.`service` WHERE (`id` = '5');"

""" Client ADD 
INSERT INTO `appexpress`.`client` (`ID_CLIENT`, `NAME_CLIENT`, `surname_CLIENT`, `EMAIL_CLIENT`, `ADDRESS_CLIENT`, `PHONE_CLIENT`, `PASSWORD_CLIENT`) VALUES ('hean_client20', 'REMOVED', 'client', 'REMOVED', 'Rue des Allies 93', '486650303', 'hean2000');
"""
path = os.path.abspath('/var/www/express/static/images')
#path = os.path.abspath('static/images/')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','pdf','doc','docx'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploadimage', methods=['POST'])
def upload_image():
    file = request.files['image']
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return 'File uploaded successfully'



# Servir une Image  =======================================================================



@app.route('/getimage')
def get_image(name:str = ""):
    result = f"{app.config['UPLOAD_FOLDER']}/default.png"
    fullname = f"{app.config['UPLOAD_FOLDER']}/default.png"
    """ On recupère le nom de l'image """
    if name == "":
        reqname = request.args.get('name')
    else:
        reqname = name
    """On cherche son nom dans le repertoire des images"""
    for root, directories, files in os.walk(app.config['UPLOAD_FOLDER']):
        for name in files:
            if name.__contains__(reqname):
                fullname = os.path.join(root,name)
                result = fullname
    
    return send_file(result, mimetype=magic.from_file(result, mime=True))


# Fonction qui permet de telecharger toutes les images d'un repertoire
@app.route('/getallimages')
def get_all_images():
    result = f"{app.config['UPLOAD_FOLDER']}/default.png"
    fullname = f"{app.config['UPLOAD_FOLDER']}/default.png"
    """ On recupère le nom de l'image """
    reqname = request.args.get('name')
    """On cherche son nom dans le repertoire des images"""
    for root, directories, files in os.walk(app.config['UPLOAD_FOLDER']):
        for name in files:
            fullname = os.path.join(root,name)
            result = fullname
            send_file(result, mimetype=magic.from_file(result, mime=True))


# ------ database management ------
#fill the database
@app.route('/filldatabase')
def fill_database():
    cursor = mysql.new_cursor( dictionary = True)
    # get stores
    cursor.execute("SELECT * FROM REMOVED.store")
    stores = cursor.fetchall()
    cursor.reset()
    # get services
    cursor.execute("SELECT * FROM REMOVED.service")
    services = cursor.fetchall()
    #fill the store_has_service table
    for service in services:
        for store in stores:
            cursor.reset()
            print((f"INSERT INTO `REMOVED`.`store_has_service` (`store_name`, `service_name`,`cost`) VALUES ('{store['name']}', '{service['name']}', '5.00');"))
            cursor.execute(f"INSERT INTO `REMOVED`.`store_has_service` (`store_name`, `service_name`,`cost`) VALUES ('{store['name']}', '{service['name']}', '5.00');")
            mysql.connection.commit()

# ------ Dictionaries ------
# Have to use Fr, En, Nl & It
## Services are missing
dictionary = {'fr':{
    'title1': 'Découvrez notre pressing écologique',
    'days' : ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'],
    'title2': 'Livraison',
    'subtitle1': "Nous collectons, nettoyons et livrons vos vêtements à domicile ou au bureau selon vos disponibilités.",
    'text1': "Vous ne pouvez pas vous déplacer pour venir récupérer votre linge de maison nettoyé ? Vous souhaitez vous faire livrer votre linge? Vous n’êtes pas disponible durant les heures d’ouverture de notre magasin ou vous ne pouvez pas vous déplacer pour des raisons diverses ?",
    'text2': "Si vous souhaitez faire appel à notre service de livraison pour votre linge, contactez-nous dès à présent. Nous vous proposons un service de livraison sur-mesure à l’adresse de votre choix partout en Belgique.",
    'title3': "Nous travaillons dur pour vous offrir le meilleur service de pressing à domicile",
    'title4': "Nos services",
    'subtitle4': "Nous vous proposons un service de pressing à domicile de qualité pour vous faciliter la viei.",
    'title5': "Où nous trouver ?",
    'subtitle5-1' : "Vous recherchez une blanchisserie en Belgique ou en ligne ?",
    'subtitle5-2' : "Vous avez besoin d’un service de pressing à domicile ?",
    'subtitle5-3' : "Vous souhaitez faire nettoyer votre linge de maison par des professionnels ?",
    'subtitle5-4' : "Decouvrez les services de notre pressing écologique",
    'title6': "Contactez-nous",
    'text6-1': "Pour obtenir un renseignment sur l'une ou l'autre de nos prestations, n'hésitez pas,",
    'text6-2': "contactez-nous",
    'text6-3': "Mieux? Passer nous voir directement dans nos magasin ou écrivez nous.",
    'Home': 'Accueil',
    'Pricing': 'Tarifs',
    'About': 'A propos',
    'Contact': 'Contact',
    'goto': 'Y Aller',
    'see': 'Voir',
    'categories': 'Catégories',
    'talk': 'Parlons',
    'talk-sub':"Vous avez une question ou une demande particulière ? N'hésitez pas à nous contacter via le formulaire ci-dessous ou par téléphone.",
    'name': 'Nom',
    'mail': 'Mail',
    'message': 'Message',
    'about-text1': ["Vous recherchez une blanchisserie non loin d'Ixelles et Bruxelles ? ", "Vous avez besoin d'un service de pressing à domicile ? ", "Vous souhaitez faire nettoyer votre linge de maison par des professionnels ? ", "Découvrez les services de notre pressing écologique. "],
    'about-text2': ["Ex-Press Dry Clean,", "c’est plus de 20 ans d’expérience auprès de nos clients particuliers et professionnels à Bruxelles et dans toutes les communes environnantes. ", "Nos experts du linge prennent soin de vos vêtements, de votre linge de maison ainsi que de vos chaussures au quotidien. Service de blanchisserie ou nettoyage à sec pour les textiles les plus fragiles, nous nous adaptons à vos exigences et celles de votre linge.","du secteur, nous sommes à l’affût des dernières nouveautés en termes de pressing écologique, technologies et produits professionnels mis en vente sur le marché pour prendre soin de votre linge.  Nous les renouvelons régulièrement afin de vous assurer un service parfait en toutes circonstances."],
    'about-text3': ["Notre pressing écologique vous propose un service de qualité pour nettoyer vos vêtements, votre linge de maison et vos chaussures. ", "Nous utilisons des produits de nettoyage respectueux de l’environnement pour prendre soin de votre linge et de vos vêtements. ", "Nous vous proposons un service de pressing à domicile pour vous faciliter la vie. ", "Nous collectons, nettoyons et livrons vos vêtements à domicile ou au bureau selon vos disponibilités. ","Depuis de nombreuses années, nous ne travaillons plus avec le Perchloro-éthylène. Ce solvant autrefois utilisé par les blanchisseries industrielles pour le nettoyage à sec a été classé parmi les substances cancérigènes, hautement toxiques et polluantes par les Hautes Autorités Européennes. Nous l’avons remplacé par le HiGlo pour ce qui est de notre machine situé à Etterbeek et nous utilisons le Sensene pour notre centrale de Zaventem. Des Solvants tout aussi efficace  et entièrement écologique et biodégradable. Pour enlever vos taches, nous utilisons désormais des produits 100% écologiques respectueux de votre santé et de la planète. L’écologie, à l’instar de vos taches, est aussi notre cheval de bataille !"],
    'about-text4': ["Nous sommes fiers de vous proposer des services professionnels de blanchisserie, de nettoyage à sec et de couture à Etterbeek, St-Josse, Moortebeek et Zaventem. Trois adresses différentes sous une même enseigne pour être chaque jour un peu plus près de nos clients !"],
    'strengths': [
        {
            'title': 'work1_title',
            'description':"work1_content",
            'illustration':"strength1.jpg"
        },
        {
            'title': 'work2_title', 
            'description':"work2_content",
            'illustration':"strength2.jpg"
        },
        {
            'title': 'work3_title',
            'description':"work3_content",
            'illustration':"strength3.jpg"
        },
        {
            'title': "work4_title",
            'description':"work4_content",
            'illustration':"strength4.jpg"
        }
    ]
}, 'en':{
    'title1': 'Discover our ecological dry cleaning',
    'days' : ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    'title2': 'Delivery',
    'subtitle1': "We collect, clean and deliver your clothes to your home or office according to your availability.",
    'text1': "You can't move to pick up your cleaned household linen? Do you want to have your clothes delivered? You are not available during the opening hours of our store or you cannot move for various reasons?",
    'text2': "If you want to use our laundry delivery service, contact us now. We offer you a tailor-made delivery service to the address of your choice throughout Belgium.",
    'title3': "We work hard to offer you the best home dry cleaning service",
    'title4': "Our services",
    'subtitle4': "We offer you a quality home dry cleaning service to make your life easier.",
    'title5': "Where to find us ?",
    'subtitle5-1' : "Are you looking for a laundry in Belgium or online?",
    'subtitle5-2' : "Do you need a home dry cleaning service?",
    'subtitle5-3' : "Do you want to have your household linen cleaned by professionals?",
    'subtitle5-4' : "Discover the services of our ecological dry cleaning",
    'title6': "Contact us",
    'text6-1': "To obtain information on one or the other of our services, do not hesitate,",
    'text6-2': "contact us",
    'text6-3': "Better? Come and see us directly in our store or write to us.",
    'Home': 'Home',
    'Pricing': 'Pricing',
    'About': 'About',
    'Contact': 'Contact',
    'goto': 'Go to',
    'see': 'See',
    'categories': 'Categories',
    'talk': 'Talk',
    'talk-sub':"You have a question or a particular request? Do not hesitate to contact us via the form below or by phone.",
    'name': 'Name',
    'mail': 'Mail',
    'message': 'Message',
    'about-text1': ["Are you looking for a laundry not far from Ixelles and Brussels? ", "Do you need a home dry cleaning service? ", "Do you want to have your household linen cleaned by professionals? ", "Discover the services of our ecological dry cleaning. "],
    'about-text2': ["Ex-Press Dry Clean,", "it is more than 20 years of experience with our private and professional clients in Brussels and all surrounding municipalities. ", "Our linen experts take care of your clothes, your household linen as well as your shoes on a daily basis. Laundry service or dry cleaning for the most fragile textiles, we adapt to your requirements and those of your linen.","sector, we are on the lookout for the latest news in terms of ecological dry cleaning, technologies and professional products put on sale on the market to take care of your linen. We renew them regularly to ensure you a perfect service in all circumstances."],
    'about-text3': ["Our ecological dry cleaning offers you a quality service to clean your clothes, household linen and shoes. ", "We use environmentally friendly cleaning products to take care of your linen and clothes. ", "We offer you a home dry cleaning service to make your life easier. ", "We collect, clean and deliver your clothes to your home or office according to your availability. ","For many years, we no longer work with Perchloroethylene. This solvent formerly used by industrial laundries for dry cleaning has been classified as carcinogenic, highly toxic and polluting by the European High Authorities. We have replaced it with HiGlo for our machine located in Etterbeek and we use Sensene for our Zaventem plant. Solvents just as effective and entirely ecological and biodegradable. To remove your stains, we now use 100% ecological products that are respectful of your health and the planet. Ecology, like your stains, is also our battle horse!"],
    'about-text4': ["We are proud to offer you professional laundry, dry cleaning and sewing services in Etterbeek, St-Josse, Moortebeek and Zaventem. Three different addresses under the same sign to be a little closer to our customers every day!"],
    'strengths': [
        {
            'title': 'Exceptional Quality Care',
            'description':"Our laundry company is dedicated to delivering exceptional quality care for every garment. We use state-of-the-art equipment and eco-friendly detergents that ensure your clothes are cleaned thoroughly while maintaining their original texture and color. Each item is inspected and treated by our skilled professionals to remove stains and protect delicate fabrics, providing you with perfectly clean and fresh-smelling laundry every time.",
            'illustration':"strength1.jpg"
        },
        {
            'title': 'Convenient Pickup & Delivery Service',
            'description':"We understand that your time is valuable, which is why we offer a convenient pickup and delivery service. Simply schedule a pickup time that suits you, and our reliable team will collect your laundry from your doorstep. Once cleaned and carefully packaged, we will return it to you at a time of your choosing. This hassle-free service is designed to fit seamlessly into your busy lifestyle, making laundry day a thing of the past.",
            'illustration':"strength2.jpg"
        },
        {
            'title': 'Customizable Laundry Plans',
            'description':"Our customizable laundry plans are tailored to meet your unique needs. Whether you require weekly, bi-weekly, or monthly services, we offer flexible scheduling options that can be adjusted to suit your requirements. Additionally, our specialized plans for different types of laundry, such as business attire, casual wear, and household items, ensure that every piece of fabric receives the specific care it needs.",
            'illustration':"strength3.jpg"
        },
        {
            'title': 'Affordable Pricing',
            'description':"Quality laundry services don't have to come with a hefty price tag. Our competitive pricing structure is designed to offer exceptional value without compromising on quality. We provide clear and transparent pricing with no hidden fees, so you always know what to expect. Plus, we offer special discounts and loyalty programs to make our services even more affordable for our regular customers.",
            'illustration':"strength4.jpg"
        }
    ]

}, 
'nl':{
    'title1': 'Ontdek onze ecologische droogkuis',
    'title2': 'Levering',
    'days' : ['Maandag', 'Dinsdag', 'Woensdag', 'Donderdag', 'Vrijdag', 'Zaterdag', 'Zondag'],
    'subtitle1': "Wij halen, reinigen en leveren uw kleding aan huis of op kantoor volgens uw beschikbaarheid.",
    'text1': "Kunt u niet verplaatsen om uw schoongemaakte huishoudlinnen op te halen? Wilt u uw kleding laten bezorgen? Bent u niet beschikbaar tijdens de openingstijden van onze winkel of kunt u om verschill",
    'text2': "Als u gebruik wilt maken van onze wasservice, neem dan nu contact met ons op. Wij bieden u een op maat gemaakte bezorgservice op het door u gekozen adres in heel België.",
    'title3': "We werken hard om u de beste thuisdroogreinigingsservice te bieden",
    'title4': "Onze diensten",
    'subtitle4': "Wij bieden u een kwaliteitsvolle thuisdroogreinigingsservice om uw leven gemakkelijker te maken.",
    'title5': "Waar vindt u ons ?",
    'subtitle5-1' : "Bent u op zoek naar een wasserij in België of online?",
    'subtitle5-2' : "Heeft u een thuisdroogreinigingsservice nodig?",
    'subtitle5-3' : "Wilt u uw huishoudlinnen laten reinigen door professionals?",
    'subtitle5-4' : "Ontdek de diensten van onze ecologische droogkuis",
    'title6': "Contacteer ons",
    'text6-1': "Om informatie te verkrijgen over een van onze diensten, aarzel niet,",
    'text6-2': "neem contact met ons op",
    'text6-3': "Beter? Kom direct naar onze winkel of schrijf ons.",
    'Home': 'Home',
    'Pricing': 'Tarieven',
    'About': 'Over',
    'Contact': 'Contact',
    'goto': 'Ga naar',
    'see': 'Zie',
    'categories': 'Categorieën',
    'talk': 'Praten',
    'talk-sub':"Heeft u een vraag of een speciaal verzoek? Aarzel niet om contact met ons op te nemen via het onderstaande formulier of telefonisch.",
    'name': 'Naam',
    'mail': 'Mail',
    'message': 'Bericht',
    'about-text1': ["Bent u op zoek naar een wasserij niet ver van Elsene en Brussel? ", "Heeft u een thuisdroogreinigingsservice nodig? ", "Wilt u uw huishoudlinnen laten reinigen door professionals? ", "Ontdek de diensten van onze ecologische droogkuis. "],
    'about-text2': ["Ex-Press Dry Clean,", "is meer dan 20 jaar ervaring bij onze particuliere en professionele klanten in Brussel en alle omliggende gemeenten. ", "Onze linnenexperts zorgen dagelijks voor uw kleding, uw huishoudlinnen en uw schoenen. Wasserij- of droogreinigingsdienst voor de meest kwetsbare textielen, wij passen ons aan uw eisen en die van uw linnen aan.","sector, zijn we op de hoogte van het laatste nieuws op het gebied van ecologische droogreiniging, technologieën en professionele producten die op de markt worden verkocht om voor uw linnen te zorgen. We vernieuwen ze regelmatig om u een perfecte service in alle omstandigheden te garanderen."],
    'about-text3': ["Onze ecologische droogkuis biedt u een kwaliteitsvolle service om uw kleding, huishoudlinnen en schoenen te reinigen. ", "We gebruiken milieuvriendelijke reinigingsproducten om voor uw linnen en kleding te zorgen. ", "We bieden u een thuisdroogreinigingsservice om uw leven gemakkelijker te maken. ", "Wij halen, reinigen en leveren uw kleding aan huis of op kantoor volgens uw beschikbaarheid. ","Al vele jaren werken we niet meer met Perchloorethyleen. Dit oplosmiddel dat vroeger door industriële wasserijen werd gebruikt voor droogreiniging, is door de Europese Hoge Autoriteiten geclassificeerd als kankerverwekkend, zeer giftig en vervuilend. We hebben het vervangen door HiGlo voor onze machine in Etterbeek en we gebruiken Sensene voor onze Zaventem-plant. Even effectieve en volledig ecologische en biologisch afbreekbare oplosmiddelen. Om uw vlekken te verwijderen, gebruiken we nu 100% ecologische producten die respectvol zijn voor uw gezondheid en de planeet. Ecologie, net als uw vlekken, is ook ons strijdros!"],
    'about-text4': ["We zijn er trots op u professionele wasserij-, droogreinigings- en naaiservices aan te bieden in Etterbeek, St-Josse, Moortebeek en Zaventem. Drie verschillende adressen onder hetzelfde bord om elke dag een beetje dichter bij onze klanten te zijn!"],
    'strengths': [
        {
            'title': 'Uitzonderlijke kwaliteitszorg',
            'description':"Ons wasserijbedrijf is toegewijd aan het leveren van uitzonderlijke kwaliteitszorg voor elk kledingstuk. We gebruiken geavanceerde apparatuur en milieuvriendelijke wasmiddelen die ervoor zorgen dat uw kleding grondig wordt gereinigd terwijl de oorspronkelijke textuur en kleur behouden blijven. Elk item wordt geïnspecteerd en behandeld door onze bekwame professionals om vlekken te verwijderen en delicate stoffen te beschermen, waardoor u elke keer perfect schone en fris ruikende was krijgt.",
            'illustration':"strength1.jpg"
        },
        {
            'title': 'Handige ophaal- en bezorgservice',
            'description':"We begrijpen dat uw tijd kostbaar is, daarom bieden we een handige ophaal- en bezorgservice aan. Plan eenvoudig een ophaaltijd die bij u past, en ons betrouwbare team haalt uw wasgoed op bij uw voordeur. Zodra het is gereinigd en zorgvuldig verpakt, zullen we het op een door u gekozen tijdstip aan u teruggeven. Deze moeiteloze service is ontworpen om naadloos aan te sluiten bij uw drukke levensstijl, waardoor de wasdag tot het verleden behoort.",
            'illustration':"strength2.jpg"
        },
        {
            'title': 'Aanpasbare wasplannen',
            'description':"Onze aanpasbare wasplannen zijn ontworpen om aan uw unieke behoeften te voldoen. Of u nu wekelijkse, tweewekelijkse of maandelijkse diensten nodig heeft, wij bieden flexibele planningsopties die kunnen worden aangepast aan uw wensen. Bovendien zorgen onze gespecialiseerde plannen voor verschillende soorten was, zoals zakelijke kleding, vrijetijdskleding en huishoudelijke artikelen, ervoor dat elk stuk stof de specifieke zorg krijgt die het nodig heeft.",   
            'illustration':"strength3.jpg"
        },
        {
            'title': 'Betaalbare prijzen',
            'description':"Kwaliteitsvolle wasservices hoeven niet duur te zijn. Onze concurrerende prijsstructuur is ontworpen om uitzonderlijke waarde te bieden zonder in te boeten aan kwaliteit. We bieden duidelijke en transparante prijzen zonder verborgen kosten, zodat u altijd weet wat u kunt verwachten. Bovendien bieden we speciale kortingen en loyaliteitsprogramma's om onze diensten nog betaalbaarder te maken voor onze vaste klanten.",
            'illustration':"strength4.jpg"
        }
    ]

}, 'it':{
    'title1': 'Scopri il nostro lavaggio a secco ecologico',
    'title2': 'Consegna',
    'days' : ['Lunedì', 'Martedì', 'Mercoledì', 'Giovedì', 'Venerdì', 'Sabato', 'Domenica'],
    'subtitle1': "Ritiriamo, puliamo e consegniamo i tuoi vestiti a casa o in ufficio secondo la tua disponibilità.",
    'text1': "Non puoi spostarti per ritirare il tuo bucato pulito? Vuoi farti consegnare i tuoi vestiti? Non sei disponibile durante l'orario di apertura del nostro negozio o non puoi spostarti per vari motivi?",
    'text2': "Se desideri usufruire del nostro servizio di lavanderia a domicilio, contattaci ora. Ti offriamo un servizio di consegna su misura all'indirizzo da te scelto in tutta Belgio.",
    'title3': "Lavoriamo duramente per offrirti il miglior servizio di lavaggio a secco a domicilio",
    'title4': "I nostri servizi",
    'subtitle4': "Ti offriamo un servizio di lavaggio a secco a domicilio di qualità per semplificarti la vita.",
    'title5': "Dove trovarci ?",
    'subtitle5-1' : "Stai cercando una lavanderia in Belgio o online?",
    'subtitle5-2' : "Hai bisogno di un servizio di lavaggio a secco a domicilio?",
    'subtitle5-3' : "Vuoi far pulire il tuo bucato da casa da professionisti?",
    'subtitle5-4' : "Scopri i servizi del nostro lavaggio a secco ecologico",
    'title6': "Contattaci",
    'text6-1': "Per ottenere informazioni su uno o l'altro dei nostri servizi, non esitare,",
    'text6-2': "contattaci",
    'text6-3': "Meglio? Vieni a trovarci direttamente nel nostro negozio o scrivici.",
    'Home': 'Home',
    'Pricing': 'Prezzi',
    'About': 'Su di noi',
    'Contact': 'Contatto',
    'goto': 'Vai a',
    'see': 'Vedi',
    'categories': 'Categorie',
    'talk': 'Parlare',
    'talk-sub':"Hai una domanda o una richiesta particolare? Non esitare a contattarci tramite il modulo sottostante o per telefono.",
    'name': 'Nome',
    'mail': 'Mail',
    'message': 'Messaggio',
    'about-text1': ["Stai cercando una lavanderia non lontano da Ixelles e Bruxelles? ", "Hai bisogno di un servizio di lavaggio a secco a domicilio? ", "Vuoi far pulire il tuo bucato da professionisti? ", "Scopri i servizi del nostro lavaggio a secco ecologico. "],
    'about-text2': ["Ex-Press Dry Clean,", "è più di 20 anni di esperienza con i nostri clienti privati e professionali a Bruxelles e in tutti i comuni circostanti. ", "I nostri esperti di biancheria si prendono cura dei tuoi vestiti, della tua biancheria da casa e delle tue scarpe quotidianamente. Servizio di lavanderia o lavaggio a secco per i tessuti più fragili, ci adattiamo alle tue esigenze e a quelle della tua biancheria.","settore, siamo sempre alla ricerca delle ultime novità in materia di lavaggio a secco ecologico, tecnologie e prodotti professionali messi in vendita sul mercato per prendersi cura della tua biancheria. Li rinnoviamo regolarmente per garantirti un servizio perfetto in tutte le circostanze."],
    'about-text3': ["Il nostro lavaggio a secco ecologico ti offre un servizio di qualità per pulire i tuoi vestiti, la tua biancheria da casa e le tue scarpe. ", "Utilizziamo prodotti per la pulizia rispettosi dell'ambiente per prenderti cura della tua biancheria e dei tuoi vestiti. ", "Ti offriamo un servizio di lavaggio a secco a domicilio per semplificarti la vita. ", "Ritiriamo, puliamo e consegniamo i tuoi vestiti a casa o in ufficio secondo la tua disponibilità. ","Da molti anni non lavoriamo più con il Percloroetilene. Questo solvente usato in passato dalle lavanderie industriali per il lavaggio a secco è stato classificato come cancerogeno, altamente tossico e inquinante dalle Autorità Europee. L'abbiamo sostituito con l'HiGlo per la nostra macchina situata a Etterbeek e utilizziamo il Sensene per la nostra centrale di Zaventem. Solventi altrettanto efficaci e completamente ecologici e biodegradabili. Per rimuovere le macchie, ora utilizziamo prodotti al 100% ecologici rispettosi della tua salute e del pianeta. L'ecologia, come le tue macchie, è anche il nostro cavallo di battaglia!"],
    'about-text4': ["Siamo orgogliosi di offrirti servizi professionali di lavanderia, lavaggio a secco e sartoria a Etterbeek, St-Josse, Moortebeek e Zaventem. Tre indirizzi diversi sotto lo stesso segno per essere un po' più vicini ai nostri clienti ogni giorno!"],
    'strengths': [
        {
            'title': 'Cura della qualità eccezionale',
            'description':"La nostra azienda di lavanderia si impegna a fornire una cura della qualità eccezionale per ogni capo. Utilizziamo attrezzature all'avanguardia e detergenti ecologici che garantiscono una pulizia profonda dei tuoi vestiti preservandone la texture e il colore originali. Ogni articolo viene ispezionato e trattato dai nostri professionisti qualificati per eliminare le macchie e proteggere i tessuti delicati, offrendoti così un bucato perfettamente pulito e fresco ogni volta.",
            'illustration':"strength1.jpg"
        },
        {
            'title': 'Servizio di ritiro e consegna comodo',
            'description':"Sappiamo che il tuo tempo è prezioso, ecco perché offriamo un servizio di ritiro e consegna comodo. Basta pianificare un orario di ritiro che ti convenga, e il nostro team affidabile verrà a ritirare il tuo bucato alla tua porta. Una volta pulito e accuratamente confezionato, te lo restituiremo all'ora che preferisci. Questo servizio senza stress è progettato per integrarsi perfettamente nel tuo stile di vita frenetico, facendo del giorno del bucato un lontano ricordo.",
            'illustration':"strength2.jpg"
        },
        {
            'title': 'Piani di lavanderia personalizzabili',
            'description':"I nostri piani di lavanderia personalizzabili sono progettati per soddisfare le tue esigenze specifiche. Che tu abbia bisogno di un servizio di pulizia regolare o occasionale, abbiamo una soluzione adatta al tuo programma e al tuo budget. I nostri pacchetti flessibili ti consentono di scegliere i servizi di cui hai bisogno, quando ne hai bisogno, offrendoti così una soluzione di lavanderia su misura che soddisfa le tue aspettative.",
            'illustration':"strength3.jpg"
        },
        {
            'title': 'Prezzi competitivi',
            'description':"Offriamo prezzi competitivi per i nostri servizi di lavanderia e lavaggio a secco. I nostri prezzi convenienti sono progettati per soddisfare le tue esigenze di pulizia senza compromettere il tuo budget. Offriamo pacchetti di lavanderia flessibili che ti consentono di scegliere i servizi di cui hai bisogno, quando ne hai bisogno, offrendoti così una soluzione di pulizia su misura che soddisfa le tue aspettative.",    
            'illustration':"strength4.jpg"
        }
    ]
}}

""" @app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response
 """
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7001)
    refresh()
