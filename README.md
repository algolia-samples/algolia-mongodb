# Algolia MongoDB Listings Application

This repository contains the local files for the sample Algolia MongoDB Listings Application that is implemented as part of a blogpost series located [here]().

## Features

- A Python script to load an Algolia index with sample data from MongoDB. It is available both as a [Jupyter Notebook](data-pipeline/Algolia_index_load.ipynb) and a [Python script](data-pipeline/Algolia_index_load.py)
- A [Web application](search-web-application/) to query the Algolia index directly and display search results

## Algolia Index loading

To try the loading of the Algolia index based on the sample dataset, you need an Algolia API key, which you can obtain by:
1. [Registering](https://www.algolia.com/users/sign_up) for a free Algolia account, or [Logging in](https://www.algolia.com/users/sign_in) to your existing account
2. After signing in, an Algolia Application will automatically be created for you. You can either use the default (unnamed) application, or create a new application
2. Go to your [API Keys](https://www.algolia.com/account/api-keys/all) section of your application and retrieve your **Application ID** and **Admin API Key**
You will need to use both the **Application ID** and **Admin API Key** in when connecting your Algolia account from the Python code below

Open either the:
- publicly hosted Notebook on [Google collab](https://colab.research.google.com/drive/1hO996af5PzI1piGdFlTyr1InhGJmUED0)
- local [Jupyter Notebook](data-pipeline/Algolia_index_load.ipynb)
- local [Python script](data-pipeline/Algolia_index_load.py)
They are all responsible for loading the Algolia index. Change the **algolia_app_id** and the **algolia_admin_key** variables to your API keys and run the script.

The script will: 
1. Connect to Algolia using the [Algolia Python API](https://www.algolia.com/doc/api-client/getting-started/install/python/?client=python) and validate the connection
2. Connect to a running MongoDB instance and retrieve sample data
3. Prepare the Algolia index
3. Load the dataset into Algolia from the MongoDB instance and replace the existing index

## Testing the demo application

You can also easily try out the Search Web Application by either:
- opening the [StackBlitz](https://stackblitz.com/github/algolia-samples/algolia-mongodb/tree/main/search-web-application?file=src%2Falgolia.js) hosted version of the application on the cloud. This contains both the source and the created application and allows you to make modifications and see the changes real-time.
- opening the [local](search-web-application/) files for the web application. You will need to have [NodeJS](https://nodejs.org/en/download/) on your machine and run **npm install** and **npm start** from the *search-web-application* directory to run the app.


