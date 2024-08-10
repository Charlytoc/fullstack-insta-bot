from server.utils.groq_actions import create_groq_completion
from server.utils.agent_data import get_system_prompt

completion = create_groq_completion(system_prompt=get_system_prompt(""),prompt= "Que días atiende la doctora y en que horario")


print(completion)

print(len(completion))