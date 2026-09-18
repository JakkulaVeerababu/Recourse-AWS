import asyncio
from strands import Agent
from strands.models import BedrockModel

async def main():
    model = BedrockModel(model_id="amazon.nova-pro-v1:0", region_name="us-east-1")
    agent = Agent(name="test", model=model)
    res = await agent.invoke_async("ping")
    print(res.content)

if __name__ == "__main__":
    asyncio.run(main())
