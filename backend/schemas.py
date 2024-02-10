from pydantic import BaseModel

class UserCreate(BaseModel): #what data format I expect when user creates an account
    email: str
    full_name: str
    password: str
    age: int
    gender: str #can be 'M' or 'F'
    phone_number: str
    work_status: str
    immigration_status: str
    skills: str
    interests: str
    past_volunteer_experience: str

class UserLogin(BaseModel): #what data format I expect when user logs in
    email: str
    password: str

class ChangeAdmin(BaseModel): #what data format I expect when user changes another user's admin status
    curr_user_email: str
    new_user_email: str

class ChangeEvent(BaseModel): #what data format I expect when we create or change an event
    email: str
    title: str
    date: str
    time: str
    requirements: str
    capacity: int
    deadline: str
    location: str
    description: str
    tasks: str
    
class AdminEvent(BaseModel): #what data format I expect when we delete an event
    email: str
    title: str

class KickUser(BaseModel): #what data format I expect when we kick a user from an event
    curr_user_email: str
    new_user_email: str
    title: str
    
class GenerateTasks(BaseModel): #what data format I expect when I generate tasks for a user
    user_email: str
    event_title: str
    
#key is field name, value is list of possible values
profile_choices = {'gender': ['m', 'f'], 'work_status': ['student', 'employed', 'unemployed'], 'immigration_status': ['citizen', 'pr', 'student visa' , 'other']}