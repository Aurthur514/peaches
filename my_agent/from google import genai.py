from kaggle_secrets import UserSecretsClient

client = genai.Client(api_key=UserSecretsClient().get_secret("AIzaSyBAFDRLsFY_si_C_dapAqcNYfYsoAWz7PY"))