from functools import partial
from webargs import fields
from webargs.aiohttpparser import parser, use_args
from marshmallow import Schema, validate
from .utils import check_valid_date
from app.views.config import config

citizen_info = {
    "citizen_id": fields.Int(required=True),
    "town": fields.Str(required=True),
    "street": fields.Str(required=True),
    "building": fields.Str(required=True),
    "apartment": fields.Int(required=True),
    "name": fields.Str(required=True),
    "birth_date": fields.Str(
        validate=partial(check_valid_date, date_format=config['birth_date_format']),
        required=True
        ),
    "gender": fields.Str(
        validate=validate.OneOf(config['valid_genders']),
        required=True
    ),
    "relatives": fields.List(
        fields.Int(),
        required=True
    )
}

recieve_import_data_args = {
    "citizens" : fields.List(
        fields.Nested(citizen_info, required=True),
        required=True
    )
}


update_citizen_info_args = {
    "town": fields.Str(),
    "street": fields.Str(),
    "building": fields.Str(),
    "apartment": fields.Int(),
    "name": fields.Str(),
    "birth_date": fields.Str(
        validate=partial(check_valid_date,
            date_format=config['birth_date_format']
        )
    ),
    "gender": fields.Str(
        validate=validate.OneOf(config['valid_genders'])
    ),
    "relatives": fields.List(
        fields.Int()
    )
}
