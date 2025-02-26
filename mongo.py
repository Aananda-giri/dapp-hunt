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

from bson import ObjectId


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


        # to perform full text search, we must create a text index on a collection.
        self.collection.create_index([("text_content", "text")])


        # message_collection
        self.messages_collection = self.db.messages
        self.messages_collection.create_index('source', unique=True)

        # brainstorm messages collection
        self.brainstorm_collection = self.db.brainstorm
        self.brainstorm_collection.create_index('source', unique=True)

        # Summary collection (store lean canvas data)
        self.summary_collection = self.db.summaries
        self.summary_collection.create_index('source', unique=True)

        # Questions collection
        self.questions_collection = self.db.questions
        self.questions_collection.create_index('source')

        # Session collection for login sessions
        self.session_collection = self.db.session
        # Create TTL index for auto-expiring sessions if it doesn't exist
        self.session_collection.create_index("expires", expireAfterSeconds=0)

        # Canvas questions
        self.canvas_question_collection = self.db.canvas_question_collection
        self.canvas_question_collection.create_index('user_id', unique=True)
        '''
        example data canvas_question_collection:
        {
            "user_id":"110498293652394239535",
            'overall': 'What is <your-product-name>? Give a description of what it does and why it exists.',
            'target_users': 'Who is <your-product-name> intended for? These groups of people are called target users.',
            'problems': 'What are the reasons for target users to seek out, and adopt, <your-product-name>?',
            'solutions': 'How does <your-product-name> address each one of these reasons?',
            'unfair_advantage': 'What makes <your-product-name> difficult to compete with?',
            'unique_value_proposition': 'What makes <your-product-name> unique or special compared to others?',
            'channels': 'Which channels does <your-product-name> use to reach its target users?',
            'costs': 'What operating costs are incurred by <your-product-name>?',
            'revenue': 'How does <your-product-name> generate revenue?'
        }
        '''
    
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
    
    def append_brainstorm_message(self, source, query, response):
        
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
        result = self.brainstorm_collection.update_one(
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

    def update_summary(self, source, summaries):
        """
        Updates the 'summaries' field for an existing document with the given source.
        If not found, inserts a new document.

        Parameters:
            mongo: MongoDB client object
            source (str): The unique source identifier
            summaries (list): List of summaries to update or insert
        """
        collection = self.summary_collection  # Access the summary collection

        # Upsert operation: update summaries if source exists, otherwise insert new
        collection.update_one(
            {"source": source},  # Search condition
            {
                "$set": {
                    "summaries": summaries,
                    "created_at": datetime.now()
                }
            },
            upsert=True  # Insert if not found
        )

        print(f"Summary for '{source}' updated or created successfully.")

    # def update_summary(self, source:str, title:str, new_text:str):
    #     try:
    #         full_document = self.summary_collection.find_one({'source' : source})

    #         all_summaries = full_document['summaries']

    #         # update summary of specific topic
    #         all_summaries[title.lower()] = new_text

    #         # update if exists, create new otherwise
    #         query = {"source": source}

    #         # Define the update operation
    #         update = {
    #             "$set": {
    #                 "summaries": all_summaries,
    #                 "created_at": datetime.now()
    #             }
    #         }

    #         # Use update_one with upsert=True
    #         self.summary_collection.update_one(query, update, upsert=True)
    #     except Exception as e:
    #         print(f' failed to update summary for {source} with title: {title} and new_text: {new_text[:50]}...\n error:{e}')
    
    def get_messages(self, source, model_name, exclude_timestamp=True):
        """
        * returns only query and response
        * not returning datetime field (cause it is giving serialization error) : todo: fix datetime serialization error.

        returns messages in format:
        [
            {
                'query': <some-query>,
                'response': <some-response>
            }, 

            ...
        ]
        """

        if model_name.startswith('chat'):
            print('chat model')
            # chat messeges
            chat_history = self.messages_collection.find({'source':source})
        else:
            print('brainstorm model')
            # brainstorm messages
            chat_history = self.brainstorm_collection.find({'source':source})

        # Iterate through the cursor to get each document
        messages = []
        for message in chat_history:
            messages.extend(message['messages'])

        if exclude_timestamp:
            # to solve error: datetime.datetime(2025, 1, 28, 16, 10, 58, 583000) is not JSON serializable
            messages_new = []
            for message in messages:
                messages_new.append({
                    'query':message['query'],
                    'response':message['response']
                })
        else:
            messages_new = []
            for message in messages:
                message['timestamp'] = str(message['timestamp'])
                messages_new.append(message)
        return messages_new
    
    # Create a question
    def create_question(self, source: str, question: str, answer: str):
        question_data = {"source": source, "question": question, "answer": answer}
        result = self.questions_collection.insert_one(question_data)
        return str(result.inserted_id)

    # Delete a question by ID
    def delete_question(self, question_id: str):
        result = self.questions_collection.delete_one({"_id": ObjectId(question_id)})
        return result.deleted_count > 0

    # Update a question by ID
    def update_question(self, question_id: str, updated_data: dict):
        update_fields = {key: value for key, value in updated_data.items() if key in ["source", "question", "answer"]}
        result = self.questions_collection.update_one({"_id": ObjectId(question_id)}, {"$set": update_fields})
        return result.modified_count > 0
    
    def delete_canvas_question_field(self, user_id: str, field: str):
        """
        Deletes a specific field from a user's document.
        user_id: it is userid given by google

        
        user_id is unique
        """
        result = self.canvas_question_collection.update_one(
            {"user_id": user_id},
            {"$unset": {field: ""}}
        )
        return result.modified_count > 0  # Returns True if a field was deleted

    def add_canvas_question_field(self, user_id: str, field: str, value: str):
        """Adds or updates a specific field in a user's document."""
        result = self.canvas_question_collection.update_one(
            {"user_id": user_id},
            {"$set": {field: value}},
            upsert=True  # Creates the document if user_id does not exist
        )
        return result.modified_count > 0  # Returns True if a field was added/updated

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