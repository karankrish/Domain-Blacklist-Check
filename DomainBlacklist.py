from spam_lists import SPAMHAUS_DBL
from spam_lists import SPAMHAUS_ZEN
from spam_lists import SURBL_MULTI
from pymongo import MongoClient
import json
import os
from datetime import datetime
import mysql.connector
import logging
from logging.handlers import RotatingFileHandler
from datetime import timezone
import threading
from elasticsearch import Elasticsearch



logging.basicConfig(filename='log/DomainBlacklist.log', level=logging.ERROR, 
                    format='%(asctime)s %(levelname)s %(name)s %(message)s')
logger=logging.getLogger("DomainBlacklist.log")
handler = RotatingFileHandler("log/DomainBlacklist.log", maxBytes=2000, backupCount=25) 
if not logger: 
    logger.addHandler(handler)
with open('config.json') as f:
    config = json.load(f)  

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(tz=None)

def run(key):
    
    ID=key[0]
    hostname=key[1]
    try:
        DomainBlacklist_data=DomainBlacklist(key)
        data={}
        data['_id']=ID
        data['hostname']=hostname
        data["LastUpdate"]=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data['DomainBlacklist']=DomainBlacklist_data
        msd(data)
       # elasticsearch(data)
    except Exception as e:
        logger.error("------run---------" +str(e))
        data={}
        data['_id']=ID
        data['hostname']=hostname
    #print(key[1])
    return 
    

def Main():
    try:
        
        worker_data =  mySQL_read()    
        for i in worker_data:
            #threading.Thread(target=run, args = (i,)).start()
            run(i)
    except Exception as e:
        logger.error("------Main---------" +str(e))

    return 

def mySQL_read():
    try:
        asd=[]  
        mydb = mysql.connector.connect(
    	  host= config['mysql']['host'],
    	  user= config['mysql']['user'],
    	  passwd= config['mysql']['passwd'],
    	  database= config['mysql']['database']
    	)
        mycursor = mydb.cursor()
        mycursor.execute("SELECT user_reg_id,company_domain FROM registered_user")
        #mycursor.execute("SELECT user_reg_id,company_domain FROM registered_user limit 0,5")
        row = mycursor.fetchone()
        while row is not None:
            asd.append(row)
            row = mycursor.fetchone()
    except Exception as e:
        logger.error("------mySQL_read---------" +str(e))
        asd=[]

    return asd

def DomainBlacklist(key):
    
    try:
        hostname=key[1]
        Blacklist=[]
        source = os.popen('curl -s -H "Accept: application/json" -H "X-Auth-Token: 73b788d1-0539-4794-9c7a-9b5b9d3bac6f" -X GET https://api.apility.net/baddomain/'+hostname).read()
        d = json.loads(source)
        Blacklist = d["response"]["domain"]["blacklist"]
        if (hostname in SPAMHAUS_DBL) == True:

             Blacklist.append("SPAMHAUS_DBL")
             
        if (hostname in SPAMHAUS_ZEN) == True:

            Blacklist.append("SPAMHAUS_ZEN")

        if (hostname in SURBL_MULTI) == True:

            Blacklist.append("SURBL")

        h= len(Blacklist)
  
        
    except Exception as e:
        logger.error(hostname +"--------DomainBlacklist : ----------" + str(e))
        
        Blacklist='0'
        h='0'
    json_data = {}
    json_data["domainBlacklist"] = h
    json_data["Blacklist"] = Blacklist   
   
    return json_data




def msd(data):
    try:

        client =MongoClient(config['mongodb']['host'],
                                       username=config['mongodb']['username'],
                                       password=config['mongodb']['password'],
                                       authSource=config['mongodb']['authSource'])
        db = client.DomainMonitor
        collection = db.DomainBlacklist
        x=data
        #collection.insert(x)
        collection.update({'_id': x['_id']},{'$set':x}, upsert=True, multi=False)

    except Exception as e:
        logger.error("---------Mongodb connection  :-------------- " +str(e))
    return 
def elasticsearch(data):
    try:
        data.pop("_id")
        es=Elasticsearch([{'host':'35.200.240.123','port':9200}])
        res = es.index(index='domainmonitor',doc_type='data',body=data)
    except Exception as e:
        logger.error("---------Elasticsearch  :-------------- " +str(e))
    return 
    
    

if __name__ == "__main__":
    Main()
    
   

