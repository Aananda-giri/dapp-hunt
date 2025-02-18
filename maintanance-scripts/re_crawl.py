from mongo import Mongo
from document_qa import DocumentQA
import aiohttp
from bs4 import BeautifulSoup
from youtube_functions import get_subtitle, is_youtube_url

import asyncio

mongo = Mongo()
qa_system = DocumentQA()

main_collection = mongo.collection

# Fetch all unique sources from the main collection
sources = set(doc["source"] for doc in main_collection.find({}, {"source": 1}))


async def crawl_text_content(url: str) -> str:
    """Async function to crawl text content from URL"""
    if is_youtube_url(url):
        return get_subtitle(url)

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            html_content = await response.text()
            # Parse the HTML content with BeautifulSoup
            soup = BeautifulSoup(html_content, "html.parser")
            # Extract and return the text content
            return soup.get_text(strip=True)


# Iterate through sources and delete documents
for source in sources:
    print(f'source: {source}')
    urls = set(doc["url"] for doc in main_collection.find({'source':source}, {"url": 1}))
    print(f"urls: {urls}")
    # re-crawl the data
    documents = []
    for url in urls:
        text_content = asyncio.run(crawl_text_content(url))
        documents.append({
            "source": source,
            "url": url,
            "text_content": text_content
        })
    # break
    print(f"obtained {len(documents)} documents")
    
    # Delete previously crawled data
    main_collection.delete_many({"source": source})
    
    # Save documents
    qa_system.save_documents(documents)
    
    print(f're-crawled: {source}')

print("re-crawl completed.")