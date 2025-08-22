import requests
import json
from contratrix_api.settings import Settings

def send_email(name:str, recipientEmail: str, templateId: int, params: any):
    url = "https://api.brevo.com/v3/smtp/email"
    payload = json.dumps(
        {
            "to": [{"name": name, "email": f"{recipientEmail}"}],
            "templateId": templateId,
            "params": params,
            "sender": {
                "name": "Equipe Stylest.IA", 
                "email": "contato@stylestia.com.br"
            }
        }
    )
    headers = {
        "accept": "application/json",
        "api-key": Settings().BREVO_TOKEN,
        "content-type": "application/json",
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response)