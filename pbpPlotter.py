import plotly.subplots
import requests
import pandas as pd
# import json
import streamlit as st
import datetime as datetime
from datetime import timedelta
import numpy as np
# import stumpy
import matplotlib.pyplot as plt
# from multiprocessing.pool import ThreadPool
# from functools import partial
import plotly

import plotly.graph_objects as go
from hockey_rink import NHLRink, RinkImage
import seaborn as sns
import plotly.express as px
import matplotlib
matplotlib.use("TkAgg")

# INSERT GAME ID HERE
gameId="2024021307" # replace with game ID you want to use


# used to convert string times with the : symbol to seconds
def TimeConvert(word):
    words=word.split(":")
    # print(int(words[0])*60+int(words[1]))
    return int(words[0])*60+int(words[1])

# gets box score for a specifc game id from nhl api
def getBoxScore(gameId):
    req=requests.get(f"https://api.nhle.com/stats/rest/en/skater/summary?isAggregate=false&isGame=true&sort=%5B%7B%22property%22:%22points%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22goals%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22assists%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22playerId%22,%22direction%22:%22ASC%22%7D%5D&start=0&limit=50&cayenneExp=gameId={gameId}")
    data=req.json()["data"]
    df=pd.DataFrame(data)
    df=df.sort_values(by="skaterFullName")
    return df
# get shot attempts data from a specifc game id from nhl api
def getSATData(gameId):
    req=requests.get(f"https://api.nhle.com/stats/rest/en/skater/summaryshooting?isAggregate=false&isGame=true&sort=%5B%7B%22property%22:%22satTotal%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22usatTotal%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22playerId%22,%22direction%22:%22ASC%22%7D%5D&start=0&limit=50&cayenneExp=gameId={gameId}")
    data=req.json()["data"]
    df=pd.DataFrame(data)
    df=df.sort_values(by="skaterFullName")
    return df
# gets hit data from specifc game id from nhl api
def getHitData(gameId):
    req=requests.get(f"https://api.nhle.com/stats/rest/en/skater/realtime?isAggregate=false&isGame=true&sort=%5B%7B%22property%22:%22hits%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22playerId%22,%22direction%22:%22ASC%22%7D%5D&start=0&limit=50&cayenneExp=gameId={gameId}")
    data=req.json()["data"]
    df=pd.DataFrame(data)
    df=df.sort_values(by="skaterFullName")
    return df
# combines hit,sat,and box score data to make final dataset for plotting purposes
def getData(gameId):
    bs=getBoxScore(gameId)
    hd=getHitData(gameId)
    sd=getSATData(gameId)

    bs["Hits"]=hd["hits"]
    bs["SAT Dif"]=sd["satTotal"]
    bs["SAT"]=sd["satFor"]
    bs["Player"]=bs["skaterFullName"]
    bs["TOI/GP"]=bs["timeOnIcePerGame"]
    bs["+/-"]=bs["plusMinus"]
    return bs



req=requests.get(f"https://api-web.nhle.com/v1/gamecenter/{gameId}/play-by-play").json() # get play by play from NHL API

plays=req["plays"] # main data
awayTeamid=req["awayTeam"]["id"] # get the awawy team id
homeTeamid=req["homeTeam"]["id"] # home team id
awayTeam=req["awayTeam"]["commonName"]["default"] # awya team name
homeTeam=req["homeTeam"]["commonName"]["default"] # home team name

# data stores
goalX=[]
goalY=[]
goalPlayer=[]
goalTeam=[]
goalTimes=[]
rawTimes=[]
stealType=[]
stealTimes=[]
stealRt=[]
stealTeam=[]
percentMap={1:[],2:[],3:[]}
win1=0
win2=0
per=1
currFoTime=0
dalFo=[]
colFo=[]
# loop through each play and store the ones we want
for play in plays:
    if play["typeDescKey"]=="goal": # get goals
        # print(play)
        print(play["details"])
        if play["details"]["eventOwnerTeamId"]==homeTeamid:
            colFo.append(TimeConvert(play["timeInPeriod"])-TimeConvert(currFoTime))
        else:
            dalFo.append(TimeConvert(play["timeInPeriod"])-TimeConvert(currFoTime))

# face off data not used here
    elif play["typeDescKey"]=="faceoff":
        currFoTime=play["timeInPeriod"]
        print(play)
        if play["periodDescriptor"]["number"]>per: # find the period
            percentMap[per].append(win1)
            percentMap[per].append(win2)
            win1=win2=0
            per+=1 

        if play["details"]["eventOwnerTeamId"]==homeTeamid:
            win1+=1
        else:
            win2+=1 
percentMap[per].append(win1)
percentMap[per].append(win2)

    
p1F0=round(percentMap[1][0]/(percentMap[1][0]+percentMap[1][1]),2)
p1F0b=1-p1F0
p2F0=round(percentMap[2][0]/(percentMap[2][0]+percentMap[2][1]),2)
p2F0b=1-p1F0
p3F0=round(percentMap[3][0]/(percentMap[3][0]+percentMap[3][1]),2)
p3F0b=1-p1F0

print((sum(dalFo)/len(dalFo)))
      
print((sum(colFo)/len(colFo)))
# cpDf=pd.read_csv("cs2.csv",header=0)
cpDf=getData(gameId)

cpDf["lastName"]=[name.split(" ")[1] for name in cpDf.Player] # player last names
cpDf["TOI/GP"]=[int(name) for name in cpDf["TOI/GP"]] # creating time on ice in seconds from string
print(cpDf)
teams = cpDf["opponentTeamAbbrev"].unique() # unique team names 

# making the bubble plots for overall player performance from tha games
fig=plotly.subplots.make_subplots(rows=3,cols=1,subplot_titles=["All Players",f"{teams[0]} Players",f"{teams[1]} Players"])

fig1 = px.scatter(cpDf,y="Hits", x="SAT Dif",
	         size="TOI/GP", color="+/-",text=cpDf["lastName"],#textposition="top right",
                 hover_name="skaterFullName",color_continuous_scale=px.colors.sequential.Viridis,height=766,width=1200)
fig3 = px.scatter(cpDf[cpDf["opponentTeamAbbrev"]==teams[0]],y="Hits", x="SAT Dif",
	         size="TOI/GP", color="+/-",text=cpDf[cpDf["opponentTeamAbbrev"]==teams[0]]["lastName"],#textposition="top right",
                 hover_name="skaterFullName",color_continuous_scale=px.colors.sequential.Viridis,height=766,width=1200)
fig2 = px.scatter(cpDf[cpDf["opponentTeamAbbrev"]==teams[1]],y="Hits", x="SAT Dif",
	         size="TOI/GP", color="+/-",text=cpDf[cpDf["opponentTeamAbbrev"]==teams[1]]["lastName"],#textposition="top right",
                 hover_name="skaterFullName",color_continuous_scale=px.colors.sequential.Viridis,height=766,width=1200)
fig.add_traces(fig1.data,rows=1,cols=1)
fig.add_trace(fig2.data[0],row=2,col=1)
fig.add_trace(fig3.data[0],row=3,col=1)



# Define separate color axes
fig.update_layout(
    coloraxis=dict(colorscale='Plasma'),
    coloraxis2=dict(colorscale='Plasma'),
    coloraxis3=dict(colorscale='plasma'),
    # autosize=True
    height=1200
    #     width=1200,  # Set width of the figure
    # height=900,  # Set height of the figure

)

# Assign the color axis manually to each trace
fig.data[0].update(marker=dict(coloraxis='coloraxis'))
fig.data[1].update(marker=dict(coloraxis='coloraxis2'))
fig.data[2].update(marker=dict(coloraxis='coloraxis3'))

# Show individual colorbars
fig.update_traces(showlegend=True)


#st.plotly_chart(fig)
fig.show()








#plotting cooridnate data on an NHL rink plot from goals in the game


# parsing the api data
for play in plays: # loop all play by play data
    if play["typeDescKey"]=="goal": # track the goal locations
        print(play)
        goalX.append(play["details"]["xCoord"])
        goalY.append(play["details"]["yCoord"])
        goalTeam.append(play["details"]["eventOwnerTeamId"]) # determing the team
        goalPlayer.append(play["details"]["scoringPlayerId"])
        #if play["periodDescriptor"]["number"]>1:

        # now getting tim ein the game
        goalTimes.append(TimeConvert(play["timeInPeriod"])+(( play["periodDescriptor"]["number"]-1)*TimeConvert("20:00")))
        rawTimes.append(play["timeInPeriod"])
        # determing if thre was a take away or give waay before the goal
        # as in the take away or give away lead to the gooal
        if tag:
            stealTeam.append(tt)
            stealRt.append(rt)
            stealTimes.append(gt)
            stealType.append(tpe)
            tag=False
# idnteify the take away and give aywa play by play events
    elif play["typeDescKey"]=="takeaway" or  play["typeDescKey"]=="giveaway":
        print(play)
        tag=True
       # goalX.append(play["details"]["xCoord"])
       # goalY.append(play["details"]["yCoord"])
        tt=play["details"]["eventOwnerTeamId"] # which team did it
     #   goalPlayer.append(play["details"]["scoringPlayerId"])
        #if play["periodDescriptor"]["number"]>1:
        tpe=play["typeDescKey"] # was it a take way or give away


        gt=(TimeConvert(play["timeInPeriod"])+(( play["periodDescriptor"]["number"]-1)*TimeConvert("20:00")))
        rt=(play["timeInPeriod"])
    else:
        tag=False



#print(plays)
#pd.read_json()


#shots=(pd.read_parquet("https://github.com/sportsdataverse/fastRhockey-data/blob/main/nhl/pbp/parquet/play_by_play_2023.parquet?raw=true").query("event_type in ('GOAL')")
    # 
team_colors = {homeTeamid: (0, 1,0), awayTeamid: (1, 0, 0)} # home team is green awy
#team_colors = {22: (1.0, 0.5,0), 23: (0, 0, 0.6)}


teamMap = {homeTeamid: homeTeam, awayTeamid: awayTeam}
#teamMap = {22: "EDM", 23: "VAN"}

#2023030235
#used for plotting prupsoes
levels=[]
stealLevs=[]
for team in goalTeam:
    if team==homeTeamid:
        levels.append(-1)
    else:
        levels.append(1)

for team in stealTeam:
    if team==homeTeamid:
        stealLevs.append(-0.5)
    else:
        stealLevs.append(0.5)





# plotting the final data on the rink
#first_period = shots.query("game_id == 2022020001 and period == 1")
#print(first_period.columns1)
#print(first_period["x"])
first_period=pd.DataFrame({"x":goalX,"y":goalY,"event_team":goalTeam})
print(first_period)
#https://api-web.nhle.com/v1/gamecenter/2023030235/play-by-play

fig, axs = plt.subplots(1, 1, figsize=(18, 8))
rink = NHLRink()
plt.title(f"{awayTeam} @.{homeTeam} Game Goals")
axs=rink.draw(ax=axs)
rink.scatter("x", "y", facecolor=first_period.event_team.map(team_colors), s=100, edgecolor="white", data=first_period, ax=axs)
rink.plot_fn(sns.scatterplot, x="x", y="y", hue="event_team", s=100, legend=False, data=first_period, ax=axs, palette=team_colors)
print(goalTimes)

#fig.show()
plt.show()
#axs.show()
#fig.show()      
#plt.imshow()


# plotting the time line chart
fig,ax=plt.subplots(figsize=(8.8,40),layout="constrained")
#plt.xticks([20*60,40*60],["2nd Per","3rd Per"])
ax.set(title="Goal TImeline")
ax.vlines(goalTimes,0,levels,color=[(("tab:green" if tm ==homeTeamid else "tab:red"))for tm in goalTeam],lw=4)
ax.axhline(0,c="black")

for tme,lvl,tem,rt in zip(goalTimes,levels,goalTeam,rawTimes):
    ax.annotate(f"{teamMap[tem]}@{rt}",xy=(tme,lvl),size=10,
                xytext=(-3,np.sign(lvl)*3),textcoords="offset points",
                verticalalignment="bottom"if lvl>0 else"top",weight="normal",
                bbox=dict(boxstyle="square",pad=0,lw=0,fc=(1,1,1,0.7)))
    
stealMap={"takeaway":"Take","giveaway":"Give"}

for tme,lvl,tem,rt,stt in zip(stealTimes,stealLevs,stealTeam,stealRt,stealType):
    ax.annotate(f"{stealMap[stt]}@{rt}",xy=(tme,lvl),size=12,
                xytext=(-3,np.sign(lvl)*3),textcoords="offset points",
                verticalalignment="bottom"if lvl>0 else"top",weight="normal",
                bbox=dict(boxstyle="square",pad=0,lw=0,fc=(1,1,1,0.7)))
ax.vlines(stealTimes,0,stealLevs,color=[("tab:green" if tm ==homeTeamid else "tab:red")for tm in stealTeam])
ax.plot([20*60,40*60], np.zeros_like([20*60,40*60]), "ko", mfc="blue")    
ax.annotate("P2",xy=(20*60,0),xytext=(-3,np.sign(1)*3),textcoords='offset points')
ax.annotate("P3",xy=(40*60,0),xytext=(-3,np.sign(1)*3),textcoords='offset points')

ax.xaxis.set_visible(False)
ax.yaxis.set_visible(False)
ax.spines[["left","top","right"]].set_visible(False)
ax.margins(y=0.1)
plt.show()
print(stealTimes)
