"""
Trivia multiplayer lobby system using Flask-SocketIO.

Manages lobby creation, joining, synchronized gameplay, and score tracking.
All game state is held in-memory (lobby_games dict) for speed; only final
results are persisted to the database via TriviaWin.
"""

import random
import string
import logging
import threading
import jwt
import requests
from datetime import datetime, timezone
from flask import request
from flask_socketio import SocketIO, emit, join_room, leave_room

logger = logging.getLogger(__name__)

socketio = SocketIO(
    cors_allowed_origins="*", async_mode="gevent", ping_timeout=30, ping_interval=15
)

# In-memory lobby state: code -> LobbyState
lobby_games = {}


class LobbyState:
    """In-memory state for an active lobby."""

    def __init__(self, code, host_user_id, host_info, settings):
        self.code = code
        self.host_user_id = host_user_id
        self.status = "waiting"  # waiting, countdown, playing, results
        self.settings = (
            settings  # {num_questions, difficulty, category, category_name, max_players}
        )
        self.players = (
            {}
        )  # user_id -> {sid, display_name, avatar_url, discord_id, score, answers, connected}
        self.questions = []  # fetched from Open Trivia DB
        self.current_question = -1
        self.question_timer = None
        self.question_deadline = None  # timestamp when current question expires
        self.lock = threading.Lock()

        # Add host as first player
        self.players[host_user_id] = {
            "sid": None,
            "display_name": host_info.get("display_name", "Host"),
            "avatar_url": host_info.get("avatar_url"),
            "discord_id": host_info.get("discord_id", ""),
            "score": 0,
            "answers": [],
            "connected": True,
        }

    def player_count(self):
        return len([p for p in self.players.values() if p["connected"]])

    def to_dict(self):
        players_list = []
        for uid, p in self.players.items():
            if p["connected"]:
                players_list.append(
                    {
                        "user_id": uid,
                        "display_name": p["display_name"],
                        "avatar_url": p["avatar_url"],
                        "score": p["score"],
                        "answered": (
                            len(p["answers"]) > self.current_question
                            if self.current_question >= 0
                            else False
                        ),
                    }
                )
        return {
            "code": self.code,
            "status": self.status,
            "settings": self.settings,
            "players": players_list,
            "current_question": self.current_question,
            "total_questions": (
                len(self.questions) if self.questions else self.settings.get("num_questions", 10)
            ),
            "host_user_id": self.host_user_id,
        }


def _generate_code():
    """Generate a unique 6-char lobby code."""
    for _ in range(50):
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in lobby_games:
            return code
    return None


def _authenticate_socket():
    """Authenticate a WebSocket connection from the CF_Authorization token."""
    token = request.args.get("token", "")
    if not token:
        return None
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        custom = payload.get("custom", {})
        discord_user = custom.get("discord_user", {}) if isinstance(custom, dict) else {}
        if not discord_user or not discord_user.get("id"):
            return None

        from models import User

        user = User.query.filter_by(discord_id=str(discord_user["id"])).first()
        if not user:
            return None
        return user
    except Exception as e:
        logger.error("Socket auth failed: %s", e)
        return None


QUESTION_TIME_SECONDS = 20  # seconds per question
RESULTS_PAUSE_SECONDS = 5  # seconds to show answer before next question
COUNTDOWN_SECONDS = 5  # countdown before game starts


def _fetch_questions(settings):
    """Fetch questions from Open Trivia Database."""
    url = f"https://opentdb.com/api.php?amount={settings.get('num_questions', 10)}&type=multiple"
    if settings.get("category"):
        url += f"&category={settings['category']}"
    if settings.get("difficulty"):
        url += f"&difficulty={settings['difficulty']}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("response_code") != 0 or not data.get("results"):
            logger.error("Open Trivia DB returned code %s", data.get("response_code"))
            return None
        return data["results"]
    except Exception as e:
        logger.error("Failed to fetch trivia questions: %s", e)
        return None


def _prepare_question(q, index):
    """Prepare a question for sending to clients (shuffled answers, no correct answer revealed)."""
    answers = q["incorrect_answers"][:] + [q["correct_answer"]]
    random.shuffle(answers)
    return {
        "index": index,
        "question": q["question"],
        "category": q["category"],
        "difficulty": q["difficulty"],
        "answers": answers,
    }


def _advance_question(code):
    """Advance to the next question or end the game."""
    lobby = lobby_games.get(code)
    if not lobby or lobby.status != "playing":
        return

    with lobby.lock:
        lobby.current_question += 1

        if lobby.current_question >= len(lobby.questions):
            _end_game(code)
            return

        q = lobby.questions[lobby.current_question]
        q_data = _prepare_question(q, lobby.current_question)
        lobby.question_deadline = datetime.now(timezone.utc).timestamp() + QUESTION_TIME_SECONDS

    socketio.emit(
        "question",
        {
            **q_data,
            "time_limit": QUESTION_TIME_SECONDS,
        },
        room=code,
    )

    # Schedule auto-advance when time runs out
    lobby.question_timer = socketio.start_background_task(
        _question_timeout, code, lobby.current_question
    )


def _question_timeout(code, question_index):
    """Called when question time expires. Reveal answer and advance."""
    socketio.sleep(QUESTION_TIME_SECONDS)
    lobby = lobby_games.get(code)
    if not lobby or lobby.status != "playing":
        return
    if lobby.current_question != question_index:
        return  # Already advanced

    _reveal_and_advance(code)


def _all_answered(lobby):
    """Check if all connected players have answered the current question."""
    for p in lobby.players.values():
        if p["connected"] and len(p["answers"]) <= lobby.current_question:
            return False
    return True


def _reveal_and_advance(code):
    """Reveal the correct answer, show scores, then advance after a pause."""
    lobby = lobby_games.get(code)
    if not lobby or lobby.status != "playing":
        return

    q = lobby.questions[lobby.current_question]
    correct = q["correct_answer"]

    # Build per-player results for this question
    player_results = []
    for uid, p in lobby.players.items():
        if not p["connected"]:
            continue
        if len(p["answers"]) > lobby.current_question:
            ans = p["answers"][lobby.current_question]
            player_results.append(
                {
                    "user_id": uid,
                    "display_name": p["display_name"],
                    "answer": ans,
                    "correct": ans == correct,
                    "score": p["score"],
                }
            )
        else:
            # Didn't answer in time
            p["answers"].append(None)
            player_results.append(
                {
                    "user_id": uid,
                    "display_name": p["display_name"],
                    "answer": None,
                    "correct": False,
                    "score": p["score"],
                }
            )

    socketio.emit(
        "answer_reveal",
        {
            "correct_answer": correct,
            "player_results": player_results,
            "question_index": lobby.current_question,
        },
        room=code,
    )

    # Pause then advance
    socketio.start_background_task(_delayed_advance, code)


def _delayed_advance(code):
    """Wait then advance to next question."""
    socketio.sleep(RESULTS_PAUSE_SECONDS)
    _advance_question(code)


def _end_game(code):
    """End the game, persist results, emit final scores."""
    lobby = lobby_games.get(code)
    if not lobby:
        return

    lobby.status = "results"

    # Build final standings sorted by score desc
    standings = []
    for uid, p in lobby.players.items():
        standings.append(
            {
                "user_id": uid,
                "display_name": p["display_name"],
                "avatar_url": p["avatar_url"],
                "discord_id": p["discord_id"],
                "score": p["score"],
                "total": len(lobby.questions),
            }
        )
    standings.sort(key=lambda x: x["score"], reverse=True)

    # Persist each player's result as a TriviaWin
    try:
        from models import TriviaWin
        from database import db

        cat_name = lobby.settings.get("category_name", "")
        for uid, p in lobby.players.items():
            if not p["connected"] and p["score"] == 0:
                continue  # Skip fully disconnected players with no score
            win = TriviaWin(
                user_id=uid,
                score=p["score"],
                total_questions=len(lobby.questions),
                category=cat_name,
            )
            db.session.add(win)
        db.session.commit()
        logger.info("Persisted trivia results for lobby %s (%d players)", code, len(lobby.players))
    except Exception as e:
        logger.error("Failed to persist trivia results for lobby %s: %s", code, e)
        try:
            from database import db

            db.session.rollback()
        except Exception as rollback_err:
            logger.error("Failed to rollback after trivia persist error: %s", rollback_err)

    # Update DB lobby status
    try:
        from models import TriviaLobby
        from database import db

        db_lobby = TriviaLobby.query.filter_by(code=code).first()
        if db_lobby:
            db_lobby.status = "finished"
            db_lobby.finished_at = datetime.now(timezone.utc)
            db.session.commit()
    except Exception as e:
        logger.error("Failed to update lobby status for %s: %s", code, e)

    socketio.emit("game_over", {"standings": standings}, room=code)

    # Clean up in-memory state after a delay
    socketio.start_background_task(_cleanup_lobby, code)


def _cleanup_lobby(code):
    """Remove lobby from memory after a delay."""
    socketio.sleep(120)  # Keep for 2 minutes so players can see results
    lobby_games.pop(code, None)


def _abort_game(code):
    """End the game early without persisting any results."""
    lobby = lobby_games.get(code)
    if not lobby:
        return

    lobby.status = "results"

    # Build standings but don't persist
    standings = []
    for uid, p in lobby.players.items():
        standings.append(
            {
                "user_id": uid,
                "display_name": p["display_name"],
                "avatar_url": p["avatar_url"],
                "discord_id": p["discord_id"],
                "score": p["score"],
                "total": len(lobby.questions),
            }
        )
    standings.sort(key=lambda x: x["score"], reverse=True)

    # Update DB lobby status only (no TriviaWin rows)
    try:
        from models import TriviaLobby
        from database import db

        db_lobby = TriviaLobby.query.filter_by(code=code).first()
        if db_lobby:
            db_lobby.status = "finished"
            db_lobby.finished_at = datetime.now(timezone.utc)
            db.session.commit()
    except Exception as e:
        logger.error("Failed to update lobby status for aborted game %s: %s", code, e)

    socketio.emit("game_aborted", {"standings": standings}, room=code)
    logger.info("Game aborted in lobby %s by host", code)

    socketio.start_background_task(_cleanup_lobby, code)


# ==================== SOCKET EVENT HANDLERS ====================


@socketio.on("connect", namespace="/trivia")
def on_connect():
    user = _authenticate_socket()
    if not user:
        logger.warning("Trivia WS: unauthenticated connection rejected")
        return False  # Reject connection

    # Store user info on the socket session
    request.environ["trivia_user"] = user
    logger.info("Trivia WS: %s connected (sid=%s)", user.username, request.sid)

    # Send the user their DB ID so the client can identify themselves in lobby data
    emit("welcome", {"user_id": user.id})
    return True


@socketio.on("disconnect", namespace="/trivia")
def on_disconnect():
    user = request.environ.get("trivia_user")
    if not user:
        return

    # Mark player as disconnected in any lobby they're in
    for code, lobby in list(lobby_games.items()):
        if user.id in lobby.players:
            lobby.players[user.id]["connected"] = False
            lobby.players[user.id]["sid"] = None

            # Notify remaining players
            socketio.emit(
                "player_left",
                {
                    "user_id": user.id,
                    "display_name": lobby.players[user.id]["display_name"],
                    "lobby": lobby.to_dict(),
                },
                room=code,
            )

            # If host left during waiting, close the lobby
            if lobby.status == "waiting" and user.id == lobby.host_user_id:
                _close_lobby(code, "Host disconnected")
                break

            # If all players disconnected during a game, end it
            if lobby.status == "playing" and lobby.player_count() == 0:
                _end_game(code)
                break

            # If playing and all remaining players answered, advance
            if lobby.status == "playing" and _all_answered(lobby):
                _reveal_and_advance(code)

    logger.info("Trivia WS: %s disconnected", user.username if user else "unknown")


def _close_lobby(code, reason="Lobby closed"):
    """Close a lobby and notify all players."""
    lobby = lobby_games.pop(code, None)
    if not lobby:
        return

    socketio.emit("lobby_closed", {"reason": reason}, room=code)

    # Update DB
    try:
        from models import TriviaLobby
        from database import db

        db_lobby = TriviaLobby.query.filter_by(code=code).first()
        if db_lobby:
            db_lobby.status = "finished"
            db_lobby.finished_at = datetime.now(timezone.utc)
            db.session.commit()
    except Exception as e:
        logger.error("Failed to close lobby %s in DB: %s", code, e)


@socketio.on("create_lobby", namespace="/trivia")
def on_create_lobby(data):
    user = request.environ.get("trivia_user")
    if not user:
        emit("error", {"message": "Not authenticated"})
        return

    # Check if user is already in a lobby
    for code, lobby in lobby_games.items():
        if user.id in lobby.players and lobby.players[user.id]["connected"]:
            emit("error", {"message": "You are already in a lobby", "code": code})
            return

    code = _generate_code()
    if not code:
        emit("error", {"message": "Could not generate lobby code"})
        return

    settings = {
        "num_questions": min(max(int(data.get("num_questions", 10)), 5), 20),
        "difficulty": data.get("difficulty", ""),
        "category": data.get("category", ""),
        "category_name": data.get("category_name", "Any Category"),
        "max_players": min(max(int(data.get("max_players", 8)), 2), 12),
    }

    lobby = LobbyState(
        code,
        user.id,
        {
            "display_name": user.display_name or user.username,
            "avatar_url": user.avatar_url,
            "discord_id": user.discord_id,
        },
        settings,
    )
    lobby.players[user.id]["sid"] = request.sid
    lobby_games[code] = lobby

    # Persist to DB
    try:
        from models import TriviaLobby
        from database import db

        db_lobby = TriviaLobby(
            code=code,
            host_user_id=user.id,
            status="waiting",
            num_questions=settings["num_questions"],
            difficulty=settings["difficulty"],
            category=settings["category"],
            category_name=settings["category_name"],
            max_players=settings["max_players"],
        )
        db.session.add(db_lobby)
        db.session.commit()
    except Exception as e:
        logger.error("Failed to persist lobby %s: %s", code, e)

    join_room(code)
    emit("lobby_created", {"lobby": lobby.to_dict()})
    logger.info("Lobby %s created by %s", code, user.username)


@socketio.on("join_lobby", namespace="/trivia")
def on_join_lobby(data):
    user = request.environ.get("trivia_user")
    if not user:
        emit("error", {"message": "Not authenticated"})
        return

    code = str(data.get("code", "")).upper().strip()
    lobby = lobby_games.get(code)

    if not lobby:
        emit("error", {"message": "Lobby not found"})
        return

    if lobby.status != "waiting":
        emit("error", {"message": "Game already in progress"})
        return

    if lobby.player_count() >= lobby.settings.get("max_players", 8):
        emit("error", {"message": "Lobby is full"})
        return

    # Check if already in another lobby
    for other_code, other_lobby in lobby_games.items():
        if (
            other_code != code
            and user.id in other_lobby.players
            and other_lobby.players[user.id]["connected"]
        ):
            emit("error", {"message": "You are already in another lobby"})
            return

    # Rejoin if was previously in this lobby
    if user.id in lobby.players:
        lobby.players[user.id]["connected"] = True
        lobby.players[user.id]["sid"] = request.sid
    else:
        lobby.players[user.id] = {
            "sid": request.sid,
            "display_name": user.display_name or user.username,
            "avatar_url": user.avatar_url,
            "discord_id": user.discord_id,
            "score": 0,
            "answers": [],
            "connected": True,
        }

    join_room(code)
    emit("lobby_joined", {"lobby": lobby.to_dict()})

    # Notify others
    socketio.emit(
        "player_joined",
        {
            "user_id": user.id,
            "display_name": user.display_name or user.username,
            "avatar_url": user.avatar_url,
            "lobby": lobby.to_dict(),
        },
        room=code,
        skip_sid=request.sid,
    )

    logger.info("%s joined lobby %s", user.username, code)


@socketio.on("leave_lobby", namespace="/trivia")
def on_leave_lobby(data):
    user = request.environ.get("trivia_user")
    if not user:
        return

    code = str(data.get("code", "")).upper().strip()
    lobby = lobby_games.get(code)
    if not lobby or user.id not in lobby.players:
        return

    leave_room(code)
    lobby.players[user.id]["connected"] = False
    lobby.players[user.id]["sid"] = None

    # If host leaves during waiting, close lobby
    if lobby.status == "waiting" and user.id == lobby.host_user_id:
        _close_lobby(code, "Host left the lobby")
        return

    socketio.emit(
        "player_left",
        {
            "user_id": user.id,
            "display_name": lobby.players[user.id]["display_name"],
            "lobby": lobby.to_dict(),
        },
        room=code,
    )


@socketio.on("start_game", namespace="/trivia")
def on_start_game(data):
    user = request.environ.get("trivia_user")
    if not user:
        emit("error", {"message": "Not authenticated"})
        return

    code = str(data.get("code", "")).upper().strip()
    lobby = lobby_games.get(code)

    if not lobby:
        emit("error", {"message": "Lobby not found"})
        return

    if user.id != lobby.host_user_id:
        emit("error", {"message": "Only the host can start the game"})
        return

    if lobby.status != "waiting":
        emit("error", {"message": "Game already started"})
        return

    # Fetch questions
    questions = _fetch_questions(lobby.settings)
    if not questions:
        emit("error", {"message": "Could not fetch questions. Try different settings."})
        return

    lobby.questions = questions
    lobby.status = "countdown"

    # Update DB
    try:
        from models import TriviaLobby
        from database import db

        db_lobby = TriviaLobby.query.filter_by(code=code).first()
        if db_lobby:
            db_lobby.status = "playing"
            db_lobby.started_at = datetime.now(timezone.utc)
            db.session.commit()
    except Exception as e:
        logger.error("Failed to update lobby %s start status: %s", code, e)

    socketio.emit(
        "game_starting",
        {
            "countdown": COUNTDOWN_SECONDS,
            "total_questions": len(questions),
        },
        room=code,
    )

    # Start countdown then first question
    socketio.start_background_task(_start_after_countdown, code)
    logger.info(
        "Game starting in lobby %s (%d players, %d questions)",
        code,
        lobby.player_count(),
        len(questions),
    )


def _start_after_countdown(code):
    """Wait for countdown then start the first question."""
    socketio.sleep(COUNTDOWN_SECONDS)
    lobby = lobby_games.get(code)
    if not lobby or lobby.status != "countdown":
        return
    lobby.status = "playing"
    _advance_question(code)


@socketio.on("submit_answer", namespace="/trivia")
def on_submit_answer(data):
    user = request.environ.get("trivia_user")
    if not user:
        return

    code = str(data.get("code", "")).upper().strip()
    lobby = lobby_games.get(code)

    if not lobby or lobby.status != "playing":
        return

    if user.id not in lobby.players:
        return

    player = lobby.players[user.id]
    qi = lobby.current_question

    # Already answered this question
    if len(player["answers"]) > qi:
        return

    answer = data.get("answer", "")
    correct_answer = lobby.questions[qi]["correct_answer"]
    is_correct = answer == correct_answer

    if is_correct:
        # Bonus points for speed (if answered before deadline)
        player["score"] += 1

    player["answers"].append(answer)

    # Notify all players that this person answered (but not what they answered)
    socketio.emit(
        "player_answered",
        {
            "user_id": user.id,
            "question_index": qi,
            "lobby": lobby.to_dict(),
        },
        room=code,
    )

    # If all connected players have answered, reveal immediately
    if _all_answered(lobby):
        _reveal_and_advance(code)


@socketio.on("kick_player", namespace="/trivia")
def on_kick_player(data):
    user = request.environ.get("trivia_user")
    if not user:
        return

    code = str(data.get("code", "")).upper().strip()
    lobby = lobby_games.get(code)

    if not lobby or user.id != lobby.host_user_id:
        emit("error", {"message": "Only the host can kick players"})
        return

    if lobby.status != "waiting":
        emit("error", {"message": "Cannot kick during a game"})
        return

    target_id = data.get("user_id")
    if target_id == user.id:
        return  # Can't kick yourself

    if target_id in lobby.players:
        kicked = lobby.players.pop(target_id)
        # Notify the kicked player
        if kicked.get("sid"):
            socketio.emit(
                "kicked", {"reason": "You were removed from the lobby"}, room=kicked["sid"]
            )
        socketio.emit(
            "player_left",
            {
                "user_id": target_id,
                "display_name": kicked["display_name"],
                "lobby": lobby.to_dict(),
            },
            room=code,
        )


@socketio.on("end_game", namespace="/trivia")
def on_end_game(data):
    user = request.environ.get("trivia_user")
    if not user:
        return

    code = str(data.get("code", "")).upper().strip()
    lobby = lobby_games.get(code)

    if not lobby:
        emit("error", {"message": "Lobby not found"})
        return

    if user.id != lobby.host_user_id:
        emit("error", {"message": "Only the host can end the game"})
        return

    if lobby.status not in ("playing", "countdown"):
        emit("error", {"message": "No game in progress"})
        return

    _abort_game(code)


def register_trivia_rest(app):
    """Register REST endpoints for trivia lobbies on the Flask app.
    Note: This is a no-op — lobby listing is handled inside check_service()
    in webserver.py via the 'trivia-lobbies' service name. This function
    exists so the import in webserver.py doesn't break."""
    pass
