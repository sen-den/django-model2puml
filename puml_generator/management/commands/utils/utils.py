import colorsys
from hashlib import md5
from typing import Optional, Tuple

from django.db.models import ForeignKey, ManyToManyField
from model_utils import Choices


def app_name_to_colour(name: str):
    def _h(v: float):
        return str(hex(int(v * 255)))[2:].ljust(2).replace(' ', '0')

    hue = int(md5(name.encode()).hexdigest(), 16) % 360 / 360.0
    r, g, b = colorsys.hls_to_rgb(hue, 0.90, 0.60)
    r, g, b = _h(r), _h(g), _h(b)
    return f'#{r}{g}{b}'


CHOICES_COLOR = '#EEE'
AUTO_FIELDS = {"AutoField", "AutoLastModifiedField", "AutoCreatedField"}


def field_repr(field, with_help=False) -> str:
    uml = ''
    sign = '+'
    if field.__class__.__name__ in AUTO_FIELDS:
        sign = '-'
    elif field.__class__.__name__ == "ForeignKey":
        sign = '~'
    elif field.__class__.__name__ == "OneToOneField":
        sign = '~'
    elif field.__class__.__name__ == "ManyToManyField":
        sign = '#'
    uml += f'    {sign} {field.name} ({field.__class__.__name__})'
    if with_help:
        uml += f' - {field.help_text}' if field.help_text else ''
    uml += '\n'
    return uml


def choice_repr(name, items) -> str:
    uml = ''
    if items:
        uml += f'enum "{name} <choices>" as {name} {CHOICES_COLOR}'
        uml += f'{{\n'
        for choice, description in items.items():
            uml += f'    + {choice} - {description}\n'
        uml += f'}}\n\n'
    return uml


def collect_choices(field) -> Optional:
    if field.choices:
        choices = field.choices
        if isinstance(choices, Choices):
            return choices._display_map
        elif isinstance(choices, tuple):
            return {k: (k, v) for k, v in choices}


def model_repr(model, with_help=True, with_choices=True) -> Tuple[str, dict]:
    uml = ''
    meta = model._meta
    model_choices = dict()
    uml += f'class "{meta.label} <{meta.app_config.verbose_name}>" as {meta.label}'
    app, name = str(meta.label).split('.')
    app_colour = app_name_to_colour(app)
    uml += f' {app_colour} '
    uml += f'{{\n'
    uml += f'    {meta.verbose_name}\n'

    if with_help:
        uml += f'    ..\n'
        doc = str(model.__doc__).strip().replace("\n\n", "\n")
        uml += f'    {doc}\n'
    uml += f'    --\n'

    fields = list(meta.fields)
    fields.extend(meta.many_to_many)

    for field in fields:
        uml += field_repr(field, with_help=with_help)

        if with_choices:
            choices = collect_choices(field)
            if choices:
                model_choices[field.name] = choices

    uml += f'    --\n'
    uml += f'}}\n'

    for related in list(filter(lambda x: isinstance(x, ForeignKey), fields)):
        uml += f'{meta.label} -- {related.foreign_related_fields[0].model._meta.label}\n'
    for related in list(filter(lambda x: isinstance(x, ManyToManyField), fields)):
        uml += f'{meta.label} -- {related.target_field.model._meta.label}\n'

    if with_choices:
        for choice_field_name, choices in model_choices.items():
            uml += f'{meta.label} .- {choice_field_name}\n'

    uml += f'\n\n'
    return uml, model_choices


def is_app_member(model, app_name: str):
    return  str(model._meta.label).startswith(app_name + '.')


def generate_puml_class_diagram(
        models,
        with_help=True,
        with_choices=True,
        include=None,
        omit=None,
) -> str:
    global_choices = dict()

    uml = "@startuml\n"

    for model in models:
        if omit and any([is_app_member(model, to_omit) for to_omit in omit]):
            continue
        if include and all([not is_app_member(model, to_include) for to_include in include]):
            continue
        model_uml, model_choices = model_repr(model, with_help=with_help, with_choices=with_choices)
        uml += model_uml
        global_choices = {**global_choices, **model_choices}

    if with_choices:
        for key, values in global_choices.items():
            uml += choice_repr(key, values)

    uml += "@enduml\n"
    return uml
