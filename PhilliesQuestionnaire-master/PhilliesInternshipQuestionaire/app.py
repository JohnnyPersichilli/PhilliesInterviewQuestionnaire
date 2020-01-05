from flask import Flask, render_template
import pandas as pd
import numpy as np
import constants
from scipy import stats
from bs4 import BeautifulSoup
import requests
import pandas as pd
from scipy import stats
import statsapi
from sklearn import linear_model
import webbrowser

app = Flask(__name__, static_url_path='/static/')

playerData = []

closePlayerHittingStats = []
closePlayerPitchingStats = []

#adds the pitching stats to closePlayerPitchingStats for pitchers with close salaries to the qualifying offer
def parseHittingStats(statList, nameToSearch, position, salary):
    try:
        stats = statList['stats'][0]['stats']

        tempHittingStat = {
            'name': nameToSearch,
            'team': statList['current_team'],
            'salary': salary,
            'position': position,
            'HR': stats['homeRuns'],
            'RBI': stats['rbi'],
            'AVG': stats['avg'],
            'atBats': stats['atBats'],
        }
        closePlayerHittingStats.append(tempHittingStat)
    except:
        print("No hitting stats for "+nameToSearch+" in this api because data is from this year not 2016")

#adds the pitching stats to closePlayerPitchingStats for pitchers with close salaries to the qualifying offer
def parsePitchingStats(statList, nameToSearch, salary):
    try:
        stats = statList['stats'][0]['stats']

        tempPitchingStat = {
            'name': nameToSearch,
            'team': statList['current_team'],
            'salary': salary,
            'position': "P",
            'era': stats['era'],
            'wins': stats['wins'],
            'losses': stats['losses'],
            'whip': stats['whip'],
        }
        closePlayerPitchingStats.append(tempPitchingStat)
    except:
        print("No pitching stats for "+nameToSearch+" in this api because data is from this year not 2016")

#gets the salary for a given row
def getSalary(tdList):
    #set default salary value and later adjust it if valid 
    salary = constants.DEFAULT_SALARY

    #if the salary collumn isnt null
    if tdList[1].text:
        try:
            #strip the dollar sign commas and any spaces and then convert it to an int
            #used both split and replace to show more string manipulation functions
            salary = int(tdList[1].text.strip('$ ').replace(',',"") )
        except:
            print("Non numeric salary value")
    return salary

#responsible for parsing the scraped row for each player
def parsePlayerRow(row):
    tdList = row.findAll('td')

    #could use the class names to ensure grabbing the right data but for simple files such as this one this will suffice
    playerName = tdList[0].text

    salary = getSalary(tdList)

    year = int(tdList[2].text)
    level = tdList[3].text

    tempPlayer = {
        'name': playerName,
        'salary': salary,
        'year': year,
        'level': level,
    }
    playerData.append(tempPlayer)

#finds the players with the closest salary to the qualifying offer
def getStatsForClosestSal(tenClosestSalaries):
    for index, row  in tenClosestSalaries.iterrows():
        #parse the given name into first and last to be used for searching the api and opening mlb.com
        salary = row['salary']
        playerNameStr = row['name']
        nameList = playerNameStr.split(',')
        lname = nameList[0]
        fname = nameList[1].strip(' ')
        nameToSearch = fname+" "+lname

        #use mlb stats api to retrieve player id to open mlb.com and (if more time scrap mlb.com to get more player info)
        lookup_player = statsapi.lookup_player(nameToSearch, season=2016, sportId=1)
        #ensures there is at least one result
        if len(lookup_player) > 0:
            #take the first entry or the closest name to the one entered
            lookup_player = lookup_player[0]
            playerID = lookup_player['id']
            position = lookup_player['primaryPosition']['abbreviation']

            if position=='P':
                statList =  statsapi.player_stat_data(playerID, group='[pitching]', type='season')
                parsePitchingStats(statList, nameToSearch, salary)
            else:
                statList =  statsapi.player_stat_data(playerID, group='[hitting]', type='season')
                parseHittingStats(statList, nameToSearch, position, salary)

def getPredictedPitchingStats(qualifyingOffer):
    predictedPitchingData = {}
    closePlayerPitchingStatsDf = pd.DataFrame(closePlayerPitchingStats)

    #predict era
    eraReg = linear_model.LinearRegression().fit(closePlayerPitchingStatsDf[['salary']], closePlayerPitchingStatsDf['era'])
    qualifyingOfferArr = np.array([qualifyingOffer]).reshape(1, -1)
    predictedPitchingData['era'] = round(float(eraReg.predict(qualifyingOfferArr)[0]),2)

    #predict wins
    winReg = linear_model.LinearRegression().fit(closePlayerPitchingStatsDf[['salary']], closePlayerPitchingStatsDf['wins'])
    qualifyingOfferArr = np.array([qualifyingOffer]).reshape(1, -1)
    predictedPitchingData['wins'] = int(winReg.predict(qualifyingOfferArr)[0])

    #predict losses
    lossReg = linear_model.LinearRegression().fit(closePlayerPitchingStatsDf[['salary']], closePlayerPitchingStatsDf['losses'])
    qualifyingOfferArr = np.array([qualifyingOffer]).reshape(1, -1)
    predictedPitchingData['losses'] = round(float(lossReg.predict(qualifyingOfferArr)[0]),2)

    #predict whip
    whipReg = linear_model.LinearRegression().fit(closePlayerPitchingStatsDf[['salary']], closePlayerPitchingStatsDf['whip'])
    qualifyingOfferArr = np.array([qualifyingOffer]).reshape(1, -1)
    predictedPitchingData['whip'] = round(float(whipReg.predict(qualifyingOfferArr)[0]),2)

    return predictedPitchingData

def getPredictedHittingStats(qualifyingOffer):
    predictedHittingData = {}
    closePlayerHittingStatsDf = pd.DataFrame(closePlayerHittingStats)

    #predict HR
    homerunReg = linear_model.LinearRegression().fit(closePlayerHittingStatsDf[['salary']], closePlayerHittingStatsDf['HR'])
    qualifyingOfferArr = np.array([qualifyingOffer]).reshape(1, -1)
    predictedHittingData['HR'] = int(homerunReg.predict(qualifyingOfferArr)[0])

    #predict wins
    rbiReg = linear_model.LinearRegression().fit(closePlayerHittingStatsDf[['salary']], closePlayerHittingStatsDf['RBI'])
    qualifyingOfferArr = np.array([qualifyingOffer]).reshape(1, -1)
    predictedHittingData['RBI'] = int(rbiReg.predict(qualifyingOfferArr)[0])

    #predict avg
    avgReg = linear_model.LinearRegression().fit(closePlayerHittingStatsDf[['salary']], closePlayerHittingStatsDf['AVG'])
    qualifyingOfferArr = np.array([qualifyingOffer]).reshape(1, -1)
    predictedHittingData['AVG'] = round(float(avgReg.predict(qualifyingOfferArr)[0]),3)

    #predict AB
    abReg = linear_model.LinearRegression().fit(closePlayerHittingStatsDf[['salary']], closePlayerHittingStatsDf['atBats'])
    qualifyingOfferArr = np.array([qualifyingOffer]).reshape(1, -1)
    predictedHittingData['atBats'] = int(abReg.predict(qualifyingOfferArr)[0])

    return predictedHittingData

def getPredictedStatsForSalary(qualifyingOffer):
    predictedPitchingData = getPredictedPitchingStats(qualifyingOffer)
    predictedHittingData = getPredictedHittingStats(qualifyingOffer)
    return predictedPitchingData, predictedHittingData


#code for main index route
@app.route('/')
def index():
    #if player data is empty then scrape the data
    if not playerData:
        salaryURL = "https://questionnaire-148920.appspot.com/swe/data.html"

        salaryRes = requests.get(salaryURL, timeout=10)

        contents = BeautifulSoup(salaryRes.content, "html.parser")
        tableData = contents.find('table')

        #parse the player data for each row
        for row in tableData.findAll('tr'):
            parsePlayerRow(row)

    #make a pandas df with scraped player data
    tableColumns = ['name','salary','year','level']
    playerDf = pd.DataFrame(playerData, columns=tableColumns)
    length = len(playerDf)

    #create a sorted df by salary
    salarySortedDf = playerDf.sort_values(by='salary', ascending=False)

    #can also use the .head(125) to get the top 125 salarys values
    qualifyingOffer = round(salarySortedDf[:125]['salary'].mean(),2)

    #finds 10 closest salaries to the qualifying offer for comparison
    playerDf['diffToQualifing'] = abs(playerDf['salary'] - qualifyingOffer)
    tenClosestSalaries = playerDf.sort_values(by='diffToQualifing').head(15)
    print(tenClosestSalaries)

    #uses the scipy module to calculate the percentile of the salary
    qualOfferPercentile = round(stats.percentileofscore(playerDf['salary'], qualifyingOffer),2)

    getStatsForClosestSal(tenClosestSalaries)

    predictedPitchingData, predictedHittingData = getPredictedStatsForSalary(qualifyingOffer)

    #render the main.html page with the given variables
    return render_template("main.html", qualifyingOffer= qualifyingOffer, salarySortedDf= salarySortedDf, qualOfferPercentile= qualOfferPercentile, length=length, closePlayerHittingStats=closePlayerHittingStats, closePlayerPitchingStats=closePlayerPitchingStats, predictedPitchingData=predictedPitchingData, predictedHittingData=predictedHittingData)

#code for aboutme page
@app.route('/aboutme')
def aboutme():
    return render_template("aboutme.html")

#code for clicking on a given player
#should eventually be its own page with more info but right now it just opens mlb.coms info page
@app.route('/player/<playerNameStr>')
def playerInfo(playerNameStr):
    baseMlbUrl = "https://www.mlb.com/player/"

    #parse the given name into first and last to be used for searching the api and opening mlb.com
    #if it has a comma it comes from the first table and if not it comes from the second table
    if ',' in playerNameStr:
        nameList = playerNameStr.split(',')
        lname = nameList[0]
        fname = nameList[1].strip(' ')
        nameToSearch = fname+" "+lname
    else:
        nameList = playerNameStr.split(' ')
        lname = nameList[1]
        fname = nameList[0]
        nameToSearch = fname+" "+lname

    #use mlb stats api to retrieve player id to open mlb.com and (if more time scrap mlb.com to get more player info)
    lookup_player = statsapi.lookup_player(nameToSearch, season=2016, sportId=1)
    #ensures there is at least one result
    if len(lookup_player) > 0:
        #take the first entry or the closest name to the one entered
        lookup_player = lookup_player[0]
        playerID = lookup_player['id']
        stats =  statsapi.player_stats(playerID, group='[hitting]', type='season')
        #can also use "-".join() to make concattanted player url
        playerURL = baseMlbUrl + fname.lower() +"-"+lname.lower()+"-"+str(playerID)
        #open mlb.com stat page of the player
        webbrowser.open(playerURL, new=0)
    #returning the about me page just because it is unclear how else to get there and wanted to showcase it
    return index()

if __name__ == "__main__":
    app.run(debug=True)