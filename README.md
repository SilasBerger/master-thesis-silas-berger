# Master Thesis Silas Berger
This repository contains all code and files related to my master thesis project and report.

## twitter-localizaiton-backend
Code for the backend, containing the data collection mechanism, localization pipeline and REST API, not including any database dumps.

### Usage
To run the backend API, complete the following steps:
1. In `database`, run `docker-compose up -d`
2. In the same directory, run `./restore-mongo.sh`. In the script, specify the file name of the latest MongoDB dump you want to restore (needs to be located in the same directory). 
3. In `src`, run the file `app.py` (note: additional configuration may be required if not running from within PyCharm).
4. In the root of the backend folder, create and activate a new virtual environment, and then run `pip install -r requirements.txt` from the root of the `twitter-localization-backend` directory.

## twitter-localization-frontend
To run the frontend, first start up the backend as decribed above, then run the following steps:
1. In `twitter-localization-frontend`, run `npm install`.
2. In the same directory, run `npm run dev`.

## master-thesis-report
Files related to the written report.
