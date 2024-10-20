import codecs
from django.apps import apps
from django.core.management import BaseCommand

from puml_generator.management.commands.utils.utils import PlantUml, uml_to_url


def add_bool_arg(parser, name, help_yes, help_no, default=False):
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--' + name, dest=name, help=help_yes, action='store_true')
    group.add_argument('--no-' + name, dest=name, help=help_no, action='store_false')
    parser.set_defaults(**{name: default})


class Command(BaseCommand):
    help = 'Generate PlantUML diagram of project'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='output file',
            default='models_diagram.puml',
        )
        parser.add_argument(
            '--omit',
            type=str,
            nargs='+',
            help='omit applications',
        )
        parser.add_argument(
            '--include',
            type=str,
            nargs='+',
            help='include applications',
        )
        parser.add_argument(
            '--skip-choices-fields',
            type=str,
            nargs='+',
            help='skip specified choices fields',
        )
        add_bool_arg(
            parser, 'add-help',
            'docstrings should be included to diagram',
            'docstrings should not be included to diagram'
        )
        add_bool_arg(
            parser, 'add-choices',
            'models Choices fields should be described',
            'models Choices fields should not be described'
        )
        add_bool_arg(
            parser, 'split-choices',
            'models Choices fields should be generated per model',
            'models Choices fields should collapse into one if equally named'
        )
        add_bool_arg(
            parser, 'add-omitted-headers',
            'omitted models should be included as headers',
            'omitted models should not be included at all'
        )
        add_bool_arg(
            parser, 'headers-only',
            'use only model header and relations, omit fields list',
            'describe model fields'
        )
        add_bool_arg(
            parser, 'omit-history',
            'omit django-simple-history models',
            'include django-simple-history models'
        )
        parser.add_argument(
            '--title',
            type=str,
            nargs='?',
            help='provide title',
        )
        parser.add_argument(
            '--title-font-size',
            type=int,
            default=72,
            nargs='?',
            help='title font size',
        )
        add_bool_arg(
            parser, 'add-legend',
            'include explanation of the symbols used',
            'do not include explanation of the symbols used'
        )
        add_bool_arg(
            parser, 'url',
            'generate URL with diagram to planuml.com',
            'do not generate URL with diagram to planuml.com'
        )

    def handle(self, *args, **options):
        output = options['file']
        generate_with_help = options['add-help']
        generate_with_choices = options['add-choices']
        generate_with_split_choices = options['split-choices']
        skip_choices_fields = options['skip-choices-fields']
        generate_with_legend = options['add-legend']
        generate_with_omitted_headers = options['add-omitted-headers']
        generate_headers_only = options['headers-only']
        omit_history = options['omit-history']
        include = options['include']
        omit = options['omit']
        title = options['title']
        title_font_size = options['title_font_size']

        models = apps.get_models()
        generator = PlantUml(
            models,
            title=title,
            title_font_size=title_font_size,
            with_legend=generate_with_legend,
            with_help=generate_with_help,
            with_choices=generate_with_choices,
            split_choices=generate_with_split_choices,
            skip_choices_fields=skip_choices_fields,
            omit_history=omit_history,
            include=include,
            omit=omit,
            with_omitted_headers=generate_with_omitted_headers,
            generate_headers_only=generate_headers_only,
        )
        uml = generator.generate_puml_class_diagram()

        with codecs.open(output, 'w', encoding='utf-8') as file:
            file.write(uml)

        if options['url']:
            self.stdout.write(f"See your diagram at {uml_to_url(uml)}")
