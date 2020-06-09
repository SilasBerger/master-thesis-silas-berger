# Twitter Localization Research

# Usage
## Setup and Running
- Set up and activate a VirtualEnv environment, then run `pip install -r requirements.txt`
- Download the required SpaCy modules, each with `python -m spacy download <module name>`
  (e.g. `python -m spacy download de_core_news_sm`). The required module names are:
  - `de_core_news_sm`
  - `fr_core_news_sm`
  - `it_core_news_sm`
  - `en_core_web_sm`
- `cd` into the `database` directory and run `docker-compose up -d`. In case you want to restore data from a snapshot,
  refer to the section _Restoring a MongoDB Snapshot_.
- Add a file `credentials-default.json` to the `configs` directory, and refer to the `Credentials File` section for
  information on how to populate it. Note this file is gitignored in purpose, because it contains confidential
  data.
- From the root of this repository, and after activating the VirtualEnv environment, run `python -m src.playground` to
  run the `src/playground.py` file as an entry point. Note that the MingGW bash for Windows doesn't always display the
  output correctly.

## Configuration
### Restoring a MongoDB Snapshot
To restore the MongoDB database from a Docker volume snapshot (`.tar` file), first copy that snapshot file into the
`database` directory. For the purpose of this guide, we assume that the file is named `mongo-snap.tar`. Once done,
run `docker-compose up -d` to allow MongoDB to build up its initial file structure. Wait a few seconds, then run the
following commands to restore the snapshot and restart the database:

```
$ docker-compose down
$ docker run --rm -v database_mongodb_data:/data/db -v $(pwd):/backup ubuntu bash -c "cd /data/db && tar xvf /backup/mongo-snap.tar --strip 2"
$ docker-compose up -d
```

The database should now be up and running again, and it should be restored to that snapshot.

### Configs File
*Note: Local paths are to be specified relative to the root of this repository, without leading slash.*

A JSON file named `configs_default.json` needs to be placed in the `configs` directory, and needs to provide the following keys:
- `neo4j_host`: Neo4j server URI, in the format `bolt://<IP>:<Port>`
- `mongodb_host`: MongoDB server URI, in the format: `mongodb://<IP>:<Port>`
- `influencers_db`: MongoDB database name of the influencers DB
- `influencers_collection`: name of the influencers collection in the influencers DB
- `influencer_list_url`: base URL where the influencer list JSON documents are provided (generally, GitHub). Documents will be fetched at `influencer_list_url/<someListName>.json`
- `influencer_list_names`: names of the influencer list JSON documents provided at `influencer_list_url` (without `.json` extension)

This file will be committed. Run `src.util.context.load_config()` at the beginning of your script. To use a config file other than `config_default.json`, pass the name of the desired config file. Alternatively, you can pass the absolute path of a config file to this method, together with `use_path=True`. Use `context.get_project_root()` to specify the path.

### Credentials File
A JSON file named `credentials_default.json` needs to be placed in the `configs` directory, and needs to have the
following structure:
```json
{
  "neo4j_user": "neo4j",
  "neo4j_password": "knowledge",
  "twitter_api_key": "<your_twitter_api_key>",
  "twitter_api_key_secret": "<your_twitter_api_key_secret>",
  "twitter_access_token": "<your_twitter_access_token>",
  "twitter_access_token_secret": "<your_twitter_access_token_secret>",
  "geonames_username": "<your_geonames_api_username>"
}
```

This file will not be committed. Run `src.util.context.load_credentials()` at the beginning of your script. To use a
credentials file other than `credentials_default.json`, pass the name of the desired credentials file. Alternatively,
you can pass the absolute path of a credentials file to this method, together with `use_path=True`.  Use
`context.get_project_root()` to specify the path.

# Architecture
## Data
### MongoDB
The `TwitterUsers` database has the following collections:
- `influencers`: a collection of Twitter user names considered to be "Swiss influencers", including their category (politician, musician, etc.). This collection corresponds to the [related lists on GitHub](https://raw.githubusercontent.com/acknowledge/swiss-twitter-accounts/master/).
- `users`: a collection of all Twitter user objects used for any model, regardless of whether they are influencers or regular users

### Neo4j
The Neo4j graph database is used to represent all relevant relationships among Twitter users and other entities which are relevant for the various localization models.

## Source
### src.api
Flask REST API

## src.crawler
- `InfluencerListManager`: Handles synchronization between the influencer lists on GitHub and their representation in MongoDB
- `UserManager.py`: Handles the synchronization of Twitter user objects among the Twitter API, MongoDB, and the graph 

### src.database
- `neo4j_binding`: Wrapper for connection to and transactions with Neo4j graph database

### src.model
- `crawl_status`: contains constants for representing crawling status in influencers collection
- `User`: represents a Twitter user

### src.twitter
- `twitter_api_util`: utility functions for working with the Twitter API (querying rate limits, etc.)
- `TwitterApiBinding`: "Wrapper around the Tweepy binding, facilitates fetching data, iterating through cursors, handling rate limits, etc."

### src.util
Various utility modules for path manipulation, timing, etc. `context` serves as a service locator for objects shared among multiple modules.

### Other
- `app.py`: main entry point for running the application with a REST API (flask)
- `playground.py`: used as an entry point during general development without API

## Other
- `configs`: configuration files, credential files
- `database`: docker-compose file for database containers, scripts for data backup and restore

# Terminology
- `DB`, `database`: refers to any collection in the `TwitterUsers` MongoDB database
- `influencers list(s)`: plain-text lists of Swiss influencers on GitHub 
- `influencers collection`: `influencers` collection 
- `graph`: Neo4j graph database (only one exists)
- `influencer`: either entry in the `influencers` collection, or user marked as `type: influencer` in the graph or the `users` collection
- `user`: Twitter user, depends on context. Either user as taken from Twitter API, user in the DB, or user in the graph