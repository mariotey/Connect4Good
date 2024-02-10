# Connect4Good - Connects volunteers to causes they love, analyzing profiles to tailor tasks for event success.

Connect4Good is a volunteer matching application designed to connect individuals with causes they are passionate about. It analyzes volunteer profiles and event descriptions to facilitate meaningful connections. Subsequently it generates personalized tasks for volunteers tailored to each matched event. Whether you're organizing a community cleanup, a fundraising gala, or a charity run, Connect4Good helps you find the right volunteers with the right skills and interests to make your event a success.

To Run:
- Make sure you have Python 3.10.5 or later installed
- Make sure you have PostgreSQL 15.4 or later installed
    - Create a database called 'Connect4Good' that runs on port 5432
    - Make sure your username is 'postgres' and your password is 'password' (or change the URL of the DB in backend/database.py to match your credentials in the variable DB_URL)
- Clone the repostory locally and set up a virtual environment with everything in requirements.txt installed
- To run the backend:
    - Navigate to the backend directory
    - Run `uvicorn main:app` in the terminal
- To run the frontend:
    - Navigate to the frontend directory
    - Run `python manage.py runserver localhost:5000` in the terminal
- Open your web browser and go to http://localhost:5000/ to use the application