import pandas as pd
from sqlalchemy import create_engine
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("filename", type=str, help="The name of the file to process")
args = parser.parse_args()
filename = args.filename

ALLOWED_COUNTRY = ['US', 'IT', 'JP', 'DE'] #Sorry Mars
ALLOWED_OS = ['Android', 'Web', 'iOS'] # BYEBYE EINAC


# Replace with your PostgreSQL credentials
user = "postgres"
password = "ustipak1"
host = "localhost"  # Or the appropriate host
port = "5432"       # Default PostgreSQL port
database = "nordeus"

# Create the database connection string
engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}")



def read_jsonl():
    df = pd.read_json(filename, lines = True)
    df['event_type'].unique()
    l = []
    max_id = df['event_id'].max()
    duplicates = df[df.duplicated(subset='event_id', keep=False)]
    for id, x in duplicates.iterrows():
        l.append(id)
    to_update = l[1:: 2]

    for i, idx in enumerate(to_update):
        df.loc[idx, 'event_id'] = max_id + (i + 1)
    
    return df

def separate_data(df):
    df_register = df[df['event_type'] == 'registration']
    df_session = df[df['event_type'] == 'session_ping']
    df_match = df[df['event_type'] == 'match']

    return df_register, df_session, df_match

def parse_event_info(df):
    unified_data  = []
    #print(pd.DataFrame(list(df['event_data'].values)))
    for event_id, event in zip(df['event_id'].values, df['event_data'].values):
        unified_event = {'event_id': event_id, **event}
        unified_data.append(unified_event)
    df = df.drop('event_data', axis = 1)
    #df = df.drop(['event_data', 'event_type'], axis = 1)
    df_event_data = pd.DataFrame(unified_data)

    return df, df_event_data

def filter_unallowed_values(df, field, vals):
    ret = df[df[field].isin(vals)]
    return ret


def save_to_db(df, table_name):
    df.to_sql(table_name, engine, if_exists='replace', index=False)

if __name__ == "__main__":
    df = read_jsonl()

    df_register, df_session, df_match = separate_data(df)

    df_match, match_data = parse_event_info(df_match)
    df_session, session_data = parse_event_info(df_session)
    session_data = session_data.drop('type', axis = 1)
    df_register, register_data = parse_event_info(df_register)
    

    register_data = filter_unallowed_values(register_data, 'country', ALLOWED_COUNTRY)
    register_data = filter_unallowed_values(register_data, 'device_os', ALLOWED_OS)
    print('Saving to Database')
    save_to_db(df_match, 'match_events')
    save_to_db(df_register, 'register_events')
    save_to_db(df_session, 'session_events')

    save_to_db(match_data, 'match_data')
    save_to_db(session_data, 'session_data')
    save_to_db(register_data, 'register_data')
    print('Saved to DB!')



    