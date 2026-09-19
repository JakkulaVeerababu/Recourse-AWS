import boto3
item=boto3.client('dynamodb').get_item(TableName='recourse-development-incidents', Key={'PK': {'S': 'INCIDENT#INC-DISABLE-APPROVE-3'}, 'SK': {'S': 'META'}}).get('Item', {})
print(f"{item.get('status', {}).get('S')} - {item.get('investigationStage', {}).get('S')}")
