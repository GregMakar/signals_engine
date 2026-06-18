import requests as r
from gdlet_client import GDELTIngestor

# response = r.get('http://data.gdeltproject.org/gdeltv2/lastupdate-translation.txt')
# cleaned_list = [line for line in response.iter_lines()]
# print(cleaned_list)
#
# for url in cleaned_list:
#     url = str(url).split(' ')
#     print(url[2].rstrip("'"))

ingestor = GDELTIngestor()
ingestor.installer()
