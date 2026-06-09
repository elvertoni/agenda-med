import os
import django
import sys
sys.path.append('c:\\PROJETOS\\clinica-agenda')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from messaging.chatbot import handle_incoming
print('Calling handle_incoming...')
res = handle_incoming('5511999999999', 'Oi')
print('Response:', res)
