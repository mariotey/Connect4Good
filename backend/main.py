from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
import schemas, models #schemas represents format expecting from frontend, models represents database format
from database import Base, engine, SessionLocal
from utils import get_password_hash, verify_password, reset_db
from openai_llm import generate_tasks, get_embeddings, get_cosine_similarity
import uuid

Base.metadata.create_all(bind=engine) #creates the tables in the database if they don't exist

def get_session(): #function to get the database session
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

app = FastAPI()


#call this endpoint to register a user
#expecting a JSON in the schema of UserCreate
#returning a JSON with a success message in the form {'message': message} or an error message if user already exists
@app.post('/register') 
def register_user(request: schemas.UserCreate, db: Session = Depends(get_session)):
    check_existing = db.query(models.User).filter(models.User.email == request.email).first() 
    if check_existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')

    unique_id = str(uuid.uuid4())
    password = get_password_hash(request.password)
    
    if request.age <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid value for Age')
    if request.gender.lower() not in schemas.profile_choices['gender']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid value for Gender: M or F')
    if request.work_status.lower() not in schemas.profile_choices['work_status']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid value for Work Status: Student, Employed, or Unemployed')
    if request.immigration_status.lower() not in schemas.profile_choices['immigration_status']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid value for Immigration Status: Citizen, PR, Student Visa, or Other')
        
    new_user = models.User(id=unique_id, email=request.email, full_name=request.full_name, password=password, age=request.age, gender=request.gender, phone_number=request.phone_number, work_status=request.work_status, immigration_status=request.immigration_status, skills=request.skills, interests=request.interests, past_volunteer_experience=request.past_volunteer_experience)
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {'message': 'User and Profile registered successfully'}


#call this endpoint to login a user
#expecting a JSON in the schema of UserLogin
#returning a JSON with a success message in the form {'message': message} or an error message if email or password is incorrect
@app.post('/login')
def login_user(request: schemas.UserLogin, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == request.email).first() 
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect Email')
    
    hashed_password = user.password
    if not verify_password(request.password, hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect Password')
    
    return {'message': 'Login successful'}


#call this endpoint to reset the database -> fully deletes and recreates the tables
#not expecting any input
#returning a JSON with a success message in the form {'message': message}
@app.post('/reset_db')
def reset_database():
    reset_db()
    return {'message': 'Database reset successfully'}


#call this endpoint to get all information about a user
#expecting the email of the user as a string
#returning a JSON with all the information about the user - see format below 
@app.get('/user/get_user')
def get_user(email: str, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    
    events_registered = []
    for event_id in user.events_registered:
        event = db.query(models.Event).filter(models.Event.id == event_id).first()
        if not event:
            continue
        events_registered.append(event.title)
    
    return {'email': user.email,
            'full_name': user.full_name,
            'is_admin': user.is_admin, #note this is a boolean value, 'true' or 'false
            'password': user.password,
            'age': user.age,
            'gender': user.gender,
            'phone_number': user.phone_number,
            'work_status': user.work_status,
            'immigration_status': user.immigration_status,
            'skills': user.skills,
            'interests': user.interests,
            'past_volunteer_experience': user.past_volunteer_experience,
            'events_registered': events_registered #note this is a list of event titles, can be empty
            }


#call this endpoint to update the information about a user
#when a user calls them, show them their profile with all their current info filled in -> send me the entire profile with all fields and I will update
#in the DB -> this way you don't need to specify which fields are being updated as I will simply be updating all fields
#expecting a JSON in the schema of UserCreate
#returning a JSON with a success message in the form {'message': message} or an error message if any of the updated values are invalid
@app.post('/user/update_user')
def update_user(request: schemas.UserCreate, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    if request.age <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid value for Age')
    if request.gender.lower() not in schemas.profile_choices['gender']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid value for Gender: M or F')
    if request.work_status.lower() not in schemas.profile_choices['work_status']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid value for Work Status: Student, Employed, or Unemployed')
    if request.immigration_status.lower() not in schemas.profile_choices['immigration_status']:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid value for Immigration Status: Citizen, PR, Student Visa, or Other')
    
    user.email = request.email
    user.full_name = request.full_name
    user.password = get_password_hash(request.password)
    user.age = request.age
    user.gender = request.gender
    user.phone_number = request.phone_number
    user.work_status = request.work_status
    user.immigration_status = request.immigration_status
    user.skills = request.skills
    user.interests = request.interests
    user.past_volunteer_experience = request.past_volunteer_experience
    
    db.commit()
    return {'message': 'User and Profile updated successfully'}


#call this endpoint to delete a user
#expecting the email of the user as a string
#returning a JSON with a success message in the form {'message': message} or an error message if user not found
@app.post('/user/delete_user')
def delete_user(email: str, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    
    db.delete(user)
    db.commit()
    return {'message': 'User and Profile deleted successfully'}


#call this endpoint to check if user is an admin
#expecting the email of the user as a string
#returning a JSON with a boolean value in the form {'is_admin': is_admin} or an error message if user not found
@app.get('/user/is_admin')
def is_admin(email: str, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    
    return {'is_admin': user.is_admin}


#call this endpoint to promote another user to admin - current user must be an admin and the new user must exist
#expecting a JSON in the schema of ChangeAdmin
#returning a JSON with a success message in the form {'message': message} or an error message if either user not found or current user is not an admin
@app.post('/user/promote_admin')
def promote_admin(request: schemas.ChangeAdmin, db: Session = Depends(get_session)):
    curr_user = db.query(models.User).filter(models.User.email == request.curr_user_email).first()
    new_user = db.query(models.User).filter(models.User.email == request.new_user_email).first()
    
    if not curr_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Admin User not found')
    if not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='New User not found')
    if not curr_user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Current User is not an admin')
    
    new_user.is_admin = True
    db.commit()
    return {'message': 'User promoted to admin successfully'}

#call this endpoint to demote another user from admin - current user must be an admin and the new user must exist
#expecting a JSON in the schema of ChangeAdmin
#returning a JSON with a success message in the form {'message': message} or an error message if either user not found or current user is not an admin
@app.post('/user/demote_admin')
def demote_admin(request: schemas.ChangeAdmin, db: Session = Depends(get_session)):
    curr_user = db.query(models.User).filter(models.User.email == request.curr_user_email).first()
    new_user = db.query(models.User).filter(models.User.email == request.new_user_email).first()
    
    if not curr_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Admin User not found')
    if not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='New User not found')
    if not curr_user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Current User is not an admin')
    
    new_user.is_admin = False
    db.commit()
    return {'message': 'User demoted from admin successfully'}
    

#call this endpoint to let an admin user create a volunteer event - no two events can have the same title
#expecting a JSON in the schema of ChangeEvent
#returning a JSON with a success message in the form {'message': message} or a corresponding error message
@app.post('/event/create_event')
def create_event(request: schemas.ChangeEvent, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User is not an admin')
    
    check_event = db.query(models.Event).filter(models.Event.title == request.title).first()
    if check_event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event already exists')
    if request.capacity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid value for Capacity')
    
    unique_id = str(uuid.uuid4())
    new_event = models.Event(id=unique_id, title=request.title, date=request.date, time=request.time, requirements=request.requirements, capacity=request.capacity, deadline=request.deadline, location=request.location, description=request.description, tasks=request.tasks)

    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return {'message': 'Event created successfully'}


#call this endpoint to let an admin user update a volunteer event
#just like with updating a user, you will already pre-fill all existing values on the frontend, then user makes changes, then you send me the entire event with all fields and I will update the event in the DB
#expecting a JSON in the schema of ChangeEvent
#returning a JSON with a success message in the form {'message': message} or a corresponding error message
@app.post('/event/update_event')
def update_event(request: schemas.ChangeEvent, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User is not an admin')
    
    event = db.query(models.Event).filter(models.Event.title == request.title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event not found')
    if request.capacity <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid value for Capacity')
    
    event.title = request.title
    event.date = request.date
    event.time = request.time
    event.requirements = request.requirements
    event.capacity = request.capacity
    event.deadline = request.deadline
    event.location = request.location
    event.description = request.description
    event.tasks = request.tasks
    
    db.commit()
    return {'message': 'Event updated successfully'}


#call this endpoint to let an admin user delete a volunteer event
#expecting a JSON in the schema of AdminEvent
#returning a JSON with a success message in the form {'message': message} or a corresponding error message
@app.post('/event/delete_event')
def delete_event(request: schemas.AdminEvent, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User is not an admin')
    
    event = db.query(models.Event).filter(models.Event.title == request.title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event not found')
    
    db.delete(event)
    db.commit()
    return {'message': 'Event deleted successfully'}


#call this endpoint to get all information about a volunteer event
#expecting the title of the event as a string
#returning a JSON with all the information about the event - see format below
@app.get('/event/get_event')
def get_event(title: str, db: Session = Depends(get_session)):
    event = db.query(models.Event).filter(models.Event.title == title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event not found')
    
    return {'title': event.title,
            'date': event.date,
            'time': event.time,
            'requirements': event.requirements,
            'capacity': event.capacity,
            'deadline': event.deadline,
            'location': event.location,
            'description': event.description,
            'tasks': event.tasks
            }
    

#call this endpoint to let user register for a volunteer event
#expecting the email of the user and the title of the event as strings
#returning a JSON with a success message in the form {'message': message} or a corresponding error message
@app.post('/event/register_event')
def register_event(email: str, title: str, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    
    event = db.query(models.Event).filter(models.Event.title == title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event not found')
    if len(event.users_registered) >= event.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event is full already')
    
    #check if user is already registered for the event
    if user.id in event.users_registered:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User already registered for event')
    
    event.users_registered = event.users_registered + [user.id]
    user.events_registered = user.events_registered + [event.id]
    db.commit()
    return {'message': 'User registered for event successfully'}


#call this endpoint to let user unregister from a volunteer event
#expecting the email of the user and the title of the event as strings
#returning a JSON with a success message in the form {'message': message} or a corresponding error message
@app.post('/event/unregister_event')
def unregister_event(email: str, title: str, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    
    event = db.query(models.Event).filter(models.Event.title == title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event not found')
    
    #check if user is registered for the event
    if user.id not in event.users_registered:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not registered for event')
    
    event.users_registered = [x for x in event.users_registered if x != user.id]
    user.events_registered = [x for x in user.events_registered if x != event.id]
    db.commit()
    return {'message': 'User unregistered from event successfully'}


#call this endpoint to get a list of all users registered for a volunteer event
#expecting a JSON in the schema of AdminEvent
#returning a JSON with a list of all user emails registered for the event
@app.post('/event/get_users_registered')
def get_event_registers(request: schemas.AdminEvent, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User is not an admin')
    
    event = db.query(models.Event).filter(models.Event.title == request.title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event not found')
    
    users_registered = []
    for user_id in event.users_registered:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        users_registered.append(user.email)
        
    return {'users_registered': users_registered}


#call this endpoint when an admin user wants to view a user's info + profile
#expecting a JSON in the schema of ChangeAdmin
#returning a JSON with all the information about the user - see format below (note is_admin and events_registered are included here)
@app.post('/admin/get_user')
def admin_get_user(request: schemas.ChangeAdmin, db: Session = Depends(get_session)):
    curr_user = db.query(models.User).filter(models.User.email == request.curr_user_email).first()
    if not curr_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Admin User not found')
    if not curr_user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Current User is not an admin')
    
    new_user = db.query(models.User).filter(models.User.email == request.new_user_email).first()
    if not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='New User not found')
    
    events_registered = []
    for event_id in new_user.events_registered:
        event = db.query(models.Event).filter(models.Event.id == event_id).first()
        events_registered.append(event.title)
    
    return {'email': new_user.email,
            'full_name': new_user.full_name,
            'is_admin': new_user.is_admin,
            'age': new_user.age,
            'gender': new_user.gender,
            'phone_number': new_user.phone_number,
            'work_status': new_user.work_status,
            'immigration_status': new_user.immigration_status,
            'skills': new_user.skills,
            'interests': new_user.interests,
            'past_volunteer_experience': new_user.past_volunteer_experience,
            'events_registered': events_registered #note this is a list of event titles, can be empty
            }


#call this endpoint when an admin user wants to kick a user out of an event
#expecting a JSON in the schema of KickUser
#returning a JSON with a success message in the form {'message': message} or a corresponding error message
@app.post('/admin/kick_user')
def admin_kick_user(request: schemas.KickUser, db: Session = Depends(get_session)):
    curr_user = db.query(models.User).filter(models.User.email == request.curr_user_email).first()
    if not curr_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Admin User not found')
    if not curr_user.is_admin:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Current User is not an admin')
    
    new_user = db.query(models.User).filter(models.User.email == request.new_user_email).first()
    if not new_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='New User not found')
    
    event = db.query(models.Event).filter(models.Event.title == request.title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event not found')
    
    if new_user.id not in event.users_registered:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='New User not registered for event')
    
    event.users_registered = [x for x in event.users_registered if x != new_user.id]
    new_user.events_registered = [x for x in new_user.events_registered if x != event.id]
    db.commit()
    
    return {'message': 'User kicked from event successfully'}


#call this endpoint to get a list of all events
#not expecting any input
#returning a JSON with a list of all event titles
@app.get('/event/get_events')
def get_events(db: Session = Depends(get_session)):
    events = db.query(models.Event).all()
    event_titles = [event.title for event in events]
    return {'event_titles': event_titles}
    

#call this endpoint to get the list of events a user is registered for
#expecting the email of the user as a string
#returning a JSON with a list of all event titles the user is registered for
@app.get('/user/get_user_events')
def get_user_events(email: str, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    
    events_registered = []
    for event_id in user.events_registered:
        event = db.query(models.Event).filter(models.Event.id == event_id).first()
        if not event:
            continue
        events_registered.append(event.title)
    
    return {'events_registered': events_registered}


#call this endpoint to generate personalized tasks for a user based on an event
#expecting a JSON in the schema of GenerateTasks
#returning a JSON containing a single string that is the model's response
@app.post('/user/generate_tasks')
def generate_tasks_llm(request: schemas.GenerateTasks, db: Session = Depends(get_session)):
    event = db.query(models.Event).filter(models.Event.title == request.event_title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event not found')
    
    user = db.query(models.User).filter(models.User.email == request.user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    
    event_description = 'Event Description: \n' + event.description + '\n\n' + 'Event Tasks: \n' + event.tasks
    user_description = 'User Skills: \n' + user.skills + '\n\n' + 'User Interests: \n' + user.interests + '\n\n' + 'User Past Volunteer Experience: \n' + user.past_volunteer_experience
    
    return {'response': generate_tasks(event_description, user_description)}


#call this endpoint to get the top 5 most similar events to a given user's profile
#expecting the email of the user as a string
#returning a JSON with a list of the top 5 most similar event titles - will return less than 5 if there are less than 5 events in the database
@app.get('/user/get_similar_events')
def match_events(email: str, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    
    events = db.query(models.Event).all()
    event_descriptions = [event.description for event in events]
    user_description = user.skills + ' ' + user.interests + ' ' + user.past_volunteer_experience
    
    event_embeddings = [get_embeddings(event) for event in event_descriptions]
    user_embedding = get_embeddings(user_description)
    
    similarities = [get_cosine_similarity(user_embedding, event_embedding) for event_embedding in event_embeddings]
    top_5_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:5]
    top_5_events = [events[i].title for i in top_5_indices]
    
    return {'top_5_events': top_5_events}


#call this endpoint to check if a user is registered for an event
#expecting a JSON in the schema of GenerateTasks
#returning a JSON with a boolean value in the form {'is_registered': is_registered}
@app.post('/user/is_registered')
def is_registered(request: schemas.GenerateTasks, db: Session = Depends(get_session)):
    user = db.query(models.User).filter(models.User.email == request.user_email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='User not found')
    
    event = db.query(models.Event).filter(models.Event.title == request.event_title).first()
    if not event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Event not found')
    
    return {'is_registered': user.id in event.users_registered}

