import json
from typing import Protocol

import boto3

from app.ai.schemas import AskResponse
from app.config import Settings


class AIProvider(Protocol):
    def ask(self, question: str, book_id: str | None) -> AskResponse: ...


class MockProvider:
    def ask(self, question: str, book_id: str | None) -> AskResponse:
        subject = f"the selected book ({book_id})" if book_id else "the CloudOps library"
        return AskResponse(
            answer=f"Mock AI response for {subject}: {question}",
            provider="mock",
            citations=["Local development dataset"],
        )


class BedrockProvider:
    def __init__(self, settings: Settings):
        if not settings.bedrock_model_id:
            raise ValueError("BEDROCK_MODEL_ID is required when AI_PROVIDER=bedrock")
        self.settings = settings
        self.runtime = boto3.client("bedrock-runtime", region_name=settings.aws_region)
        self.agent_runtime = boto3.client("bedrock-agent-runtime", region_name=settings.aws_region)

    def ask(self, question: str, book_id: str | None) -> AskResponse:
        if self.settings.bedrock_knowledge_base_id:
            return self._retrieve_and_generate(question, book_id)
        return self._invoke_model(question, book_id)

    def _retrieve_and_generate(self, question: str, book_id: str | None) -> AskResponse:
        prompt = f"Book ID: {book_id or 'all'}\nQuestion: {question}"
        response = self.agent_runtime.retrieve_and_generate(
            input={"text": prompt},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": self.settings.bedrock_knowledge_base_id,
                    "modelArn": self.settings.bedrock_model_id,
                },
            },
        )
        citations = [
            ref.get("location", {}).get("s3Location", {}).get("uri", "Bedrock Knowledge Base")
            for item in response.get("citations", [])
            for ref in item.get("retrievedReferences", [])
        ]
        return AskResponse(answer=response["output"]["text"], provider="bedrock-kb", citations=citations)

    def _invoke_model(self, question: str, book_id: str | None) -> AskResponse:
        prompt = f"You are a technical book assistant. Book: {book_id or 'general'}. Question: {question}"
        body = json.dumps(
            {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 800,
                "temperature": 0.2,
                "messages": [{"role": "user", "content": prompt}],
            }
        )
        response = self.runtime.invoke_model(modelId=self.settings.bedrock_model_id, body=body)
        payload = json.loads(response["body"].read())
        return AskResponse(answer=payload["content"][0]["text"], provider="bedrock", citations=[])


def build_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider.lower() == "bedrock":
        return BedrockProvider(settings)
    return MockProvider()

