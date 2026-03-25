"""
Remote Desktop signaling system using Flask-SocketIO.

Manages WebRTC session creation, viewer connections, and SDP/ICE signaling.
All session state is ephemeral (in-memory); nothing is persisted to the database.
"""

import random
import string
import logging
import threading
import time
import jwt
from flask import request
from flask_socketio import emit, join_room, leave_room

logger = logging.getLogger(__name__)

# In-memory session state: code -> RemoteSession
remote_sessions = {}

SESSION_TIMEOUT = 1800  # 30 minutes idle timeout


class RemoteSession:
    """In-memory state for an active remote desktop session."""

    def __init__(self, code, host_user_id, host_info):
        self.code = code
        self.host_user_id = host_user_id
        self.host_sid = None
        self.host_info = host_info  # {display_name, avatar_url, discord_id}
        self.viewers = {}  # user_id -> {sid, display_name, avatar_url, discord_id, control_granted}
        self.pending_viewers = {}  # user_id -> {sid, display_name, avatar_url, discord_id}
        self.created_at = time.time()
        self.last_activity = time.time()
        self.lock = threading.Lock()

    def touch(self):
        self.last_activity = time.time()

    def is_expired(self):
        return (time.time() - self.last_activity) > SESSION_TIMEOUT

    def viewer_count(self):
        return len(self.viewers)

    def to_dict(self):
        return {
            "code": self.code,
            "host_user_id": self.host_user_id,
            "host_name": self.host_info.get("display_name", "Unknown"),
            "host_avatar": self.host_info.get("avatar_url"),
            "viewer_count": self.viewer_count(),
            "viewers": [
                {
                    "user_id": uid,
                    "display_name": v["display_name"],
                    "avatar_url": v["avatar_url"],
                    "control_granted": v.get("control_granted", False),
                }
                for uid, v in self.viewers.items()
            ],
        }


def _generate_session_code():
    """Generate a unique 6-char session code."""
    for _ in range(50):
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in remote_sessions:
            return code
    return None


def _authenticate_remote_socket():
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
        logger.error("Remote socket auth failed: %s", e)
        return None


def register_remote_ws(socketio):
    """Register all /remote namespace WebSocket event handlers."""

    @socketio.on("connect", namespace="/remote")
    def on_connect():
        user = _authenticate_remote_socket()
        if not user:
            logger.warning("Remote WS: unauthenticated connection rejected")
            return False
        request.environ["remote_user"] = user
        emit("welcome", {"user_id": user.id})
        logger.info("Remote WS: %s connected (sid=%s)", user.username, request.sid)

    @socketio.on("disconnect", namespace="/remote")
    def on_disconnect():
        user = request.environ.get("remote_user")
        if not user:
            return

        # Clean up any sessions this user was hosting or viewing
        codes_to_remove = []
        for code, session in list(remote_sessions.items()):
            with session.lock:
                if session.host_user_id == user.id and session.host_sid == request.sid:
                    # Host disconnected — end session
                    codes_to_remove.append(code)
                elif user.id in session.viewers and session.viewers[user.id]["sid"] == request.sid:
                    # Viewer disconnected
                    del session.viewers[user.id]
                    leave_room(code)
                    socketio.emit(
                        "viewer_left",
                        {"user_id": user.id, "display_name": user.display_name or user.username},
                        room=code,
                        namespace="/remote",
                    )
                elif user.id in session.pending_viewers:
                    del session.pending_viewers[user.id]

        for code in codes_to_remove:
            session = remote_sessions.pop(code, None)
            if session:
                socketio.emit(
                    "session_ended",
                    {"reason": "Host disconnected"},
                    room=code,
                    namespace="/remote",
                )
                logger.info("Remote session %s ended (host disconnected)", code)

        logger.info("Remote WS: %s disconnected (sid=%s)", user.username, request.sid)

    @socketio.on("create_session", namespace="/remote")
    def on_create_session(data=None):
        user = request.environ.get("remote_user")
        if not user:
            emit("error", {"message": "Not authenticated"})
            return

        # Check if user already hosts a session
        for code, session in remote_sessions.items():
            if session.host_user_id == user.id:
                emit("error", {"message": "You already have an active session"})
                return

        code = _generate_session_code()
        if not code:
            emit("error", {"message": "Could not generate session code"})
            return

        session = RemoteSession(
            code=code,
            host_user_id=user.id,
            host_info={
                "display_name": user.display_name or user.username,
                "avatar_url": user.avatar_url,
                "discord_id": user.discord_id,
            },
        )
        session.host_sid = request.sid
        remote_sessions[code] = session

        join_room(code)
        emit("session_created", {"session": session.to_dict()})

        # Broadcast updated session list to all connected clients
        _broadcast_sessions_list(socketio)

        logger.info("Remote session %s created by %s", code, user.username)

    @socketio.on("join_session", namespace="/remote")
    def on_join_session(data):
        user = request.environ.get("remote_user")
        if not user:
            emit("error", {"message": "Not authenticated"})
            return

        code = (data or {}).get("code", "").strip().upper()
        session = remote_sessions.get(code)
        if not session:
            emit("error", {"message": "Session not found"})
            return

        if session.host_user_id == user.id:
            emit("error", {"message": "You cannot join your own session"})
            return

        with session.lock:
            if user.id in session.viewers:
                emit("error", {"message": "Already in this session"})
                return

            # Add to pending — host must approve
            session.pending_viewers[user.id] = {
                "sid": request.sid,
                "display_name": user.display_name or user.username,
                "avatar_url": user.avatar_url,
                "discord_id": user.discord_id,
            }
            session.touch()

        # Notify host of join request
        if session.host_sid:
            socketio.emit(
                "viewer_request",
                {
                    "user_id": user.id,
                    "display_name": user.display_name or user.username,
                    "avatar_url": user.avatar_url,
                },
                room=session.host_sid,
                namespace="/remote",
            )

        emit("join_pending", {"code": code, "message": "Waiting for host approval..."})
        logger.info("Remote: %s requested to join session %s", user.username, code)

    @socketio.on("approve_viewer", namespace="/remote")
    def on_approve_viewer(data):
        user = request.environ.get("remote_user")
        if not user:
            emit("error", {"message": "Not authenticated"})
            return

        code = (data or {}).get("code", "").strip().upper()
        viewer_user_id = (data or {}).get("user_id")
        session = remote_sessions.get(code)
        if not session or session.host_user_id != user.id:
            emit("error", {"message": "Not the host of this session"})
            return

        with session.lock:
            pending = session.pending_viewers.pop(viewer_user_id, None)
            if not pending:
                emit("error", {"message": "No pending request from this user"})
                return

            session.viewers[viewer_user_id] = {
                **pending,
                "control_granted": False,
            }
            session.touch()

        # Add viewer to the room
        viewer_sid = pending["sid"]
        socketio.server.enter_room(viewer_sid, code, namespace="/remote")

        # Notify the viewer they were approved
        socketio.emit(
            "join_approved",
            {"session": session.to_dict()},
            room=viewer_sid,
            namespace="/remote",
        )

        # Notify everyone in the room
        socketio.emit(
            "viewer_joined",
            {
                "user_id": viewer_user_id,
                "display_name": pending["display_name"],
                "avatar_url": pending["avatar_url"],
                "session": session.to_dict(),
            },
            room=code,
            namespace="/remote",
        )

        _broadcast_sessions_list(socketio)
        logger.info("Remote: viewer %d approved in session %s", viewer_user_id, code)

    @socketio.on("deny_viewer", namespace="/remote")
    def on_deny_viewer(data):
        user = request.environ.get("remote_user")
        if not user:
            emit("error", {"message": "Not authenticated"})
            return

        code = (data or {}).get("code", "").strip().upper()
        viewer_user_id = (data or {}).get("user_id")
        session = remote_sessions.get(code)
        if not session or session.host_user_id != user.id:
            emit("error", {"message": "Not the host of this session"})
            return

        with session.lock:
            pending = session.pending_viewers.pop(viewer_user_id, None)

        if pending and pending.get("sid"):
            socketio.emit(
                "join_denied",
                {"reason": "Host denied your request"},
                room=pending["sid"],
                namespace="/remote",
            )

    @socketio.on("toggle_control", namespace="/remote")
    def on_toggle_control(data):
        user = request.environ.get("remote_user")
        if not user:
            emit("error", {"message": "Not authenticated"})
            return

        code = (data or {}).get("code", "").strip().upper()
        viewer_user_id = (data or {}).get("user_id")
        session = remote_sessions.get(code)
        if not session or session.host_user_id != user.id:
            emit("error", {"message": "Not the host of this session"})
            return

        with session.lock:
            viewer = session.viewers.get(viewer_user_id)
            if not viewer:
                emit("error", {"message": "Viewer not found"})
                return
            viewer["control_granted"] = not viewer["control_granted"]
            granted = viewer["control_granted"]
            session.touch()

        # Notify the viewer
        if viewer.get("sid"):
            socketio.emit(
                "control_toggled",
                {"granted": granted},
                room=viewer["sid"],
                namespace="/remote",
            )

        # Notify everyone
        socketio.emit(
            "session_updated",
            {"session": session.to_dict()},
            room=code,
            namespace="/remote",
        )

        logger.info(
            "Remote: control %s for viewer %d in session %s",
            "granted" if granted else "revoked",
            viewer_user_id,
            code,
        )

    @socketio.on("signal", namespace="/remote")
    def on_signal(data):
        """Relay WebRTC signaling data (SDP offers/answers, ICE candidates)."""
        user = request.environ.get("remote_user")
        if not user:
            emit("error", {"message": "Not authenticated"})
            return

        code = (data or {}).get("code", "").strip().upper()
        target_user_id = (data or {}).get("target_user_id")
        signal_data = (data or {}).get("signal")
        session = remote_sessions.get(code)
        if not session:
            emit("error", {"message": "Session not found"})
            return

        session.touch()

        # Find target SID
        target_sid = None
        if target_user_id == session.host_user_id:
            target_sid = session.host_sid
        elif target_user_id in session.viewers:
            target_sid = session.viewers[target_user_id].get("sid")

        if not target_sid:
            emit("error", {"message": "Target user not in session"})
            return

        socketio.emit(
            "signal",
            {
                "from_user_id": user.id,
                "signal": signal_data,
            },
            room=target_sid,
            namespace="/remote",
        )

    @socketio.on("input_event", namespace="/remote")
    def on_input_event(data):
        """Relay mouse/keyboard input from viewer to host."""
        user = request.environ.get("remote_user")
        if not user:
            return

        code = (data or {}).get("code", "").strip().upper()
        session = remote_sessions.get(code)
        if not session:
            return

        # Only relay if this viewer has control
        viewer = session.viewers.get(user.id)
        if not viewer or not viewer.get("control_granted"):
            return

        session.touch()

        if session.host_sid:
            socketio.emit(
                "input_event",
                {
                    "from_user_id": user.id,
                    "event": (data or {}).get("event"),
                },
                room=session.host_sid,
                namespace="/remote",
            )

    @socketio.on("end_session", namespace="/remote")
    def on_end_session(data):
        user = request.environ.get("remote_user")
        if not user:
            emit("error", {"message": "Not authenticated"})
            return

        code = (data or {}).get("code", "").strip().upper()
        session = remote_sessions.get(code)
        if not session or session.host_user_id != user.id:
            emit("error", {"message": "Not the host of this session"})
            return

        remote_sessions.pop(code, None)
        socketio.emit(
            "session_ended",
            {"reason": "Host ended the session"},
            room=code,
            namespace="/remote",
        )
        _broadcast_sessions_list(socketio)
        logger.info("Remote session %s ended by host", code)

    @socketio.on("leave_session", namespace="/remote")
    def on_leave_session(data):
        user = request.environ.get("remote_user")
        if not user:
            return

        code = (data or {}).get("code", "").strip().upper()
        session = remote_sessions.get(code)
        if not session:
            return

        with session.lock:
            if user.id in session.viewers:
                del session.viewers[user.id]
            elif user.id in session.pending_viewers:
                del session.pending_viewers[user.id]
            else:
                return

        leave_room(code)
        socketio.emit(
            "viewer_left",
            {"user_id": user.id, "display_name": user.display_name or user.username},
            room=code,
            namespace="/remote",
        )
        _broadcast_sessions_list(socketio)
        emit("left_session", {"code": code})


def _broadcast_sessions_list(socketio):
    """Broadcast the current active sessions list to all connected /remote clients."""
    sessions_list = []
    for code, s in remote_sessions.items():
        if not s.is_expired():
            sessions_list.append(s.to_dict())
    socketio.emit("sessions_list", {"sessions": sessions_list}, namespace="/remote")


def cleanup_expired_sessions(socketio):
    """Remove expired sessions. Called periodically."""
    expired = [code for code, s in remote_sessions.items() if s.is_expired()]
    for code in expired:
        session = remote_sessions.pop(code, None)
        if session:
            socketio.emit(
                "session_ended",
                {"reason": "Session timed out"},
                room=code,
                namespace="/remote",
            )
            logger.info("Remote session %s expired", code)
    if expired:
        _broadcast_sessions_list(socketio)
