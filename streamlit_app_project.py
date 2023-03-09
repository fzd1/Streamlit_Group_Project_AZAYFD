import altair as alt
import pandas as pd
import streamlit as st
import vega_datasets as vd
from urllib.request import Request, urlopen

alt.data_transformers.disable_max_rows()

st.set_page_config(layout="wide")
@st.cache_data
def load_data():

    #Vaccination Sites
    vaccine_sites = pd.read_csv("https://storage.googleapis.com/covid19-open-data/covid19-vaccination-access/facility-boundary-us-all.csv")

    #Vaccines Receives 
    vaccines = pd.read_csv("https://storage.googleapis.com/covid19-open-data/v3/vaccinations.csv")

    #Hospitilizations
    hosp_data = pd.read_csv("https://storage.googleapis.com/covid19-open-data/v3/hospitalizations.csv")

    #Link
    link = pd.read_csv("https://storage.googleapis.com/covid19-open-data/v3/index.csv")

    #epi data
    epi_data = pd.read_csv("https://storage.googleapis.com/covid19-open-data/v3/epidemiology.csv")

    ##Filter to USA Only
    #Vaccines
    vaccines_USA = pd.merge(vaccines, link, how='left', left_on='location_key', right_on='location_key')
    vaccines_USA = vaccines_USA[vaccines_USA["country_code"] == 'US']

    #Hospitilization
    hosp_USA = pd.merge(hosp_data, link, how='left', left_on='location_key', right_on='location_key')
    hosp_USA = hosp_USA[hosp_USA["country_code"] == 'US']

    #merge and subset epi + data to US
    US_Subset = link[link["country_code"] == 'US']
    US_epi_data = pd.merge(epi_data, US_Subset, left_on='location_key', right_on='location_key')

    #trim data to 3 columns of date, subregion1_name, cumulative deceased
    trim_US_epi_data = US_epi_data[['date','subregion1_name','cumulative_deceased']].copy().dropna()

    #Covid Tracking data, Deaths per 100k
    req = Request("https://covidtracking.com/race/data/covid-county-by-race.csv")
    req.add_header('User-Agent', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:77.0) Gecko/20100101 Firefox/77.0')
    content = urlopen(req)
    ctd = pd.read_csv(content)    

    
    return vaccines_USA, hosp_USA, vaccine_sites, trim_US_epi_data, ctd

vaccines_USA, hosp_USA, vaccine_sites, trim_US_epi_data, ctd  = load_data()

#Join Vega Data to COVID Data 
state_pop = vd.data.population_engineers_hurricanes()[['state', 'id']]
state_map = alt.topo_feature(vd.data.us_10m.url, 'states')

click = alt.selection_multi(fields=['state'])

merge_data = pd.merge(vaccine_sites, state_pop['state'], how='left', left_on='facility_sub_region_1', right_on='state')



# US states background
background = alt.Chart(state_map).mark_geoshape(
    fill='lightgray',
    stroke='white'
).mark_geoshape().transform_lookup(
    lookup='id',
    from_=alt.LookupData(state_pop, 'id', ['state'])).encode(
    tooltip=['state:N']).add_selection(click).properties(
    
    
).project('albersUsa')

## Create Plot of Vaccine Center Locations

x = alt.Chart(merge_data).mark_circle(size=3, color='orange').encode(
    longitude='facility_longitude:Q',
    latitude='facility_latitude:Q',
).project(
    type='albersUsa'
).properties(
title="Map of Vaccination Sites for COVID-19 by Selected State")

map = background + x

# y = alt.Chart(trim_US_epi_data[trim_US_epi_data["subregion1_name"] == states_dropdown]).mark_line().encode(
#     x=alt.X('date:T', sort="-y", title='Date'),y=alt.Y('cumulative_deceased', title='Cumulative Deaths')
# ).properties(title="Cumulative Deaths from Covid-19 by Selected State")


## Merge Hospitlization and Vaccination
merger = pd.merge(vaccines_USA, hosp_USA, how='inner', left_on=['date','location_key'], right_on=['date','location_key'])

merge1 = pd.merge(merger, state_pop['state'], how='inner', left_on=['subregion1_name_y'], right_on='state')

final = merge1.groupby(['state', 'date']).sum()

final1 = final.reset_index()

base = alt.Chart(final1)

plot1 = base.mark_line().encode(x=alt.X('date:T', sort="-y", title='Date'),
    y=alt.Y('cumulative_persons_vaccinated', title='Cumulative Persons Vaccinated'), color = alt.Color(field="state", legend=None), opacity=alt.condition(click, alt.value(1), alt.value(0)),
    tooltip=['state:N', 'cumulative_persons_vaccinated:Q']
).add_selection(click
).properties(
                    
                    ).properties(title="Cumulative Persons Vaccinated Over Time for COVID-19 by Selected State")

plot2 = base.mark_line().encode( x=alt.X('date:T', title='Date'),
    y=alt.Y('current_hospitalized_patients', title='Current Persons Hospitalized'), color = alt.Color(field="state", legend=None), opacity=alt.condition(click, alt.value(1), alt.value(0)),
    tooltip=['state:N', 'cumulative_persons_vaccinated:Q']
).add_selection(click
).properties(
                    
                    ).properties(title="Current Persons Hospitalized Over Time for COVID-19 by Selected State")

horizontal = alt.hconcat(plot1, plot2)
c = alt.vconcat(map, horizontal, center=True)
# chart = map & horizontal

# st.write("## US COVID-19 data by States")
st.title('US COVID-19 data by States')
st.altair_chart(c, use_container_width=False)

# create drop down menu for selection of states
states_dropdown = st.selectbox('States', trim_US_epi_data.subregion1_name.unique())


z = alt.Chart(ctd[ctd["state"] == states_dropdown]).mark_bar().encode(
    x='countyName:O',
    y='deathsPer100k',
    color='largestRace1'
)

z2 = alt.Chart(ctd.sort_values(by=['deathsPer100k'], ascending=False).head(10)).mark_bar().encode(
    x='deathsPer100k',
    y=alt.Y('countyName:O',sort='-x'),
    color='largestRace1'
)

vert = alt.vconcat(z, z2)

st.altair_chart(vert, use_container_width=False)
#st.altair_chart(horizontal, use_container_width=False)

#hosp_USA, vaccines_USA, 
#the heads are the subsets of the data, sort="-y",
# x='deathsPer100k', vaccine_sites[vaccine_sites["facility_sub_region_1"] == states_dropdown