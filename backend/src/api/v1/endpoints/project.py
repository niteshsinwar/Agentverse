"""
Project Structure API Endpoints
Dynamic project tree visualization and analysis
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from dataclasses import dataclass, asdict

router = APIRouter()


@dataclass
class FileInfo:
    """File information structure"""
    name: str
    type: str  # 'file' or 'directory'
    size: Optional[int] = None
    modified: Optional[str] = None
    lines: Optional[int] = None
    extension: Optional[str] = None
    children: Optional[List['FileInfo']] = None


class ProjectTreeGenerator:
    """Generate dynamic project tree structure"""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.ignore_patterns = {
            '__pycache__', '.git', '.env', 'node_modules', '.DS_Store',
            '*.pyc', '*.pyo', '*.egg-info', 'logs', 'data'
        }

    def generate_tree(self, include_stats: bool = True) -> Dict[str, Any]:
        """Generate complete project tree"""

        tree_data = {
            "project_name": "Agentverse Backend",
            "root_path": str(self.root_path),
            "generated_at": datetime.now().isoformat(),
            "structure": self._build_tree_node(self.root_path, include_stats),
            "statistics": self._calculate_statistics() if include_stats else None
        }

        return tree_data

    def _build_tree_node(self, path: Path, include_stats: bool) -> FileInfo:
        """Build tree node recursively"""

        if path.is_file():
            return self._create_file_info(path, include_stats)

        # Directory
        children = []
        try:
            for item in sorted(path.iterdir()):
                if self._should_ignore(item):
                    continue

                child_node = self._build_tree_node(item, include_stats)
                children.append(child_node)

        except PermissionError:
            pass  # Skip directories we can't read

        return FileInfo(
            name=path.name or "root",
            type="directory",
            children=children
        )

    def _create_file_info(self, path: Path, include_stats: bool) -> FileInfo:
        """Create file info object"""

        file_info = FileInfo(
            name=path.name,
            type="file",
            extension=path.suffix if path.suffix else None
        )

        if include_stats:
            try:
                stat = path.stat()
                file_info.size = stat.st_size
                file_info.modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

                # Count lines for text files
                if path.suffix in ['.py', '.js', '.ts', '.html', '.css', '.json', '.yaml', '.yml', '.md', '.txt','.png']:
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            file_info.lines = sum(1 for _ in f)
                    except:
                        file_info.lines = None

            except (OSError, IOError):
                pass

        return file_info

    def _should_ignore(self, path: Path) -> bool:
        """Check if path should be ignored"""
        name = path.name

        # Ignore hidden files/directories
        if name.startswith('.') and name not in ['.env.example']:
            return True

        # Ignore specific patterns
        if name in self.ignore_patterns:
            return True

        # Ignore log files and databases
        if name.endswith(('.log', '.db', '.db-wal', '.db-shm')):
            return True

        return False

    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate project statistics"""

        stats = {
            "total_files": 0,
            "total_directories": 0,
            "total_lines": 0,
            "total_size_bytes": 0,
            "file_types": {},
            "language_stats": {}
        }

        self._collect_stats(self.root_path, stats)

        # Calculate derived statistics
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        stats["avg_file_size_bytes"] = (
            round(stats["total_size_bytes"] / stats["total_files"], 2)
            if stats["total_files"] > 0 else 0
        )

        return stats

    def _collect_stats(self, path: Path, stats: Dict[str, Any]):
        """Recursively collect statistics"""

        if self._should_ignore(path):
            return

        if path.is_file():
            stats["total_files"] += 1

            # File size
            try:
                size = path.stat().st_size
                stats["total_size_bytes"] += size
            except:
                pass

            # File extension
            ext = path.suffix.lower()
            if ext:
                stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1

            # Language-specific stats
            language = self._get_language_from_extension(ext)
            if language:
                if language not in stats["language_stats"]:
                    stats["language_stats"][language] = {"files": 0, "lines": 0}

                stats["language_stats"][language]["files"] += 1

                # Count lines
                if ext in ['.py', '.js', '.ts', '.html', '.css', '.json', '.yaml', '.yml','.png']:
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = sum(1 for _ in f)
                            stats["total_lines"] += lines
                            stats["language_stats"][language]["lines"] += lines
                    except:
                        pass

        elif path.is_dir():
            stats["total_directories"] += 1
            try:
                for item in path.iterdir():
                    self._collect_stats(item, stats)
            except PermissionError:
                pass

    def _get_language_from_extension(self, ext: str) -> Optional[str]:
        """Map file extension to programming language"""

        language_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.txt': 'Text',
            '.sql': 'SQL',
            '.sh': 'Shell'
        }

        return language_map.get(ext)


@router.get("/tree")
async def get_project_tree(
    include_stats: bool = True,
    format_type: str = "detailed"  # "detailed" or "simple"
):
    """
    Get dynamic project tree structure.

    Returns the complete backend project structure with optional statistics.
    """
    try:
        # Get project root (backend directory)
        current_file = Path(__file__)
        backend_root = current_file.parent.parent.parent.parent.parent  # Navigate to backend root

        generator = ProjectTreeGenerator(backend_root)
        tree_data = generator.generate_tree(include_stats)

        if format_type == "simple":
            # Return simplified version without detailed file info
            tree_data["structure"] = _simplify_tree(tree_data["structure"])

        return tree_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate project tree: {str(e)}")


@router.get("/structure/analysis")
async def analyze_project_structure():
    """
    Analyze project structure for best practices.

    Returns analysis of the project structure including recommendations.
    """
    try:
        current_file = Path(__file__)
        backend_root = current_file.parent.parent.parent.parent.parent

        generator = ProjectTreeGenerator(backend_root)
        tree_data = generator.generate_tree(include_stats=True)

        analysis = {
            "structure_health": _analyze_structure_health(tree_data),
            "recommendations": _get_structure_recommendations(tree_data),
            "complexity_score": _calculate_complexity_score(tree_data),
            "maintainability_score": _calculate_maintainability_score(tree_data),
            "generated_at": datetime.now().isoformat()
        }

        return analysis

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze structure: {str(e)}")


def _simplify_tree(node: FileInfo) -> Dict[str, Any]:
    """Simplify tree structure for basic viewing"""

    simplified = {
        "name": node.name,
        "type": node.type
    }

    if node.children:
        simplified["children"] = [_simplify_tree(child) for child in node.children]

    return simplified


def _analyze_structure_health(tree_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze the health of project structure"""

    stats = tree_data.get("statistics", {})

    health = {
        "overall_score": 85,  # Would calculate based on various metrics
        "issues": [],
        "strengths": []
    }

    # Check for issues
    if stats.get("total_files", 0) > 200:
        health["issues"].append("High file count - consider further modularization")

    if len(stats.get("file_types", {})) < 3:
        health["issues"].append("Limited file type diversity")

    # Check for strengths
    if "Python" in stats.get("language_stats", {}):
        health["strengths"].append("Well-structured Python codebase")

    if stats.get("total_directories", 0) > 10:
        health["strengths"].append("Good modular organization")

    return health


def _get_structure_recommendations(tree_data: Dict[str, Any]) -> List[str]:
    """Get recommendations for improving project structure"""

    recommendations = [
        "Consider adding API versioning for future compatibility",
        "Implement comprehensive error handling middleware",
        "Add automated code quality checks",
        "Consider implementing caching layer for better performance"
    ]

    return recommendations


def _calculate_complexity_score(tree_data: Dict[str, Any]) -> float:
    """Calculate project complexity score (0-100)"""

    stats = tree_data.get("statistics", {})

    # Simple complexity calculation based on various factors
    file_complexity = min(stats.get("total_files", 0) / 10, 10)
    dir_complexity = min(stats.get("total_directories", 0) / 5, 10)

    return round((file_complexity + dir_complexity) * 5, 1)


def _calculate_maintainability_score(tree_data: Dict[str, Any]) -> float:
    """Calculate maintainability score (0-100)"""

    # Higher is better for maintainability
    base_score = 75

    stats = tree_data.get("statistics", {})

    # Bonus for good organization
    if stats.get("total_directories", 0) >= 8:
        base_score += 5

    # Bonus for reasonable file sizes
    avg_size = stats.get("avg_file_size_bytes", 0)
    if 500 <= avg_size <= 5000:  # Reasonable file sizes
        base_score += 5

    return min(base_score, 100.0)