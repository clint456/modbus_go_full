"""历史记录管理模块。"""

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class HistoryEntry:
    """历史记录条目。"""

    timestamp: datetime
    event_type: str
    description: str
    details: dict


class HistoryManager:
    """历史记录管理器。"""

    def __init__(self, max_size: int = 1000):
        """初始化历史记录管理器。

        Args:
            max_size: 最大记录数量
        """
        self.max_size = max_size
        self.entries: List[HistoryEntry] = []

    def add_entry(self, event_type: str, description: str, details: dict = None) -> None:
        """添加历史记录。

        Args:
            event_type: 事件类型
            description: 描述
            details: 详细信息
        """
        entry = HistoryEntry(
            timestamp=datetime.now(),
            event_type=event_type,
            description=description,
            details=details or {},
        )
        self.entries.append(entry)

        # 保持最大记录数限制
        if len(self.entries) > self.max_size:
            self.entries.pop(0)

    def get_entries(self, limit: int = 100) -> List[dict]:
        """获取历史记录。

        Args:
            limit: 返回的最大记录数

        Returns:
            历史记录列表
        """
        entries = self.entries[-limit:]
        return [
            {
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "description": e.description,
                "details": e.details,
            }
            for e in entries
        ]

    def clear(self) -> None:
        """清空历史记录。"""
        self.entries.clear()
