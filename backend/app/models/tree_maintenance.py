"""树木养护措施记录模型。"""

from ..constants import TREE_MEASURE_TYPE
from ..extensions import db
from ..utils.dates import format_date, format_datetime
from .mixins import TimestampMixin


class TreeMaintenance(TimestampMixin, db.Model):
    """树木养护措施：复壮、支撑、防腐等措施逐次登记在树木档案下。"""

    __tablename__ = "tree_maintenance"

    id = db.Column(db.Integer, primary_key=True)
    record_no = db.Column(db.String(32), nullable=False, unique=True, index=True)
    tree_id = db.Column(
        db.Integer, db.ForeignKey("tree.id", ondelete="CASCADE"), nullable=False, index=True
    )
    measure_type = db.Column(db.String(32), nullable=False, index=True)
    measure_date = db.Column(db.Date, nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    operator = db.Column(db.String(64))
    remark = db.Column(db.Text)

    tree = db.relationship("Tree", back_populates="maintenances")

    def to_dict(self, detail=False):
        data = {
            "id": self.id,
            "record_no": self.record_no,
            "tree_id": self.tree_id,
            "tree": self.tree.to_brief() if self.tree else None,
            "measure_type": self.measure_type,
            "measure_type_label": TREE_MEASURE_TYPE.label(self.measure_type),
            "measure_date": format_date(self.measure_date),
            "content": self.content,
            "operator": self.operator,
            "created_at": format_datetime(self.created_at),
            "updated_at": format_datetime(self.updated_at),
        }
        if detail:
            data["remark"] = self.remark
        return data
