from datetime import datetime
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
)
from app.forms import (
    AddComponent,
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
    components = Component.query.order_by(Component.id.asc()).all()

    return render_template(
        "all_components.html",
        title=f"All components",
        components=components,
    )


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


@app.route("/all_components/component_view/<id>", methods=["GET", "POST"])
def component_view(id):
    component = Component.query.get(id)
    return render_template(
        "component.html",
        title=f"{component.material_number}",
        component=component,
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


@app.route("/all_components/component_view/<id>/change_check", methods=["GET", "POST"])
def change_check(id):
    component = Component.query.get(id)
    component.check = not component.check
    db.session.commit()
    return redirect(request.referrer)


@app.route(
    "/all_components/component_view/<id>/change_on_shortage", methods=["GET", "POST"]
)
def change_shortage(id):
    component = Component.query.get(id)
    component.on_shortage = not component.on_shortage
    db.session.commit()
    return redirect(request.referrer)


@app.route("/all_components/component_view/<id>/update_note", methods=["GET", "POST"])
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
    "/all_components/component_view/<id>/update_leadtime", methods=["GET", "POST"]
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
    "/all_components/component_view/<id>/update_unit_price", methods=["GET", "POST"]
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


@app.route("/all_components/component_view/<id>/update_status", methods=["GET", "POST"])
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
    "/all_components/component_view/<id>/update_qty/<qty_type>/<qty_name>",
    methods=["GET", "POST"],
)
def update_component_qty(id, qty_type, qty_name):
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
