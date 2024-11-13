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








