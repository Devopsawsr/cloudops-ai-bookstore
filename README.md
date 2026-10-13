# CloudOps AI Bookstore

A modular monolithic e-book learning application designed for an AWS single-VM deployment and later extraction into EKS microservices.

## Architecture

- FastAPI modular monolith
- PostgreSQL for operational and AI conversation data
- Amazon Bedrock Runtime for model inference
- Amazon Bedrock Knowledge Bases for grounded RAG answers
- Amazon ECR for immutable application images
- Docker Compose on EC2 for the first AWS deployment
- Amazon RDS PostgreSQL for operational data
- Amazon S3 for approved e-book documents
- AWS Secrets Manager for runtime secrets
- AWS Systems Manager for deployment without inbound SSH
- CloudWatch Logs for application and Nginx logs
- EC2 instance profile for AWS credentials

Kiro is used as the AI-assisted development environment. It is not deployed as part of the runtime application.

## AWS deployment path

1. Create the ECR repository, RDS database, S3 document bucket and EC2 instance.
2. Attach the least-privilege application IAM instance profile and the SSM managed-instance permissions to EC2.
3. Install Docker, the Compose plugin, AWS CLI and SSM Agent on EC2.
4. Create `/opt/cloudops-ai-bookstore/app.env` from values retrieved securely from Secrets Manager.
5. Configure the GitHub `aws-dev` environment variables and OIDC deploy role.
6. Run the **Deploy AWS Dev** workflow.

The application is then available through the EC2 public endpoint on port 80. An Application Load Balancer and HTTPS can be introduced after functional validation.

## Enable Amazon Bedrock

1. Attach a least-privilege IAM role to the EC2 instance.
2. Request access to the required Bedrock model in the chosen AWS Region.
3. Set `AI_PROVIDER=bedrock`.
4. Set `BEDROCK_MODEL_ID` to the selected inference profile or model ARN.
5. Optionally set `BEDROCK_KNOWLEDGE_BASE_ID` to enable RAG.
6. Restart the application.

Never commit AWS keys, database passwords or other secrets. Only upload public-domain, licensed or organization-approved documents to the knowledge base.

## GitHub environment configuration

Repository environment: `aws-dev`

Variables:

- `AWS_REGION`
- `ECR_REPOSITORY`
- `EC2_INSTANCE_ID`

Secret:

- `AWS_DEPLOY_ROLE_ARN`

The deploy role uses GitHub OIDC. AWS access keys are neither required nor permitted in the repository.

## Automated validation

Every pull request and push to `main` or `develop` runs Ruff, the API tests and a container build. Tests use an isolated SQLite database and mock AI provider; deployed environments use RDS and Amazon Bedrock exclusively.

## Planned progression

1. Provision and validate the AWS development environment.
2. Deploy the modular monolith from ECR to one EC2 instance.
3. Integrate Bedrock Runtime.
4. Add an S3-backed Bedrock Knowledge Base and citations.
5. Add authentication, cart, orders and recommendation modules.
6. Add CloudWatch dashboards, alarms, security controls and AWS Budgets.
7. Extract stable modules into the existing EKS microservices platform.

