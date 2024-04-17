"""
    Notify sns with Lambda destination outputs
"""

import json
import os

# pylint: disable=import-error
import boto3

sns = boto3.client("sns")


# pylint: disable=unused-argument
def lambda_handler(event, context):
    """
    entrypoint
    """
    sns.publish(
        TopicArn=os.getenv("SNS_TOPIC_ARN"),
        Message="Error has occurred:\n\n"
        + str(json.loads(event["Records"][0]["body"])["responsePayload"]),
        Subject=os.getenv("SNS_SUBJECT"),
    )
    return {"statusCode": 200, "body": json.dumps("Notification done")}
