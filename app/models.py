from app import db

from datetime import datetime


class Component(db.Model):
    __tablename__ = "component"
    id = db.Column(db.Integer, primary_key=True)

    material_number = db.Column(db.Integer, unique=True)
    material_description = db.Column(db.String(64), default=None)
    supplier_material_number = db.Column(db.Integer, unique=True)
    manufacturer_part = db.Column(db.String(64), unique=True)
    leadtime = db.Column(db.Integer, default=0)
    component_type = db.Column(db.String(64), default=None)  # TODO to remove?
    status = db.Column(db.String(64), default=None)
    note = db.Column(db.String(160), default=None)
    check = db.Column(db.Boolean, default=False)
    on_shortage = db.Column(db.Boolean, default=False)
    incoming_shipments_qty = db.Column(db.Integer, default=0)
    free_to_order_qty = db.Column(db.Integer, default=0)
    supplier_stock_qty = db.Column(db.Integer, default=0)
    open_po_qty = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, default=0.0)
    comments = db.relationship("ComponentComment", backref="component", lazy=True)


class ComponentComment(db.Model):
    __tablename__ = "component_comment"
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))
    text = db.Column(db.String(160))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
