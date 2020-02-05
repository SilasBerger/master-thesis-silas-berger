# Master Thesis Silas Berger
This repository contains all code and files related to my master thesis project and report.

## Components
### twitter-localizaiton-backend
Code for the backend, containing the data collection mechanism, localization pipeline and REST API, not including any database dumps.

### twitter-localization-frontend
To run the frontend, first start up the backend as decribed above, then run the following steps:
1. In `twitter-localization-frontend`, run `npm install`.
2. In the same directory, run `npm run dev`.

### master-thesis-report
Files related to the written report.

## Usage
To run the backend API, complete the following steps:
1. In the root of the `twitter-localization-backend` directory, create and activate a new virtual environment, and then run `pip install -r requirements.txt` from the same directory.
2. In `database`, run `docker-compose up -d`
3. In the same directory, run `./restore-mongo.sh`. In the script, specify the file name of the latest MongoDB dump you want to restore (needs to be located in the same directory). 
4. Repeat step 3 with `./restore-neo4j.sh` for the Neo4j dump.
5. Complete the steps outlined in section "Credentials File".
6. In `src`, run the file `app.py` (note: additional configuration may be required if not running from within PyCharm).

Alternatively to step 6, you can run `src/playground.py` to run any other component of the system, such as a model evaluation.

### Credentials File
Create a file `configs/credentials_default.json` with the following contents:

```json
{
  "neo4j_user": "neo4j",
  "neo4j_password": "knowledge",
  "twitter_api_key": "<TWITTER_API_KEY>",
  "twitter_api_key_secret": "<TWITTER_API_SECRET>",
  "twitter_access_token": "<TWITTER_ACCESS_TOKEN>",
  "twitter_access_token_secret": "<TWITTER_ACCESS_SECRET>",
  "geonames_username": "<GEONAMES_API_USERNAME>"
}
```

and fill in the requred credentials for the Twitter and GeoNames API.

