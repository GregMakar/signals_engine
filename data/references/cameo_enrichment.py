"""
this is where cameo.yaml enrichment logic goes.

when necessary you can scrape this https://parusanalytics.com/eventdata/cameo.dir/cameocontents.html
for detailed description of each CAMEO code in order to be used in the yaml.

more basic CAMEO mappers that use the cameo_event_codes.csv should also be built here.

this will likely come in handy when building NLP logic, or UI since CAMEO codes are
basically as machine friendly as it gets.

NOTE: make sure to always repr as str, since they sometimes have leading 0s
"""

