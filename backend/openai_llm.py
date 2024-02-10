import os
from openai import OpenAI
from langchain_openai import ChatOpenAI 
from numpy import dot
from numpy.linalg import norm

openai_api_key = os.environ.get("OPENAI_API_KEY")

embeddings = OpenAI(api_key=openai_api_key)

llm = ChatOpenAI(openai_api_key=openai_api_key, model='gpt-3.5-turbo-0125', temperature=0.5)

def generate_tasks(event_description: str, user_description: str):
    context = 'Here is a description and list of tasks of the volunteering event: \n' + event_description + '\n\n' + "Here is the user's list of skills, description of his interests and past volunteer experiences : " + user_description + '\n\n'
    query = 'Can you generate 3 to 5 personalized tasks for the user that are tailored to the event? Try not to repeat tasks that are already in the event description. Do not use any lists, keep the response in a single paragraph.'

    prompt = context + '\n\n' + query
    return llm.invoke(prompt).content

def get_embeddings(text: str):
    return embeddings.embeddings.create(input=text, model="text-embedding-3-small").data[0].embedding

def get_cosine_similarity(embedding1, embedding2):
    return dot(embedding1, embedding2)/(norm(embedding1)*norm(embedding2))