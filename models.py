from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from datetime import date

class UserStatsRequest(BaseModel):
    user_id: str
    day: Optional[date] = None

class PlayerStatsResponse(BaseModel):
    user_country: str
    local_time: datetime
    time_since_last_login: int
    time_spent_playing: int
    number_of_sessions: int
    home_points: int
    away_points: int
    match_to_game_ratio: float

class GameStatsRequest(BaseModel):
    day: Optional[date] = None

class GameStatsResponse(BaseModel):
    active_users: int
    num_sessions: int
    average_session_num: float
    users_with_most_points: list[str]
