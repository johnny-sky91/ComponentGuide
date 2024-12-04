from app import db

from datetime import datetime


class Component(db.Model):
    __tablename__ = "component"
    id = db.Column(db.Integer, primary_key=True)

    material_number = db.Column(db.Integer, unique=True)
    material_description = db.Column(db.String(64))
    supplier_material_number = db.Column(db.Integer, unique=True)
    manufacturer_part = db.Column(db.String(64), unique=True)
    component_type = db.Column(db.String(64), default=None)
    status = db.Column(db.String(64), default=None)
    note = db.Column(db.String(160), default=None)
    check = db.Column(db.Boolean, default=False)
    on_shortage = db.Column(db.Boolean, default=False)

    comments = db.relationship("ComponentComment", backref="component", lazy=True)

    def __repr__(self):
        return f"<Component {self.name}>"


class ComponentComment(db.Model):
    __tablename__ = "component_comment"
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))
    text = db.Column(db.String(160))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
