from dataclasses import dataclass, asdict
from pathlib import Path
import json
import uuid


GENOME_FILE="runtime/genome.json"


@dataclass
class GenomeRecord:

    id:str

    objective:str

    plan:dict

    success:bool

    score:float

    result:dict


class ExecutionGenome:

    def __init__(self):

        Path("runtime").mkdir(
            exist_ok=True
        )

        if not Path(GENOME_FILE).exists():

            with open(
                GENOME_FILE,
                "w",
                encoding="utf8"
            ) as f:

                json.dump([],f)

    def store(
        self,
        objective,
        plan,
        success,
        score,
        result
    ):

        record=GenomeRecord(

            id=str(uuid.uuid4()),

            objective=objective,

            plan=plan,

            success=success,

            score=score,

            result=result
        )

        data=self.load()

        data.append(
            asdict(record)
        )

        with open(
            GENOME_FILE,
            "w",
            encoding="utf8"
        ) as f:

            json.dump(
                data,
                f,
                indent=2
            )

    def load(self):

        with open(
            GENOME_FILE,
            encoding="utf8"
        ) as f:

            return json.load(f)
