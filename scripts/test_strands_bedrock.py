import asyncio
from strands import Agent
from strands.models import BedrockModel

async def main():
    model = BedrockModel(model_id="apac.anthropic.claude-3-7-sonnet-20250219-v1:0", region_name="ap-south-1")
    agent = Agent(name="test", model=model)
    res = await agent.invoke_async("ping")
    print(res.content)

if __name__ == "__main__":
    asyncio.run(main())
