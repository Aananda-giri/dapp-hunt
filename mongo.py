import csv
from datetime import datetime
import os
import time
from pymongo.server_api import ServerApi

from typing import List

# load dotenv: giving absulute path otherwise load_dotenv not working with `sys.path.append` from worker_spider.py
from dotenv import load_dotenv
# Get the absolute path to the directory containing this script
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construct the absolute path to the .env file
dotenv_path = os.path.join(current_dir, '.env')

load_dotenv(dotenv_path)

assert os.environ.get('mongo_uri') != None, "mongo_uri not found"

# Creating mangodb
from pymongo import MongoClient




from pymongo.mongo_client import MongoClient




class Mongo():
    def __init__(self, db_name='dapp-hunt', collection_name="web_pages", local=False):
        self.uri=os.environ.get('mongo_uri')
        
        # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
        self.client = MongoClient(self.uri, server_api=ServerApi('1'))
        
        self.ping()

        # Create the database for our example (we will use the same database throughout the tutorial
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]  # using single collection for all urls
        # # one time operation
        # self.collection.create_index('url', unique=True)
        self.collection.create_index('source')


        # message_collection
        self.messages_collection = self.db.messages
        self.messages_collection.create_index('source', unique=True)

        self.summary_collection = self.db.summaries
        self.summary_collection.create_index('source', unique=True)
    
    def ping(self):
        # Send a ping to confirm a successful connection
        try:
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(e)

    def add_documents(self, documents:List):
        '''
        documents:
        [
            {
                'source' : 'google.com',
                'url': 'https://google.com',
                'text_content': 'google is a search enginee.',
            
            },
            {
                'source' : 'bing.com',
                'url': 'https://bing.com',
                'text_content': 'bing is a search enginee too..',
            
            },


        ]
        '''
        self.collection.insert_many(documents)

    def list_documents(self, source:str = 'google.com'):
        '''
        e.g.
        [{'_id': ObjectId('67966cc2a2417a3b77cf17c4'), 'source': 'google.com', 'url': 'https://google.com', 'text_content': 'google is a search enginee.'}, {'_id': ObjectId('67966cd50d2a547e72a678ee'), 'source': 'google.com', 'url': 'https://google.com', 'text_content': 'google is a search enginee.'}]
        '''

        return list(self.collection.find({'source':source}))
    
    def append_message(self, source, query, response):
        '''
            * append new message to existinig message_collection
        '''
        new_message = {
            "query": query,
            "response": response,
            "timestamp": datetime.now(),
            "source": source
        }

        # Add the new message to the 'messages' array for the specific source
        result = self.messages_collection.update_one(
            {"source": source},  # Filter by source
            {"$push": {"messages": new_message}},  # Add the new message to the array
            upsert=True  # Create a document if it doesn't exist
        )

        if result.upserted_id:
            print(f"New document created with ID: {result.upserted_id}")
        else:
            print("Document updated successfully.")
        # list(messages_collection.find({}))
    def exists(self, source):
        return self.collection.find_one({'source':source})
if __name__=="__main__":
    # delete all data and create unique index for field: 'url'
    mongo = Mongo()
    
    documents = [
            {
                'source' : 'google.com',
                'url': 'https://google.com',
                'text_content': 'google is a search enginee.',
            
            },
            {
                'source' : 'bing.com',
                'url': 'https://bing.com',
                'text_content': 'bing is a search enginee too..',
            
            },


        ]
    # mongo.add_documents(documents)
    print(mongo.list_documents('google.com'))