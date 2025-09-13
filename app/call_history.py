#!/usr/bin/env python3
"""
Call history tracking for the SIP AI Agent.

This module provides comprehensive call history tracking with persistence,
analytics, and export functionality for the web dashboard.
"""

import json
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from logging_config import get_logger

logger = get_logger("call_history")


class CallHistoryItem:
    """Represents a single call history entry."""

    def __init__(
        self,
        call_id: str,
        caller: Optional[str] = None,
        callee: Optional[str] = None,
        direction: str = "incoming",
        start_time: Optional[float] = None,
    ):
        self.call_id = call_id
        self.caller = caller
        self.callee = callee
        self.direction = direction
        self.start_time = start_time or time.time()
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        self.status = "active"
        self.tokens_used = 0
        self.cost = 0.0
        self.audio_quality_metrics: Dict[str, Any] = {}
        self.error_message: Optional[str] = None

    def end_call(self, status: str = "completed", error_message: Optional[str] = None):
        """End the call and calculate duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = status
        self.error_message = error_message
        logger.info(
            "Call ended",
            call_id=self.call_id,
            duration=self.duration,
            status=status,
        )

    def update_tokens(self, tokens: int):
        """Update token usage for the call."""
        self.tokens_used += tokens
        logger.debug(
            "Token usage updated",
            call_id=self.call_id,
            tokens_added=tokens,
            total_tokens=self.tokens_used,
        )

    def update_audio_quality(self, metrics: Dict[str, Any]):
        """Update audio quality metrics."""
        self.audio_quality_metrics.update(metrics)
        logger.debug(
            "Audio quality updated",
            call_id=self.call_id,
            metrics=metrics,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "call_id": self.call_id,
            "caller": self.caller,
            "callee": self.callee,
            "direction": self.direction,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "status": self.status,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "audio_quality_metrics": self.audio_quality_metrics,
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CallHistoryItem":
        """Create from dictionary."""
        item = cls(
            call_id=data["call_id"],
            caller=data.get("caller"),
            callee=data.get("callee"),
            direction=data.get("direction", "incoming"),
            start_time=data.get("start_time"),
        )
        item.end_time = data.get("end_time")
        item.duration = data.get("duration")
        item.status = data.get("status", "completed")
        item.tokens_used = data.get("tokens_used", 0)
        item.cost = data.get("cost", 0.0)
        item.audio_quality_metrics = data.get("audio_quality_metrics", {})
        item.error_message = data.get("error_message")
        return item


class CallHistoryManager:
    """Manages call history with persistence and analytics."""

    def __init__(self, history_file: str = "call_history.json", max_history: int = 1000):
        self.history_file = history_file
        self.max_history = max_history
        self.active_calls: Dict[str, CallHistoryItem] = {}
        self.call_history: List[CallHistoryItem] = []
        self.load_history()

    def start_call(
        self,
        call_id: str,
        caller: Optional[str] = None,
        callee: Optional[str] = None,
        direction: str = "incoming",
    ) -> CallHistoryItem:
        """Start tracking a new call."""
        if call_id in self.active_calls:
            logger.warning("Call already exists", call_id=call_id)
            return self.active_calls[call_id]

        call_item = CallHistoryItem(
            call_id=call_id,
            caller=caller,
            callee=callee,
            direction=direction,
        )

        self.active_calls[call_id] = call_item
        logger.info(
            "Call started",
            call_id=call_id,
            caller=caller,
            callee=callee,
            direction=direction,
        )

        return call_item

    def end_call(
        self,
        call_id: str,
        status: str = "completed",
        error_message: Optional[str] = None,
    ) -> Optional[CallHistoryItem]:
        """End a call and move it to history."""
        if call_id not in self.active_calls:
            logger.warning("Call not found in active calls", call_id=call_id)
            return None

        call_item = self.active_calls.pop(call_id)
        call_item.end_call(status, error_message)

        # Add to history
        self.call_history.append(call_item)

        # Trim history if it exceeds max
        if len(self.call_history) > self.max_history:
            self.call_history = self.call_history[-self.max_history :]

        # Save to disk
        self.save_history()

        logger.info(
            "Call ended and moved to history",
            call_id=call_id,
            duration=call_item.duration,
            status=status,
        )

        return call_item

    def update_call_tokens(self, call_id: str, tokens: int):
        """Update token usage for an active call."""
        if call_id in self.active_calls:
            self.active_calls[call_id].update_tokens(tokens)

    def update_call_audio_quality(self, call_id: str, metrics: Dict[str, Any]):
        """Update audio quality metrics for an active call."""
        if call_id in self.active_calls:
            self.active_calls[call_id].update_audio_quality(metrics)

    def get_active_calls(self) -> List[CallHistoryItem]:
        """Get list of active calls."""
        return list(self.active_calls.values())

    def get_call_history(
        self, limit: Optional[int] = None, status_filter: Optional[str] = None
    ) -> List[CallHistoryItem]:
        """Get call history with optional filtering."""
        history = self.call_history.copy()

        if status_filter:
            history = [call for call in history if call.status == status_filter]

        if limit:
            history = history[-limit:]

        return history

    def get_call_statistics(self) -> Dict[str, Any]:
        """Get call statistics for analytics."""
        if not self.call_history:
            return {
                "total_calls": 0,
                "completed_calls": 0,
                "failed_calls": 0,
                "average_duration": 0.0,
                "total_duration": 0.0,
                "total_tokens": 0,
                "total_cost": 0.0,
            }

        completed_calls = [call for call in self.call_history if call.status == "completed"]
        failed_calls = [call for call in self.call_history if call.status == "failed"]

        total_duration = sum(
            call.duration for call in completed_calls if call.duration
        )
        total_tokens = sum(call.tokens_used for call in self.call_history)
        total_cost = sum(call.cost for call in self.call_history)

        return {
            "total_calls": len(self.call_history),
            "completed_calls": len(completed_calls),
            "failed_calls": len(failed_calls),
            "active_calls": len(self.active_calls),
            "average_duration": total_duration / len(completed_calls) if completed_calls else 0.0,
            "total_duration": total_duration,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "success_rate": len(completed_calls) / len(self.call_history) if self.call_history else 0.0,
        }

    def export_to_csv(self, filepath: str) -> str:
        """Export call history to CSV file."""
        import csv

        with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = [
                "call_id",
                "caller",
                "callee",
                "direction",
                "start_time",
                "end_time",
                "duration",
                "status",
                "tokens_used",
                "cost",
                "error_message",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for call in self.call_history:
                row = {
                    "call_id": call.call_id,
                    "caller": call.caller or "",
                    "callee": call.callee or "",
                    "direction": call.direction,
                    "start_time": datetime.fromtimestamp(call.start_time).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "end_time": datetime.fromtimestamp(call.end_time).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    if call.end_time
                    else "",
                    "duration": call.duration or "",
                    "status": call.status,
                    "tokens_used": call.tokens_used,
                    "cost": call.cost,
                    "error_message": call.error_message or "",
                }
                writer.writerow(row)

        logger.info("Call history exported to CSV", filepath=filepath)
        return filepath

    def load_history(self):
        """Load call history from disk."""
        if not os.path.exists(self.history_file):
            logger.info("No existing call history file found")
            return

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.call_history = [
                    CallHistoryItem.from_dict(item) for item in data.get("history", [])
                ]
                logger.info(
                    "Call history loaded",
                    total_calls=len(self.call_history),
                    file=self.history_file,
                )
        except Exception as e:
            logger.error("Failed to load call history", error=str(e))
            self.call_history = []

    def save_history(self):
        """Save call history to disk."""
        try:
            data = {
                "history": [call.to_dict() for call in self.call_history],
                "last_updated": time.time(),
                "version": "1.0",
            }

            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug("Call history saved", file=self.history_file)
        except Exception as e:
            logger.error("Failed to save call history", error=str(e))

    def cleanup_old_calls(self, days_to_keep: int = 30):
        """Remove calls older than specified days."""
        cutoff_time = time.time() - (days_to_keep * 24 * 3600)
        original_count = len(self.call_history)

        self.call_history = [
            call for call in self.call_history if call.start_time > cutoff_time
        ]

        removed_count = original_count - len(self.call_history)
        if removed_count > 0:
            logger.info(
                "Cleaned up old calls",
                removed_count=removed_count,
                remaining_count=len(self.call_history),
            )
            self.save_history()


# Global call history manager instance
call_history_manager = CallHistoryManager()


def get_call_history_manager() -> CallHistoryManager:
    """Get the global call history manager instance."""
    return call_history_manager
