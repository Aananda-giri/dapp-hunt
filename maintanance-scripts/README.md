# 2. Re-crawl all the sources

- why: there was bug in chinking documents resulting in saving only the first chunk. fixed the bug and re-crawling saves all the chunks instead of just first chunk

* code: `./clean_mongo`

* sources = get all unique `source` from `mongo.collection`
  for source in sources:
  get all unique `url` for `source` from collection
  delete all documents with source: `source`

# 1. Clean mongo

- why: before delete function was created, different collection have residual data from deleted source, this script helps clean those residual data.

* code: `./clean_mongo`

* delete all records with sources that are not present in main collection: `mongo.collection`

## available collections:

mongo.collection
mongo.summary_collection
mongo.messages_collection
mongo.brainstrom_collection
