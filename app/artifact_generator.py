import json
from datetime import datetime
from pathlib import Path


def save_artifact(
    goal,
    history,
    outputs
):

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    artifact = {

        "artifactVersion": "1.0",

        "generatedAt":
            str(datetime.now()),

        "capability": {

            "name":
                "ReadAccountBalance",

            "description":
                goal
        },

        "inputs": [

            {
                "name":
                    "account_id",

                "type":
                    "string"
            }
        ],

        "outputs":
            outputs,

        "steps":
            history
    }

    artifact_folder = Path(
        "artifacts"
    )

    artifact_folder.mkdir(
        exist_ok=True
    )

    artifact_file = (
        artifact_folder
        /
        f"read_account_balance_{timestamp}.json"
    )

    with open(
        artifact_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            artifact,
            f,
            indent=4
        )

    return str(
        artifact_file
    )