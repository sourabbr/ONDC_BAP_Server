# -*- coding: utf-8 -*-

from flask import Flask
from flask.wrappers import Request
from flask import request
from flask import jsonify

import requests

import os
import time
from datetime import datetime
import json
import uuid

app = Flask(__name__)
# api = restful.Api(app)

transaction_id_map = {}
message_id_map = {}

bpp_ack_response = {
  "message": {
    "ack": {
      "status": "ACK"
    }
  }
}

log_file = open('log.txt', 'w+')

def Logger (heading, value):
    print ("\n******" + heading + "******\n")
    print (value)
    log_file.write ("\n******" + heading + "******\n")
    log_file.write (str(value))
    
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

@app.route('/search',methods=["GET","POST"])
def search():

    # Read request from tally buyer app
    req = request.get_data()
    req_str = bytes.decode(req)
    data = json.loads(req_str)
    Logger("Request from Tally Buyer App", req_str)

    # Create transaction id and message id
    tran_id = str (uuid.uuid4())
    msg_id = str (uuid.uuid4())
    Logger("Action", "Search")
    Logger("Transaction ID", tran_id)    
    Logger("Message ID", msg_id)

    # Update Transaction ID and message ID map
    transaction_id_map[tran_id] = msg_id
    message_id_map[msg_id] = ""

    # ONDC_TODO
    # Prepare and send request to BG
    resp = SendPostRequest ("https://172.25.0.132:443", data)
    if (not resp):
        print ("Error")
        return resp
    
    # Check for data from onsearch
    while NoDataReceived (tran_id):
        time.sleep(0.5)

    res = ReadResp (msg_id)

    # ONDC_TODO
    # Format response as per response to be sent to Tally buyer app

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

    # ONDC_TODO
    # Read transaction id from request
    tran_id = "123"
    # Create message id    
    msg_id = str (uuid.uuid4())   

    Logger("Action", "Select")
    Logger("Transaction ID", tran_id)    
    Logger("Message ID", msg_id)

    # Update Transaction ID and message ID map
    transaction_id_map[tran_id] = msg_id
    message_id_map[msg_id] = ""

    # ONDC_TODO
    # Prepare and send request to BPP
    
    # Check for data from onsearch
    while NoDataReceived (tran_id):
        time.sleep(0.5)

    res = ReadResp (msg_id)

    # ONDC_TODO
    # Format response as per response to be sent to Tally buyer app

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
    msg_id = res["context"]["message_id"]
    Logger("Action", "OnSelect")
    Logger("Transaction ID", tran_id)    
    Logger("Message ID", msg_id)

    WriteResp (msg_id, req_str)
         
    return jsonify (bpp_ack_response)


if __name__ == '__main__':
    app.run(port=5000, debug=True)






