from datetime import datetime
from sqlalchemy import func
import pandas as pd
import os, io
from flask import (
    render_template,
    flash,
    redirect,
    url_for,
    request,
    make_response,
)
from flask import current_app as app
from app import db
from app.models import (
    Component,
    ComponentComment,
    SupplierShipment,
    SupplierStock,
    OpenPo,
    IncomingShipment,
    Project,
)
from app.forms import (
    AddComponent,
    AddComponentComment,
    UpdateComponentNote,
    UpdateComponentLeadtime,
    UpdateComponentUnitPrice,
    UpdateComponentStatus,
    UpdateComponentStock,
    UpdateComponentOrders,
    SearchComponent,
)
from app.other_functions.data_preparation import (
    prepare_open_po,
    prepare_supplier_shipments,
    prepare_open_projects,
    prepare_supplier_stock,
    prepare_incoming_shipments,
)


@app.context_processor
def inject_date_cw():
    current_date = datetime.now().date()
    week_number = current_date.isocalendar()[1]
    return dict(current_date=current_date, week_number=week_number)


@app.route("/all_components/<what_view>", methods=["GET", "POST"])
def all_components(what_view):
    query_mapping = {
        "check_true": {"check": True},
        "shortage_true": {"on_shortage": True},
    }
    components_query = Component.query
    if what_view.lower() in query_mapping:
        query_filters = query_mapping[what_view.lower()]
        components_query = components_query.filter_by(**query_filters)

    form_search = SearchComponent()

    if form_search.submit_search.data and form_search.validate():
        to_search = form_search.component.data
        components_query = components_query.filter(
            Component.material_number.like(f"%{to_search}%")
            | Component.manufacturer_part.like(f"%{to_search}%")
        )

    components = components_query.order_by(Component.id.asc()).all()

    total_supplier_stock = [
        0 if not x.supplier_stock else x.supplier_stock[0].supplier_stock_qty
        for x in components
    ]

    total_supplier_shipments = [
        0 if not x.supplier_shipment else x.supplier_shipment for x in components
    ]

    total_supplier_shipments = [
        (
            sum([shipment.asn_qty + shipment.ssd_qty for shipment in shipments])
            if shipments != 0
            else shipments
        )
        for shipments in total_supplier_shipments
    ]

    total_fto_plant = [x.stock - x.orders for x in components]

    total_fto = [
        fto_plant + supplier_stock + supplier_shipments
        for fto_plant, supplier_stock, supplier_shipments in zip(
            total_fto_plant, total_supplier_stock, total_supplier_shipments
        )
    ]
    comments = [None if not x.comments else x.comments[-1].text for x in components]

    return render_template(
        "all_components.html",
        title="All components",
        components=components,
        comments=comments,
        total_fto=total_fto,
        form_search=form_search,
    )


def table_to_dataframe(table_name):
    data = table_name.query.all()
    data_dicts = [
        {
            column.name: getattr(record, column.name)
            for column in table_name.__table__.columns
        }
        for record in data
    ]
    df = pd.DataFrame(data_dicts)
    return df


@app.route("/all_components/download_data", methods=["GET", "POST"])
def download_component_data():
    components_df = table_to_dataframe(table_name=Component)
    out = io.BytesIO()
    writer = pd.ExcelWriter(out, engine="xlsxwriter")
    components_df.to_excel(excel_writer=writer, index=False, sheet_name="Components")
    writer._save()
    download_response = make_response(out.getvalue())
    now = datetime.now()
    timestamp = now.strftime("%y%m%d")
    filename = f"ComponentGuide_data_{timestamp}"
    download_response.headers["Content-Disposition"] = (
        f"attachment; filename={filename}.xlsx"
    )
    download_response.headers["Content-type"] = "application/x-xlsx"
    return download_response


@app.route("/supplier_stock", methods=["GET", "POST"])
def supplier_stock():
    components_stock = SupplierStock.query.order_by(SupplierStock.component_id.desc())
    components = [Component.query.get(stock.component_id) for stock in components_stock]
    supplier_all_stock = {
        stock: component for stock, component in zip(components_stock, components)
    }
    total_value = round(
        sum(
            stock.supplier_stock_qty * component.unit_price
            for stock, component in supplier_all_stock.items()
        )
    )
    total_value = f"{total_value:,}"
    total_qty = sum([x.supplier_stock_qty for x in components_stock])
    return render_template(
        "supplier_stock.html",
        title="Supplier stock",
        supplier_all_stock=supplier_all_stock,
        total_value=total_value,
        total_qty=total_qty,
    )


@app.route("/supplier_stock/update_supplier_stock", methods=["GET", "POST"])
def update_supplier_stock():
    SupplierStock.query.delete()
    db.session.commit()
    file = request.files["file"]
    file.save(file.filename)
    supplier_stock = prepare_supplier_stock(stock_file=file)
    for index, row in supplier_stock.iterrows():
        try:
            component = (
                Component.query.filter_by(material_number=row["Customer Part #"])
                .first()
                .id
            )
            new_stock = SupplierStock(
                component_id=component,
                supplier_stock_qty=row["Qty on Hand"],
                stock_date=row["Calendar Day"],
            )
            db.session.add(new_stock)
            db.session.commit()
        except AttributeError:
            pass

    os.remove(file.filename)
    return redirect(request.referrer)


@app.route("/open_po", methods=["GET", "POST"])
def open_po():
    all_open_po = OpenPo.query.order_by(OpenPo.document_date.asc())
    components = [Component.query.get(po.component_id) for po in all_open_po]
    ready_open_po = {po: component for po, component in zip(all_open_po, components)}
    return render_template(
        "open_po.html",
        title="Open PO",
        ready_open_po=ready_open_po,
    )


@app.route("/open_po/update_open_po", methods=["GET", "POST"])
def update_open_po():
    OpenPo.query.delete()
    db.session.commit()
    file = request.files["file"]
    file.save(file.filename)
    all_open_po = prepare_open_po(open_po_file=file)
    for index, row in all_open_po.iterrows():
        try:
            component = (
                Component.query.filter_by(material_number=row["Material"]).first().id
            )
            new_open_po = OpenPo(
                component_id=component,
                customer_po=row["Purchasing Document"],
                po_qty=row["Order Quantity"],
                document_date=row["Document Date"],
            )
            db.session.add(new_open_po)
            db.session.commit()
        except AttributeError:
            pass

    os.remove(file.filename)
    return redirect(request.referrer)


@app.route("/supplier_shipments", methods=["GET", "POST"])
def supplier_shipments():
    shipments = SupplierShipment.query.all()
    components = [Component.query.get(shipment.component_id) for shipment in shipments]
    all_shipments_info = {
        shipment: {
            "component": component,
            "week": int(shipment.mad_date.strftime("%W")),
        }
        for shipment, component in zip(shipments, components)
    }

    from collections import defaultdict

    weekly_values = defaultdict(float)
    for shipment, info in all_shipments_info.items():
        week = info["week"]
        value = round(
            info["component"].unit_price * (shipment.asn_qty + shipment.ssd_qty)
        )
        weekly_values[week] += value

    return render_template(
        "supplier_shipments.html",
        title="Supplier shipments",
        all_shipments_info=all_shipments_info,
        weekly_values=weekly_values,
    )


@app.route("/supplier_shipments/update_supplier_shipments", methods=["GET", "POST"])
def update_supplier_shipments():
    SupplierShipment.query.delete()
    db.session.commit()
    file = request.files["file"]
    file.save(file.filename)
    supplier_shipments = prepare_supplier_shipments(shipment_file=file)
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


@app.route("/open_projects", methods=["GET", "POST"])
def open_projects():
    projects = Project.query.order_by(Project.id.desc())
    components = [Component.query.get(project.component_id) for project in projects]
    all_projects_info = zip(components, projects)
    return render_template(
        "projects.html",
        title="Open projects",
        all_projects_info=all_projects_info,
    )


@app.route("/open_projects/update_open_projects", methods=["GET", "POST"])
def update_open_projects():
    Project.query.delete()
    db.session.commit()
    file = request.files["file"]
    file.save(file.filename)
    open_projects = prepare_open_projects(project_file=file)
    for index, row in open_projects.iterrows():
        new_ddo_end_date = row["DDO end date"]
        new_project_qty = row["QTY"]
        if pd.isnull(new_ddo_end_date):
            new_ddo_end_date = None
        if pd.isna(new_project_qty):
            new_project_qty = None
        else:
            pass
        try:
            component = Component.query.filter_by(material_number=row["SAP"]).first().id
            new_project = Project(
                component_id=component,
                project_material_number=row["SAP"],
                customer=row["Customer"],
                project_date=row["Month"],
                project_qty=new_project_qty,
                component_availability=row["Availability"],
                component_comment=row["Comments / hints"],
                ddo_status=row["DDO"],
                ddo_end_date=new_ddo_end_date,
                project_status=row["Overall rate"],
            )
            db.session.add(new_project)
            db.session.commit()
        except AttributeError:
            pass

    os.remove(file.filename)
    return redirect(request.referrer)


@app.route("/incoming_shipments", methods=["GET", "POST"])
def incoming_shipments():
    shipments = IncomingShipment.query.order_by(IncomingShipment.component_id.desc())
    components = [Component.query.get(shipment.component_id) for shipment in shipments]
    all_shipments_info = {
        shipment: component for shipment, component in zip(shipments, components)
    }
    total_value = round(
        sum(
            stock.incoming_shipments_qty * component.unit_price
            for stock, component in all_shipments_info.items()
        )
    )
    total_value = f"{total_value:,}"
    total_qty = sum([x.incoming_shipments_qty for x in shipments])
    return render_template(
        "incoming_shipments.html",
        title="Incoming shipments",
        all_shipments_info=all_shipments_info,
        total_value=total_value,
        total_qty=total_qty,
    )


@app.route("/incoming_shipments/clear_incoming_shipments", methods=["GET", "POST"])
def clear_incoming_shipments():
    IncomingShipment.query.delete()
    db.session.commit()
    return redirect(request.referrer)


@app.route("/incoming_shipments/update_incoming_shipments", methods=["GET", "POST"])
def update_incoming_shipments():
    IncomingShipment.query.delete()
    db.session.commit()
    file = request.files["file"]
    file.save(file.filename)
    incoming_shipments = prepare_incoming_shipments(shipment_file=file)
    for index, row in incoming_shipments.iterrows():
        new_customer_po = row["FTS order"]
        if pd.isna(new_customer_po):
            new_customer_po = None
        else:
            new_customer_po = int(row["FTS order"])
        try:
            component = (
                Component.query.filter_by(material_number=int(row["Customer Part #"]))
                .first()
                .id
            )
            new_shipment = IncomingShipment(
                component_id=component,
                incoming_shipments_qty=int(row["Ship out QTY"]),
                customer_po=new_customer_po,
            )
            db.session.add(new_shipment)
            db.session.commit()
        except AttributeError:
            pass

    os.remove(file.filename)
    return redirect(request.referrer)


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


@app.route("/update_stock/<int:id>", methods=["POST"])
def update_stock(id):
    component = Component.query.get_or_404(id)
    form_stock = UpdateComponentStock()
    if form_stock.validate_on_submit():
        component.stock = form_stock.new_stock.data
        db.session.commit()
        flash("Stock updated!")
    return redirect(request.referrer)


@app.route("/update_orders/<int:id>", methods=["POST"])
def update_orders(id):
    component = Component.query.get_or_404(id)
    form_orders = UpdateComponentOrders()
    if form_orders.validate_on_submit():
        component.orders = form_orders.new_orders.data
        db.session.commit()
        flash("Orders updated!")
    return redirect(request.referrer)


@app.route("/update_leadtime/<int:id>", methods=["POST"])
def update_leadtime(id):
    component = Component.query.get_or_404(id)
    form_leadtime = UpdateComponentLeadtime()
    if form_leadtime.validate_on_submit():
        component.leadtime = form_leadtime.new_leadtime.data
        db.session.commit()
        flash("Leadtime updated!")
    return redirect(request.referrer)


def remaining_from_shipments(shipments, initial_balance):
    remaining = []
    current_balance = initial_balance
    for shipment in shipments:
        if current_balance < 0:
            if current_balance + shipment >= 0:
                remaining.append(current_balance + shipment)
                current_balance = 0
            else:
                remaining.append(0)
                current_balance += shipment
        else:
            remaining.append(shipment)
            current_balance += shipment

    return remaining


@app.route("/all_components/component_view/<int:id>", methods=["GET", "POST"])
def component_view(id):
    component = Component.query.get_or_404(id)
    supplier_shipments = SupplierShipment.query.filter_by(component_id=id).all()
    incoming_shipments = IncomingShipment.query.filter_by(component_id=id).all()
    supplier_stock = SupplierStock.query.filter_by(component_id=id).first()
    if supplier_stock is None:
        supplier_stock = 0
    else:
        supplier_stock = supplier_stock.supplier_stock_qty

    open_po = OpenPo.query.filter_by(component_id=id).all()
    supplier_stock_left = max(0, supplier_stock - sum([x.po_qty for x in open_po]))
    free_to_order = (
        component.stock + sum([x.po_qty for x in open_po]) - component.orders
    )
    comments = (
        ComponentComment.query.filter_by(component_id=id)
        .order_by(ComponentComment.id.desc())
        .all()
    )
    supplier_shipments_qty = [x.asn_qty + x.ssd_qty for x in supplier_shipments]
    initial_balance_qty = supplier_stock - sum([x.po_qty for x in open_po])
    remaining_supplier_shipments = remaining_from_shipments(
        shipments=supplier_shipments_qty, initial_balance=initial_balance_qty
    )

    form_stock = UpdateComponentStock()
    form_orders = UpdateComponentOrders()
    form_leadtime = UpdateComponentLeadtime()

    return render_template(
        "component.html",
        title=f"{component.material_number}",
        component=component,
        comments=comments,
        supplier_shipments=supplier_shipments,
        supplier_stock=supplier_stock,
        open_po=open_po,
        incoming_shipments=incoming_shipments,
        form_stock=form_stock,
        form_orders=form_orders,
        form_leadtime=form_leadtime,
        supplier_stock_left=supplier_stock_left,
        free_to_order=free_to_order,
        remaining_supplier_shipments=remaining_supplier_shipments,
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
        return redirect(url_for("component_view", id=id))
    return render_template(
        f"update/update_note.html",
        title=f"{component.material_number}",
        form=form,
        current_note=component.note,
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


@app.route("/all_components/next_component_qty/<step>/<int:id>", methods=["GET"])
def next_component_qty(step, id):
    if step.lower() == "forward":
        new_id = id + 1
    else:
        new_id = id - 1
    next_group = Component.query.get(new_id)
    if next_group:
        return redirect(
            url_for(
                "update_component_qty",
                id=new_id,
                qty_type="free_to_order_qty",
                qty_name="free to order",
            )
        )
    else:
        flash("No more components")
        return redirect(request.referrer)


@app.route(
    "/all_components/component_view/<int:id>/add_comment", methods=["GET", "POST"]
)
def add_component_comment(id):
    component = Component.query.get(id)
    form = AddComponentComment()
    if form.validate_on_submit():
        new_comment = ComponentComment(
            component_id=id, text=form.text.data, timestamp=datetime.now()
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
