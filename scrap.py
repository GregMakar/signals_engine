from src.clients.openalex_client import OpenAlexClient
from json import dumps

client = OpenAlexClient()

# response = client.get_json_list(entity='works', per_page=1,
#                                 search='natural language processing',
#                                 )

response = client.search_works(query='codelco', per_page=1)
print(dumps(response, indent=4))

# response = client.search_author('A5064595532')
# print(dumps(response, indent=6))

