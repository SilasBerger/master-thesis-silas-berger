# Twitter Localization Research

# Usage
- set up and activate a VirtualEnv environment, run `pip install -r requirements.txt`
- start DBs (Docker compose, TBA)
- add a credentials file (see below)

## Configuration

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
A JSON file named `credentials_default.json` needs to be placed in the `configs` directory, and needs to provide the following keys:
- `neo4j_user`: username for the Neo4j database
- `neo4j_password`: password for this Neo4j user

This file will not be committed. Run `src.util.context.load_credentials()` at the beginning of your script. To use a credentials file other than `credentials_default.json`, pass the name of the desired credentials file. Alternatively, you can pass the absolute path of a credentials file to this method, together with `use_path=True`.  Use `context.get_project_root()` to specify the path.

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