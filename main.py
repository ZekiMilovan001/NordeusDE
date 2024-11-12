from fastapi import FastAPI
import psycopg2
from psycopg2.extras import RealDictCursor
import time

from models import *
from utils import *

while True:
    try:
        conn = psycopg2.connect(host = host, database = database, user = user, password = password, cursor_factory = RealDictCursor)
        cursor = conn.cursor()
        print('Connected to DB!')
        break
    except Exception as error:
        print(error)
        time.sleep(2)
    
app = FastAPI()

@app.get('/player_stats', response_model = PlayerStatsResponse)
def get_player_stats(request: UserStatsRequest):
    response = {}
    day, date_specified = fix_day(request.day)

    #FETCH REGISTER INFO
    user_id = request.user_id
    fetch_user = """
        SELECT event_timestamp, country 
        FROM register_data 
        JOIN register_events 
        ON register_data.event_id = register_events.event_id 
        WHERE user_id = %s
        """
    cursor.execute(fetch_user, (user_id,))
    res = cursor.fetchone()
    user_country = res['country']
    response['user_country'] = user_country
    local_time = get_time(res['event_timestamp'], country_to_timezone[res['country']])
    response['local_time'] = local_time

    #FETCH LAST LOGIN
    fetch_last_login = """
        SELECT event_timestamp
        FROM session_events
        JOIN session_data
        ON session_events.event_id = session_data.event_id
        WHERE user_id =  %s
        ORDER BY event_timestamp DESC
        LIMIT 1
        """
    cursor.execute(fetch_last_login, (user_id, ))
    last_login = cursor.fetchone()['event_timestamp']
    delta_login = get_delta_time(day.timestamp(), last_login)
    response['time_since_last_login'] = delta_login
    # FETCH SESSION COUNT AND PLAY TIME
    fetch_play_time_session_count = """
        WITH SessionData AS (
            SELECT 
                event_timestamp,
                CASE 
                    WHEN event_timestamp - LAG(event_timestamp) OVER (PARTITION BY user_id ORDER BY event_timestamp ASC) <= 60
                        THEN 0 
                    ELSE 1 
                END AS new_session_flag
            FROM session_events 
            JOIN session_data ON session_events.event_id = session_data.event_id
            WHERE user_id = %s AND event_timestamp BETWEEN %s AND %s
        ),
        SessionBoundaries AS (
            SELECT 
                event_timestamp,
                SUM(new_session_flag) OVER (ORDER BY event_timestamp) AS session_id
            FROM SessionData
        ),
        SessionDurations AS (
            SELECT 
                session_id,
                MAX(event_timestamp) - MIN(event_timestamp) AS session_duration
            FROM SessionBoundaries
            GROUP BY session_id
        )
        SELECT 
            COUNT(session_id) AS session_count,                 
            COALESCE(SUM(session_duration), 0) AS play_time
        FROM SessionDurations;
        """
    lb, ub = get_day_bounds(day.timestamp())
    if not date_specified:
         lb = 0
    cursor.execute(fetch_play_time_session_count, (user_id, lb, ub, ))
    res = cursor.fetchone()
    play_time = res['play_time']
    response['time_spent_playing'] = res['play_time']
    response['number_of_sessions'] = res['session_count']
   
    #FETCH POINTS
    fetch_points = """
        SELECT SUM(
            CASE
                WHEN home_goals_scored > away_goals_scored then 3
                WHEN home_goals_scored < away_goals_scored then 0
                ELSE 1
            END) 
        FROM match_events JOIN match_data
        ON match_events.event_id = match_data.event_id
        WHERE home_user_id = %s AND home_goals_scored IS NOT NULL AND event_timestamp BETWEEN %s AND %s
        UNION
        SELECT SUM(
            CASE
                WHEN home_goals_scored < away_goals_scored then 3
                WHEN home_goals_scored > away_goals_scored then 0
                ELSE 1
            END )
        FROM match_events JOIN match_data
        ON match_events.event_id = match_data.event_id
        WHERE away_user_id = %s AND home_goals_scored IS NOT NULL AND event_timestamp BETWEEN %s AND %s
        """
    cursor.execute(fetch_points, (user_id, lb, ub, user_id, lb, ub, ))
    res = cursor.fetchall()
    response['home_points'] = 0
    response['away_points'] = 0
    if len(res) > 0 and res[0]['sum'] is not None:
        response['home_points'] = res[0]['sum']
    if len(res) > 1 and res[1]['sum'] is not None:
        response['away_points'] = res[1]['sum']

    #FETCH MATCH RATIO
    fetch_match_time = """
        WITH games AS(
        WITH starts AS (
            SELECT home_user_id, away_user_id, event_timestamp as start_time
            FROM match_data JOIN match_events
            ON match_data.event_id = match_events.event_id
            WHERE home_goals_scored IS NULL AND home_user_id = %s AND event_timestamp BETWEEN %s AND %s
            UNION
            SELECT home_user_id, away_user_id, event_timestamp as start_time
            FROM match_data JOIN match_events
            ON match_data.event_id = match_events.event_id
            WHERE home_goals_scored IS NULL AND away_user_id = %s AND event_timestamp BETWEEN %s AND %s

        )
        ,ends AS(
            SELECT home_user_id, away_user_id, event_timestamp as end_time
            FROM match_data JOIN match_events
            ON match_data.event_id = match_events.event_id
            WHERE home_goals_scored IS NOT NULL AND home_user_id = %s AND event_timestamp BETWEEN %s AND %s
            UNION
            SELECT home_user_id, away_user_id, event_timestamp as end_time
            FROM match_data JOIN match_events
            ON match_data.event_id = match_events.event_id
            WHERE home_goals_scored IS NOT NULL AND away_user_id = %s AND event_timestamp BETWEEN %s AND %s
        ) 

        SELECT ends.home_user_id, ends.away_user_id, start_time, end_time, end_time - start_time as diff
        FROM starts JOIN ends
        ON starts.home_user_id = ends.home_user_id and starts.away_user_id = ends.away_user_id
        WHERE end_time > start_time AND end_time - start_time <= 180

        ),
        session_games_home AS (
            SELECT session_data.event_id, user_id, event_timestamp, start_time, end_time, 60 - (start_time - event_timestamp) as live_game
            FROM session_data JOIN session_events
            ON session_data.event_id = session_events.event_id JOIN games
            ON games.home_user_id = session_data.user_id AND start_time > event_timestamp AND (start_time - event_timestamp) < 60
            UNION
            SELECT session_data.event_id, user_id, event_timestamp, start_time, end_time, end_time - event_timestamp as live_game
            FROM session_data JOIN session_events
            ON session_data.event_id = session_events.event_id JOIN games
            ON games.home_user_id = session_data.user_id AND end_time > event_timestamp AND (end_time - event_timestamp) < 60
        ),
        session_games_away AS (
            SELECT session_data.event_id, user_id, event_timestamp, start_time, end_time, 60 - (start_time - event_timestamp) as live_game
            FROM session_data JOIN session_events
            ON session_data.event_id = session_events.event_id JOIN games
            ON games.away_user_id = session_data.user_id AND start_time > event_timestamp AND (start_time - event_timestamp) < 60
            UNION
            SELECT session_data.event_id, user_id, event_timestamp, start_time, end_time, end_time - event_timestamp as live_game
            FROM session_data JOIN session_events
            ON session_data.event_id = session_events.event_id JOIN games
            ON games.away_user_id = session_data.user_id AND end_time > event_timestamp AND (end_time - event_timestamp) < 60
        )
        SELECT SUM(live_game) FROM session_games_home
        WHERE user_id = %s
        UNION
        SELECT SUM(live_game) FROM session_games_away
        WHERE user_id = %s
        """
    cursor.execute(fetch_match_time, (user_id, lb, ub, user_id, lb, ub, user_id, lb, ub, user_id, lb, ub, user_id, user_id, ))
    res = cursor.fetchall()
    match_time = 0
    
    if len(res) >= 1 and res[0]['sum'] is not None:
         match_time += res[0]['sum']
    if len(res) >= 2 and res[1]['sum'] is not None:
        match_time =+ res[1]['sum']
    
    match_ratio = 0
    if play_time > 0:
        match_ratio = match_time / play_time
    response['match_to_game_ratio'] = match_ratio * 100

    return PlayerStatsResponse(**response)

@app.get('/game_stats', response_model = GameStatsResponse)
def get_game_stats(request: GameStatsRequest):
    response = {}
    day, date_specified = fix_day(request.day)

    #FETCH ACTIVE USER INFO
    lb, ub = get_day_bounds(day.timestamp())
    if not date_specified:
        lb = 0
    fetch_active_users = """
        SELECT COUNT(DISTINCT(user_id)) 
        FROM session_data JOIN session_events
        ON session_data.event_id = session_events.event_id
        WHERE event_timestamp BETWEEN %s AND %s
    """

    cursor.execute(fetch_active_users, (lb , ub,))
    response['active_users'] = coalesce(cursor.fetchone()['count'])

    #FETCH SESSION INFO
    fetch_session_info = """
        WITH SessionData AS (
            SELECT 
                user_id,
                CASE 
                    WHEN event_timestamp - LAG(event_timestamp) OVER (PARTITION BY user_id ORDER BY event_timestamp ASC) <= 60
                        THEN 0 
                    ELSE 1 
                END AS new_session_flag
            FROM session_events 
            JOIN session_data ON session_events.event_id = session_data.event_id
            WHERE event_timestamp BETWEEN %s AND %s
        ),
        UserSessions AS (
            SELECT 
                user_id,
                SUM(new_session_flag) AS session_count
            FROM SessionData
            GROUP BY user_id
			HAVING SUM(new_session_flag) >= 1
        )
        SELECT 
            SUM(session_count),
            (SELECT AVG(session_count) FROM UserSessions) AS avg_session_count
        FROM UserSessions;
        """
    cursor.execute(fetch_session_info, (lb, ub, ))
    res = cursor.fetchone()
    response['num_sessions'] = coalesce(res['sum'])
    response['average_session_num'] = coalesce(res['avg_session_count'])

    #FETCH BEST PLAYERS
    fetch_best_players = """
        WITH UserPoints AS (
            SELECT 
                user_id, 
                COALESCE(
                    (SELECT SUM(
                        CASE
                            WHEN home_goals_scored > away_goals_scored THEN 3
                            WHEN home_goals_scored < away_goals_scored THEN 0
                            ELSE 1
                        END
                    ) 
                    FROM match_events 
                    JOIN match_data ON match_events.event_id = match_data.event_id
                    WHERE home_user_id = register_data.user_id 
                    AND home_goals_scored IS NOT NULL
                    ), 0)
                +
                COALESCE(
                    (SELECT SUM(
                        CASE
                            WHEN home_goals_scored < away_goals_scored THEN 3
                            WHEN home_goals_scored > away_goals_scored THEN 0
                            ELSE 1
                        END
                    ) 
                    FROM match_events 
                    JOIN match_data ON match_events.event_id = match_data.event_id
                    WHERE away_user_id = register_data.user_id 
                    AND home_goals_scored IS NOT NULL
                    ), 0) AS points_scored
            FROM register_data
        ),
        MaxPoints AS (
            SELECT MAX(points_scored) AS max_points
            FROM UserPoints
        )
        SELECT user_id, points_scored
        FROM UserPoints
        JOIN MaxPoints ON UserPoints.points_scored = MaxPoints.max_points
        """
    cursor.execute(fetch_best_players)
    l = []
    res = cursor.fetchall()
    for x in res:
        l.append(x['user_id'])
    response['users_with_most_points'] = l
    return GameStatsResponse(**response)



