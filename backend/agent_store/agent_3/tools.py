# Custom Tools
from __future__ import annotations
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.core.agents.base_agent import agent_tool
from src.core.config.settings import get_settings; settings = get_settings()

# All operations are confined to this base directory (from config.yaml -> paths.workspace)
BASE_ROOT = Path(settings.PATHS.get("workspace", "./workspace")).resolve()
BASE_ROOT.mkdir(parents=True, exist_ok=True)

def _safe_path(p: str) -> Path:
    """Resolve a user path inside BASE_ROOT. Raises on escape attempts."""
    if not p:
        p = "."
    candidate = (BASE_ROOT / p.lstrip("/\\")).resolve()
    base = BASE_ROOT
    if str(candidate) != str(base) and not str(candidate).startswith(str(base) + os.sep):
        raise ValueError(f"Path escapes workspace: {candidate}")
    return candidate

def _file_info(p: Path) -> Dict[str, Any]:
    """Get file/directory information."""
    try:
        stat = p.stat()
        return {
            "name": p.name,
            "path": str(p.relative_to(BASE_ROOT)),
            "is_dir": p.is_dir(),
            "is_file": p.is_file(),
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:],
            "exists": True
        }
    except Exception as e:
        return {
            "name": p.name,
            "path": str(p.relative_to(BASE_ROOT)),
            "is_dir": False,
            "is_file": False,
            "size": 0,
            "modified": 0,
            "permissions": "000",
            "exists": False,
            "error": str(e)
        }

@agent_tool
def get_workspace_info() -> Dict[str, Any]:
    """Get information about the workspace sandbox directory."""
    return {
        "workspace_root": str(BASE_ROOT),
        "workspace_exists": BASE_ROOT.exists(),
        "workspace_size": len(list(BASE_ROOT.rglob("*"))) if BASE_ROOT.exists() else 0,
        "description": f"All file operations are sandboxed to: {BASE_ROOT}"
    }

@agent_tool
def get_absolute_path(relative_path: str = ".") -> str:
    """Get the absolute path of a file/folder within the workspace sandbox.
    
    Args:
        relative_path: Path relative to workspace root (default: current workspace)
    
    Returns:
        Absolute path within the sandbox
    """
    try:
        safe_path = _safe_path(relative_path)
        return str(safe_path)
    except ValueError as e:
        return f"Error: {e}"

@agent_tool
def ls(path: str = ".") -> Dict[str, Any]:
    """List directory entries under workspace. Returns metadata per entry."""
    p = _safe_path(path)
    if not p.exists():
        return {"ok": False, "error": f"Not found: {path}"}
    if p.is_file():
        return {"ok": True, "entries": [_file_info(p)]}
    entries = sorted([_file_info(x) for x in p.iterdir()], key=lambda x: (not x["is_dir"], x["name"].lower()))
    return {"ok": True, "cwd": str(p.relative_to(BASE_ROOT)), "entries": entries}

@agent_tool
def read_file(path: str, encoding: str = "utf-8", max_bytes: int = 1_000_000) -> Dict[str, Any]:
    """Read a text file. Truncates beyond max_bytes for safety."""
    p = _safe_path(path)
    if not p.exists() or not p.is_file():
        return {"ok": False, "error": f"File not found: {path}"}
    data = p.read_bytes()
    truncated = False
    if len(data) > max_bytes:
        data = data[:max_bytes]
        truncated = True
    try:
        text = data.decode(encoding, errors="replace")
    except Exception as e:
        return {"ok": False, "error": f"Decode error: {e}"}
    return {"ok": True, "path": str(p.relative_to(BASE_ROOT)), "truncated": truncated, "content": text}

@agent_tool
def write_file(path: str, content: str, encoding: str = "utf-8", overwrite: bool = True) -> Dict[str, Any]:
    """Write text to a file; creates parents. Set overwrite=False to error on existing."""
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists() and not overwrite:
        return {"ok": False, "error": "File exists and overwrite=False"}
    p.write_text(content, encoding=encoding)
    return {"ok": True, "bytes": len(content.encode(encoding)), "path": str(p.relative_to(BASE_ROOT))}

@agent_tool
def append_file(path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """Append text to a file; creates file and parents if needed."""
    p = _safe_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding=encoding) as f:
        f.write(content)
    return {"ok": True, "path": str(p.relative_to(BASE_ROOT))}

@agent_tool
def mkdir(path: str, parents: bool = True, exist_ok: bool = True) -> Dict[str, Any]:
    """Create a directory within the workspace sandbox."""
    p = _safe_path(path)
    p.mkdir(parents=parents, exist_ok=exist_ok)
    return {
        "ok": True, 
        "relative_path": str(p.relative_to(BASE_ROOT)),
        "absolute_path": str(p),
        "workspace_root": str(BASE_ROOT)
    }

@agent_tool
def rm(path: str, recursive: bool = False) -> Dict[str, Any]:
    """Remove a file or (with recursive=True) a directory tree."""
    p = _safe_path(path)
    if not p.exists():
        return {"ok": True, "note": "Path did not exist", "path": str(p.relative_to(BASE_ROOT))}
    if p.is_dir():
        if recursive:
            shutil.rmtree(p)
        else:
            try:
                p.rmdir()
            except OSError:
                return {"ok": False, "error": "Directory not empty. Set recursive=True."}
    else:
        p.unlink()
    return {"ok": True, "path": str(p.relative_to(BASE_ROOT))}

@agent_tool
def mv(src: str, dst: str, overwrite: bool = True) -> Dict[str, Any]:
    s = _safe_path(src)
    d = _safe_path(dst)
    d.parent.mkdir(parents=True, exist_ok=True)
    if d.exists() and not overwrite:
        return {"ok": False, "error": "Destination exists and overwrite=False"}
    shutil.move(str(s), str(d))
    return {"ok": True, "from": str(s.relative_to(BASE_ROOT)), "to": str(d.relative_to(BASE_ROOT))}

@agent_tool
def cp(src: str, dst: str, recursive: bool = True, overwrite: bool = True) -> Dict[str, Any]:
    s = _safe_path(src)
    d = _safe_path(dst)
    d.parent.mkdir(parents=True, exist_ok=True)
    if d.exists() and not overwrite:
        return {"ok": False, "error": "Destination exists and overwrite=False"}
    if s.is_dir():
        if not recursive:
            return {"ok": False, "error": "Source is directory; set recursive=True"}
        if d.exists():
            shutil.rmtree(d)
        shutil.copytree(s, d)
    else:
        shutil.copy2(s, d)
    return {"ok": True, "from": str(s.relative_to(BASE_ROOT)), "to": str(d.relative_to(BASE_ROOT))}

@agent_tool
def glob(pattern: str) -> Dict[str, Any]:
    """Glob within workspace (e.g., '**/*.py'). Returns relative paths."""
    matches = [str(p.relative_to(BASE_ROOT)) for p in BASE_ROOT.glob(pattern)]
    return {"ok": True, "count": len(matches), "matches": matches}

@agent_tool
def stat_path(path: str) -> Dict[str, Any]:
    p = _safe_path(path)
    if not p.exists():
        return {"ok": False, "error": "Not found"}
    return {"ok": True, **_file_info(p)}

@agent_tool
def tail(path: str, n: int = 100, encoding: str = "utf-8") -> Dict[str, Any]:
    """Return last N lines of a text file."""
    p = _safe_path(path)
    if not p.exists() or not p.is_file():
        return {"ok": False, "error": "File not found"}
    with p.open("r", encoding=encoding, errors="replace") as f:
        buf = f.readlines()[-n:]
    return {"ok": True, "path": str(p.relative_to(BASE_ROOT)), "lines": buf}

