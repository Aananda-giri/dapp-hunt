import requests
import json, re
from typing import List, Dict, Optional
from pymongo import MongoClient
from mongo import Mongo

from a16z.brainstorm_prompt import get_brainstorm_prompt
from atoma_sdk import AtomaSDK
from dotenv import load_dotenv
import os
load_dotenv()

assert os.environ.get('ATOMA_BEARER') != None

from openai import OpenAI

class DocumentQA:
    def __init__(self, api_token: str='', mongo='', chunk_size: int = 5000, overlap: int = 100):
        if not api_token:
            api_token = os.environ.get('ATOMA_BEARER')
            assert api_token !=None, "No atoma bearer found in .env"
        
        if not mongo:
            mongo = Mongo()
            
        self.api_token = api_token
        self.mongo = mongo
        
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        assert openai_api_key !=None, "openai api key not found"
        self.openai_client = OpenAI(api_key=openai_api_key)
        
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

    def query_llm(self, query: str, max_tokens: int = 10000, model_name='gpt-4o', include_thinking_text=False) -> str:
        """
        Send a query to the LLM API and return the response

        * model name is one of these values: "o1", "r1", "llama3-70B"
        """
        with open('prompt.txt','a') as f:
            f.write(query)

        # print(f'query: {query}')
        # query using deepseek r1 model
        #---------------------------
        if model_name == 'r1':
            # use deepseek-r1 model
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
                    ], model="deepseek-ai/DeepSeek-R1", frequency_penalty=0, max_tokens=max_tokens, n=1, presence_penalty=0, seed=123, stop=[
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
        elif model_name == 'llama3-70B':
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
        
        elif model_name in ["gpt-4o", "gpt-4o-mini", "o3-mini", "o1"]:
            print(f'one of gpt models. using {model_name} model')

            completion = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            )

            # print(completion.choices[0].message.content)
            return completion.choices[0].message.content
        else:
            print(f'using Default model:gpt-4o model')
            completion = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": query
                    }
                ]
            )
            # print(completion.choices[0].message.content)
            return completion.choices[0].message.content

    def split_document(self, document: Dict) -> List[Dict]:
        """Split document into overlapping chunks"""
        
        text = document['text_content']
        chunks = []
        start = 0
        while start < len(document['text_content']):
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

    def search_documents(self, query:str, source: str, n: int = 10, full_text_search=False) -> List[Dict]:
        """
        * full text search on `text_content` to perform Search for most relevant documents from a specific source
        
        * this is previous version that just finds n documents from given document.
        cursor = self.mongo.collection.find(
                {'source': source},
                {'text_content': 1, 'url': 1, '_id': 0}
            ).limit(n)
        """
        if full_text_search:
            print(f'full text search')
            # consumes more time
            cursor = self.mongo.collection.find(
                {
                    'source': source,
                    '$text': {'$search': query}
                },
                {
                    'text_content': 1, 
                    'url': 1, 
                    '_id': 0,
                    'score': {'$meta': "textScore"}  # This will include the relevance score
                }
            # Sort by relevance
            ).sort([('score', {'$meta': "textScore"})]).limit(n)
        else:
            # consume less time: finds n documents from given document.
            cursor = self.mongo.collection.find(
                    {'source': source},
                    {'text_content': 1, 'url': 1, '_id': 0}
                ).limit(n)
        return list(cursor)

    def query_documents(self, query: str, source: str, n_docs: int = 100, bullet_points:bool = False, feed_message_history:bool=False, summary={}, brainstorm=False, model_name='gpt-4o', full_text_search=False, include_documents=True) -> str:
        """# Added for brainstorming (False by default)
        Complete pipeline: search documents and query LLM with context
        """
        # Get relevant documents
        context = ""
        if include_documents:
            relevant_docs = self.search_documents(query=query, source=source, n=n_docs, full_text_search=full_text_search)
        
            # Prepare context from relevant documents
            context = "\n\n".join([doc['text_content'] for doc in relevant_docs])
        
        if brainstorm:
            # brainstorm prompt for chat interface
            prompt = get_brainstorm_prompt(source, context)
        elif bullet_points:
            # bullet points for lean canvas
            prompt = f"""please give very short response (not more than few sentences) You are a research-focused chatbot engaging in a conversation with a human. \n\n Your task is to provide professional and detailed answers to questions based strictly on the given context and messages history related to {source}.\n\n If the context or message history does not contain sufficient information to answer the question, clearly inform the user with very short message. Feel free to use the information user has provided in previous chat for answering new questions. Please answers in short bullet points which we can put in bullet points. Please respond with very short one sentence response if Question is actually suggestion or additional information. \n\nBelow is the context: \n\nContext: \n\n{context} \n\n"""
        else:
            # Prepare prompt with context and query
            prompt = f"""\n You are a research-focused chatbot engaging in a conversation with a human. \n\n Your task is to provide professional and detailed answers to questions based on the given context and messages history related to {source}.\n\n If the context or message history does not contain sufficient information to answer the question, clearly inform the user with very short message. Feel free to use the information user has provided in previous chat for answering new questions.\n\n Below is the context: Please respond with very short one sentence response if Question is actually suggestion or additional information. \n\nContext: \n\n{context} \n\n"""
        
        if feed_message_history:
            
            formatted_messages = ''
            if brainstorm:
                mongo_messages = list(self.mongo.brainstorm_collection.find({'source': source}, {'messages': 1}))
            else:
                mongo_messages = list(self.mongo.messages_collection.find({'source': source}, {'messages': 1}))
            for messages in mongo_messages:
                for message in messages['messages']:
                    formatted_messages += f'''user: {message['query']} \n assistant: {message['response']} \n\n'''
            prompt += "## previous Messages: \n\n" + formatted_messages

            # print(f'feeding message history for source:\'{source}\': {formatted_messages[:100]}... mongo_msg:{mongo_messages}')
        if summary:
            prompt += "\n\n ## summary:\n Here is the summary you have previously generated: \n\n" 
            summary_str = ''
            for key, value in summary.items():
                summary_str += f'\n### {key}: \n ' + value
            prompt += summary_str
        # Add query to the prompt
        prompt += f"\n\n user: {query}"
        
        # Get LLM response
        return self.query_llm(prompt, model_name=model_name)
    
    def should_we_show_update_lean_canvas_checkbox(self, assistant_message):
        # update checkbox is checkbox right below message with which you can update the lean canvas.
        prompt = f'''
    below is the response generated by a assistant. please respopond with one word yes or no we should show the checkbox to update the data.


    ## Example responses and whether or not to show checkbox


    Assistant-Message: hi, how can i help you today?
    no

    Assistant-Message: should i update your overview?
    yes

    Assistant-Message: Your startup idea addresses a significant problem in today's information-saturated world. To dive deeper, could you clarify if you've identified a particular target market or user base? Additionally, do you see any specific macro trends, such as AI adoption or digital literacy, that align with your solution?
    no
                        
    ## below is current Assistant-message:
    {assistant_message}
    '''
        decision_response = self.query_llm(prompt)
        return "yes" in decision_response.lower()
    def regenerate_lean_canvas_v2(self, model_name, source):
        messages = self.mongo.get_messages(source, model_name)

        prompt = """can you please regenerate lean canvas based on below conversation history.
        please return output in json format.

        # Message history\n
        """

        formatted_messages = ''
        for message in messages:
            formatted_messages += f'''## user: {message['query']} \n## assistant: {message['response']} \n\n'''

        formatted_messages += f'''## user: yes\n\n'''   # user responding yes to Assistants proposal of updaing the lean canvas.
        prompt += formatted_messages



        ## Add lean canvas summary to prompt
        summary = self.mongo.summary_collection.find_one({"source": source})
        summary = summary["summaries"] if summary else {}
        import json
        prompt += f'''## Previous summary
        ```
        {json.dumps(summary)}
        ```
        '''

        prompt += '''
## output
* please generate a new summary in json format and please generating any other text than updated json summary
* Also, lets not assume things, please generate output based on given data (previous lean canvas) or conversations.
### example output1
```
{
    "overall": "AI-powered test case generation platform for software QA and compliance testing automation.",
    "target_users": "* Software development teams needing accelerated QA cycles\n* Enterprises with complex compliance requirements (e.g., finance, healthcare)\n* \n* DevOps teams using CI/CD pipelines\n* QA departments in mid-large tech companies",
    "problems": "* Manual test case creation is time-consuming and error-prone\n* QA bottlenecks delaying software release cycles\n* High costs of compliance testing in regulated industries\n* Difficulty scaling QA processes for agile development",
    "solutions": "Proprietary AI that analyzes code/requirements to auto-generate test cases\n* CI/CD pipeline integration for continuous testing\n* Adaptive compliance testing for software-behavior-based regulations\n* 10x faster test coverage than manual creation",
    "unfair_advantage": "Founding team combines QA domain expertise + AI/ML technical depth\n* Proprietary test generation algorithms (patent-pending?)\n* First-mover advantage in AI-native compliance testing integration\n* Existing integrations with industry-standard CI/CD tools",
    "unique_value_proposition": "Ship faster with AI-generated test suites that keep pace with development\n* Replace 80% of manual test design work with reliable automation\n* Compliance-as-code testing for regulated industries\n* Self-improving test coverage through ML feedback loops",
    "channels": "Enterprise sales to DevOps/QA leadership\n* Partnerships with CI/CD platform providers\n* Developer community adoption through GitHub/GitLab integrations\n* Industry-specific compliance conferences (FINOS, HIMSS)",
    "costs": "AI model training/maintenance infrastructure\n* Cloud compute costs for test generation engine\n* Enterprise sales team compensation\n* Compliance certification maintenance",
    "revenue": "SaaS pricing based on test cases generated/month\n* Enterprise tier with custom compliance modules\n* Revenue share from CI/CD platform marketplace\n* Professional services for implementation/training"
}
```

        '''
        response = self.query_llm(prompt, model_name=model_name)
        # Remove code block markers
        cleaned_text = re.sub(r"^```json\n|\n```$", "", response.strip())

        # Parse as JSON
        summary_json_data = json.loads(cleaned_text)
        
        # update summmary in mongo
        self.mongo.update_summary(source, summary_json_data)

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
