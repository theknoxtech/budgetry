import plaid
from plaid.api import plaid_api
from flask import current_app


ENV_MAP = {
    'sandbox': plaid.Environment.Sandbox,
    'development': plaid.Environment.Development,
    'production': plaid.Environment.Production,
}


def get_plaid_client():
    env = current_app.config.get('PLAID_ENV', 'sandbox')
    configuration = plaid.Configuration(
        host=ENV_MAP.get(env, plaid.Environment.Sandbox),
        api_key={
            'clientId': current_app.config['PLAID_CLIENT_ID'],
            'secret': current_app.config['PLAID_SECRET'],
        }
    )
    api_client = plaid.ApiClient(configuration)
    return plaid_api.PlaidApi(api_client)
