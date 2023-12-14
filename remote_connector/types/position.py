import dataclasses


@dataclasses.dataclass(slots=True, frozen=True)
class Position:
    x: float
    y: float
    z: float
    heading: float

    def __hash__(self):
        return hash((self.x, self.y, self.z))
