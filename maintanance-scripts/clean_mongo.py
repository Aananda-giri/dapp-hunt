from mongo import Mongo
mongo = Mongo()

# Define collections
main_collection = mongo.collection
summary_collection = mongo.summary_collection
messages_collection = mongo.messages_collection
brainstorm_collection = mongo.brainstrom_collection

# Fetch all unique sources from the main collection
valid_sources = set(doc["source"] for doc in main_collection.find({}, {"source": 1}))

# Function to delete documents with invalid sources
def clean_collection(collection):
    collection.delete_many({"source": {"$nin": list(valid_sources)}})

# Clean up each collection
clean_collection(summary_collection)
clean_collection(messages_collection)
clean_collection(brainstorm_collection)

print("Cleanup completed.")
