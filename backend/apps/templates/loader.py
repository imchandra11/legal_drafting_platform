from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

class TemplateLoader:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader("templates"),
            autoescape=select_autoescape()
        )
        
    def render_template(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(context)
    
    def get_fields(self, template_name: str) -> list:
        template = self.env.get_template(template_name)
        return list(template.make_module().variables)