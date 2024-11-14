# Nordeus Data Engineering challange

## Enviroment setup (for Windows)

Create folder and then open a terminal in that folder and run these commands:
1. `git clone https://github.com/ZekiMilovan001/NordeusDE.git`
2. `python -m venv venv`
3. `./venv/Scripts/activate`
4. `pip install -r requirements.txt`

## Setting Up the .env File

The `.env` file generally contains sensitive configuration settings for your project, such as database credentials. Here’s how to set up and manage  `.env` file. <br>

### Steps to Fill Out the .env File

1. **USER**: 
   - Set this to your PostgreSQL username (the user that has access to the database).
   - Example: `USER=postgres`.

2. **PASSWORD**:
   - Set this to your PostgreSQL user's password.
   - Example: `PASSWORD=password123`.

3. **HOST**:
   - Set this to the host where your PostgreSQL database is running.
   - If it’s running on your local machine, you can use `localhost`.
   - Example: `HOST=localhost`.

4. **PORT**:
   - Set this to the port number that PostgreSQL is listening on (default is 5432).
   - Example: `PORT=5432`.

5. **DATABASE**:
   - Set this to the name of your PostgreSQL database.
   - Example: `DATABASE=nordeus`.

Once you have filled out the `.env` file, it should look like this:

```plaintext
USER=postgres
PASSWORD=password123
HOST=localhost
PORT=5432
DATABASE=nordeus
```
## Setup Instructions
1. **Install PostgreSQL** and **pgAdmin**.

2. **Create a Database in pgAdmin**:
   - Open **pgAdmin**.
   - In the left panel, navigate to:  
     `Servers > PostgreSQL`.
   - **Right-click** on `PostgreSQL`, then select:  
     `Create > Database`.
   - Enter a name for your database.

   > **Note:** This is a simple approach to quickly get started with the API. 😊

3. **Extract Data into Database**:
   - Run the `process.py` script to extract data from `.jsonl` files into the database.
   - **Example:** `python process.py events_test.jsonl`
4. Start **Uvicorn** server:
   - Run `uvicorn main:app` in the terminal.
5. Start using API (e.g. Postman)

---
# REST API
## 1. **Get Player Stats**

**Endpoint**: `/player_stats`  
**Method**: `GET`  
**Description**: Retrieve statistics for a specific player.
<br>
### Request 
- **`user_id`** (required, *string* ): Represents a unique identifier for a user.
- **`date`** (optional): In the format `YYYY-MM-DD`.
  - If no date is specified, the API calculates all-time stats for the specified user.
  - If a date is specified, the API calculates stats for the given date only.
### Response 
- **Country of the user** (*string*): The country of the user.
- **Registration datetime** (*datetime*): The date and time the user registered, shown in their local timezone.
- **Days since last login** (*int*): 
  - If no date is specified, calculates the days since the user's last login.
  - If a date is provided, calculates the days up to the last login date.
- **Number of sessions** (*int*):
  - If a date is specified, returns the session count for that day.
  - If no date is specified, returns the all-time number of sessions.
- **Time spent in game (in seconds)** (*int*):
  - If a date is provided, gives the time spent on that day.
  - If no date is specified, gives the all-time total time spent in the game.
- **Total points on matches** (*int*):
  - Points are based on matches that started on the specified date, categorized by the user's role as home or away.
  - If no date is specified, provides all-time points, calculated as:
    - Win = 3 points
    - Draw = 1 point
    - Loss = 0 points
- **Match time as a percentage of total game time** (*float*):
  - Represents the percentage of total game session time spent actively participating in matches.
  - If no date is specified, provides the all-time percentage.
### Example output:
```plaintext
{
    "user_country": "US",
    "local_time": "2024-10-09T13:27:35-04:00",
    "time_since_last_login": 34,
    "time_spent_playing": 780,
    "number_of_sessions": 2,
    "home_points": 3,
    "away_points": 0,
    "match_to_game_ratio": 14.487179487179487
}
```

## 2. **Get Game-wide Stats**

**Endpoint**: `/game_stats`  
**Method**: `GET`  
**Description**: Retrieve statistics for a game state.
### Request
- **`date`** (optional): In the format `YYYY-MM-DD`.
  - If no date is specified, the API calculates all-time game statistics.
  - If a date is specified, the API calculates statistics for the specified date only.
### Response
- **Number of daily active users** (*int*):
  - If a date is specified, returns the number of users who had at least one session on that day.
  - If no date is specified, returns the total number of users with at least one session ever.
- **Number of sessions** (*int*): The total number of sessions recorded.
- **Average number of sessions** (*float*):
  - Calculates the average number of sessions per user for users with at least one session.
- **User(s) with the most points overall** (*list of strings*): The user or users who have accumulated the most points in total.
### Example output:
```plaintext
{
    "active_users": 3,
    "num_sessions": 5,
    "average_session_num": 1.6666666666666667,
    "users_with_most_points": [
        "52d65a1b-8012-934e-001b-19e6ba3cdc0e"
    ]
}
```
# Discussion
## Dataset description (events.jsonl)

### Parameters
| Parameter Name    | Parameter Type | Parameter Description |
|-------------------|----------------|------------------------|
| `event_id`        | `INT`          | Unique identifier representing an event |
| `event_timestamp` | `INT`          | Time of event represented as Unix time |
| `event_type`      | `STRING`       | One of the following: `registration`, `session_ping`, `match` |
| `event_data`      | `JSON OBJECT`  | JSON object containing all event-specific data (check event data below) |

For our analysis, we are interested in three types of events: **registration**, **session_ping**, and **match**.

---

## Event Types

### Registration
The **registration** event is generated when a user registers. At that time, the user receives a unique identifier to track them across all other events. This event also includes the country and OS of the device used.

| Parameter Name | Parameter Type | Parameter Description |
|----------------|----------------|------------------------|
| `country`      | `STRING`       | Country from which the user registered |
| `user_id`      | `STRING`       | Unique identifier representing a user |
| `device_os`    | `STRING`       | OS of the device user registered from. Valid values: `iOS`, `Android`, `Web` |

### Session_ping
A **session** is the continuous period during which a player interacts with a game. Sessions are tracked using **session_ping** events. This event is sent when a user opens the game and every 60 seconds afterward, as long as the game remains open. If more than 60 seconds pass between two ping events, they are considered different sessions. The first event in a session has the type `session_start`, and the last event has the type `session_end`.

| Parameter Name | Parameter Type | Parameter Description |
|----------------|----------------|------------------------|
| `user_id`      | `STRING`       | Unique identifier representing a user |
| `type`         | `STRING`       | Possible values: `session_start`, `session_end`, and `""` (empty string) |

## Match Event

This event is triggered when a match starts and finishes. If the match has started, the values for `home_goals_scored` and `away_goals_scored` will be `NULL`. When the event signals that the match has finished, these fields will contain non-`NULL` values.

### Event Parameters

| Parameter           | Type      | Description                                                                 |
|---------------------|-----------|-----------------------------------------------------------------------------|
| `match_id`          | STRING    | Identifier representing one match (same value for both match start and end) |
| `home_user_id`      | STRING    | Unique identifier representing the home user                                |
| `away_user_id`      | STRING    | Unique identifier representing the away user                                |
| `home_goals_scored` | INTEGER   | Number of goals scored by the home team (or `NULL` if the match just started) |
| `away_goals_scored` | INTEGER   | Number of goals scored by the away team (or `NULL` if the match just started) |

---

## Dataset: Timezones

For simplicity, each country is assigned exactly one timezone.

### Dataset Parameters

| Parameter   | Type   | Description                                                                |
|-------------|--------|----------------------------------------------------------------------------|
| `country`   | STRING | Country code                                                               |
| `timezone`  | STRING | Timezone for the country. Possible values: "America/New_York", "Asia/Tokyo", "Europe/Berlin", "Europe/Rome" |
---
## Approach
### Data cleaning
1. Checked the data integrity as per column definitions given in the task.
      - Checked if `goals_scored` fields have all ***int*** values. (*They do*)
      - Checked if `user_id` field in registration *unique*. (i.e. Checked if one user can register once with same `user_id`)
      - Checked if `device_os` and `country` fields contain unallowed values. (They did, *Mars* for `country` and *ENIAC* for `device_os`)
      - > **Note 1:** There was repetition of registration for same `user_id` value, but also one of them had `device_os` value *ENIAC*, which after discarding it, solves the problem.
      - > **Note 2:** Regarding the *Mars* field, in this solution, I discarded that register row, but also `country` value could be changed to random or one of the allowed values for `country`, depending on requirements and is open for discussion.
      - Droped the `type` column in session data, since i wanted that bonus 😎.
2. Explored additional information about dataset.
      - Checked if `session_ping` and `match` types of pings can happen at the same time. (i.e. Checked if general playtime can be queried using only session info. It can.)
### Data organization
The data was split into 3 main sub-categories that refer to their respective `event_type` values, thus 3 initial tables:
      - *Register data* 
      - *Session data*
      - *Match data*
All of these tables contain before mentioned fields. <br>
The `event_data` field was discarded from these tables, but it formed three new tables:
      - *Register events*
      - *Session events*
      - *Match events*
These tables contain event information for their respective events, explained before, with addition of `event_id` to each of them, which acts as a foreign key to *data* tables.


### Queries - Player Stats
Since some of them are pretty simple, such as extracting country of the registered user, I will be skipping some.
1. How many days have passed since this user last logged in?
      - Idea was to filter data based on `date` parameter (`event_time` date-value <= `date`) and get the most recent one, then calculate delta between that time and `date` value.
2. Number of sessions for that user on that day. If no date is provided give the all time number of sessions.
      - *Time filter:* Idea was to find bounds of `date` parameter. Lower bound is first second of the day, for given `date` parameter (or 0 if no values were passed) and upper bound is last second of the day (or last second of current day, if no values were passed).
      - *Session count:* Idea was to sort by `event_timestamp` ascendingly for each `user_id` value and calculating value of the new flag field as:
           - 0: if difference between current and last ping is less than 60 seconds, as per task definition. (i.e. if it is not start of new session)
           - 1: in other cases, meaning that that row is the start of new session.
           - By summing these flags, all session starts are counted and number of sessions is extracted.
      - *Session duration:* : Idea was to find sum of all differences between last and first ping in each session.
3. Total points won on matches grouped by whether the user was home or away, for specific day or all time, depending if `date` parameter has value.
           - *Time filter:* same idea as before.
           - *Home points:* filter data where `user_id` is equal to `home_user_id` field and sum points accordingly.
           - *Away points:* filter data where `user_id` is equal to `away_user_id` field and sum points accordingly.
4. Match time as a percentage of total game time. Represents how much of a player's overall game session was spent actively participating in a match, compared to the entire time spent in the game
      - *Starts* and *Ends* temporary tables: Fitered by match start or end.
      - *Games table*: It has same data as original, with the addition of start and end time for each game.
      - *Games away* and *Games home* table: Has contents of *Games table* but filtered whether user was playing at home or away. Wiith addition of `live_game` field, that is showing how much player was participating in a match since start of it (e.g. 60 - `players_latency`, where `player_latency` is telling us how late player was late for the match start). Similar stands for match ends.
      - *Result* by comining these tables and summing `live_game` values for that player, we can extract how much time player has spent playing matches actively. Ratio is caluclated using already found time spent value.
### Queries - Game Stats
1. Number of daily active users.
      - Counted unique occurencies of `user_id` filtered by before mentioned criteria.
2. Number of sessions and average number of sessions for users that have at least one session.
      - Used same flag "trick" as in ***Player stats*** but for every player, filtered by before mentioned criteria.
3. The user/users with the most points overall.
      - Found maximum number of points overall, then filtered all players who have that number of points, filtered by before mentioned criteria.
---

## What could've been done differentely
1. The general session data could've been stored into one table, containing all fields, since all event types have same fields (excluding `event_data` field), but I've chosen to separate them for the optimization reasons (less data to be queried) and for the sake of simplicity, also, they were not needed at the same time in the *API*. If *ALL* data got combined into one big table, a lot of fields would be ***NULL***, since `event_data` has different attributes depending on `event_type` value, thus wasting memory and slowing down the queries.
2. *"Table for each query"*: If the data was manipulated in such a way, that table gets created for every query in task requirements, the queries would be faster, shorter/simpler (reducing code in API router), but introducing redudancy in data and making loading and cleaning process more complex.
---
## My comments
Generally, in the API implementation, I've chosen to distribute more workolad on the database and minimize work with the fetched data in the router, since database has internal optimization tools, which are smarter than I am probably, hence, increasing the speed. I also was thinking about using 2<sup>nd</sup> approach, but I felt like it was not the goal of this challange to reduce the SQL ussage to `select * from table` and do the rest using pandas, although I do like the idea of faster API calls more, but at the and of the day, ***you gotta pay the toll somewhere***, is it at loading or at reading.



![uwu_hamster](https://github.com/user-attachments/assets/82ed4a84-2937-4230-aa1b-8e593de3b397)






