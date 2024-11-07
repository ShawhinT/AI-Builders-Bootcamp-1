# Replicating Maven Broadcast Function (Script version)
# ABB #1 - Session 1

# Code authored by: Shaw Talebi

# IMPORTS
import csv

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from top_secret import app_password

# DEFINE VARIABLES
course_name = "AI Builders Bootcamp"
start_date = "Nov 8th, 2024"
end_date = "Dec 20th, 2024"
portal_open_date = "Nov 4th, 2024"

# CONSTRUCT EMAIL
subject = f"Welcome to {course_name}!"
print(subject)

body = lambda student_name : f"""Hey {student_name},

I'm super excited to have you here!

We'll be getting started on {start_date} and finishing up on {end_date}.

Keep your eye out for the course portal, which will open up on {portal_open_date}.

Let me know if you have any questions in the meantime :)

-Shaw"""
print(body("Test"))

# READ NAMES/EMAILS FROM CSV
filename = "data/emails.csv" # path to CSV file

recipients_list = [] # initialize an empty list to store recipient tuples

# read CSV file and populate the recipients list
with open(filename, mode='r') as csvfile:
    csv_reader = csv.DictReader(csvfile)
    for row in csv_reader:
        name = row["Name"].split(" ")[0]
        email = row["Email"]
        recipients_list.append((name, email))

print('\n')
print("Recipients List:", recipients_list)

# SEND EMAILS
# define email credentials and recipient
sender_email = "your email here"
password = app_password

# connect to the server
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()  # start TLS encryption
    server.login(sender_email, password)  # log into email account

    # send the email to each recipient with personalized content
    for name, email in recipients_list:
        # set up the MIME
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = email
        message["Subject"] = subject
        
        # email body with personalization
        personalized_body = body(name)
        message.attach(MIMEText(personalized_body, "plain"))

        # send the email
        server.sendmail(sender_email, email, message.as_string())
        print(f"Email sent successfully to {name} at {email}!")