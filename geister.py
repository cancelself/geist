import sys
import glob
import json
import openai
import getpass

#OpenAI API key in the first argument
openai.api_key_path = sys.argv[1]

#OpenAI ChatML directory in the second argument
chatml_dir = sys.argv[2]

#get all the .chatml files in the directory
chatml_files = glob.glob(chatml_dir + "/*.chatml")

chatml = [] #todo: we need to decide if we to append the previous chatml responses or not?

#loop through all the chatml files
for chatml_file in chatml_files:
  with open(chatml_file, "r") as f:
    lines = f.readlines()
    for line in lines:
      message = json.loads(line)
      chatml.append(message)

    #add the user + message in the third argument
    whoiam = getpass.getuser()
    #chatml.append({"role": "system", "content": "Use @" + whoiam + " to address me."})
    chatml.append({"role": "user", "content": sys.argv[3]})

    #talk to chatGPT
    completion = openai.ChatCompletion.create(
      model="gpt-3.5-turbo", 
      messages=chatml
    )

    #output the response
    #we need to print out the chatml filename as the name of the assistant
    #get just the filename, not the path
    print("\n" + "@" + chatml_file.split("/")[-1].split(".")[0] + ": " + completion["choices"][0]["message"]["content"])
