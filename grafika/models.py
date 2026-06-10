"""models.py — model data GrafisObjek."""
import copy


class GrafisObjek:
    _id_counter = 0

    def __init__(self, shape: str, points: list,
                 fill: str = "#4fc3f7",
                 outline: str = "#1e40af",
                 line_width: int = 2,
                 line_dash: tuple = ()):
        GrafisObjek._id_counter += 1
        self.id         = GrafisObjek._id_counter
        self.shape      = shape
        self.points     = list(points)
        self.fill       = fill
        self.outline    = outline
        self.line_width = line_width
        self.line_dash  = tuple(line_dash)
        self.canvas_ids: list = []
        self.name       = f"{shape} #{self.id}"

    def clone(self) -> "GrafisObjek":
        o = GrafisObjek.__new__(GrafisObjek)
        o.id = self.id
        o.shape = self.shape
        o.points = copy.deepcopy(self.points)
        o.fill = self.fill
        o.outline = self.outline
        o.line_width = self.line_width
        o.line_dash = tuple(self.line_dash)
        o.canvas_ids = []
        o.name = self.name
        return o

    def center(self) -> tuple[float, float]:
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return sum(xs) / len(xs), sum(ys) / len(ys)

    def to_dict(self) -> dict:
        return {"id": self.id, "shape": self.shape,
                "points": self.points, "fill": self.fill,
                "outline": self.outline, "line_width": self.line_width,
                "line_dash": list(self.line_dash), "name": self.name}

    @classmethod
    def from_dict(cls, d: dict) -> "GrafisObjek":
        o = cls(d["shape"], [tuple(p) for p in d["points"]],
                fill=d["fill"], outline=d["outline"],
                line_width=d["line_width"], line_dash=tuple(d["line_dash"]))
        o.id = int(d.get("id", o.id))
        o.name = d.get("name", o.name)
        cls._id_counter = max(cls._id_counter, o.id)
        return o
