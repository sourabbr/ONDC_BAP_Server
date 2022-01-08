# -*- coding: utf-8 -*-

from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify

import requests

import time
from datetime import datetime
import json
import uuid

### Global variable strings
Core_Version_Key_Str = "core_version"
BAP_ID_Key_Str      = "bap_id"
BAP_URI_Key_Str     = "bap_uri"
BPP_ID_Key_Str      = "bpp_id"
BPP_URI_Key_Str     = "bpp_uri"
Trans_ID_Key_Str    = "transaction_id"
Msg_ID_Key_Str      = "message_id"
TimeStamp_Key_Str   = "timestamp"

Core_Version_Value   = "1.0.0"

#ONDC_TODO
# update the values
BAP_ID_Value         = "https://mock_bpp.com/"
BAP_URI_Value        = "https://mock_bpp.com/"


app = Flask(__name__)
# api = restful.Api(app)

@app.route('/')
def index():
    return render_template('index.html')

transaction_id_map = {}
message_id_map = {}

bpp_ack_response = {
  "message": {
    "ack": {
      "status": "ACK"
    }
  }
}

def Logger (heading, value):
    log_file = open('log.txt', 'a+')
    print ("\n******" + heading + "******\n")
    print (value)
    log_file.write ("\n******" + heading + "******\n")
    log_file.write (str(value))
    log_file.close ()
    
def CreateRespFile (msg_id):
    resp_file = open (msg_id, 'w+')
    resp_file.close ()

def ReadRespFile (msg_id):
    resp_file = open (msg_id, 'r+')
    response = resp_file.read ()
    resp_file.close ()
    return response

def WriteRespFile (msg_id, req_str):
    resp_file = open(msg_id, 'w+')
    resp_file.write(req_str)
    resp_file.close()

def ReadResp (msg_id):
    return message_id_map[msg_id]

def WriteResp (msg_id, req_str):
    message_id_map[msg_id] = req_str

def NoDataReceived (tran_id):
    return not message_id_map[transaction_id_map[tran_id]] 

def SendPostRequest (url, data):
    headers = {'Content-type': 'text/html; charset=UTF-8'}
    response = requests.post(url, json=data, headers=headers)
    resp_body = response.json () 
    if (resp_body["message"]["ack"]["status"] == "ACK"):
        return True
    else:
        return False

def PrepareSendRequest (req_body, msg_id):
    req_body['context'][Msg_ID_Key_Str]    = msg_id
    req_body['context'][TimeStamp_Key_Str] = str(datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z")

@app.route('/search',methods=["GET","POST"])
def search():

    # Read request from tally buyer app
    req = request.get_data()
    req_str = bytes.decode(req)
    data = json.loads(req_str)
    Logger("Request from Tally Buyer App", req_str)

    # Create transaction id and message id
    # tran_id = str (uuid.uuid4())
    # msg_id = str (uuid.uuid4())
    tran_id = str (1209849124)
    msg_id = str (12341242343)
    Logger("Action", "Search")
    Logger("Transaction ID", tran_id)
    Logger("Message ID", msg_id)

    # Update Transaction ID and message ID map
    transaction_id_map[tran_id] = msg_id
    message_id_map[msg_id] = ""

    # Prepare and send request to BG
    data['context'][Core_Version_Key_Str] = Core_Version_Value
    data['context'][BPP_ID_Key_Str] = BAP_ID_Value
    data['context'][BPP_URI_Key_Str] = BAP_URI_Value
    data['context'][Trans_ID_Key_Str] = tran_id
    
    PrepareSendRequest(data, msg_id)

    resp = SendPostRequest ("http://localhost:5001/sourab", data)

    if (not resp):
        #ONDC_TODO
        #Need to agree with client what error to send
        Logger("Error NACK")
        return resp
    
    # Check for data from onsearch
    while NoDataReceived (tran_id):
        time.sleep(0.5)

    res = ReadResp (msg_id)

    # sending response to client as it is.
    Logger("Response being sent to Tally Buyer App", res)    
    return res


@app.route('/onsearch', methods=["POST"])
def onsearch():

    # Read request form BG    
    req = request.get_data()
    req_str = bytes.decode(req)
    Logger ("Request from BG", req_str)

    # Format as dictionary
    res = json.loads(req_str)

    tran_id = res["context"]["transaction_id"]
    msg_id = res["context"]["message_id"]
    Logger("Action", "OnSearch")
    Logger("Transaction ID", tran_id)    
    Logger("Message ID", msg_id)

    WriteResp (msg_id, req_str)
         
    return jsonify (bpp_ack_response)


@app.route('/select',methods=["GET","POST"])
def select():

    # Read request from tally buyer app
    req = request.get_data()
    req_str = bytes.decode(req)
    Logger("Request from Tally Buyer App", req_str)

    # Format as dictionary
    res = json.loads(req_str)

    tran_id = res["context"]["transaction_id"]
    bpp_uri = res["context"]["bpp_uri"]

    # Create message id 
    msg_id = str (uuid.uuid4())   

    Logger("Action", "Select")
    Logger("Transaction ID", tran_id)    
    Logger("Message ID", msg_id)

    # Update Transaction ID and message ID map
    transaction_id_map[tran_id] = msg_id
    message_id_map[msg_id] = ""

    PrepareSendRequest (res, msg_id)

    resp = SendPostRequest (bpp_uri, res)

    if (not resp):
        Logger("Error NACK")
        return resp
    
    # Check for data from onsearch
    while NoDataReceived (tran_id):
        time.sleep(0.5)

    res = ReadResp (msg_id)

    Logger("Response being sent to Tally Buyer App", res)    
    return res

@app.route('/onselect', methods=["POST"])
def onselect():

    # Read request form BPP    
    req = request.get_data()
    req_str = bytes.decode(req)
    Logger ("Request from BPP", req_str)

    # Format as dictionary
    res = json.loads(req_str)

    tran_id = res["context"]["transaction_id"]
    msg_id  = res["context"]["message_id"]

    Logger("Action", "OnSelect")
    Logger("Transaction ID", tran_id)
    Logger("Message ID", msg_id)

    WriteResp (msg_id, req_str)

    return jsonify (bpp_ack_response)


# init flow
@app.route('/init', methods=["GET","POST"])
def init():

    # Read request from tally buyer app
    req = request.get_data()
    req_str = bytes.decode(req)
    Logger("Request from Tally Buyer App", req_str)

    # Format as dictionary
    res = json.loads(req_str)

    tran_id = res["context"]["transaction_id"]
    bpp_uri = res["context"]["bpp_uri"]

    # Create message id 
    msg_id = str (uuid.uuid4())   

    Logger("Action", "Init")
    Logger("Transaction ID", tran_id)    
    Logger("Message ID", msg_id)

    # Update Transaction ID and message ID map
    transaction_id_map[tran_id] = msg_id
    message_id_map[msg_id] = ""

    PrepareSendRequest (res, msg_id)

    resp = SendPostRequest (bpp_uri, res)

    if (not resp):
        Logger("Error NACK")
        return resp
    
    # Check for data from onsearch
    while NoDataReceived (tran_id):
        time.sleep(0.5)

    res = ReadResp (msg_id)

    Logger("Response being sent to Tally Buyer App", res)    
    return res

@app.route('/oninit', methods=["POST"])
def oninit():

    # Read request form BPP    
    req = request.get_data()
    req_str = bytes.decode(req)
    Logger ("Request from BPP", req_str)

    # Format as dictionary
    res = json.loads(req_str)

    tran_id = res["context"]["transaction_id"]
    msg_id  = res["context"]["message_id"]

    Logger("Action", "Oninit")
    Logger("Transaction ID", tran_id)
    Logger("Message ID", msg_id)

    WriteResp (msg_id, req_str)

    return jsonify (bpp_ack_response)


# confirm flow
@app.route('/confirm', methods=["GET","POST"])
def confirm():

    # Read request from tally buyer app
    req = request.get_data()
    req_str = bytes.decode(req)
    Logger("Request from Tally Buyer App", req_str)

    # Format as dictionary
    res = json.loads(req_str)

    tran_id = res["context"]["transaction_id"]
    bpp_uri = res["context"]["bpp_uri"]

    # Create message id 
    msg_id = str (uuid.uuid4())   

    Logger("Action", "Confirm")
    Logger("Transaction ID", tran_id)    
    Logger("Message ID", msg_id)

    # Update Transaction ID and message ID map
    transaction_id_map[tran_id] = msg_id
    message_id_map[msg_id] = ""

    PrepareSendRequest (res, msg_id)

    resp = SendPostRequest (bpp_uri, res)

    if (not resp):
        Logger("Error NACK")
        return resp
    
    # Check for data from onsearch
    while NoDataReceived (tran_id):
        time.sleep(0.5)

    res = ReadResp (msg_id)

    Logger("Response being sent to Tally Buyer App", res)    
    return res


@app.route('/onconfirm', methods=["POST"])
def oninit():

    # Read request form BPP    
    req = request.get_data()
    req_str = bytes.decode(req)
    Logger ("Request from BPP", req_str)

    # Format as dictionary
    res = json.loads(req_str)

    tran_id = res["context"]["transaction_id"]
    msg_id  = res["context"]["message_id"]

    Logger("Action", "Onconfirm")
    Logger("Transaction ID", tran_id)
    Logger("Message ID", msg_id)

    WriteResp (msg_id, req_str)

    return jsonify (bpp_ack_response)


# Cancel flow
@app.route('/cancel', methods=["GET","POST"])
def init():

    # Read request from tally buyer app
    req = request.get_data()
    req_str = bytes.decode(req)
    Logger("Request from Tally Buyer App", req_str)

    # Format as dictionary
    res = json.loads(req_str)

    tran_id = res["context"]["transaction_id"]
    bpp_uri = res["context"]["bpp_uri"]

    # Create message id 
    msg_id = str (uuid.uuid4())   

    Logger("Action", "Cancel")
    Logger("Transaction ID", tran_id)    
    Logger("Message ID", msg_id)

    # Update Transaction ID and message ID map
    transaction_id_map[tran_id] = msg_id
    message_id_map[msg_id] = ""

    PrepareSendRequest (res, msg_id)

    resp = SendPostRequest (bpp_uri, res)

    if (not resp):
        Logger("Error NACK")
        return resp
    
    # Check for data from onsearch
    while NoDataReceived (tran_id):
        time.sleep(0.5)

    res = ReadResp (msg_id)

    Logger("Response being sent to Tally Buyer App", res)    
    return res


@app.route('/oncancel', methods=["POST"])
def oninit():

    # Read request form BPP    
    req = request.get_data()
    req_str = bytes.decode(req)
    Logger ("Request from BPP", req_str)

    # Format as dictionary
    res = json.loads(req_str)

    tran_id = res["context"]["transaction_id"]
    msg_id  = res["context"]["message_id"]

    Logger("Action", "Oncancel")
    Logger("Transaction ID", tran_id)
    Logger("Message ID", msg_id)

    WriteResp (msg_id, req_str)

    return jsonify (bpp_ack_response)


if __name__ == '__main__':
    app.run(port=5000, debug=True)