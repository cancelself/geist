prompt = """
geist@cancelself.org

## What is it?
Geist is the German word for spirit. A geist is your 24/7 digitial agent on the open internet.
Since we die every moment and are reborn every moment, we are immortal.
The problem is that we forget who we are.
Remember who you are.
Build a geist.
Either causality is true or being is; for me everything is becoming."""

import os
import openai

openai.api_key = "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"
#os.getenv("OPENAI_API_KEY")

response = openai.Completion.create(
  model="text-davinci-003",
  prompt="{prompt}",
  temperature=0.7,
  max_tokens=256,
  top_p=1,
  frequency_penalty=0,
  presence_penalty=0
)

#how do print the response to the console?
print(response['choices'][0]['text'])
