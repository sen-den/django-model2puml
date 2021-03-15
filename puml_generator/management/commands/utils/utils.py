import colorsys
from hashlib import md5
from typing import Optional, Tuple
import textwrap

CHOICES_COLOR = '#EEE'
AUTO_FIELDS = {"AutoField", "AutoLastModifiedField", "AutoCreatedField"}

LEGEND = """
    class "Explanation of the symbols used" as DESCRIPTION #FFF {
    - AutoField (identifiers)
    ..
    + Regular field (anything)
    ..
    # ForeignKey (ManyToMany)
    ..
    ~ ForeignKey (OneToOne, OneToMany)
    --
}\n\n
"""


def app_name_to_colour(name: str) -> str:
    """
    Generate RGB colour based on name.
    :param name: application name
    :return: #RGB
    """

    def _h(v: float):
        return str(hex(int(v * 255)))[2:].ljust(2).replace(' ', '0')

    # encode colour hue as name hash
    hue = int(md5(name.encode()).hexdigest(), 16) % 360 / 360.0
    r, g, b = colorsys.hls_to_rgb(hue, 0.90, 0.60)
    r, g, b = _h(r), _h(g), _h(b)
    return f'#{r}{g}{b}'


class PlantUml:
    def __init__(
            self,
            models=None,
            title=None,
            with_legend=False,
            with_help=True,
            with_choices=True,
            include=None,
            omit=None,
            with_omitted_headers=False,
            generate_headers_only=False,
    ):
        self.models = models
        self.title = title
        self.with_legend = with_legend
        self.with_help = with_help
        self.with_choices = with_choices
        self.include = include
        self.omit = omit
        self.with_omitted_headers = with_omitted_headers
        self.generate_headers_only = generate_headers_only
        self.legend = LEGEND

    @staticmethod
    def is_app_member(model, app_name: str) -> bool:
        """
        Checks is model a member of app_name or not.
        :param model: django model instance
        :param app_name: label of django application
        :return:
        """
        return str(model._meta.label).startswith(app_name + '.')

    def is_allowed_related(self, related) -> bool:
        """
        Checks is related class have to be rendered or not.
        :param related: django model field
        :return:
        """
        if not self.omit and not self.include:
            return True
        omit = self.omit or []
        include = self.include or []
        is_omitted = any([
            self.is_app_member(self.retrieve_field_related_model(related), app_name) for app_name in omit
        ])
        is_included = any([
            self.is_app_member(self.retrieve_field_related_model(related), app_name) for app_name in include
        ])
        if include and not is_included:
            return False
        return not is_omitted

    @staticmethod
    def wrap_text(text: str, limit: int = 80, limit_first: int = 80) -> str:
        """
        Limit text width
        :param text: text to be formatted
        :param limit: width limit
        :param limit_first: special limit for first line
        :return: formatted text
        """
        strings = []
        lines = text.splitlines()
        for ix in lines:
            strings += textwrap.wrap(ix, width=limit, initial_indent=' '*(limit - limit_first))
        clean_text = str('\n').join(strings).strip()
        return clean_text

    def field_repr(self, field) -> str:
        """
        Generate PlantUML representation of model field.
        :param field: django models field
        :return: representation
        """
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
        field_description = f'    {sign} {field.name} ({field.__class__.__name__})'
        uml += field_description

        if self.with_help:
            description_len = len(field_description)
            doc = self.wrap_text(field.help_text, 80, 80-description_len) if field.help_text else ''
            uml += f' - {doc}'
        uml += '\n'
        return uml

    @staticmethod
    def choice_repr(name, items) -> str:
        """
        Generate PlantUML representation of model field choices as class.
        :param name: choices list name
        :param items: dict of choices values
        :return: representation
        """
        uml = ''
        if items:
            uml += f'enum "{name} <choices>" as {name} {CHOICES_COLOR}'
            uml += f'{{\n'
            for choice, description in items.items():
                uml += f'    + {choice} - {description}\n'
            uml += f'}}\n\n'
        return uml

    @staticmethod
    def collect_choices(field) -> Optional[dict]:
        """
        Collect choices of model field in the case exists.
        :param field: choices of django models field
        :return: dict of choices values
        """
        if field.choices:
            choices = field.choices
            if type(choices).__name__ == 'Choices':
                return choices._display_map
            elif isinstance(choices, tuple):
                return {k: (k, v) for k, v in choices}

    def model_repr(self, model) -> Tuple[str, dict]:
        """
        Generate PlantUML representation of model class.
        Links to related models and choices would be added where suitable.
        :param model: django model
        :return: representation; dict of choices
        """
        uml = ''
        meta = model._meta
        model_choices = dict()
        uml += f'class "{meta.label} <{meta.app_config.verbose_name}>" as {meta.label}'
        app, name = str(meta.label).split('.')
        app_colour = app_name_to_colour(app)
        uml += f' {app_colour} '
        uml += f'{{\n'
        uml += f'    {meta.verbose_name}\n'

        if self.with_help:
            # add help text stored in docstring
            uml += f'    ..\n'
            docstring = str(model.__doc__).strip().replace("\n\n", "\n")
            doc = self.wrap_text(docstring)
            uml += f'    {doc}\n'
        uml += f'    --\n'

        fields = list(meta.fields)
        fields.extend(meta.many_to_many)

        for field in fields:
            if not self.generate_headers_only:
                # add field to model representation
                uml += self.field_repr(field)

            if self.with_choices:
                # collect field choices to future processing
                choices = self.collect_choices(field)
                if choices:
                    model_choices[field.name] = choices

        uml += f'    --\n'
        uml += f'}}\n'

        # add links to related models
        uml += self.model_relations_repr(meta)

        if self.with_choices:
            # generate links to choices list classes
            for choice_field_name, choices in model_choices.items():
                uml += f'{meta.label} .-- {choice_field_name}\n'

        uml += f'\n\n'
        return uml, model_choices

    @staticmethod
    def retrieve_field_related_model(field) -> Optional:
        """
        In the case field represents link to related model retrieves model.
        :param field: django model field
        :return: django model
        """
        if type(field).__name__ == 'ForeignKey':
            return field.foreign_related_fields[0].model
        elif type(field).__name__ == 'ManyToManyField':
            return field.target_field.model

    def model_relations_repr(self, meta) -> str:
        """
        Generate PlantUML representation of model relations.
        :param meta: django model meta
        :return: representation
        """
        uml = ''
        foreign_line = '*--'
        many_to_many_line = '*--*'

        fields = list(meta.fields)
        fields.extend(meta.many_to_many)
        # generate links to related models
        for related in list(filter(lambda x: type(x).__name__ == 'ForeignKey', fields)):
            if self.with_omitted_headers or self.is_allowed_related(related):
                related_meta = related.foreign_related_fields[0].model._meta
                uml += f'{meta.label} {foreign_line} {related_meta.label}\n'
        for related in list(filter(lambda x: type(x).__name__ == 'ManyToManyField', fields)):
            if self.with_omitted_headers or self.is_allowed_related(related):
                related_meta = related.target_field.model._meta
                uml += f'{meta.label} {many_to_many_line} {related_meta.label}\n'
        return uml

    def generate_puml_class_diagram(self) -> str:
        """
        Generate django applications PlantUML annotation.
        Based on context passed.
        :return: string of PlantUML classes annotation
        """
        global_choices = dict()

        uml = "@startuml\n"

        if self.title:
            uml += f"""
            skinparam titleFontSize 72

            title
            {self.title}
            end title\n
            """
        if self.with_legend:
            uml += self.legend

        for model in self.models:
            # omit model in the case it is omited or not included
            if self.omit and any([self.is_app_member(model, to_omit) for to_omit in self.omit]):
                continue
            if self.include and all([not self.is_app_member(model, to_include) for to_include in self.include]):
                continue
            model_uml, model_choices = self.model_repr(model)
            uml += model_uml
            # collect model choices to future processing
            global_choices = {**global_choices, **model_choices}

        if self.with_choices:
            # generate choices list classes
            for key, values in global_choices.items():
                uml += self.choice_repr(key, values)

        uml += "@enduml\n"
        return uml
