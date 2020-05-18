import csv
import os
import matplotlib
from matplotlib import pyplot
import matplotlib.dates as matplotlib_dates
from datetime import datetime
import sys
import numpy as np
import pickle

savePlots = True

def movingaverage(interval, window_size):
    window= np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')

matplotlib.use('tkagg')

scatterPlotsToGenerate = [
    #sentiment over time
    ["epoch", "posScore", "Positive score over time"],
    ["epoch", "negScore", "Negative score over time"],
    ["epoch", "neutralityIndexScore", "Neutrality index score over time"],

    #interactions and types over time
    ["epoch", "retweets", "Retweets over time"],
    ["epoch", "replies", "Replies over time"],
    ["epoch", "favorites", "Favorites over time"],
    ["epoch", "totalInteractions", "Total interactions over time"],

    #interaction types in relation to positive sentiment
    ["posScore", "retweets", "Retweets in relation to positive score"],
    ["posScore", "replies", "Replies in relation to positive score"],
    ["posScore", "favorites", "Favorites in relation to positive score"],
    ["posScore", "totalInteractions", "Total interactions in relation to positive score"],

    #interaction types in relation to positive sentiment
    ["neutralityIndexScore", "retweets", "Retweets in relation to neutrality index score"],
    ["neutralityIndexScore", "replies", "Replies in relation to neutrality index score"],
    ["neutralityIndexScore", "favorites", "Favorites in relation to neutrality index score"],
    ["neutralityIndexScore", "totalInteractions", "Total interactions in relation to neutrality index score"],

    #interaction types in relation to negative sentiment
    ["negScore", "retweets", "Retweets in relation to negative score"],
    ["negScore", "replies", "Replies in relation to negative score"],
    ["negScore", "favorites", "Favorites in relation to negative score"],
    ["negScore", "totalInteractions", "Total interactions in relation to negative score"],

    #character count
    ["characterCount", "retweets", "Retweets in relation to character count"],
    ["characterCount", "replies", "Replies in relation to character count"],
    ["characterCount", "favorites", "Favorites in relation to character count"],
    ["characterCount", "totalInteractions", "Total interactions in relation to character count"],

    #word count
    ["wordCount", "retweets", "Retweets in relation to word count"],
    ["wordCount", "replies", "Replies in relation to word count"],
    ["wordCount", "favorites", "Favorites in relation to word count"],
    ["wordCount", "totalInteractions", "Total interactions in relation to word count"],
    
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
files = [file for file in os.listdir('~/Desktop/twitter') if ((file[0] == '$') and (file[-4:] == '.csv'))]
data = {}
count = 0
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

    #generate histograms
    for plotType in histogramsToGenerate:
        #get the min and max of this dataset
        xaxMin = min(data[user][plotType[0]])
        xaxMax = max(data[user][plotType[0]])
        #create the graph
        fig, axs = pyplot.subplots()
        pyplot.hist(x=data[user][plotType[0]], bins=200)
        axs.set_xlabel(indicies[plotType[0]])
        axs.set_ylabel('Volume')
        axs.set_title('@{0}\n{1}'.format(user, plotType[1]))
        fig.set_size_inches(15, 10)
        #draw election lines
        if plotType[0] == 'epoch':
            pyplot.gca().xaxis.set_major_formatter(matplotlib_dates.DateFormatter('%m/%Y'))
            pyplot.gca().xaxis.set_major_locator(matplotlib_dates.DayLocator(interval=90))
            pyplot.gcf().autofmt_xdate()
            pyplot.xticks(rotation=55) #dates are long; rotate labels 90 deg
            #plot election cycles
            for cycle in electionCycleEndDates:
                if cycle == 'primaries':
                    for party in electionCycleEndDates[cycle]:    
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
            pyplot.legend(loc="upper left")
        if savePlots:
            if not os.path.exists("./graphs/{0}".format(user)):
                os.mkdir("./graphs/{0}".format(user))
            pyplot.savefig('./graphs/{0}/{1}.png'.format(user, plotType[1]))
            print("Saved {0} {1}".format(user, plotType[1]))
        else:
            pyplot.show()
        pyplot.close() #close when done

    #generate scatter plots
    for plotType in scatterPlotsToGenerate:

        #get the min and max of this dataset
        xaxMin = min(data[user][plotType[0]])
        xaxMax = max(data[user][plotType[0]])

        #scatter plots
        try:
            fig, axs = pyplot.subplots()
            chartTitle = '@{0}\n{1}'.format(user, plotType[2])
            axs.set_title(chartTitle)
            axs.set_xlabel(indicies[plotType[0]])
            axs.set_ylabel(indicies[plotType[1]])
            fig.set_size_inches(15 ,10) #assuming 80dpi
            pyplot.scatter(x=data[user][plotType[0]], y=data[user][plotType[1]], s=5)
            pyplot.grid(True)
            
            #following statements are conditional based upon which axis is which
            #if date
            if plotType[0] == 'epoch':
                pyplot.gca().xaxis.set_major_formatter(matplotlib_dates.DateFormatter('%m/%Y'))
                pyplot.gca().xaxis.set_major_locator(matplotlib_dates.DayLocator(interval=90))
                pyplot.gcf().autofmt_xdate()
                pyplot.xticks(rotation=55) #dates are long; rotate labels 90 deg
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
            if 'score' in str.lower(plotType[1]) or 'index' in str.lower(plotType[1]):
                #draw a line at zero
                pyplot.axhline(y=0, color='r', linestyle='--')
                #calculate the moving average
                y_av = movingaverage(data[user][plotType[1]], 500)
                pyplot.plot(data[user][plotType[0]], y_av, "r", label='Simple Moving Avg (500)')
            if 'score' in str.lower(plotType[0]) or 'index' in str.lower(plotType[0]):
                pyplot.axvline(x=0, color='r', linestyle='--')

            #legend needs to be generated last so that all lines are added
            pyplot.legend(loc="upper left")

            if savePlots:
                if not os.path.exists("./graphs/{0}".format(user)):
                    os.mkdir("./graphs/{0}".format(user))
                pyplot.savefig('./graphs/{0}/{1}.png'.format(user, plotType[2]))
                print("Saved {0} {1}".format(user, plotType[2]))
            else:
                pyplot.show()
            pyplot.close() #close when done
        except KeyboardInterrupt:
            print("Bye")
            sys.exit()
        except:
            pyplot.close()
            print("Error! Skipping...")


    count += 1
    data = [] #reset