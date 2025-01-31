from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    SubmitField,
    SelectField,
    TextAreaField,
    FloatField,
    BooleanField,
    IntegerField,
    DateField,
    FileField,
    validators,
)
from wtforms.validators import (
    DataRequired,
    InputRequired,
    NumberRange,
    ValidationError,
    Optional,
)
from app.models import (
    Component,
)


class AddComponent(FlaskForm):
    material_number = IntegerField(
        "Material number",
        validators=[DataRequired(message="Material number can't be empty")],
    )
    material_description = TextAreaField("Material description", validators=[])
    supplier_material_number = IntegerField(
        "Supplier material number",
        validators=[DataRequired(message="Supplier material number can't be empty")],
    )
    manufacturer_part = TextAreaField(
        "Manufacturer part",
        validators=[DataRequired(message="Manufacturer part can't be empty")],
    )

    submit = SubmitField("Add new component")

    def validate_material_number(self, field):
        material_number = field.data
        component = Component.query.filter_by(material_number=material_number).first()
        if component:
            raise ValidationError("Component is already registered")


class UpdateComponentNote(FlaskForm):
    note = TextAreaField(
        "New note",
        validators=[DataRequired(message="New note can't be empty")],
    )
    submit = SubmitField("Update note")


class UpdateComponentLeadtime(FlaskForm):
    new_leadtime = IntegerField(
        "New leadtime",
        validators=[DataRequired(message="New leadtime can't be empty")],
    )
    submit_leadtime = SubmitField("Update leadtime")


class UpdateComponentUnitPrice(FlaskForm):
    unit_price = FloatField(
        "New unit price",
        validators=[DataRequired(message="New unit price can't be empty")],
    )
    submit = SubmitField("Update unit price")


class UpdateComponentStatus(FlaskForm):
    status = SelectField(
        "New status",
        validators=[DataRequired(message="New status can't be empty")],
    )
    submit = SubmitField("Update status")


class UpdateComponentStock(FlaskForm):
    new_stock = IntegerField(
        "New QTY",
        validators=[],
    )
    submit_stock = SubmitField("Update stock qty")


class UpdateComponentOrders(FlaskForm):
    new_orders = IntegerField(
        "New QTY",
        validators=[],
    )
    submit_orders = SubmitField("Update orders qty")


class AddComponentComment(FlaskForm):
    text = TextAreaField(
        "New comment",
        validators=[DataRequired(message="New comment can't be empty")],
    )
    submit = SubmitField("Add comment")


class SearchComponent(FlaskForm):
    component = StringField("Search component", validators=[DataRequired()])
    submit_search = SubmitField("Search")


class AddNewVarious(FlaskForm):
    new_various_name = StringField("Various name", validators=[DataRequired()])
    new_various_value = StringField("Various value", validators=[DataRequired()])
    submit = SubmitField("Add various")


class UpdateVarious(FlaskForm):
    new_various_value = StringField("Various value", validators=[DataRequired()])
    submit = SubmitField("Update various")
