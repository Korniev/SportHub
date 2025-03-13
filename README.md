# SportHub
This is the only platform where users can: View live results of matches, races, fights (WebSockets / updates). Create fantasy teams for different sports (football, F1, boxing / MMA). View statistics and analytics (tables, graphs, athlete ratings). Communicate in chat or comment on current events.


for alembic migrations:
1. cd backend
2. export DATABASE_URL_SYNC=postgresql://sporthub_user:secretpassword@localhost:5432/sporthub_db
3. alembic revision --autogenerate -m "SOME MESSAGE"
4. alembic upgrade head