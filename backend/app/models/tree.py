"""树木档案模型。"""

from ..constants import TREE_GROWTH_VIGOR, TREE_PROTECTION_LEVEL
from ..extensions import db
from ..utils.dates import format_datetime
from ..utils.numbers import to_float
from .mixins import TimestampMixin, coordinate_column, quantity_column


class Tree(TimestampMixin, db.Model):
    """树木档案：一树一档，登记树种、体量、保护级别与养护责任单位。"""

    __tablename__ = "tree"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(32), nullable=False, unique=True, index=True)
    green_space_id = db.Column(
        db.Integer, db.ForeignKey("green_space.id", ondelete="CASCADE"), nullable=False, index=True
    )
    species = db.Column(db.String(96), nullable=False, index=True)
    latin_name = db.Column(db.String(128))
    dbh_cm = db.Column(quantity_column())
    height_m = db.Column(quantity_column())
    age_years = db.Column(db.Integer)
    protection_level = db.Column(db.String(16), nullable=False, default="ordinary", index=True)
    growth_vigor = db.Column(db.String(16))
    responsible_unit = db.Column(db.String(128))
    longitude = db.Column(coordinate_column())
    latitude = db.Column(coordinate_column())
    location_desc = db.Column(db.String(255))
    remark = db.Column(db.Text)

    green_space = db.relationship("GreenSpace", back_populates="trees", lazy="joined")
    maintenances = db.relationship(
        "TreeMaintenance",
        back_populates="tree",
        cascade="all, delete-orphan",
        order_by="desc(TreeMaintenance.measure_date), desc(TreeMaintenance.id)",
    )

    def to_brief(self):
        """下拉框与关联展示用的精简结构。"""

        return {
            "id": self.id,
            "code": self.code,
            "species": self.species,
            "protection_level": self.protection_level,
            "protection_level_label": TREE_PROTECTION_LEVEL.label(self.protection_level),
        }

    def to_dict(self, detail=False):
        data = {
            "id": self.id,
            "code": self.code,
            "green_space_id": self.green_space_id,
            "green_space": self.green_space.to_brief() if self.green_space else None,
            "species": self.species,
            "latin_name": self.latin_name,
            "dbh_cm": to_float(self.dbh_cm),
            "height_m": to_float(self.height_m),
            "age_years": self.age_years,
            "protection_level": self.protection_level,
            "protection_level_label": TREE_PROTECTION_LEVEL.label(self.protection_level),
            "growth_vigor": self.growth_vigor,
            "growth_vigor_label": (
                TREE_GROWTH_VIGOR.label(self.growth_vigor) if self.growth_vigor else None
            ),
            "responsible_unit": self.responsible_unit,
            "longitude": to_float(self.longitude, digits=6),
            "latitude": to_float(self.latitude, digits=6),
            "location_desc": self.location_desc,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
        }
        if detail:
            data["remark"] = self.remark
        return data
