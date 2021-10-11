import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, date
import time
from datawrapper import Datawrapper

ACCESS_TOKEN = os.getenv('DW_API_KEY')

dw = Datawrapper(access_token=ACCESS_TOKEN)
### Function to get the covid json as a dataframe and the latest update date as a datetime
def getCovidJSON(url):
    try:
        r = requests.get(url,timeout=3)
        r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print(f"Http Error:{errh}")
    except requests.exceptions.ConnectionError as errc:
        print(f"Error Connecting:{errc}")
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:{errt}")
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else:{err}")
    
    rJSON = r.json()

    updateString = rJSON['CSVInfo']['update']
    updateDate = datetime.strptime(updateString, '%b %d %Y %I:%M%p')

    latest = rJSON['US_MAP_DATA']

    data = pd.DataFrame.from_dict(latest)
    return(data, updateDate)

### Function to update datawrapper charts
def updateChart(dw_chart_id, dataSet, updateDate, dw_api_key):
    dw.add_data(
    chart_id=dw_chart_id,
    data=dataSet
    )

    time.sleep(2)

    headers = {
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Authorization": "Bearer " + dw_api_key
    }

    response = requests.request(method="PATCH", 
                                url="https://api.datawrapper.de/v3/charts/" + dw_chart_id, 
                                json={"metadata": {
                                        "annotate": {
                                            "notes": "Updated " + str(updateDate.strftime('%B %d, %Y'))
                                    }
                                }},
                                headers=headers)

    response.raise_for_status()

    time.sleep(2)

    dw.publish_chart(chart_id=dw_chart_id)

### Function to do data manipulation to initial CDC Dataframe

def mutateCDCData(df):
    cdcDataColumns = df[["abbr", "name", "fips", "tot_cases", "new_cases07", "tot_death", "new_deaths07", "state_level_community_transmission"]]

    unneededRows = ["60", "64", "69", "72", "70", "68", "00", "78"]

    cdcDataColRow = cdcDataColumns[~(cdcDataColumns['fips'].isin(unneededRows))]

    cdcBadNY = cdcDataColRow[cdcDataColRow['name'] != 'NY (including NYC)']

    nycNYS = cdcBadNY.loc[cdcBadNY['fips'].isin(['36', '57']), ["tot_cases", "new_cases07", "tot_death", "new_deaths07"]]

    fullNYS = nycNYS.sum(axis=0, numeric_only=True)

    fullNYST = pd.DataFrame(fullNYS).transpose()

    nysTrans = cdcBadNY[cdcBadNY['fips'] == "36"]
    nysTransV = nysTrans.state_level_community_transmission.item()

    fullNYST['abbr'], fullNYST['name'], fullNYST['fips'], fullNYST['state_level_community_transmission'] = ["NY", "New York", "36", nysTransV]

    noNY = cdcBadNY[~(cdcBadNY['fips'].isin(['36', '57']))]

    cdcClean = pd.concat([noNY, fullNYST])

    cdcClean['Update_Date'] = cdcUpdateDate.date()

    return cdcClean

##### Getting latest Covid JSON from VWDJ Github

cdcUpdate = getCovidJSON("https://covid.cdc.gov/covid-data-tracker/COVIDData/getAjaxData?id=US_MAP_DATA")

cdcData = cdcUpdate[0]
cdcUpdateDate = cdcUpdate[1]

cdcClean = mutateCDCData(cdcData)

cdcToday = pd.read_csv('cdcData.csv', header=0)

fileDate = datetime.strptime(cdcToday['Update_Date'][0], "%Y-%m-%d").date()
jsonDate = cdcUpdateDate.date()

# If there is new data, update the charts
if fileDate != jsonDate:
    cdcClean.to_csv('cdcData.csv', index=False)

    genBar = cdcClean[['name', 'tot_cases', 'new_cases07', 'tot_death', 'new_deaths07']]

    genBar.sort_values(by=['tot_cases'])

    genBar.rename(columns={
        'name': 'STATE', 
        'tot_cases': 'TOTAL CASES', 
        'new_cases07': 'NEW CASES LAST 7 DAYS',
        'tot_death': 'TOTAL DEATHS',
        'new_deaths07': 'NEW DEATHS LAST 7 DAYS'
    })

    updateChart('kK8S7', genBar, cdcUpdateDate, ACCESS_TOKEN)

    time.sleep(2)

    deathMap = cdcClean[['name', 'tot_death']]
    deathMap.sort_values(by=['name'])
    deathMap.rename(columns={
        'name': 'Names',
        'tot_death': 'Values'
    })

    updateChart('sLHpR', deathMap, cdcUpdateDate, ACCESS_TOKEN)

    time.sleep(2)

    casesMap = cdcClean[['name', 'tot_cases']]
    casesMap.sort_values(by=['name'])
    casesMap.rename(columns={
        'name': 'Names',
        'tot_cases': 'Values'
    })

    updateChart('60PT0', casesMap, cdcUpdateDate, ACCESS_TOKEN)

    time.sleep(2)

    transmissionMap = cdcClean[['name', 'state_level_community_transmission']]
    transmissionMap.sort_values(by=['name'])
    transmissionMap.rename(columns={
        'name': 'Names',
        'state_level_community_transmission': 'Values'
    })

    updateChart('DPnc2', transmissionMap, cdcUpdateDate, ACCESS_TOKEN)
