import base64
import json
import os
from datetime import datetime, timezone

import boto3

s3 = boto3.client("s3")
sns = boto3.client("sns")


def lambda_handler(event, _context):
    bucket = os.environ["BUCKET"]
    topic_arn = os.environ["TOPIC_ARN"]
    written = 0
    alerts = 0
    for item in event.get("Records", []):
        payload = json.loads(base64.b64decode(item["kinesis"]["data"]).decode())
        observed = payload.get("observed_at") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        when = datetime.fromisoformat(observed.replace("Z", "+00:00"))
        key = f"results/dt={when:%Y-%m-%d}/hour={when:%H}/{payload['course']}-{when:%Y%m%dT%H%M%SZ}.json"
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(payload).encode(),
            ContentType="application/json",
        )
        written += 1
        previous = payload.get("previous_marks")
        if previous is not None and abs(float(payload["marks"]) - float(previous)) >= 5:
            sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps({
                    "course": payload["course"],
                    "learner": payload.get("learner"),
                    "marks": payload["marks"],
                    "previous_marks": previous,
                    "passed": payload.get("passed"),
                    "attempt": payload.get("attempt"),
                    "key": key,
                }),
            )
            alerts += 1
    return {"written": written, "alerts": alerts}
