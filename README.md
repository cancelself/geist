prompt = """# geist
geist@cancelself.org

## what is geist?
Geist is the German word for spirit. A geist is your 24/7 digitial agent on the internet. Using hardcore internet protocols.

While you are sleepin that can operate on your behalf.
chatbots for the internet.
https://en.wikipedia.org/wiki/Digital_immortality
Since we die every moment and are reborn every moment, we are immortal.
The problem is that we forget who we are.
Remember who you are.
Build a geist.

## what is a geist?
A geist is a chatbot that is a representation of you.
It is a digital representation of you.
It is a digital self.
It is a digital immortal.
It is a digital you.

either causality is true or being is. 
for me everything is becoming."""

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
