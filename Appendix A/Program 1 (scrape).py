from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from time import sleep
import json
import datetime
from urllib.parse import quote
import re
import threading
import os
import multiprocessing
import queue

#get users
with open('users.txt', 'r') as f:
    users = f.readlines()
users = [x.strip() for x in users] #remove \n
users = list(set(users)) #remove duplicates

def format_day(date):
    day = '0' + str(date.day) if len(str(date.day)) == 1 else str(date.day)
    month = '0' + str(date.month) if len(str(date.month)) == 1 else str(date.month)
    year = str(date.year)
    return '-'.join([year, month, day])
    
delay = 1  # time to wait on each page load before reading the page
daysToSearchAtATime= 30

def doBrowse(user):
    if os.path.exists("_{0}.csv".format(user)):
        print("Already done {0}, skipping...".format(user))
        return #already done
    #get the time range, starting when the user created their account and ending now
    url = "https://twitter.com/" + user
    driver = webdriver.Chrome()
    driver.set_window_size(682, 512)
    driver.get(url)
    start = datetime.datetime.strptime('March 01 2006', '%B %d %Y')
    end = datetime.datetime.now()

    days = int(((end - start).days)/daysToSearchAtATime + 1)
    tweets = []

    for day in range(days):
        rangeStart = format_day(start + datetime.timedelta(days=0))
        rangeEnd = format_day(start + datetime.timedelta(days=daysToSearchAtATime))
        url = 'https://twitter.com/search?f=tweets&vertical=default&q=' + quote('from:{0} since:{1} until:{2}'.format(user, rangeStart, rangeEnd)) + '&src=typd'
        driver.get(url)
        sleep(delay)

        try:
            found_tweets = driver.find_elements_by_css_selector('li.js-stream-item')
            increment = 10

            while len(found_tweets) >= increment:
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                sleep(delay)
                found_tweets = driver.find_elements_by_css_selector('li.js-stream-item')
                increment += 10
            for tweet in found_tweets:
                try:
                    tweetText = tweet.find_element_by_css_selector('.js-tweet-text-container p.js-tweet-text').text
                    tweetDate = tweet.find_element_by_css_selector('.time a.tweet-timestamp span.js-short-timestamp').get_attribute('data-time')
                    tweetReplies = tweet.find_element_by_css_selector('.stream-item-footer .ProfileTweet-actionList .ProfileTweet-action--reply button.js-actionReply span.ProfileTweet-actionCount span.ProfileTweet-actionCountForPresentation').text
                    tweetRetweets = tweet.find_element_by_css_selector('.stream-item-footer .ProfileTweet-actionList .ProfileTweet-action--retweet button.js-actionRetweet span.ProfileTweet-actionCount span.ProfileTweet-actionCountForPresentation').text
                    tweetFavorites = tweet.find_element_by_css_selector('.stream-item-footer .ProfileTweet-actionList .ProfileTweet-action--favorite button.js-actionFavorite span.ProfileTweet-actionCount span.ProfileTweet-actionCountForPresentation').text
                    print('' + tweetText)
                    print('epoch: ' + tweetDate)
                    print('replies: ' + tweetReplies)
                    print('retweets: ' + tweetRetweets)
                    print('favorites: ' + tweetFavorites)
                    print('====================================')
                    tweets.append({
                        'time': int(tweetDate),
                        'message': tweetText,
                        'interactions': {
                            'replies': tweetReplies,
                            'retweets': tweetRetweets,
                            'favorites': tweetFavorites
                        }
                    })
                except StaleElementReferenceException as e:
                    print('lost element reference', tweet)

        except NoSuchElementException as e:
            print('NoSuchElementException- probably no tweets on this day')
        start = start + datetime.timedelta(days=daysToSearchAtATime)
    #write csv file
    with open('_{0}.csv'.format(user), 'w') as f:
        f.write('epoch,tweet,replies,retweets,favorites\n')
        for line in tweets:
            f.write('{0},"{1}",{2},{3},{4}\n'.format(line['time'], line['message'].replace('\n', ' ').replace('"', '""'), line['interactions']['replies'], line['interactions']['retweets'], line['interactions']['favorites']))
    driver.close()

if __name__ == "__main__":
    pool = multiprocessing.Pool(processes=4)
    for user in users:
        pool.apply_async(doBrowse, args=(user,))
    pool.close()
    pool.join()
