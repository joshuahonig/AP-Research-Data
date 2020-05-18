import os
import csv
import random
import boto3
import json
from progress.bar import ShadyBar
import sys

allTweets = []
client = boto3.client(
    'comprehend', 
    region_name='us-east-2',
    aws_access_key_id='[REDACTED]',
    aws_secret_access_key='[REDACTED]'
)

for fileInList in os.listdir("../../../twitter"):
    if fileInList[0] == "_":
        with open('../../../twitter/' + fileInList, 'r') as f:
            print("Reading tweets from {0}".format(fileInList))
            data = list(csv.reader(f))
            for tweet in data:
                if tweet[1] == "tweet": pass #this is the first row of each csv file
                allTweets.append(tweet[1])

#shuffle tweets
random.shuffle(allTweets) #shuffle
print("Before removing duplicates:", len(allTweets))

allTweets = allTweets[0:100000]
deduplicatedAllTweets = []
bar = ShadyBar('Deduplicating', max=len(allTweets))
counter = 0
for i in allTweets:
  if i not in deduplicatedAllTweets and i != '':
    deduplicatedAllTweets.append(i)
  counter += 1
  if counter % 1000 == 0:
      bar.next(1000)

allTweets = deduplicatedAllTweets #remove duplicates
print("After removing duplicates:", len(allTweets))

#select the first 50K
#   aws comprehend's API gives the first 50K units free, leave 5000 off for saftey
tweetsToProcess = allTweets[0:45000]

tweetsToProcessAtATime = 25 #how many tweets to process per batch job

#establish a progress bar object
bar = ShadyBar('Processing', max=len(tweetsToProcess))

x = 0
while x < len(tweetsToProcess):
    batchList = tweetsToProcess[x : x+tweetsToProcessAtATime] #grab 25 at a time
    #hit API
    try:
        response = client.batch_detect_sentiment(TextList=batchList, LanguageCode='en')
        #write results
        with open("results.csv", "a") as f:
            #write results one row at a time
            for i in range(0, tweetsToProcessAtATime):
                try:
                    result = response['ResultList'][i]
                    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow([
                        batchList[i],
                        result['Sentiment'], 
                        result['SentimentScore']['Positive'],
                        result['SentimentScore']['Negative'],
                        result['SentimentScore']['Neutral'],
                        result['SentimentScore']['Mixed']
                    ])
                except Exception as e: print(e) #there are less than 25 results; this is fine
    except:
        print('\n', x)
        print(batchList)
        print(len(batchList))
        print(batchList[x])
    
    #increment
    x += tweetsToProcessAtATime
    bar.next(tweetsToProcessAtATime)