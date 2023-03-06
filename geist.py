#```
# @geist: My name, Geist, is derived from the German word for "spirit" or "ghost".
# ```

import sys
import json
import openai
import getpass

#OpenAI API key in the first argument
openai.api_key_path = sys.argv[1]

#OpenAI ChatML file in the second argument
chatml_file = sys.argv[2]
chatml = []
with open(chatml_file, "r") as f:
  lines = f.readlines()
  for line in lines:
    message = json.loads(line)
    chatml.append(message)

#add the user + message in the third argument
whoiam = getpass.getuser()
chatml.append({"role": "system", "content": "Please prefix all your responses with the name of the user, @" + whoiam + ": "})
chatml.append({"role": "user", "content": sys.argv[3]})

#talk to chatGPT
completion = openai.ChatCompletion.create(
  model="gpt-3.5-turbo", 
  messages=chatml
)

#output the response
print("\n" + completion["choices"][0]["message"]["content"] + "\n")