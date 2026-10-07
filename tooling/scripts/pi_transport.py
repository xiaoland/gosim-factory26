"""Bind Pi's native identities to one endpoint supplied by the run owner."""
import os


def model_bindings(base_url=None, visual_url=None, *, require_key=True,
                   providers=('factory26', 'factory26-visual')):
    endpoint = base_url or os.environ.get('OPENAI_BASE_URL')
    key = os.environ.get('OPENAI_API_KEY')
    if not endpoint or (require_key and not key):
        raise ValueError('Harness requires OPENAI_BASE_URL and OPENAI_API_KEY')
    environment = dict(os.environ)
    if key:
        # Frozen native sessions may retain these historical credential names.
        environment.update(FACTORY26_API_KEY=key, FACTORY26_GATEWAY_TOKEN=key)
    bindings = {name: {'provider': name, 'base_url': endpoint,
                      'credential_env': 'OPENAI_API_KEY'} for name in providers}
    return bindings, environment
