import boto3
client = boto3.client('lambda', region_name='ap-south-1')
print("Reading zip...")
with open('investigation-agent.zip', 'rb') as f:
    zip_content = f.read()
print(f"Uploading {len(zip_content)} bytes...")
res = client.update_function_code(FunctionName='recourse-development-investigation-agent', ZipFile=zip_content)
print("Uploaded!", res.get('LastModified'))
