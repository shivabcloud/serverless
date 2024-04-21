import os
import base64
import json
import pymysql
import requests
import uuid
import logging
from datetime import datetime, timedelta, timezone

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()

def verify_email(event, context):
    """Triggered by a message on a Cloud Pub/Sub topic.
    Args:
        event (dict): Event payload.
        context (google.cloud.functions.Context): Metadata for the event.
    """
    try:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        message_data = json.loads(pubsub_message)
        user_email = message_data["username"]
        logger.info(f"Received message for user: {user_email}")
    except Exception as e:
        logger.error(f"Error processing Pub/Sub message: {e}")
        return
    
    token = str(uuid.uuid4())
    # Construct Verification Link
    verification_link = f"https://bhargavcloud27.me./v1/user/verify?token={token}"
    logger.debug(verification_link + " is the verification link")

    # Send Email using Mailgun
    try:
        mailgun_domain = os.environ.get('MAILGUN_DOMAIN')
        mailgun_api_key = os.environ.get('MAILGUN_API_KEY')
        logger.debug(f'domain value: {mailgun_domain}')
        logger.debug(f'apikey value: {mailgun_api_key}')
        request_url = f'https://api.mailgun.net/v3/{mailgun_domain}/messages'
        response = requests.post(
            request_url,
            auth=("api", mailgun_api_key),
            data={
                "from": "Webapp function <cloudassignment@bhargavcloud27.me>",
                "to": [user_email],
                "subject": "Verify Your Email",
                "text": f"Click here to verify your email: {verification_link}"
            })

        if response.status_code != 200:
            logger.error(f'Error sending email via Mailgun: {response.text}')
        else:
            logger.info(f'Email sent successfully to {user_email}')
    except Exception as e:
        logger.error(f'Error sending email: {e}')
        return



    # Database Connection
    db_name = os.environ.get('DB_DATABASE_NAME')
    db_user = os.environ.get('DB_USER_DETAILS')
    db_host = os.environ.get('DB_DATABASE_HOST')
    db_connection_name = os.environ.get('DB_CONNECTION_NAME')
    db_password = os.environ.get('DB_PASSWORD_VALUE')

    try:
        db = pymysql.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            database=db_name,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        logger.info("Database connection Successful")
    except Exception as e:
        logger.error(f'Error connecting to DB: {e}')
        return

    
    # Generate Token and Expiration
    # token = str(uuid.uuid4())
    expiration = datetime.now(timezone.utc) + timedelta(minutes=2)

    # Store in Database
    try:
        with db.cursor() as cursor:
            sql = "INSERT INTO verify_token (token, username, expiration) VALUES (%s, %s, %s)"
            cursor.execute(sql, (token, user_email, expiration))
        db.commit()
        logger.info("Token stored in database")
    except Exception as e:
        logger.error(f"DB Error on token storage: {e}")
        db.rollback()
        return

    # # Construct Verification Link
    # verification_link = f"http://bhargavcloud27.me.:8080/v1/user/verify?token={token}"

    # # Send Email using Mailgun
    # try:
    #     mailgun_domain = os.environ.get('MAILGUN_DOMAIN')
    #     mailgun_api_key = os.environ.get('MAILGUN_API_KEY')
    #     request_url = f'https://api.mailgun.net/v3/{mailgun_domain}/messages'
    #     response = requests.post(
    #         request_url,
    #         auth=("api", mailgun_api_key),
    #         data={
    #             "from": "Mailgun-cloud assignment",
    #             "to": [user_email],
    #             "subject": "Verify Your Email",
    #             "text": f"Click here to verify your email: {verification_link}"
    #         })

    #     if response.status_code != 200:
    #         logger.error(f'Error sending email via Mailgun: {response.text}')
    #     else:
    #         logger.info(f'Email sent successfully to {user_email}')
    # except Exception as e:
    #     logger.error(f'Error sending email: {e}')
    #     return

    if db:
        db.close()
        logger.info("Database connection closed")
