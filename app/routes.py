from datetime import datetime
from flask import render_template
from flask import current_app as app
from app import db


@app.context_processor
def inject_date_cw():
    current_date = datetime.now().date()
    week_number = current_date.isocalendar()[1]
    return dict(current_date=current_date, week_number=week_number)


@app.route("/", methods=["GET", "POST"])
def base_view():
    return render_template("base.html", title=f"Base view")
