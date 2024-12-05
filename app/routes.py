from datetime import datetime
from flask import render_template, flash, redirect, url_for
from flask import current_app as app
from app import db
from app.models import Component, ComponentComment


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
