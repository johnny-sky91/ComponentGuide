from app import db


class Component(db.Model):
    __tablename__ = "component"
    id = db.Column(db.Integer, primary_key=True)
    material_number = db.Column(db.Integer, unique=True)
    material_description = db.Column(db.String(64), default=None)
    supplier_material_number = db.Column(db.Integer, unique=True)
    manufacturer_part = db.Column(db.String(64), unique=True)
    leadtime = db.Column(db.Integer, default=0)
    status = db.Column(db.String(64), default=None)
    note = db.Column(db.String(160), default=None)
    check = db.Column(db.Boolean, default=False)
    on_shortage = db.Column(db.Boolean, default=False)
    stock = db.Column(db.Integer, default=0)
    orders = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Float, default=0.0)
    comments = db.relationship("ComponentComment", backref="component", lazy=True)
    supplier_shipment = db.relationship(
        "SupplierShipment", backref="component", lazy=True
    )
    supplier_stock = db.relationship("SupplierStock", backref="component", lazy=True)
    open_po = db.relationship("OpenPo", backref="component", lazy=True)
    incoming_shipment = db.relationship(
        "IncomingShipment", backref="component", lazy=True
    )
    project = db.relationship("Project", backref="component", lazy=True)


class ComponentComment(db.Model):
    __tablename__ = "component_comment"
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))
    text = db.Column(db.String(160))
    timestamp = db.Column(db.DateTime)


class SupplierShipment(db.Model):
    __tablename__ = "supplier_shipment"
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))
    supplier_po = db.Column(db.Integer, default=None)
    customer_po = db.Column(db.Integer, default=None)
    asn_qty = db.Column(db.Integer, default=0)
    ssd_qty = db.Column(db.Integer, default=0)
    mad_date = db.Column(db.Date, default=None)


class SupplierStock(db.Model):
    __tablename__ = "supplier_stock"
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))
    supplier_stock_qty = db.Column(db.Integer, default=0)
    stock_date = db.Column(db.Date, default=None)


class OpenPo(db.Model):
    __tablename__ = "open_po"
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))
    customer_po = db.Column(db.Integer, default=None)
    po_qty = db.Column(db.Integer, default=0)
    document_date = db.Column(db.Date, default=None)


class IncomingShipment(db.Model):
    __tablename__ = "incoming_shipments"
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))
    customer_po = db.Column(db.Integer, default=None)
    incoming_shipments_qty = db.Column(db.Integer, default=0)


class Project(db.Model):
    __tablename__ = "project"
    id = db.Column(db.Integer, primary_key=True)
    component_id = db.Column(db.Integer, db.ForeignKey("component.id"))
    customer = db.Column(db.String(64))
    project_date = db.Column(db.Date)
    project_material_number = db.Column(db.Integer)
    project_qty = db.Column(db.Integer, default=0)
    component_availability = db.Column(db.String(64), default=None)
    component_comment = db.Column(db.String(64), default=None)
    ddo_status = db.Column(db.String(64), default=None)
    ddo_end_date = db.Column(db.Date)
    project_status = db.Column(db.String(64), default=None)


class VariousValues(db.Model):
    __tablename__ = "various_values"
    id = db.Column(db.Integer, primary_key=True)
    value_name = db.Column(db.String(128), unique=True, nullable=False)
    value = db.Column(db.String(128), nullable=False)
