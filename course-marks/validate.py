import base64
import json
import os

import boto3

COURSES = {
    "aws", "terraform", "kubernetes", "docker", "python", "linux", "git", "jenkins",
}
kinesis = boto3.client("kinesis")
sqs = boto3.client("sqs")


def response(status, payload):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload),
    }


def fail(status, message, body):
    sqs.send_message(
        QueueUrl=os.environ["DLQ_URL"],
        MessageBody=json.dumps({"message": message, "body": body}),
    )
    return response(status, {"ok": False, "message": message})


def lambda_handler(event, _context):
    token = os.environ["COURSE_MARKS_TOKEN"]
    stream_name = os.environ["STREAM_NAME"]
    headers = {str(key).lower(): value for key, value in (event.get("headers") or {}).items()}
    if headers.get("x-course-marks-token") != token:
        return response(401, {"ok": False, "message": "Unauthorized"})
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode()
    try:
        body = json.loads(raw)
    except json.JSONDecodeError:
        return fail(400, "Request body must be JSON.", raw)
    if not isinstance(body, dict):
        return fail(400, "Request body must be a JSON object.", body)
    course = str(body.get("course") or "").strip().lower()
    learner = str(body.get("learner") or "Learner").strip() or "Learner"
    try:
        marks = float(body["marks"])
    except (KeyError, TypeError, ValueError):
        return fail(400, "Marks are required and must be a number from 0 to 100.", body)
    try:
        attempt = int(body.get("attempt") or 1)
    except (TypeError, ValueError):
        return fail(400, "Attempt must be 1, 2, or 3.", body)
    if course not in COURSES or not 0 <= marks <= 100 or attempt not in (1, 2, 3):
        return fail(400, "Choose an ebook course. Marks must be 0 to 100. Attempt must be 1, 2, or 3.", body)
    previous = body.get("previous_marks")
    if previous is not None and previous != "":
        try:
            previous = float(previous)
        except (TypeError, ValueError):
            return fail(400, "Previous marks must be a number from 0 to 100.", body)
        if not 0 <= previous <= 100:
            return fail(400, "Previous marks must be 0 to 100.", body)
    record = {
        "learner": learner,
        "course": course,
        "marks": marks,
        "pass_percentage": marks,
        "passed": marks >= 70,
        "previous_marks": previous,
        "attempt": attempt,
        "environment": "practice",
    }
    result = kinesis.put_record(
        StreamName=stream_name,
        Data=json.dumps(record).encode(),
        PartitionKey=course,
    )
    return response(202, {
        "ok": True,
        "learner": learner,
        "course": course,
        "marks": marks,
        "pass_percentage": marks,
        "passed": record["passed"],
        "attempt": attempt,
        "environment": "practice",
        "sequence": result["SequenceNumber"],
    })
