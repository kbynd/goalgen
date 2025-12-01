"""
Template Engine for GoalGen Code Generation

Provides Jinja2-based template rendering with custom filters and utilities
for generating code across all 14 generator modules.
"""

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import json
from typing import Any, Dict, List, Optional
import re


class TemplateEngine:
    """Template engine for code generation"""

    def __init__(self, templates_dir: Path):
        """
        Initialize template engine

        Args:
            templates_dir: Path to templates directory
        """
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Register custom filters
        self.env.filters['camel_case'] = self.camel_case
        self.env.filters['snake_case'] = self.snake_case
        self.env.filters['pascal_case'] = self.pascal_case
        self.env.filters['kebab_case'] = self.kebab_case
        self.env.filters['title_case'] = self.title_case
        self.env.filters['upper_case'] = self.upper_case
        self.env.filters['to_json'] = self.to_json
        self.env.filters['indent'] = self.indent_text
        self.env.filters['quote'] = self.quote
        self.env.filters['comment'] = self.comment

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a template with context

        Args:
            template_name: Template file name (relative to templates_dir)
            context: Template context variables

        Returns:
            Rendered template string
        """
        template = self.env.get_template(template_name)
        return template.render(**context)

    def render_to_file(
        self,
        template_name: str,
        context: Dict[str, Any],
        output_path: Path,
    ) -> None:
        """
        Render template and write to file

        Args:
            template_name: Template file name
            context: Template context variables
            output_path: Output file path
        """
        content = self.render(template_name, context)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)

    # Custom filters

    @staticmethod
    def camel_case(text: str) -> str:
        """Convert to camelCase"""
        parts = re.split(r'[_\-\s]+', text)
        return parts[0].lower() + ''.join(word.capitalize() for word in parts[1:])

    @staticmethod
    def snake_case(text: str) -> str:
        """Convert to snake_case"""
        # Insert underscore before capitals
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        # Insert underscore before capital in sequence
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        # Replace spaces/hyphens with underscore
        s3 = re.sub(r'[\s\-]+', '_', s2)
        return s3.lower()

    @staticmethod
    def pascal_case(text: str) -> str:
        """Convert to PascalCase"""
        parts = re.split(r'[_\-\s]+', text)
        return ''.join(word.capitalize() for word in parts)

    @staticmethod
    def kebab_case(text: str) -> str:
        """Convert to kebab-case"""
        # Insert hyphen before capitals
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', text)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1)
        # Replace spaces/underscores with hyphen
        s3 = re.sub(r'[\s_]+', '-', s2)
        return s3.lower()

    @staticmethod
    def title_case(text: str) -> str:
        """Convert to Title Case"""
        return text.replace('_', ' ').replace('-', ' ').title()

    @staticmethod
    def upper_case(text: str) -> str:
        """Convert to UPPER_CASE"""
        return TemplateEngine.snake_case(text).upper()

    @staticmethod
    def to_json(obj: Any, indent: int = 2) -> str:
        """Convert object to JSON string"""
        return json.dumps(obj, indent=indent)

    @staticmethod
    def indent_text(text: str, spaces: int = 2) -> str:
        """Indent text by number of spaces"""
        indent = ' ' * spaces
        return '\n'.join(indent + line if line.strip() else line
                        for line in text.split('\n'))

    @staticmethod
    def quote(text: str, quote_char: str = '"') -> str:
        """Wrap text in quotes"""
        return f'{quote_char}{text}{quote_char}'

    @staticmethod
    def comment(text: str, lang: str = 'python') -> str:
        """Add comment syntax for language"""
        if lang == 'python':
            return f'# {text}'
        elif lang == 'javascript' or lang == 'typescript':
            return f'// {text}'
        elif lang == 'html':
            return f'<!-- {text} -->'
        elif lang == 'bicep':
            return f'// {text}'
        else:
            return text


def load_spec(spec_path: Path) -> Dict[str, Any]:
    """
    Load goal specification JSON

    Args:
        spec_path: Path to spec JSON file

    Returns:
        Parsed spec dictionary
    """
    with open(spec_path) as f:
        return json.load(f)


def get_context_from_spec(spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract template context from spec

    Args:
        spec: Goal specification

    Returns:
        Template context dictionary with computed values
    """
    goal_id = spec['id']

    context = {
        # Core identifiers
        'goal_id': goal_id,
        'goal_title': spec.get('title', goal_id.replace('_', ' ').title()),
        'goal_description': spec.get('description', ''),

        # Naming variations
        'goal_id_camel': TemplateEngine.camel_case(goal_id),
        'goal_id_pascal': TemplateEngine.pascal_case(goal_id),
        'goal_id_kebab': TemplateEngine.kebab_case(goal_id),
        'goal_id_upper': TemplateEngine.upper_case(goal_id),

        # Spec sections
        'tasks': spec.get('tasks', []),
        'agents': spec.get('agents', {}),
        'tools': spec.get('tools', {}),
        'evaluators': spec.get('evaluators', []),
        'triggers': spec.get('triggers', {}),
        'context_schema': spec.get('context', {}),
        'ux': spec.get('ux', {}),
        'assets': spec.get('assets', {}),

        # Architecture
        'topology': spec.get('topology', {}),
        'state_management': spec.get('state_management', {}),
        'api': spec.get('api', {}),
        'authentication': spec.get('authentication', {}),

        # Deployment
        'deployment': spec.get('deployment', {}),
        'runtime_config': spec.get('runtime_config', {}),

        # Computed values
        'num_tasks': len(spec.get('tasks', [])),
        'num_agents': len(spec.get('agents', {})),
        'num_tools': len(spec.get('tools', {})),
        'num_evaluators': len(spec.get('evaluators', [])),

        # Flags
        'has_teams': spec.get('ux', {}).get('teams', {}).get('enabled', False),
        'has_webchat': spec.get('ux', {}).get('webchat', {}).get('enabled', False),
        'has_evaluators': len(spec.get('evaluators', [])) > 0,
        'has_tools': len(spec.get('tools', {})) > 0,

        # Environment
        'environments': spec.get('deployment', {}).get('environments', ['dev', 'staging', 'prod']),
    }

    return context


# Template directory structure
TEMPLATE_STRUCTURE = {
    'scaffold': [
        'README.md.j2',
        'LICENSE.j2',
        '.gitignore.j2',
        'directory_structure.sh.j2',
    ],
    'langgraph': [
        'quest_builder.py.j2',
        'checkpointer_adapter.py.j2',
        'state.py.j2',
    ],
    'api': [
        'main.py.j2',
        'orchestrator.py.j2',
        'session_store.py.j2',
        'config.py.j2',
        'auth.py.j2',
        'rbac.py.j2',
        'models.py.j2',
        'Dockerfile.j2',
        'requirements.txt.j2',
    ],
    'teams': [
        'manifest.json.j2',
        'adaptive_cards/welcome.json.j2',
        'adaptive_cards/message.json.j2',
        'deploy_team.sh.j2',
    ],
    'webchat': [
        'package.json.j2',
        'vite.config.ts.j2',
        'tsconfig.json.j2',
        'index.html.j2',
        'src/App.tsx.j2',
        'src/main.tsx.j2',
        'src/auth/entra-auth.ts.j2',
        'src/components/ChatWindow.tsx.j2',
        'src/components/MessageList.tsx.j2',
        'src/components/InputBox.tsx.j2',
        'src/signalr-client.ts.j2',
        'src/store.ts.j2',
    ],
    'tools': [
        'function_app/function_app.py.j2',
        'function_app/requirements.txt.j2',
        'function_app/host.json.j2',
        'http_wrapper.py.j2',
    ],
    'agents': [
        'agent_base.py.j2',
        'agent_impl.py.j2',
    ],
    'evaluators': [
        'evaluator_base.py.j2',
        'evaluator_impl.py.j2',
        'rules.py.j2',
    ],
    'infra': [
        'main.bicep.j2',
        'modules/container-app.bicep.j2',
        'modules/function-app.bicep.j2',
        'modules/cosmos.bicep.j2',
        'modules/redis.bicep.j2',
        'modules/keyvault.bicep.j2',
        'modules/signalr.bicep.j2',
        'modules/storage.bicep.j2',
        'modules/log-analytics.bicep.j2',
        'modules/app-insights.bicep.j2',
        'modules/container-registry.bicep.j2',
        'parameters.dev.json.j2',
        'parameters.staging.json.j2',
        'parameters.prod.json.j2',
    ],
    'security': [
        'keyvault-setup.bicep.j2',
        'managed-identity.bicep.j2',
        'rbac-assignments.bicep.j2',
    ],
    'assets': [
        'prompts/system_prompt.txt.j2',
        'prompts/agent_prompts.txt.j2',
    ],
    'cicd': [
        'workflows/deploy.yml.j2',
        'workflows/test.yml.j2',
    ],
    'deployment': [
        'deploy.sh.j2',
        'destroy.sh.j2',
        'local_run.sh.j2',
        'config.sh.j2',
    ],
    'tests': [
        'pytest.ini.j2',
        'conftest.py.j2',
        'unit/test_orchestrator.py.j2',
        'integration/test_langgraph.py.j2',
        'docker-compose.yml.j2',
    ],
}


if __name__ == '__main__':
    # Example usage
    templates_dir = Path(__file__).parent / 'templates'
    engine = TemplateEngine(templates_dir)

    # Test filters
    print('camelCase:', engine.camel_case('travel_planning'))
    print('PascalCase:', engine.pascal_case('travel_planning'))
    print('kebab-case:', engine.kebab_case('travel_planning'))
    print('UPPER_CASE:', engine.upper_case('travel_planning'))
