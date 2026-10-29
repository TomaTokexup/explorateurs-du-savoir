# Premier appel à l'API Claude
from dotenv import load_dotenv
import anthropic

load_dotenv()                  # charge ANTHROPIC_API_KEY depuis le fichier .env
client = anthropic.Anthropic() # le client trouve la clé tout seul

message = client.messages.create(
    model="claude-haiku-5-5",
    max_tokens=300,
    messages=[
        {"role": "user", "content": "Donne une question de calcul mental pour un élève de CM1, avec sa réponse."}
    ],
)

print(message.content[0].text)
print(f"\nTokens utilisés : {message.usage.input_tokens} en entrée, {message.usage.output_tokens} en sortie")