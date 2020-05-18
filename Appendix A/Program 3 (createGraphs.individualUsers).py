import csv
import os
import matplotlib
from matplotlib import pyplot
import matplotlib.dates as matplotlib_dates
from datetime import datetime
import sys
import numpy as np
import pickle
import randomcolor
import traceback

savePlots = True

def movingaverage(interval, window_size):
    window= np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')

matplotlib.use('tkagg')

scatterPlotsToGenerate = [
    #sentiment over time
    ["epoch", "posScore", "Positive score over time"],
    ["epoch", "negScore", "Negative score over time"],
    ["epoch", "neutralityIndexScore", "Neutrality index score over time"]
    
]

histogramsToGenerate = [
    ["epoch", "Tweet volume"],
    ["characterCount", "Character count volume"],
    ["wordCount", "Word count volume"]
]

#used to convert dict indicies to human readable form
indicies = {
    "epoch": "Date",
    "tweet": "Tweet",
    "replies": "Replies",
    "retweets": "Retweets",
    "favorites": "Favorites",
    "totalInteractions": "Total Interactions",
    "posScore": "Positive Score",
    "negScore": "Negative Score",
    "neutralityIndexScore": "Neutrality Index Score",
    "verdict": "Verdict",
    "wordCount": "Word Count",
    "characterCount": "Character Count"
}

groups = {
    "birthYear": {
        "1930-1940": [],
        "1940-1950": [],
        "1950-1960": [],
        "1960-1970": [],
        "1970-1980": []
    },
    "party": {
        "Democrat": [],
        "Republican": [],
        "Independent": [],
        "Green": [],
        "Libertarian": []
    },
    "gender": {
        "Male": [],
        "Female": []
    }
}

#load the demographic data for each candidate
demographics = {}
with open('demographicData.csv') as f:
    reader = csv.reader(f)
    for row in reader:
        temp = {
            str.lower(row[0]): {
                "party": row[1],
                "gender": row[3],
                "birthYear": row[4],
                "name": row[5]
            }
        }
        demographics.update(temp)

def getTime(timestr, fmt='%b %d %Y'):
    return(datetime.strptime(timestr, fmt))
electionCycleEndDates = {
    "primaries": {
        "republican": [
            getTime('Mar 4 2008'), #this is the day that McCain secured the nomination; some state elections happened before or after this date (super Tuesday)
            getTime('May 29 2012'), #see above (Romney); this was not a super tuesday
            getTime('May 26 2016') #see above (Trump)
        ],
        "democrat": [
            getTime('Jun 3 2008'), #see above comments for republican primaries
            getTime('Jul 26 2016') #see above
        ]
    },
    "general": [
        getTime('Nov 4 2008'),
        getTime('Nov 6 2012'),
        getTime('Nov 8 2016')
    ]
}

#create a list of the CSVs we want
files = [file for file in os.listdir('.') if ((file[0] == '$') and (file[-4:] == '.csv'))]
allUsersData = []
for file in files:
    data = {
        file[1:-12]: {
                        "epoch": [],
                        "tweet": [],
                        "replies": [],
                        "retweets": [],
                        "favorites": [],
                        "totalInteractions": [],
                        "posScore": [],
                        "negScore": [],
                        "neutralityIndexScore": [],
                        "verdict": [],
                        "wordCount": [],
                        "characterCount": []
                    }
    }
    user = file[1:-12] #for more readable code
    print('Processing', user)
    with open(file) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] != 'user' and row[1] != 'epoch': #make sure this row isn't the header row
                data[user]['epoch'].append( datetime.fromtimestamp(int(row[1])) )
                data[user]['tweet'].append((row[2]))
                data[user]['replies'].append((int(row[3])))
                data[user]['retweets'].append((int(row[4])))
                data[user]['favorites'].append((int(row[5])))
                data[user]['totalInteractions'].append((int(row[6])))
                data[user]['posScore'].append((float(row[7])))
                data[user]['negScore'].append((float(row[8])))
                data[user]['neutralityIndexScore'].append(( float(row[7]) + float(row[8]) ))
                data[user]['verdict'].append((row[9]))
                data[user]['wordCount'].append((len(str.split(row[2]))))
                data[user]['characterCount'].append((len(row[2])))

        #this line is gross, but it sorts the data: https://stackoverflow.com/a/9764364/11467212
        data[user]['epoch'], data[user]['tweet'], data[user]['replies'], data[user]['retweets'], data[user]['favorites'], data[user]['totalInteractions'], data[user]['posScore'], data[user]['negScore'], data[user]['neutralityIndexScore'], data[user]['verdict'], data[user]['wordCount'], data[user]['characterCount'] = zip(*sorted(zip(
            data[user]['epoch'], 
            data[user]['tweet'], 
            data[user]['replies'], 
            data[user]['retweets'], 
            data[user]['favorites'], 
            data[user]['totalInteractions'], 
            data[user]['posScore'], 
            data[user]['negScore'], 
            data[user]['neutralityIndexScore'], 
            data[user]['verdict'], 
            data[user]['wordCount'], 
            data[user]['characterCount']
            )))
    allUsersData.append(data)
    #look up demographic information and add to groups array
    #birth year
    try:
        party = demographics[str.lower(user)]['party']
        gender = demographics[str.lower(user)]['gender']

        #need to find the range that the age is in
        birthYr = demographics[str.lower(user)]['birthYear']
        for yrRange in groups['birthYear']:
            lower = int(yrRange.split('-')[0])
            upper = int(yrRange.split('-')[1])
            if lower < int(birthYr) <= upper:
                groups['birthYear'][yrRange].append(user)
        groups['party'][party].append(user)
        groups['gender'][gender].append(user)
    except KeyError:
        print("Index error on demographics for", user, ", skipping...")

for groupType in groups:
    for cohort in groups[groupType]:

        #generate scatter plots
        for plotType in scatterPlotsToGenerate:
            userlist = groups[groupType][cohort]
            usercolors = {}
            for user in userlist:
                randColor = randomcolor.RandomColor(seed=user)
                usercolors.update({user: randColor.generate()})
            #find largest and smallest epoch values in all of the datasets
            smallestEpoch = None
            largestEpoch = None
            for index in allUsersData:
                for user in index:
                    if user in userlist:
                        xAxMinOfThisDataset = min(index[user][plotType[0]])
                        xAxMaxOfThisDataset = max(index[user][plotType[0]])
                        if smallestEpoch is None: #if it hasn't been set yet
                            smallestEpoch = xAxMinOfThisDataset
                        elif xAxMinOfThisDataset < smallestEpoch:
                            smallestEpoch = xAxMinOfThisDataset
                        if largestEpoch is None: #if it hasn't been set yet
                            largestEpoch = xAxMaxOfThisDataset
                        elif xAxMaxOfThisDataset > largestEpoch:
                            largestEpoch = xAxMaxOfThisDataset
            xaxMin = smallestEpoch
            xaxMax = largestEpoch

            try:
                fig, axs = pyplot.subplots()
                axs.set_title('{0}, {1}\n{2}'.format(groupType, cohort, plotType[1]))
                axs.set_xlabel(indicies[plotType[0]])
                axs.set_ylabel(indicies[plotType[1]])
                fig.set_size_inches(15 ,10) #assuming 80dpi
                for index in allUsersData:
                    for user in index:
                        if user in userlist:
                            #pyplot.scatter(x=index[user][plotType[0]], y=index[user][plotType[1]], s=5, c=usercolors[user][0] + '19') #+19 adds 25% opacity
                            pass #do not plot dots; too noisy
                pyplot.grid(True)
                pyplot.xticks(rotation=55) #dates are long; rotate labels 90 deg
                #following statements are conditional based upon which axis is which
                #if date
                if plotType[0] == 'epoch':
                    pyplot.gca().xaxis.set_major_formatter(matplotlib_dates.DateFormatter('%m/%Y'))
                    pyplot.gca().xaxis.set_major_locator(matplotlib_dates.DayLocator(interval=90))
                    pyplot.gcf().autofmt_xdate()
                    #plot the general election dates
                    for cycle in electionCycleEndDates:
                        if cycle == 'primaries':
                            for party in electionCycleEndDates[cycle]:    
                                #pyplot.axvline(x=party, color='g', linestyle='-.', linewidth=3.0, label='General election' if drawnLineCount == 0 else "")
                                lineColor = ''
                                label = ''
                                if party == 'democrat':
                                    lineColor = 'b' #blue
                                    label = 'Democratic primaries'
                                elif party == 'republican':
                                    lineColor = 'r' #red
                                    label = 'Republican primaries'
                                drawnLineCount = 0
                                for primary in electionCycleEndDates[cycle][party]:
                                    if xaxMin < primary < xaxMax: #only draw line if there's data during this time period
                                        pyplot.axvline(x=primary, color=lineColor, linestyle='-.', linewidth=3.0, label=label if drawnLineCount == 0 else "")
                                        drawnLineCount += 1
                        else:
                            drawnLineCount = 0
                            for general in electionCycleEndDates[cycle]:
                                # < if drawnLineCount == 0 else "" > only adds the label for one of the lines, otherwise the legend will have duplicate values
                                if xaxMin < general < xaxMax:
                                    pyplot.axvline(x=general, color='g', linestyle='-.', linewidth=3.0, label='General election' if drawnLineCount == 0 else "")
                                    drawnLineCount += 1
                #draw horizontal line @ 0
                drawMovingAverageFor = ['posScore', 'negScore', 'neutralityIndexScore']
                if plotType[1] in drawMovingAverageFor:
                    #draw a line at zero
                    pyplot.axhline(y=0, color='r', linestyle='--')
                    #calculate the moving average
                    for index in allUsersData:
                        for user in index:
                            if user in userlist:
                                try:
                                    y_av = movingaverage(index[user][plotType[1]], 500)
                                    pyplot.plot(index[user][plotType[0]], y_av, color=usercolors[user][0],  label='Simple Moving Avg (500) for ' + user, linestyle="-.")
                                except ValueError:
                                    print(user, "doesn't have enough data points to generate a moving average; skipping...")
                if 'score' in str.lower(plotType[0]) or 'index' in str.lower(plotType[0]):
                    pyplot.axvline(x=0, color='r', linestyle='--')

                #legend needs to be generated last so that all lines are added
                pyplot.legend(loc="upper left")

                if savePlots:
                    folderName = "{0} {1}".format(groupType, cohort)
                    if not os.path.exists("./graphs/{0}".format(folderName)):
                        os.mkdir("./graphs/{0}".format(folderName))
                    pyplot.savefig('./graphs/{0}/{1}.png'.format(folderName, plotType[2]))
                    print("Saved {0} {1}".format(folderName, plotType[2]))
                else:
                    pyplot.show()
                pyplot.close() #close when done
            except KeyboardInterrupt:
                print("Bye")
                sys.exit()
            except:
                print(traceback.format_exc())
                pyplot.close()
                print("Error! Skipping...")
