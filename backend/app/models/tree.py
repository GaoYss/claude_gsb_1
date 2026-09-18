"""树木档案与逐次养护措施模型。"""

from ..constants import TREE_CARE_TYPE, TREE_PROTECTION_LEVEL, TREE_VIGOR
from ..extensions import db
from ..utils.dates import format_date, format_datetime
from ..utils.numbers import to_float
from .mixins import TimestampMixin, amount_column, quantity_column


class TreeProfile(TimestampMixin, db.Model):
    """树木单独档案：一树一档，登记树种、规格、树龄、保护级别与责任单位。"""

    __tablename__ = "tree_profile"

    id = db.Column(db.Integer, primary_key=True)
    tree_no = db.Column(db.String(32), nullable=False, unique=True, index=True)
    green_space_id = db.Column(
        db.Integer, db.ForeignKey("green_space.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tree_species = db.Column(db.String(96), nullable=False, index=True)
    scientific_name = db.Column(db.String(128))
    dbh_cm = db.Column(quantity_column())
    height_m = db.Column(quantity_column())
    crown_width_m = db.Column(quantity_column())
    age_years = db.Column(db.Integer)
    protection_level = db.Column(db.String(16), nullable=False, default="none", index=True)
    vigor = db.Column(db.String(16), nullable=False, default="vigorous", index=True)
    responsible_unit = db.Column(db.String(128), nullable=False, index=True)
    responsible_person = db.Column(db.String(64))
    contact_phone = db.Column(db.String(32))
    location_desc = db.Column(db.String(255))
    longitude = db.Column(db.Numeric(11, 8, asdecimal=False))
    latitude = db.Column(db.Numeric(11, 8, asdecimal=False))
    planted_date = db.Column(db.Date)
    register_date = db.Column(db.Date, nullable=False, index=True)
    remark = db.Column(db.Text)

    green_space = db.relationship("GreenSpace", back_populates="trees", lazy="joined")
    maintenances = db.relationship(
        "TreeMaintenance",
        back_populates="tree",
        cascade="all, delete-orphan",
        order_by="TreeMaintenance.care_date.desc(), TreeMaintenance.id.desc()",
    )

    def to_brief(self):
        """养护措施等关联展示用的精简结构。"""

        return {
            "id": self.id,
            "tree_no": self.tree_no,
            "tree_species": self.tree_species,
            "protection_level": self.protection_level,
        }

    def to_dict(self, detail=False):
        data = {
            "id": self.id,
            "tree_no": self.tree_no,
            "green_space_id": self.green_space_id,
            "green_space": self.green_space.to_brief() if self.green_space else None,
            "tree_species": self.tree_species,
            "scientific_name": self.scientific_name,
            "dbh_cm": to_float(self.dbh_cm),
            "height_m": to_float(self.height_m),
            "crown_width_m": to_float(self.crown_width_m),
            "age_years": self.age_years,
            "protection_level": self.protection_level,
            "protection_level_label": TREE_PROTECTION_LEVEL.label(self.protection_level),
            "vigor": self.vigor,
            "vigor_label": TREE_VIGOR.label(self.vigor),
            "responsible_unit": self.responsible_unit,
            "responsible_person": self.responsible_person,
            "contact_phone": self.contact_phone,
            "location_desc": self.location_desc,
            "longitude": to_float(self.longitude, digits=8),
            "latitude": to_float(self.latitude, digits=8),
            "planted_date": format_date(self.planted_date),
            "register_date": format_date(self.register_date),
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
        }
        if detail:
            data["remark"] = self.remark
            data["maintenances"] = [item.to_dict() for item in self.maintenances]
        return data


class TreeMaintenance(TimestampMixin, db.Model):
    """树木养护措施：复壮、支撑、防腐等措施逐次登记在档案下。"""

    __tablename__ = "tree_maintenance"

    id = db.Column(db.Integer, primary_key=True)
    tree_id = db.Column(
        db.Integer, db.ForeignKey("tree_profile.id", ondelete="CASCADE"), nullable=False, index=True
    )
    care_type = db.Column(db.String(32), nullable=False, index=True)
    care_date = db.Column(db.Date, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    operator = db.Column(db.String(64))
    result = db.Column(db.String(255))
    cost = db.Column(amount_column())
    remark = db.Column(db.Text)

    tree = db.relationship("TreeProfile", back_populates="maintenances")

    def to_dict(self, detail=False):
        data = {
            "id": self.id,
            "tree_id": self.tree_id,
            "care_type": self.care_type,
            "care_type_label": TREE_CARE_TYPE.label(self.care_type),
            "care_date": format_date(self.care_date),
            "content": self.content,
            "operator": self.operator,
            "result": self.result,
            "cost": to_float(self.cost),
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
        }
        if detail:
            data["remark"] = self.remark
            data["tree"] = self.tree.to_brief() if self.tree else None
        return data
