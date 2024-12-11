from datetime import datetime
import pandas as pd
import os
from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
)

from flask import current_app as app
from app import db
from app.models import (
    Component,
    ComponentComment,
    SupplierShipment,
)
from app.forms import (
    AddComponent,
    AddComponentComment,
    UpdateComponentNote,
    UpdateComponentLeadtime,
    UpdateComponentUnitPrice,
    UpdateComponentStatus,
    UpdateComponentQty,
)


@app.context_processor
def inject_date_cw():
    current_date = datetime.now().date()
    week_number = current_date.isocalendar()[1]
    return dict(current_date=current_date, week_number=week_number)


@app.route("/")
@app.route("/all_components", methods=["GET", "POST"])
def all_components():
    filter_type = request.args.get("filter", "all")

    filters = {
        "all": {
            "query": Component.query.order_by(Component.id.asc()),
            "title": "All components",
        },
        "incoming_shipments": {
            "query": Component.query.filter(
                Component.incoming_shipments_qty > 0
            ).order_by(Component.id.asc()),
            "title": "Incoming shipments",
        },
        "supplier_stock": {
            "query": Component.query.filter(Component.supplier_stock_qty > 0).order_by(
                Component.id.asc()
            ),
            "title": "Supplier stock",
        },
        "open_po": {
            "query": Component.query.filter(Component.open_po_qty > 0).order_by(
                Component.id.asc()
            ),
            "title": "Open PO",
        },
    }

    selected_filter = filters.get(filter_type, filters["all"])
    components = selected_filter["query"].all()
    title = selected_filter["title"]

    return render_template(
        "all_components.html",
        title=title,
        components=components,
    )


@app.route("/supplier_shipments", methods=["GET", "POST"])
def supplier_shipments():
    shipments = SupplierShipment.query.order_by(SupplierShipment.component_id.desc())
    components = [Component.query.get(shipment.component_id) for shipment in shipments]
    all_shipments_info = zip(components, shipments)
    return render_template(
        "supplier_shipments.html",
        title="Supplier shipments",
        all_shipments_info=all_shipments_info,
    )


@app.route("/supplier_shipments/update_supplier_shipments", methods=["GET", "POST"])
def update_supplier_shipments():
    SupplierShipment.query.delete()
    db.session.commit()
    file = request.files["file"]
    file.save(file.filename)
    supplier_shipments = prepare_supplier_shipments_data(shipment_file=file)
    for index, row in supplier_shipments.iterrows():
        try:
            component = (
                Component.query.filter_by(material_number=row["Customer Part #"])
                .first()
                .id
            )
            new_shipment = SupplierShipment(
                component_id=component,
                supplier_po=row["TDS PO #"],
                customer_po=row["Customer PO #"],
                asn_qty=row["ASN Qty"],
                ssd_qty=row["SSD Qty"],
                mad_date=row["MAD Date"],
            )
            db.session.add(new_shipment)
            db.session.commit()
        except AttributeError:
            pass

    os.remove(file.filename)
    return redirect(request.referrer)


def prepare_supplier_shipments_data(shipment_file):
    data = pd.read_excel(shipment_file)
    data.columns = data.iloc[0]
    data = data.iloc[1:, :]
    data = data[data["Confirmation Type"] == "SSD"]
    ready_list = [
        "Customer Part #",
        "Customer PO #",
        "TDS PO #",
        "MAD Date",
        "SSD Qty",
        "ASN Qty",
    ]
    ready_data = data[ready_list]
    ready_data.reset_index(drop=True, inplace=True)

    return ready_data


@app.route("/all_components/add_new_component", methods=["GET", "POST"])
def add_new_component():
    form = AddComponent()
    if form.validate_on_submit():
        new_component = Component(
            material_number=form.material_number.data,
            material_description=form.material_description.data,
            supplier_material_number=form.supplier_material_number.data,
            manufacturer_part=form.manufacturer_part.data,
        )
        db.session.add(new_component)
        db.session.commit()
        flash(f"New component added - {new_component.material_number}")
        return redirect(url_for("all_components"))
    return render_template(
        "add/add_new_component.html", title="Add new Component", form=form
    )


@app.route("/all_components/component_view/<int:id>", methods=["GET", "POST"])
def component_view(id):
    component = Component.query.get(id)
    supplier_shipments = (
        SupplierShipment.query.filter_by(component_id=id)
        .order_by(SupplierShipment.mad_date.desc())
        .all()
    )
    print(supplier_shipments)

    comments = (
        ComponentComment.query.filter_by(component_id=id)
        .order_by(ComponentComment.id.desc())
        .all()
    )
    return render_template(
        "component.html",
        title=f"{component.material_number}",
        component=component,
        comments=comments,
        supplier_shipments=supplier_shipments,
    )


@app.route("/all_components/next_component/<step>/<int:id>", methods=["GET"])
def next_component(step, id):
    if step.lower() == "forward":
        new_id = id + 1
    else:
        new_id = id - 1

    next_group = Component.query.get(new_id)
    if next_group:
        return redirect(url_for("component_view", id=new_id))
    else:
        flash("No more components")
        return redirect(url_for("component_view", id=id))


@app.route(
    "/all_components/component_view/<int:id>/change_check", methods=["GET", "POST"]
)
def change_check(id):
    component = Component.query.get(id)
    component.check = not component.check
    db.session.commit()
    return redirect(request.referrer)


@app.route(
    "/all_components/component_view/<int:id>/change_on_shortage",
    methods=["GET", "POST"],
)
def change_shortage(id):
    component = Component.query.get(id)
    component.on_shortage = not component.on_shortage
    db.session.commit()
    return redirect(request.referrer)


@app.route(
    "/all_components/component_view/<int:id>/update_note", methods=["GET", "POST"]
)
def update_component_note(id):
    component = Component.query.get(id)
    form = UpdateComponentNote()
    if form.validate_on_submit():
        component.note = form.note.data
        db.session.commit()
        return redirect(request.referrer)
    return render_template(
        f"update/update_note.html",
        title=f"{component.material_number}",
        form=form,
        current_note=component.note,
        component=component,
    )


@app.route(
    "/all_components/component_view/<int:id>/update_leadtime", methods=["GET", "POST"]
)
def update_component_leadtime(id):
    component = Component.query.get(id)
    form = UpdateComponentLeadtime()
    if form.validate_on_submit():
        component.leadtime = form.leadtime.data
        db.session.commit()
        return redirect(request.referrer)
    return render_template(
        f"update/update_leadtime.html",
        title=f"{component.material_number}",
        form=form,
        current_leadtime=component.leadtime,
        component=component,
    )


@app.route(
    "/all_components/component_view/<int:id>/update_unit_price", methods=["GET", "POST"]
)
def update_component_unit_price(id):
    component = Component.query.get(id)
    form = UpdateComponentUnitPrice()
    if form.validate_on_submit():
        component.unit_price = form.unit_price.data
        db.session.commit()
        return redirect(request.referrer)
    return render_template(
        f"update/update_unit_price.html",
        title=f"{component.material_number}",
        form=form,
        component=component,
    )


component_statuses = ["Active", "EOL", "POE"]


@app.route(
    "/all_components/component_view/<int:id>/update_status", methods=["GET", "POST"]
)
def update_component_status(id):
    form = UpdateComponentStatus()
    component = Component.query.get(id)
    form.status.choices = component_statuses

    if form.validate_on_submit():
        component.status = form.status.data
        db.session.commit()
        return redirect(url_for("component_view", id=id))
    return render_template(
        f"update/update_status.html",
        title=f"{component.material_number}",
        form=form,
        component=component,
    )


@app.route(
    "/all_components/component_view/<int:id>/update_qty/<qty_type>/<qty_name>",
    methods=["GET", "POST"],
)
def update_component_qty(id, qty_type, qty_name):
    print(qty_type)
    print(qty_name)
    form = UpdateComponentQty()
    component = Component.query.get(id)
    qty_current = getattr(component, qty_type)
    if form.validate_on_submit():
        setattr(component, qty_type, form.new_qty.data)
        db.session.commit()
        flash(f"QTY updated!")
        return redirect(url_for("component_view", id=id))
    return render_template(
        f"update/update_qty.html",
        title=f"{component.material_number}",
        form=form,
        component=component,
        qty_current=qty_current,
        qty_name=qty_name,
    )


@app.route(
    "/all_components/component_view/<int:id>/add_comment", methods=["GET", "POST"]
)
def add_component_comment(id):
    component = Component.query.get(id)
    form = AddComponentComment()
    if form.validate_on_submit():
        new_comment = ComponentComment(
            component_id=id,
            text=form.text.data,
        )
        db.session.add(new_comment)
        db.session.commit()
        flash(f"New comment added")
        return redirect(url_for("component_view", id=id))
    return render_template(
        f"add/add_comment.html",
        title=f"{component.material_description}",
        form=form,
    )


@app.route(
    "/all_components/component_view/<int:id>/remove_comment/<int:comment_id>",
    methods=["GET", "POST"],
)
def remove_component_comment(id, comment_id):
    ComponentComment.query.filter_by(id=comment_id, component_id=id).delete()
    db.session.commit()
    return redirect(request.referrer)
