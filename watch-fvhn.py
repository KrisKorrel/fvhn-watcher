import traceback

import requests
import re
import psycopg2
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

LOCAL = False
DEBUG = False


def main():
    response = requests.get("https://www.floorvanhetnederend.com")
    content = response.content.decode('utf-8')
    matches = re.findall(r'data-gtm4wp_product_name=\"([^\"]*)\"', content)

    print(f"Matches: {matches}")
    first_match = matches[0]
    print(f"First match: {first_match}")

    if LOCAL:
        conn = psycopg2.connect(host='127.0.0.1', port=5432, database='my_db')
    else:
        DATABASE_URL = os.environ['DATABASE_URL']
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS my_table (item VARCHAR(500));")
    cursor.execute("SELECT * FROM my_table LIMIT 1;")
    results = cursor.fetchall()
    if len(results) == 0:
        result = ""
    else:
        result = results[0][0]
    print("DB result:", result)

    if result != first_match:
        cursor.execute(f"INSERT INTO my_table (item) VALUES (%s)", (first_match,))

    conn.commit()
    cursor.close()
    conn.close()

    if result != first_match or DEBUG:
        notify_new_product()


def notify_new_product():
    subject = 'New product by Floor van het Nederend'
    content = 'Check out https://www.floorvanhetnederend.com'
    send_email(subject=subject, content=content)


def send_error():
    subject = "Something went wrong"
    content = traceback.format_exc()
    send_email(subject=subject, content=content)


def send_email(subject, content):
    print(f"Sending mail with subject {subject}")
    send_grid_api_key = os.environ.get("SENDGRID_API_KEY")
    from_mail = os.environ.get("SENDGRID_FROM_MAIL")
    to_mail = os.environ.get("SENDGRID_TO_MAIL")

    assert send_grid_api_key is not None, "SENDGRID_API_KEY is not set"
    assert from_mail is not None, "SENDGRID_FROM_MAIL is not set"
    assert to_mail is not None, "SENDGRID_TO_MAIL is not set"

    message = Mail(
        from_email=from_mail,
        to_emails=to_mail,
        subject=subject,
        html_content=content,
    )

    sg = SendGridAPIClient(send_grid_api_key)
    response = sg.send(message)

    print(response.status_code)
    print(response.body)
    print(response.headers)
    print("Sent mail")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        send_error()
        raise e
