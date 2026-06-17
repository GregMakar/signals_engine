import pandas as pd
from src.storage.parquet_store import ParquetStore

pd.set_option("display.max_columns", None)      # show all columns
pd.set_option("display.width", None)            # don't wrap based on terminal width
# pd.set_option("display.max_colwidth", None)     # don't truncate cell contents

store = ParquetStore()
full_df = store.load('openalex_first_test')

df = full_df[['authors']]
print(df)

authors_df = (
    df
    .explode("authors")                       # one row per author
    .dropna(subset=["authors"])               # remove empty author rows
)

authors_df = pd.json_normalize(authors_df["authors"])

authors_df = authors_df.set_index("full_name")
print(authors_df)