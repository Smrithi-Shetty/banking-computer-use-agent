import json
from datetime import datetime
from pathlib import Path


def load_latest_artifact():

    artifact_folder = Path(
        "artifacts"
    )

    artifacts = list(
        artifact_folder.glob("*.json")
    )

    if not artifacts:

        raise FileNotFoundError(
            "No artifacts found."
        )

    latest_artifact = max(
        artifacts,
        key=lambda f: f.stat().st_mtime
    )

    return latest_artifact


def replay():

    artifact_file = (
        load_latest_artifact()
    )

    with open(
        artifact_file,
        "r",
        encoding="utf-8"
    ) as f:

        artifact = json.load(f)

    outputs = artifact.get(
        "outputs",
        {}
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    Path(
        "evidence/replay"
    ).mkdir(
        parents=True,
        exist_ok=True
    )

    replay_evidence_file = (
        Path("evidence/replay")
        /
        f"replay_result_{timestamp}.json"
    )

    result = {
        "status": "SUCCESS",
        "artifact": str(
            artifact_file
        ),
        "replay_timestamp": str(datetime.now()),
        "outputs": outputs
    }

    with open(
        replay_evidence_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=4
        )

    result["evidence"] = str(
        replay_evidence_file
    )

    return result


if __name__ == "__main__":

    result = replay()

    print(
        json.dumps(
            result,
            indent=4
        )
    )