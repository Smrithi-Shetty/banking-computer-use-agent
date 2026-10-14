import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any


ARTIFACT_FOLDER = Path("artifacts")
REPLAY_EVIDENCE_FOLDER = Path(
    "evidence/replay"
)

REQUIRED_OUTPUTS = {
    "account_number",
    "total_balance",
    "available_balance",
}

VALID_SCENARIOS = {
    "success",
    "account-not-found",
    "transient-timeout",
    "auth-failed",
}


def load_latest_artifact() -> Path:
    artifacts = list(
        ARTIFACT_FOLDER.glob("*.json")
    )

    if not artifacts:
        raise FileNotFoundError(
            "No capability artifacts were found."
        )

    return max(
        artifacts,
        key=lambda file: file.stat().st_mtime,
    )


def load_artifact(
    artifact_file: Path,
) -> dict[str, Any]:
    with open(
        artifact_file,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def validate_artifact(
    artifact: dict[str, Any],
) -> tuple[bool, str | None]:
    required_sections = {
        "artifactVersion",
        "capability",
        "outputs",
        "steps",
    }

    missing_sections = (
        required_sections
        - artifact.keys()
    )

    if missing_sections:
        return (
            False,
            "Artifact is missing required "
            "sections: "
            + ", ".join(
                sorted(missing_sections)
            ),
        )

    outputs = artifact.get(
        "outputs",
        {},
    )

    if not isinstance(outputs, dict):
        return (
            False,
            "Artifact outputs must be an object.",
        )

    return True, None


def build_success_result(
    artifact_file: Path,
    artifact: dict[str, Any],
    replay_timestamp: str,
) -> dict[str, Any]:
    outputs = artifact.get(
        "outputs",
        {},
    )

    missing_outputs = (
        REQUIRED_OUTPUTS
        - outputs.keys()
    )

    if missing_outputs:
        return {
            "status": "HARD_FAILURE",
            "code": "INVALID_ARTIFACT_OUTPUTS",
            "message": (
                "The artifact does not contain "
                "all required outputs."
            ),
            "missing_outputs": sorted(
                missing_outputs
            ),
            "artifact": str(artifact_file),
            "replay_timestamp": (
                replay_timestamp
            ),
        }

    return {
        "status": "SUCCESS",
        "code": "REPLAY_COMPLETED",
        "message": (
            "The capability artifact was "
            "loaded and validated successfully."
        ),
        "artifact": str(artifact_file),
        "replay_timestamp": replay_timestamp,
        "outputs": {
            "account_number": outputs[
                "account_number"
            ],
            "total_balance": outputs[
                "total_balance"
            ],
            "available_balance": outputs[
                "available_balance"
            ],
        },
    }


def build_business_outcome(
    artifact_file: Path,
    replay_timestamp: str,
) -> dict[str, Any]:
    return {
        "status": "BUSINESS_OUTCOME",
        "code": "ACCOUNT_NOT_FOUND",
        "message": (
            "The replay completed normally, "
            "but no matching account was found."
        ),
        "artifact": str(artifact_file),
        "replay_timestamp": replay_timestamp,
        "outputs": {},
    }


def build_recoverable_error(
    artifact_file: Path,
    replay_timestamp: str,
) -> dict[str, Any]:
    retry_count = 1
    max_retries = 1

    return {
        "status": "RECOVERABLE_ERROR",
        "code": "TRANSIENT_PAGE_TIMEOUT",
        "message": (
            "A transient page-load timeout "
            "occurred. The bounded retry policy "
            "was applied."
        ),
        "artifact": str(artifact_file),
        "replay_timestamp": replay_timestamp,
        "retry_count": retry_count,
        "max_retries": max_retries,
        "retry_exhausted": (
            retry_count >= max_retries
        ),
        "outputs": {},
    }


def build_hard_failure(
    artifact_file: Path | None,
    replay_timestamp: str,
    message: str | None = None,
) -> dict[str, Any]:
    result = {
        "status": "HARD_FAILURE",
        "code": "AUTHENTICATION_FAILED",
        "message": (
            message
            or (
                "Authentication failed. "
                "Deterministic replay cannot "
                "continue safely."
            )
        ),
        "replay_timestamp": replay_timestamp,
        "outputs": {},
    }

    if artifact_file is not None:
        result["artifact"] = str(
            artifact_file
        )

    return result


def save_replay_evidence(
    result: dict[str, Any],
    timestamp_for_filename: str,
) -> Path:
    REPLAY_EVIDENCE_FOLDER.mkdir(
        parents=True,
        exist_ok=True,
    )

    evidence_file = (
        REPLAY_EVIDENCE_FOLDER
        / (
            "replay_result_"
            f"{timestamp_for_filename}.json"
        )
    )

    result["evidence"] = str(
        evidence_file
    )

    with open(
        evidence_file,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            indent=4,
        )

    return evidence_file


def replay(
    scenario: str = "success",
) -> dict[str, Any]:
    replay_datetime = datetime.now()

    replay_timestamp = (
        replay_datetime.isoformat()
    )

    timestamp_for_filename = (
        replay_datetime.strftime(
            "%Y%m%d_%H%M%S"
        )
    )

    artifact_file: Path | None = None

    try:
        if scenario not in VALID_SCENARIOS:
            raise ValueError(
                "Unsupported replay scenario: "
                f"{scenario}"
            )

        artifact_file = (
            load_latest_artifact()
        )

        artifact = load_artifact(
            artifact_file
        )

        artifact_valid, validation_error = (
            validate_artifact(
                artifact
            )
        )

        if not artifact_valid:
            result = {
                "status": "HARD_FAILURE",
                "code": "INVALID_ARTIFACT",
                "message": validation_error,
                "artifact": str(
                    artifact_file
                ),
                "replay_timestamp": (
                    replay_timestamp
                ),
                "outputs": {},
            }

        elif scenario == "account-not-found":
            result = build_business_outcome(
                artifact_file=artifact_file,
                replay_timestamp=(
                    replay_timestamp
                ),
            )

        elif scenario == "transient-timeout":
            result = build_recoverable_error(
                artifact_file=artifact_file,
                replay_timestamp=(
                    replay_timestamp
                ),
            )

        elif scenario == "auth-failed":
            result = build_hard_failure(
                artifact_file=artifact_file,
                replay_timestamp=(
                    replay_timestamp
                ),
            )

        else:
            result = build_success_result(
                artifact_file=artifact_file,
                artifact=artifact,
                replay_timestamp=(
                    replay_timestamp
                ),
            )

    except FileNotFoundError as error:
        result = {
            "status": "HARD_FAILURE",
            "code": "ARTIFACT_NOT_FOUND",
            "message": str(error),
            "replay_timestamp": (
                replay_timestamp
            ),
            "outputs": {},
        }

    except json.JSONDecodeError as error:
        result = {
            "status": "HARD_FAILURE",
            "code": "INVALID_ARTIFACT_JSON",
            "message": str(error),
            "artifact": (
                str(artifact_file)
                if artifact_file
                else None
            ),
            "replay_timestamp": (
                replay_timestamp
            ),
            "outputs": {},
        }

    except Exception as error:
        result = {
            "status": "HARD_FAILURE",
            "code": "UNEXPECTED_REPLAY_FAILURE",
            "message": str(error),
            "artifact": (
                str(artifact_file)
                if artifact_file
                else None
            ),
            "replay_timestamp": (
                replay_timestamp
            ),
            "outputs": {},
        }

    save_replay_evidence(
        result=result,
        timestamp_for_filename=(
            timestamp_for_filename
        ),
    )

    return result


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic replay and "
            "produce structured evidence."
        )
    )

    parser.add_argument(
        "--scenario",
        choices=sorted(
            VALID_SCENARIOS
        ),
        default="success",
        help=(
            "Select the replay outcome to "
            "demonstrate."
        ),
    )

    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_arguments()

    replay_result = replay(
        scenario=arguments.scenario
    )

    print(
        json.dumps(
            replay_result,
            indent=4,
        )
    )