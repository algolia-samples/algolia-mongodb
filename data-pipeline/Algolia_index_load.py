# -*- coding: utf-8 -*-
"""Algolia_MongoDB_index_load.ipynb

Original file is located at
    https://colab.research.google.com/drive/1hO996af5PzI1piGdFlTyr1InhGJmUED0

# Script Overview
This script is used to:
1. Connect to Algolia using the [Algolia Python API](https://www.algolia.com/doc/api-client/getting-started/install/python/?client=python) and validate the connection
2. Connect to a running MongoDB instance and retrieve sample data
3. Prepare the Algolia index
3. Load the dataset into Algolia from the MongoDB instance and replace the existing index

# Prerequisites

Install the Algolia client by running: pip3 install --upgrade "algoliasearch>=2.0,<3.0"
Install the MongoDB client by running: pip3 install 'pymongo[srv]'

## Step 1 - Connect to Algolia
The following steps will contain logic to connect to Algolia using the Python API and validate the connection
#### Prerequisites
If you want to try this yourself, you need to generate an API key that you can use to test:
1. [Register](https://www.algolia.com/users/sign_up) for a free Algolia account, or [Log in](https://www.algolia.com/users/sign_in) to your existing account
2. After signing in, an Algolia Application will automatically be created for you. You can either use the default (unnamed) application, or create a new application
2. Go to your [API Keys](https://www.algolia.com/account/api-keys/all) section of your application and retrieve your **Application ID** and **Admin API Key**
You will need to use both the **Application ID** and **Admin API Key** in when connecting your Algolia account from the Python code below
"""

# Define the Algolia connection parameters. Fill these out with your own AppId & AdminKey retrieved from the Algolia Dashboard.

# The Application ID of your Algolia Application
algolia_app_id = '[your_sample_app_id]'
# The Admin API Key of your Algolia Application
algolia_admin_key = '[your_sample_admin_key'

# Define the Algolia Client and Index that we will use for this test
from algoliasearch.search_client import SearchClient
algolia_client = SearchClient.create(algolia_app_id, algolia_admin_key)
algolia_index = algolia_client.init_index('test_index')

# Test the index that we just created. We do this as part of the function, because these variables are not needed later
def test_algolia_index(index):
    # Clear the index, in case it contains any records
    index.clear_objects()
    # Create a sample record
    record = {"objectID": 1, "name": "test_record"}
    # Save it to the index
    index.save_object(record).wait()
    # Search the index for 'test_record'
    search = index.search('test_record')
    # Clear all items again to clear our test record
    index.clear_objects()
    # Verify that the first hit is our object
    if len(search["hits"]) == 1 and search["hits"][0]["objectID"] == '1':
        print("Algolia index test successful")
    else:
        raise Exception("Algolia test failed")
        
# Call our test function
test_algolia_index(algolia_index)

"""## Step 2 - Connect to the MongoDB instance and retrieve sample data
The following steps will connect to our sample MongoDB database and read the sample data.
The sample data is the official sample AirBnb dataset available for Mongo, as it closely resembles our production data.
#### MongoDB Location
I have created a sample Database on [MongoDB Atlas](https://www.mongodb.com/atlas/database) and loaded it sample data.
You can reach this sample database at:
- **Host**: algolialistingstest.vswcm0y.mongodb.net
- **Username**: ReadOnly
- **Password**: AlgoliaTest
- **Database**: sample_airbnb
- **Collection**: listingsAndReviews

We will only retrieve the first 5000 (out of 5555) records from this collection, to stay within Algolia index limits (Algolia limits the size of the index at 10000, but we will have two collections, as reindexing will duplicate the index and swap them when done)
"""

# Define MongoDB connection parameters. These are wrapped in a function to keep the global namespace clean
# Change these values if you are not running your own MongoDB instance
db_host = 'algolialistingstest.vswcm0y.mongodb.net'
db_name = 'sample_airbnb'
db_user = 'ReadOnly'
db_password = 'AlgoliaTest'
collection_name = 'listingsAndReviews'
        
connection_string = f'mongodb+srv://{db_user}:{db_password}@{db_host}/{db_name}?retryWrites=true&w=majority'
# Pring the connection string
print(connection_string)

# Connect to MongoDB and get the MongoDB Database and Collection instances
from pymongo import MongoClient
# Create MongoDB Client
mongo_client = MongoClient(connection_string)
# Get database instance
mongo_database = mongo_client[db_name]
# Get collection instance
mongo_collection = mongo_database[collection_name]

# Retrieve the first 5000 records from collection items
mongo_query = mongo_collection.find()
initial_items = []
for item in mongo_query:
    if (len(initial_items) < 5000):
        initial_items.append(item)
# Print out the size of our initial items array. It should be 5000 if we read all the values from Mongo correctly
print(len(initial_items))

"""## Step 3 - Prepare the Algolia Index
In this section, we will configure our Algolia index to optimize the search.
We will:
1. Prepare a **function to strip the listing objects** that are coming from MongoDB to only keep attributes that are relevant to Algolia, either for searching, ranking or displaying search results.
2. Prepare the Algolia Index configuration for Searchable attributes and their priorities, custom ranking logic we use to show our results and extra properties to improve search accuracy.

I am using the API documentation of Algolia located [here](https://www.algolia.com/doc/), which contains great resources for simple and advanced use-cases.

#### Step 3.1 - Prepare a function to strip listing objects
The objects in our MongoDB sample dataset contain many attributes, some of which are irrelevant for our Algolia index. We only keep those that are required either for searching or ranking.
- The **_id** property will be kept, as it will be the Algolia object ID as well
- The following properties will be kept either for searching, faceting or displaying: *name*,  *space*, *description*, *neighborhood_overview*, *transit*, *property type*, *address*, *accommodates*, *bedrooms*, *beds*, *number_of_reviews*, *bathrooms*, *price*, *weekly_price*, *security_deposit*, *cleaning_fee*, *images*
- The *review_scores* on the Airbnb property will be transformed to a *scores* property, which will contain the number of stars that is given to the listing
- A *_geoloc* property will be added to the object based on fields in the original *address* object. This will be used for GeoSearching.
- The following properties will be **stripped**: *summary*, *listings_url*, *notes*, *access*, *interaction*, *house_rules*, *room_type*, *bed_type*, *minimum_nights*, *maximum_nights*, *cancellation_policy*, *last_scraped*, *calendar_last_scraped*, *first_review*, *last_review*, *amenities*, *extra_people*, *guests_included*, *host*, *availability*, *review_scores*, *reviews*
"""

# We define a function first that is able to strip long texts longer than 350 characters. This is done because the sample data has some records with very long descriptions, which is irrelevant to our use-case and takes up a lot of space to display
def strip_long_text(obj, trailWithDot):
  if isinstance(obj, str):
    # Strip texts longer than 350 characters after the next full stop (.)
    ret = obj[:350].rsplit('.', 1)[0]
    if trailWithDot and len(ret) > 0 and not ret.endswith('.'):
      ret += '.'
    return ret
  else: 
    return obj
# We define a function to validate number values coming from MongoDB. MongoDB stores numbers in Decimal128 format, which is not accepted by Algolia (only as string). This function:
# 1. Converts numbers to float from Decimal128
# 2. Introduces a maximum value for these numbers, as some values in MongoDB are outliers and incorrectly filled out and it gives range filters an unreal max value.
def validate_number(num, maxValue):
  if num is None:
    return num
  else:
    val = float(str(num))
    if val > maxValue:
      return maxValue
    return val

def prepare_algolia_object(mongo_object):
    # Create an instance of the Algolia object to index, and set its objectID based on the _id of the mongo object
    r = { }
    r['objectID'] = mongo_object["_id"]
    # prepare the string attributes
    for string_property in [['name', True], ['space', True], ['description', True], ['neighborhood_overview', True], ['transit', True], ['address', False], ['property_type', False]]:
        if string_property[0] in mongo_object:
            r[string_property[0]] = strip_long_text(mongo_object[string_property[0]], string_property[1])
    
    # prepare the integer properties
    for num_property in [['accommodates', 100], ['bedrooms', 20], ['beds', 100], ['number_of_reviews', 1000000], ['bathrooms', 100], ['price', 1000], ['weekly_price', 1000], ['security_deposit', 1000], ['cleaning_fee', 1000]]:
        if num_property[0] in mongo_object:
          r[num_property[0]] = validate_number(mongo_object[num_property[0]], num_property[1])
           
    # prepare the Sortable attributes (except for scores rating)
   
    # set rating if any
    if 'review_scores' in mongo_object and 'review_scores_rating' in mongo_object['review_scores']:
        stars = round(mongo_object['review_scores']['review_scores_rating'] / 20, 0)
        r['scores'] = {
            'stars': stars,
            'has_one': stars >= 1,
            'has_two': stars >= 2,
            'has_three': stars >= 3,
            'has_four': stars >= 4,
            'has_five': stars >= 5
        }
    # set images
    if 'images' in mongo_object:
        r['images'] = mongo_object['images']
    # set GeoLocation if any
    if 'address' in mongo_object:
        if 'location' in mongo_object['address']:
            if mongo_object['address']['location']['type'] == 'Point':
                r['_geoloc'] = {
                    'lng': mongo_object['address']['location']['coordinates'][0],
                    'lat': mongo_object['address']['location']['coordinates'][1]
                }
    return r

"""#### Step 3.2 - Prepare Algolia Index properties
This section will prepare the indexing properties in the Algolia index with their priority.

We will use the following [attributes to retrieve](https://www.algolia.com/doc/api-reference/api-parameters/attributesToRetrieve/). These are attributes that will be returned by Algolia for any search result and displayed on our UI or consumed by our backend, but don't play a crucial role in the : *summary*, *description*, *space*, *neighborhood*, *transit*, *address*, *number_of_reviews*, *scores*, *price*, *cleaning_fee*, *property_type*, *accommodates*, *bedrooms*, *beds*, *bathrooms*, *security_deposit*, *images/picture_url*, *_geoloc*

We will use the following [searchable attributes](https://www.algolia.com/doc/api-reference/api-parameters/searchableAttributes/) and priorities:
1. (top priority attributes) *name*, *address/street*, *address/suburb*
2. *address/market*, *address/country*
3. *description* (this will be an [unordered](https://www.algolia.com/doc/api-reference/api-parameters/searchableAttributes/#modifiers) attribute)
4. *space* (this will be an [unordered](https://www.algolia.com/doc/api-reference/api-parameters/searchableAttributes/#modifiers) attribute)
5. *neighborhood_overview* (this will be an [unordered](https://www.algolia.com/doc/api-reference/api-parameters/searchableAttributes/#modifiers) attribute)
5. (least priority) *transit*

We will use the following [attributes for faceting](https://www.algolia.com/doc/api-reference/api-parameters/attributesForFaceting/):
1. *property_type*
2. *address/country*
3. *scores/stars*
4. *price*
5. *cleaning_fee*



We will also update the default [ranking logic](https://www.algolia.com/doc/api-reference/api-parameters/ranking/) for our index:
1. (top priority) *Geo* - providing search results close-by is the top priority for us
2. *Typo*
3. *Words*
4. *Filters*
5. *Proximity*
6. *Attribute*
7. *Exact*
8. *Custom*

We will also update our index to [ignore plurals](https://www.algolia.com/doc/api-reference/api-parameters/ignorePlurals/)

Other great resources and settings can be found on the [Official Algolia API Reference page](https://www.algolia.com/doc/api-reference/api-parameters/)


"""

algolia_index.set_settings({
    'searchableAttributes': [
        'name,address.street,address.suburb',
        'address.market,address.country',
        'unordered(description)',
        'unordered(space)',
        'unordered(neighborhood_overview)',
        'transit'
    ],
    'attributesForFaceting': [
      'property_type',
      'searchable(address.country)',
      'scores.stars',
      'price',
      'cleaning_fee'
    ],
    'attributesToRetrieve': [
      'images.picture_url',
      'summary',
      'description',
      'space',
      'neighborhood',
      'transit',
      'address',
      'number_of_reviews',
      'scores',
      'price',
      'cleaning_fee',
      'property_type',
      'accommodates',
      'bedrooms',
      'beds',
      'bathrooms',
      'security_deposit',
      '_geoloc'
    ],
    'ranking': [
       'geo',
       'typo',
       'words',
       'filters',
       'proximity',
       'attribute',
       'exact',
       'custom'
    ],
    'ignorePlurals': True
})

"""## Step 4 - Load the dataset into Algolia from the MongoDB instance
The following piece of code loads the dataset into the algolia index.
It also replaces the existing index, ensuring that the out-of-date records are replaced.
"""

# Prepare the Algolia objects
algolia_objects = list(map(prepare_algolia_object, initial_items))
algolia_index.replace_all_objects(algolia_objects, {
    'safe': True
}).wait()