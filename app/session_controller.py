import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from playwright.sync_api import Page


class SessionOwner(str, Enum):
    AUTOMATION = "AUTOMATION"
    HUMAN = "HUMAN"


class SessionStatus(str, Enum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    RESUMED = "RESUMED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class SessionController:

    def __init__(
        self,
        page: Page,
        goal: str,
        current_step: int = 0,
    ):
        self.page = page
        self.goal = goal
        self.current_step = current_step

        self.owner = SessionOwner.AUTOMATION
        self.status = SessionStatus.RUNNING

        self.handoff_folder = Path(
            "evidence/handoff"
        )

        self.handoff_folder.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.session_timestamp = (
            datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
        )

        self.session_id = (
            f"session_{self.session_timestamp}"
        )

        self.handoff_history: list[
            dict[str, Any]
        ] = []

    def _current_timestamp(self) -> str:
        return datetime.now().isoformat()

    def _save_screenshot(
        self,
        event_name: str,
    ) -> str:

        screenshot_file = (
            self.handoff_folder
            / (
                f"{self.session_id}_"
                f"{event_name}.png"
            )
        )

        self.page.screenshot(
            path=str(screenshot_file),
            full_page=True,
        )

        return str(screenshot_file)

    def _save_session_record(self) -> str:

        record_file = (
            self.handoff_folder
            / (
                f"{self.session_id}_"
                "handoff.json"
            )
        )

        record = {
            "session_id": self.session_id,
            "goal": self.goal,
            "owner": self.owner.value,
            "status": self.status.value,
            "current_step": self.current_step,
            "current_url": self.page.url,
            "page_title": self.page.title(),
            "handoff_history": (
                self.handoff_history
            ),
        }

        with open(
            record_file,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                record,
                file,
                indent=4,
            )

        return str(record_file)

    def update_step(
        self,
        step_number: int,
    ) -> None:

        self.current_step = step_number

    def handoff_to_human(
        self,
        reason: str,
    ) -> dict[str, Any]:

        self.owner = SessionOwner.HUMAN
        self.status = SessionStatus.PAUSED

        paused_screenshot = (
            self._save_screenshot(
                "handoff_started"
            )
        )

        started_event = {
            "event": "HANDOFF_STARTED",
            "timestamp": (
                self._current_timestamp()
            ),
            "reason": reason,
            "owner": self.owner.value,
            "status": self.status.value,
            "step": self.current_step,
            "url": self.page.url,
            "page_title": (
                self.page.title()
            ),
            "screenshot": paused_screenshot,
        }

        self.handoff_history.append(
            started_event
        )

        record_file = (
            self._save_session_record()
        )

        handoff_result = {
            "status": (
                "HUMAN_INTERVENTION_REQUIRED"
            ),
            "session_id": self.session_id,
            "owner": self.owner.value,
            "reason": reason,
            "current_step": self.current_step,
            "current_url": self.page.url,
            "screenshot": paused_screenshot,
            "evidence": record_file,
        }

        print(
            "\n"
            + "=" * 60
        )

        print(
            "HUMAN INTERVENTION REQUIRED"
        )

        print(
            "=" * 60
        )

        print(
            json.dumps(
                handoff_result,
                indent=4,
            )
        )

        print(
            "\nThe browser will remain open."
        )

        print(
            "Complete the required action "
            "directly in the live browser."
        )

        input(
            "\nPress Enter after the human "
            "intervention is complete..."
        )

        return self.resume_automation()

    def resume_automation(
        self,
    ) -> dict[str, Any]:

        self.owner = (
            SessionOwner.AUTOMATION
        )

        self.status = (
            SessionStatus.RESUMED
        )

        resumed_screenshot = (
            self._save_screenshot(
                "automation_resumed"
            )
        )

        resumed_event = {
            "event": "AUTOMATION_RESUMED",
            "timestamp": (
                self._current_timestamp()
            ),
            "owner": self.owner.value,
            "status": self.status.value,
            "step": self.current_step,
            "url": self.page.url,
            "page_title": (
                self.page.title()
            ),
            "screenshot": resumed_screenshot,
        }

        self.handoff_history.append(
            resumed_event
        )

        record_file = (
            self._save_session_record()
        )

        resume_result = {
            "status": "RESUMED",
            "session_id": self.session_id,
            "owner": self.owner.value,
            "current_step": self.current_step,
            "current_url": self.page.url,
            "page_title": (
                self.page.title()
            ),
            "screenshot": resumed_screenshot,
            "evidence": record_file,
        }

        print(
            "\n"
            + "=" * 60
        )

        print(
            "AUTOMATION RESUMED"
        )

        print(
            "=" * 60
        )

        print(
            json.dumps(
                resume_result,
                indent=4,
            )
        )

        return resume_result

    def mark_completed(
        self,
    ) -> dict[str, Any]:

        self.owner = (
            SessionOwner.AUTOMATION
        )

        self.status = (
            SessionStatus.COMPLETED
        )

        completed_event = {
            "event": "SESSION_COMPLETED",
            "timestamp": (
                self._current_timestamp()
            ),
            "owner": self.owner.value,
            "status": self.status.value,
            "step": self.current_step,
            "url": self.page.url,
            "page_title": (
                self.page.title()
            ),
        }

        self.handoff_history.append(
            completed_event
        )

        record_file = (
            self._save_session_record()
        )

        return {
            "status": "COMPLETED",
            "session_id": self.session_id,
            "owner": self.owner.value,
            "evidence": record_file,
        }

    def mark_failed(
        self,
        error: str,
    ) -> dict[str, Any]:

        self.status = SessionStatus.FAILED

        failed_event = {
            "event": "SESSION_FAILED",
            "timestamp": (
                self._current_timestamp()
            ),
            "owner": self.owner.value,
            "status": self.status.value,
            "step": self.current_step,
            "url": self.page.url,
            "page_title": (
                self.page.title()
            ),
            "error": error,
        }

        self.handoff_history.append(
            failed_event
        )

        record_file = (
            self._save_session_record()
        )

        return {
            "status": "FAILED",
            "session_id": self.session_id,
            "error": error,
            "evidence": record_file,
        }