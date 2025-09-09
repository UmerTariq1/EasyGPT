import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from ..config import settings


class JSONLogger:
    """JSON logger for user interactions and model outputs (JSON Lines)."""

    def __init__(self):
        self.enabled = settings.logging.enabled
        self.file_path = settings.logging.path

        if self.enabled:
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
    
    def _write_log(self, log_data: Dict[str, Any]):
        """Write a single log entry to the JSONL file."""
        if not self.enabled:
            return
            
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_data) + "\n")
        except Exception:
            # Silently fail if logging fails to avoid breaking the app
            pass
    
    def log_user_request(
        self,
        user_id: str,
        request_type: str,
        prompt: str,
        system_prompt: str,
        provider: Optional[str],
        model: Optional[str],
        temperature: float,
        max_tokens: int,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Log user input request."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        log_data = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "request_type": request_type,
            "event": "request",
            "user_input": {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "provider": provider,
                "model": model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        }
        self._write_log(log_data)
    
    def log_model_response(
        self,
        user_id: str,
        request_type: str,
        model_output: str,
        provider: str,
        model: str,
        input_tokens: Optional[int],
        output_tokens: Optional[int],
        latency_ms: Optional[int],
        timestamp: Optional[datetime] = None
    ) -> None:
        """Log model response and usage information."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        log_data = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "request_type": request_type,
            "event": "response",
            "model_output": {
                "text": model_output,
                "provider": provider,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": latency_ms,
            },
        }
        self._write_log(log_data)
    
    def log_error(
        self,
        user_id: str,
        request_type: str,
        error_message: str,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Log error information."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        log_data = {
            "timestamp": timestamp.isoformat(),
            "user_id": user_id,
            "request_type": request_type,
            "event": "error",
            "error": {
                "message": error_message
            }
        }
        self._write_log(log_data)


# Global logger instance
json_logger = JSONLogger()


def generate_user_id() -> str:
    """Generate a unique user ID for the session."""
    return str(uuid.uuid4())
