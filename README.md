# COVID-19 by the Numbers for Verywell Health

This repository runs two YAML files in the `.github/workflows` directory: `cdcScrape.yml` and `runChartUpdate.yml`.

The former YAML file runs on a cron schedule on the 46th minute of every hour that will download the [JSON](https://covid.cdc.gov/covid-data-tracker/COVIDData/getAjaxData?id=US_MAP_DATA) of the latest COVID-19 data from the [CDC Covid Tracker](https://covid.cdc.gov/covid-data-tracker/#cases_casesper100klast7days) and pretty-print it to a file called `cdcCovid.json`. It will then commit only new versions of the JSON file to the repository. 

The latter YAML file is triggered by a push to repository and will run the Python script `covidNumberCollection.py` which takes the `cdcCovid.json` file with the latest data and uses it to update the [Datawrapper](https://www.datawrapper.de/) charts that are present on Verywell health's [COVID-19 by the Numbers article](https://www.verywellhealth.com/covid-by-the-numbers-5083007).

The Python script also outputs a CSV file `cdcData.csv` that is sent to the Datawrapper charts via the [Datawrapper API](https://developer.datawrapper.de/) and also commited to the repository.

