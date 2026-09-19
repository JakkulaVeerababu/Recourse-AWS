import boto3
import json
import sys

def get_cognito_details():
    cognito = boto3.client('cognito-idp')
    pools = cognito.list_user_pools(MaxResults=10)['UserPools']
    pool = next((p for p in pools if 'approvers' in p['Name']), None)
    if not pool:
        print("Could not find user pool")
        sys.exit(1)
        
    pool_id = pool['Id']
    clients = cognito.list_user_pool_clients(UserPoolId=pool_id, MaxResults=10)['UserPoolClients']
    client_id = clients[0]['ClientId'] if clients else None
    
    return pool_id, client_id

def create_and_auth_user(pool_id, client_id, username, password):
    cognito = boto3.client('cognito-idp')
    try:
        cognito.admin_create_user(
            UserPoolId=pool_id,
            Username=username,
            TemporaryPassword=password,
            MessageAction='SUPPRESS'
        )
        cognito.admin_set_user_password(
            UserPoolId=pool_id,
            Username=username,
            Password=password,
            Permanent=True
        )
        cognito.admin_add_user_to_group(
            UserPoolId=pool_id,
            Username=username,
            GroupName='Approver'
        )
    except cognito.exceptions.UsernameExistsException:
        pass
        
    response = cognito.admin_initiate_auth(
        UserPoolId=pool_id,
        AuthFlow='ADMIN_NO_SRP_AUTH',
        AuthParameters={'USERNAME': username, 'PASSWORD': password},
        ClientId=client_id
    )
    
    return response['AuthenticationResult']['IdToken']

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == '--get-token':
        pool, client = get_cognito_details()
        token = create_and_auth_user(pool, client, 'testapprover', 'Test!1234')
        print(token)
