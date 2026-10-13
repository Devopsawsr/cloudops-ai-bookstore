# EC2 IAM role

The application uses the EC2 instance profile through the standard AWS SDK credential chain. Do not create static AWS access keys for the application.

The role should be restricted to the selected Bedrock model, Knowledge Base and approved S3 document prefix. Infrastructure as code will be added after the local mock flow is verified.

