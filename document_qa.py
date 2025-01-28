import requests
import json
from typing import List, Dict, Optional
from pymongo import MongoClient

from dotenv import load_dotenv
import os
load_dotenv()



class DocumentQA:
    def __init__(self, api_token: str, mongo_collection, chunk_size: int = 1000, overlap: int = 100):
        self.api_token = api_token
        self.mongo = mongo_collection
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

    def query_llm(self, query: str, max_tokens: int = 128) -> str:
        """
        Send a query to the LLM API and return the response
        """
        # # Add current message to conversation history
        # self.conversation_history.append({
        #     "role": "user", 
        #     "content": message
        # })
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
            self.mongo.insert_many(all_chunks)

    def search_documents(self, source: str, n: int = 100) -> List[Dict]:
        """
        todo: full text search instead of find
        Search for most relevant documents from a specific source
        """
        cursor = self.mongo.find(
            {'source': source},
            {'text_content': 1, 'url': 1, '_id': 0}
        ).limit(n)
        
        return list(cursor)

    def query_documents(self, query: str, source: str, n_docs: int = 100) -> str:
        """
        Complete pipeline: search documents and query LLM with context
        """
        # Get relevant documents
        relevant_docs = self.search_documents(source, n_docs)
        
        # Prepare context from relevant documents
        context = "\n\n".join([doc['text_content'] for doc in relevant_docs])
        
        # Prepare prompt with context and query
        prompt = f"""
        
        You are a research-focused chatbot engaging in a conversation with a human.

Your task is to provide professional and detailed answers to questions based strictly on the given context related to {source}.

If the context does not contain sufficient information to answer the question, clearly inform the user with very short message.

Below is the context:

Context:
{context}

Question: {query}"""
        
        # Get LLM response
        return self.query_llm(prompt)


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
