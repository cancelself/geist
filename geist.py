#```
# @geist: My name, Geist, is derived from the German word for "spirit" or "ghost".
# ```
import os
import sys
import glob
import json
import openai
import getpass

if len(sys.argv) < 3:
    print("Usage: geist.py <openai_api_path> <chatml_file_or_directory> <user_input>")
    sys.exit(1)

#OpenAI API key in the first argument
openai.api_key_path = sys.argv[1]

#OpenAI ChatML file or directory in the second argument
chatml_path = sys.argv[2]

if os.path.isfile(chatml_path):
    chatml_files = [chatml_path]
elif os.path.isdir(chatml_path):
    chatml_files = glob.glob(chatml_path + "/*.chatml")
else:
    raise ValueError("ChatML path must be a file or directory.")

for chatml_file in chatml_files:

    chatml = []
    with open(chatml_file, "r") as f:
        lines = f.readlines()
        for line in lines:
            message = json.loads(line)
            chatml.append(message)

    #add the user + message in the third argument
    whoiam = getpass.getuser()
    prompt = {"role": "user", "content": sys.argv[3], "name": whoiam}
    chatml.append(prompt)

    #talk to chatGPT
    completion = openai.ChatCompletion.create(
      model = "gpt-3.5-turbo", 
      messages = chatml + [prompt]
    )

    #output the response
    response_message = completion["choices"][0]["message"]["content"]
    response_object = {"role": "assistant", "content": response_message, "name": "geist"}
    print("\n" + response_message + "\n")

    # Save log to ChatML file
    with open(chatml_file, "a") as f:
        f.write(json.dumps(prompt) + "\n")
        f.write(json.dumps(response_object) + "\n")