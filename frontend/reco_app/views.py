from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
import requests

from datetime import datetime

FASTAPI_BASE_URL = "http://localhost:8000"

#################################################################################################

def index(request):
    user_email = request.COOKIES.get("user_email", "None")

    if user_email == "None":
        admin_status = False
        recomms = []
        registered = []
        username = "None"
    else:
        admin_status = requests.get(
            f"{FASTAPI_BASE_URL}/user/is_admin", 
            params={"email": user_email}
        ).json()["is_admin"]

        recomms = requests.get(
            f"{FASTAPI_BASE_URL}/user/get_similar_events", 
            params={"email": user_email}
        ).json()["top_5_events"]

        registered = requests.get(
            f"{FASTAPI_BASE_URL}/user/get_user_events", 
            params={"email": user_email}
        ).json()["events_registered"]

        username = requests.get(
            f"{FASTAPI_BASE_URL}/user/get_user", 
            params={"email": user_email}
        ).json()["full_name"]

    response = render(request, "index.html",{
        "username": username,
        "user_email": user_email,
        "admin_status": admin_status,
        "events": requests.get(
                        f"{FASTAPI_BASE_URL}/event/get_events", 
                    ).json()["event_titles"],
        "registered": registered,
        "recomms": recomms,
    })

    response.set_cookie("username", username, max_age=3600)

    return response

#################################################################################################

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        login_data = {
            "email": request.POST["email"],
            "password": request.POST["password"]
        }
        
        try:
            # Check if authentication successful
            fastapi_response = requests.post(
                f"{FASTAPI_BASE_URL}/login", 
                json=login_data
            ).json()

            print(f"\n{fastapi_response['message']}\n")

            response = HttpResponseRedirect(reverse("index"))
            response.set_cookie("user_email", request.POST["email"], max_age=3600)
            return response
        except:
            print("Login unsuccessful")
            return render(request, "login.html", {
                "message": "Invalid email and/or password."
            })
    else:
        return render(request, "login.html")

def logout_view(request):
    logout(request)

    print("Logout successfully")

    response = HttpResponseRedirect(reverse("index"))
    response.delete_cookie("user_email")
    response.delete_cookie("username")
    return response

def register(request):
    if request.method == "POST":
        if request.POST["password"] != request.POST["confirmation"]:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        register_data = {
            "email": request.POST["email"],
            "full_name": request.POST["full_name"],
            "password": request.POST["password"],
            "age": int(request.POST["age"]),
            "gender": request.POST["gender"],
            "phone_number": request.POST["phone_number"],
            "work_status": request.POST["work_status"],
            "immigration_status": request.POST["immigration_status"],
            "skills": request.POST["skills"],
            "interests": request.POST["interests"],
            "past_volunteer_experience": request.POST["past_volunteer_experience"],
        }

        # Attempt to create new user
        try:
            fastapi_response = requests.post(
                f"{FASTAPI_BASE_URL}/register", 
                json=register_data
            ).json()

            print(f"\n{fastapi_response['message']}\n")

            response = HttpResponseRedirect(reverse("index"))
            response.set_cookie("user_email", request.POST["email"], max_age=3600)
            return response

        except IntegrityError:
            return render(request, "register.html", {
                "message": "Username or email already taken."
            })

        except Exception as error:
            print(error)
            return render(request, "register.html", {
                "message": "An error occurred."
            })

    else:
        return render(request, "register.html")

#################################################################################################
    
def create_event(request):
    """
    Navigates to Event Creation page
    """

    if request.method == "POST":
        new_event_data = {
            "email": request.POST["email"],
            "title": request.POST["title"],
            "date": request.POST["date"],
            "time": request.POST["time"],
            "requirements": request.POST["requirements"],
            "capacity": int(request.POST["capacity"]),
            "deadline": request.POST["deadline"],
            "location": request.POST["location"],
            "description": request.POST["description"],
            "tasks": request.POST["tasks"],
        }

        try:
            fastapi_response = requests.post(
                f"{FASTAPI_BASE_URL}/event/create_event", 
                json=new_event_data
            ).json()
            
            print(f"\n{fastapi_response['message']}\n")

            response = HttpResponseRedirect(reverse("index"))
            response.set_cookie("user_email", request.POST["email"], max_age=3600)
            return response

        except:
            return render(request, "createEvent.html", {
                "message": "Error in creating event"
            })
    else:
        return render(request, 'createEvent.html')
  
def event(request, event_title):
    """
    Navigates to Event Page
    """
    
    user_email = request.COOKIES.get("user_email", "None")
    username = request.COOKIES.get("username", "None")

    registered_events = requests.get(
        f"{FASTAPI_BASE_URL}/user/get_user_events", 
        params={"email": user_email}
    ).json()["events_registered"]

    print(registered_events)

    if event_title not in registered_events:
        register_status = False
    else:
        register_status = True

    user_admin = requests.get(
                    f"{FASTAPI_BASE_URL}/user/is_admin", 
                    params={"email": user_email}
                ).json()["is_admin"]
    
    if user_admin:
        participants = requests.post(
                            f"{FASTAPI_BASE_URL}/event/get_users_registered", 
                            json={
                                "email": user_email,
                                "title": event_title
                            }
                        ).json()["users_registered"]
    else:
        participants = []

    return render(request, 'event.html', {
        "username": username,
        "user_email": user_email,
        "user_admin": user_admin,
        "event": requests.get(
                    f"{FASTAPI_BASE_URL}/event/get_event", 
                    params={"title":event_title}
                ).json(),
        "participants": participants,
        "registered_status": register_status,
    })

def event_edit(request, event_title):
    user_email = request.COOKIES.get("user_email", "None")
    username = request.COOKIES.get("username", "None")

    if request.method == "POST":
        updated_event = {
            "email": user_email,
            "title": event_title,
            "date": request.POST["date"],
            "time": request.POST["time"],
            "requirements": request.POST["requirements"],
            "capacity": int(request.POST["capacity"]),
            "deadline": request.POST["deadline"],
            "location": request.POST["location"],
            "description": request.POST["description"],
            "tasks": request.POST["tasks"]
        }

        print(updated_event)

        fastapi_response = requests.post(
                                f"{FASTAPI_BASE_URL}/event/update_event", 
                                json=updated_event
                            ).json()
        
        print(fastapi_response["message"])
        
        response = HttpResponseRedirect(reverse("index"))
        return response
    
    else:
        return render(request, 'event_edit.html', {
            "username": username,
            "user_email": user_email,
            "event_details": requests.get(
                                f"{FASTAPI_BASE_URL}/event/get_event", 
                                params={"title":event_title}
                            ).json(),
        })

def event_delete(request, event_title):
    
    admin_email = request.COOKIES.get("user_email", "None")

    fastapi_response = requests.post(
                            f"{FASTAPI_BASE_URL}/event/delete_event", 
                            json={
                                "email": admin_email,
                                "title": event_title
                            }
                        ).json()
    
    print(fastapi_response["message"])

    response = HttpResponseRedirect(reverse("index"))
    return response

def event_reg(request, event_title):
    """
    Registration Mechanism for Event Page, TBC
    """

    user_email = request.COOKIES.get("user_email", "None")
    username = request.COOKIES.get("username", "None")

    print(user_email, event_title)

    register_event_status  = requests.post(
                                f"{FASTAPI_BASE_URL}/event/register_event", 
                                params={
                                    "email": str(user_email),
                                    "title": str(event_title),
                                }
                            ).json()
    
    print(register_event_status["message"])

    user_admin = requests.get(
                    f"{FASTAPI_BASE_URL}/user/is_admin", 
                    params={"email": user_email}
                ).json()["is_admin"]
    
    if user_admin:
        participants = requests.post(
                            f"{FASTAPI_BASE_URL}/event/get_users_registered", 
                            json={
                                "email": user_email,
                                "title": event_title
                            }
                        ).json()["users_registered"]
    else:
        participants = []


    return render(request, 'event.html', {
        "username": username,
        "user_email": user_email,
        "user_admin": user_admin,
        "event": requests.get(
                    f"{FASTAPI_BASE_URL}/event/get_event", 
                    params={"title":event_title}
                ).json(),
        "participants": participants,
        "registered_status": register_event_status,
    })

def event_unreg(request, event_title):
    fastapi_response  = requests.post(
                            f"{FASTAPI_BASE_URL}/event/unregister_event", 
                            params={
                                "email": str(request.COOKIES.get("user_email", "None")),
                                "title": str(event_title)
                            }
                        ).json()

    print(fastapi_response["message"])

    response = HttpResponseRedirect(reverse("index"))
    return response

#################################################################################################

def get_user(request, user_email):
    username = request.COOKIES.get("username", "None")
    
    user_details = requests.get(
        f"{FASTAPI_BASE_URL}/user/get_user", 
        params={"email": user_email}
    ).json()

    user_email = request.COOKIES.get("user_email", "None")

    user_admin  = requests.get(
        f"{FASTAPI_BASE_URL}/user/is_admin", 
        params={"email": user_email}
    ).json()["is_admin"]

    return render(request, 'user.html', {
        "username": username,
        "user_email": user_email,
        "user_details": user_details,
        "user_admin": user_admin,
    })

def user_edit(request, user_email):
    user_email = request.COOKIES.get("user_email", "None")
    username = request.COOKIES.get("username", "None")

    if request.method == "POST":
        updated_user = {
            "email": user_email,
            "full_name": request.POST["full_name"],
            "password": request.POST["password"],
            "age": int(request.POST["age"]),
            "gender": request.POST["gender"],
            "phone_number": request.POST["phone_number"],
            "work_status": request.POST["work_status"],
            "immigration_status": request.POST["immigration_status"],
            "skills": request.POST["skills"],
            "interests": request.POST["interests"],
            "past_volunteer_experience": request.POST["past_volunteer_experience"],
        }

        print(updated_user)

        ## Update API request
        fastapi_response = requests.post(
            f"{FASTAPI_BASE_URL}/user/update_user", 
            json=updated_user
        ).json()

        print(fastapi_response["message"])

        response = HttpResponseRedirect(reverse("index"))
        return response

    else:
        user_details = requests.get(
            f"{FASTAPI_BASE_URL}/user/get_user", 
            params={"email": user_email}
        ).json()

        return render(request, 'user_edit.html', {
            "username": username,
            "user_email": user_email,
            "user_details": user_details,
        })
    
def user_delete(request, user_email):
    fastapi_response = requests.post(
        f"{FASTAPI_BASE_URL}/user/delete_user", 
        params={'email': user_email}
    ).json()
    
    print(f"\n{fastapi_response['message']}\n")
    
    response = HttpResponseRedirect(reverse("index"))
    response.delete_cookie("user_email")
    response.delete_cookie("username")
    return response

#################################################################################################

def admin_promote(request, user_email):
    
    admin_email = request.COOKIES.get("user_email", "None")

    fastapi_response = requests.post(
                            f"{FASTAPI_BASE_URL}/user/promote_admin", 
                            json={
                                "curr_user_email": admin_email,
                                "new_user_email": user_email
                            }
                        ).json()

    print(fastapi_response["message"])

    response = HttpResponseRedirect(reverse("index"))
    return response

def admin_demote(request, user_email):

    admin_email = request.COOKIES.get("user_email", "None")

    fastapi_response = requests.post(
                            f"{FASTAPI_BASE_URL}/user/demote_admin", 
                            json={
                                "curr_user_email": admin_email,
                                "new_user_email": user_email
                            }
                        ).json()

    print(fastapi_response["message"])

    response = HttpResponseRedirect(reverse("index"))
    return response

#################################################################################################
    