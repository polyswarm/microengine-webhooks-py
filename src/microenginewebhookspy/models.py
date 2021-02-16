from polyswarmartifact.schema import Verdict as Metadata

from microenginewebhookspy.settings import API_KEY

class Verdict(enum.Enum):
    BENIGN = 'benign'
    MALICIOUS = 'malicious'
    SUSPICIOUS = 'suspicious'
    UNKNOWN = 'unknown'


@dataclasses.dataclass
class ScanResult:
    verdict: dataclasses.InitVar[Verdict]
    metadata: Metadata
    confidence: float = dataclasses.field()


@dataclasses.dataclass
class Assertion:
    verdict: dataclasses.InitVar[Verdict]
    bid: int
    metadata: Metadata
    verdict_str: str = dataclasses.field(init=False)

    def __post_init__(self, verdict):
        self.verdict_str = verdict.value

    def __eq__(self, other):
        return isinstance(other, Assertion) and other.verdict_str == self.verdict_str \
             and other.bid == self.bid and other.metadata == self.metadata

    def __hash__(self):
        calculated_hash = 7
        calculated_hash = 53 * calculated_hash + hash(self.verdict_str)
        calculated_hash = 53 * calculated_hash + hash(self.bid)
        # Cannot hash a dict
        return calculated_hash


@dataclasses.dataclass(frozen=True)
class Bounty:
    guid: str
    artifact_type: str
    artifact_url: str
    sha256: str
    mimetype: str
    expiration: str
    phase: str
    response_url: str
    rules: Dict[Tuple[str, Any]]

    def fetch_artifact(self):
        session = requests.Session()
        with session.get(self.artifact_url) as response:
            response.raise_for_status()
            return response.content

    def post_assertion(self, assertion: Assertion):
        session = requests.Session()
        headers = {
            'Authorization': API_KEY
        }
        with session.post(self.response_url, headers=headers, json=dataclasses.asdict(assertion)) as response:
            response.raise_for_status()

    def __dict__(self):
        return dataclasses.asdict(self)
