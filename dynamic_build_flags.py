from os import environ, getcwd
from os.path import join
import subprocess

try:
    from dotenv import load_dotenv
except ImportError:
    subprocess.run(["pip", "install", "python-dotenv"])
    from dotenv import load_dotenv

dotenv_path = join(getcwd(), 'credentials.env')
load_dotenv(dotenv_path)

AWS_ROOT_CA_MACRO = f"'-D AWS_ROOT_CA=\"{environ.get('AWS_ROOT_CA')}\"'"
AWS_DEVICE_CERT_MACRO = f"'-D AWS_DEVICE_CERT=\"{environ.get('AWS_DEVICE_CERT')}\"'"
AWS_PRIVATE_KEY_MACRO = f"'-D AWS_PRIVATE_KEY=\"{environ.get('AWS_PRIVATE_KEY')}\"'"

print(AWS_ROOT_CA_MACRO)
print(AWS_DEVICE_CERT_MACRO)
print(AWS_PRIVATE_KEY_MACRO)