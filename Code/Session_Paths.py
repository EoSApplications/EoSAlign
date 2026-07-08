import os
import re
import sys
import json
import shutil
from pathlib import Path
from uuid import uuid4


Session_Environment_Variable = "EOSALIGN_SESSION_ID"
Session_Registry_Directory_Name = ".sessions"


def get_user_data_root():
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")))
    elif sys.platform == "darwin":
        base = Path(os.path.expanduser("~/Library/Application Support"))
    elif sys.platform == "linux":
        base = Path(os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share")))
    else:
        base = Path(os.path.expanduser("~/.local/share"))

    new_root = base / "EoSApplications"
    # Migrate a pre-rename install (this folder used to be named "EoS") so existing session
    # registry/figures/manual-entry data isn't silently orphaned in the old folder
    legacy_root = base / "EoS"
    if not new_root.exists() and legacy_root.exists():
        try:
            os.rename(legacy_root, new_root)
        except OSError:
            pass
    return new_root


def Safe_Path_Component(value):
    text = str(value or "").strip()
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", text)
    text = text.strip("._")
    return text or "session"


def hide_path_from_file_explorer(path):
    if sys.platform != "win32":
        return
    try:
        import ctypes

        hidden_attribute = 0x02
        existing_attributes = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if existing_attributes != -1:
            ctypes.windll.kernel32.SetFileAttributesW(
                str(path),
                existing_attributes | hidden_attribute,
            )
    except Exception:
        pass


def ensure_hidden_directory(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    hide_path_from_file_explorer(path)
    return path


def Session_Registry_Directory(create=True):
    path = get_user_data_root() / Session_Registry_Directory_Name
    if create:
        return ensure_hidden_directory(path)
    return path


def Session_Record_Path(session_id=None, create=True):
    session_id = Safe_Path_Component(session_id or get_current_session_id())
    return Session_Registry_Directory(create=create) / f"{session_id}.json"


def Write_Session_Record(session_id):
    record_path = Session_Record_Path(session_id=session_id, create=True)
    tmp_path = record_path.with_suffix(".tmp")
    payload = {
        "session_id": session_id,
        "pid": os.getpid(),
    }
    with open(tmp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle)
    os.replace(tmp_path, record_path)
    hide_path_from_file_explorer(record_path)


def Load_Session_Record(record_path):
    try:
        with open(record_path, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return None


def Is_Pid_Running(pid):
    try:
        pid = int(pid)
    except Exception:
        return False
    if pid <= 0:
        return False

    if sys.platform == "win32":
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            kernel32.CloseHandle(handle)
            return True
        except Exception:
            return False

    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def sweep_stale_session_directories():
    active_session_ids = set()
    stale_session_ids = set()
    registry_dir = Session_Registry_Directory(create=True)

    for record_path in registry_dir.glob("*.json"):
        session_id = record_path.stem
        record = Load_Session_Record(record_path)
        pid = record.get("pid") if isinstance(record, dict) else None
        if Is_Pid_Running(pid):
            active_session_ids.add(session_id)
        else:
            stale_session_ids.add(session_id)

    discovered_session_ids = set()
    for subdir_name in (".figures", ".Manual_Entry_Data_Files"):
        root = ensure_hidden_directory(get_user_data_root() / subdir_name)
        for child in root.iterdir():
            if child.is_dir():
                discovered_session_ids.add(child.name)

    removable_session_ids = (discovered_session_ids - active_session_ids) | stale_session_ids

    for subdir_name in (".figures", ".Manual_Entry_Data_Files"):
        root = ensure_hidden_directory(get_user_data_root() / subdir_name)
        for session_id in removable_session_ids:
            target = root / session_id
            if target.is_dir():
                try:
                    shutil.rmtree(target)
                except Exception:
                    pass

    for session_id in removable_session_ids:
        record_path = registry_dir / f"{session_id}.json"
        if record_path.exists():
            try:
                record_path.unlink()
            except Exception:
                pass


def start_new_session():
    session_id = uuid4().hex
    os.environ[Session_Environment_Variable] = session_id
    Write_Session_Record(session_id)
    return session_id


def get_current_session_id():
    session_id = os.environ.get(Session_Environment_Variable)
    if not session_id:
        session_id = start_new_session()
    return session_id


def get_session_directory(subdir_name, *extra_parts, create=True):
    root = ensure_hidden_directory(get_user_data_root() / subdir_name)
    session_dir = root / Safe_Path_Component(get_current_session_id())
    for part in extra_parts:
        session_dir /= Safe_Path_Component(part)
    if create:
        ensure_hidden_directory(session_dir)
    return session_dir


def cleanup_current_session_directories():
    session_id = Safe_Path_Component(get_current_session_id())
    for subdir_name in (".figures", ".Manual_Entry_Data_Files"):
        target = get_session_directory(subdir_name, create=False)
        if target.is_dir():
            try:
                shutil.rmtree(target)
            except Exception:
                pass
    record_path = Session_Record_Path(session_id=session_id, create=False)
    if record_path.exists():
        try:
            record_path.unlink()
        except Exception:
            pass
