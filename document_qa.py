import requests
import json
from typing import List, Dict, Optional
from pymongo import MongoClient

from atoma_sdk import AtomaSDK

from dotenv import load_dotenv
import os
load_dotenv()


assert os.environ.get('ATOMA_BEARER') != None

class DocumentQA:
    def __init__(self, api_token: str, mongo, chunk_size: int = 1000, overlap: int = 100):
        self.api_token = api_token
        self.mongo = mongo
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.api_url = "https://api.atoma.network/v1/chat/completions"
        self.questions = {
            "overall": "What is {source}? Give a description of what it does and why it exists.",
            "target_users": "Who is {source} intended for? These groups of people are called target users.",
            "problems": "What are the reasons for target users to seek out, and adopt, {source}?",
            "solutions": "How does {source} address each one of these reasons?",
            "unfair_advantage": "What makes {source} difficult to compete with?",
            "unique_value_proposition": "What makes {source} unique or special compared to others?",
            "channels": "Which channels does {source} use to reach its target users?",
            "costs": "What operating costs are incurred by {source}?",
            "revenue": "How does {source} generate revenue?"
        }

    def query_llm(self, query: str, max_tokens: int = 500, use_r1=False, include_thinking_text=False) -> str:
        """
        Send a query to the LLM API and return the response
        """
        # query using deepseek r1 model
        #---------------------------
        if use_r1:
            print(f'using r1 model')
            try:
                with AtomaSDK(
                    bearer_auth=os.environ.get('ATOMA_BEARER'),
                ) as atoma_sdk:
                    res = atoma_sdk.chat.create(messages=[
                        {
                            "content": query,
                            "role": "user",
                        },
                    ], model="deepseek-ai/DeepSeek-R1", frequency_penalty=0, max_tokens=2048, n=1, presence_penalty=0, seed=123, stop=[
                        "json([\"stop\", \"halt\"])",
                    ], temperature=0.7, top_p=1, user="user-1234")
                    # Handle response
                    if include_thinking_text:
                        return res.choices[0].message.content
                    else:
                        return res.choices[0].message.content.split('</think>')[-1].strip()
            except Exception as ex:
                print(f' error query llm: {ex}')
                return f"error query llm: {ex}"
        print(f'using llama3 model')
        # query using llama3 model
        #---------------------------

        # # Add current message to conversation history
        # self.conversation_history.append({
        #     "role": "user", 
        #     "content": message
        # })
        # with open('query.txt','a') as f:
        #     f.write(query)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}"
        }
        
        payload = {
            "stream": False,
            "model": "meta-llama/Llama-3.3-70B-Instruct",
            "messages": [{
                "role": "user",
                "content": query
            }],
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(self.api_url, headers=headers, data=json.dumps(payload))
            # response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            # Parse and store the assistant's response
            result = response.json()
            assistant_message = result['choices'][0]['message']['content']
            
            # # Add assistant's response to conversation history
            # self.conversation_history.append({
            #     "role": "assistant", 
            #     "content": assistant_message
            # })
            return assistant_message
        except requests.RequestException as e:
            return f"Error: {str(e)}"

    def split_document(self, document: Dict) -> List[Dict]:
        """Split document into overlapping chunks"""
        
        text = document['text_content']
        chunks = []
        start = 0
        while start < len(document):
            end = start + self.chunk_size
            chunk = {
                'source': document['source'],
                'url': document['url'],
                'text_content': text[start:end],
                'chunk_index': len(chunks)
            }
            chunks.append(chunk)
            start += self.chunk_size - self.overlap
        return chunks

    # def split_document(self, document: Dict) -> List[Dict]:
    #     """
    #     Split a document into chunks of specified size
    #     """
    #     text = document['text_content']
    #     chunks = []
        
    #     # Simple splitting by character count
    #     for i in range(0, len(text), self.chunk_size):
    #         chunk = {
    #             'source': document['source'],
    #             'url': document['url'],
    #             'text_content': text[i:i + self.chunk_size],
    #             'chunk_index': len(chunks)
    #         }
    #         chunks.append(chunk)
            
    #     return chunks

    def save_documents(self, documents: List[Dict]) -> None:
        """
        Split documents into chunks and save to MongoDB
        """
        all_chunks = []
        for doc in documents:
            chunks = self.split_document(doc)
            all_chunks.extend(chunks)
            
        if all_chunks:
            self.mongo.collection.insert_many(all_chunks)

    def search_documents(self, source: str, n: int = 100) -> List[Dict]:
        """
        todo: full text search instead of find
        Search for most relevant documents from a specific source
        """
        cursor = self.mongo.collection.find(
            {'source': source},
            {'text_content': 1, 'url': 1, '_id': 0}
        ).limit(n)
        
        return list(cursor)

    def query_documents(self, query: str, source: str, n_docs: int = 100, bullet_points:bool = False, feed_message_history:bool=False, use_r1=False) -> str:
        """
        Complete pipeline: search documents and query LLM with context
        """
        # Get relevant documents
        relevant_docs = self.search_documents(source, n_docs)
        
        # Prepare context from relevant documents
        context = "\n\n".join([doc['text_content'] for doc in relevant_docs])
        
        if bullet_points:
            prompt = f"""please give very short response (not more than few sentences) You are a research-focused chatbot engaging in a conversation with a human. \n\n Your task is to provide professional and detailed answers to questions based strictly on the given context and messages history related to {source}.\n\n If the context or message history does not contain sufficient information to answer the question, clearly inform the user with very short message. Feel free to use the information user has provided in previous chat for answering new questions. Please answers in short bullet points which we can put in bullet points. Please respond with very short one sentence response if Question is actually suggestion or additional information. \n\nBelow is the context: \n\nContext: \n\n{context} \n\n"""
        else:
            # Prepare prompt with context and query
            prompt = f"""\n You are a research-focused chatbot engaging in a conversation with a human. \n\n Your task is to provide professional and detailed answers to questions based on the given context and messages history related to {source}.\n\n If the context or message history does not contain sufficient information to answer the question, clearly inform the user with very short message. Feel free to use the information user has provided in previous chat for answering new questions.\n\n Below is the context: Please respond with very short one sentence response if Question is actually suggestion or additional information. \n\nContext: \n\n{context} \n\n"""
        
        if feed_message_history:
            
            formatted_messages = ''
            mongo_messages = list(self.mongo.messages_collection.find({'source': source}, {'messages': 1}))
            for messages in mongo_messages:
                for message in messages['messages']:
                    formatted_messages += f'''user: {message['query']} \n assistant: {message['response']} \n\n'''
            prompt += "Message History: \n\n" + formatted_messages

            # print(f'feeding message history for source:\'{source}\': {formatted_messages[:100]}... mongo_msg:{mongo_messages}')
        
        # Add query to the prompt
        prompt += f"Question: {query}"
        
        # Get LLM response
        return self.query_llm(prompt, use_r1=use_r1)

if __name__ == "__main__":
    # Example usage:

    ATOMA_BEARER = os.environ.get("ATOMA_BEARER")
    assert ATOMA_BEARER != None, "atoma api key is none"
    from mongo import Mongo
    mongo = Mongo()

    # Initialize
    qa_system = DocumentQA(
        api_token=ATOMA_BEARER,
        mongo_collection=mongo.collection,
        chunk_size=1000,
        overlap=100
    )

    # Save documents
    documents = [
        {
            "source": "www.ibm.com",
            "url": "https://www.ibm.com/think/topics/machine-learning",
            "text_content": "Machine learning (ML) is a branch of artificial intelligence..."
        }
    ]

    qa_system.query_llm("what is the purpose of life?")

    # qa_system.save_documents(documents)


    # # Query documents
    # response = qa_system.query_documents(
    #     query="What is machine learning?",
    #     source="www.ibm.com",
    #     n_docs=5
    # )
    # print(response)
