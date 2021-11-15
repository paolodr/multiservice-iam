import boto3 
import yaml, json, string, glob, os 

from botocore.exceptions import ClientError 

# Creating an boto3 clients 

iam_client = boto3.client('iam') 
sts_client = boto3.client('sts') 

#Read input file 

path = 'groups' 

for filename in glob.glob(os.path.join(path, '*.yaml')): 
    with open(os.path.join(os.getcwd(), filename), 'r') as stream: 
        out = yaml.load(stream, Loader=yaml.FullLoader) 
        accounts = out['aws']['accounts'] 
        users = out['members']
        roles = out['aws']['roles'] 
        groupname = out['name'] 

        if out.get('jfrog'): 
           jfrog_permissions = out['jfrog']['permissions'] 

    #Generate the policy json 

    trust_relationship_policy_iam_role = {} 
    condition = {} 
    AWS_users =[] 

    i=0 
    for user in users: 
        AWS_users.append('arn:aws:sts::326869539878:assumed-role/HPE-SSO/' + user) 
  
    aws_list = {'AWS': AWS_users} 
    
    statement = { 
        'Effect': 'Allow', 
        'Principal': aws_list, 
        'Action': 'sts:AssumeRole', 
        'Condition': condition 
    } 

    trust_relationship_policy_iam_role = { 
        'Version': '2012-10-17', 
        'Statement': [statement] 
    } 

    for account in accounts: 

        #Assume Admin role 

        response = sts_client.assume_role( 
            RoleArn='arn:aws:iam::'+ str(account) +':role/<role-to-be-assumed>', 
            RoleSessionName='assume_role_session' 
        ) 

        iam_role = boto3.client('iam', 
            aws_access_key_id=response['Credentials']['AccessKeyId'], 
            aws_secret_access_key=response['Credentials']['SecretAccessKey'], 
            aws_session_token=response['Credentials']['SessionToken'] 
        ) 
  
        for role in roles: 

            policy_attach_res = iam_role.update_assume_role_policy( 
                RoleName=role, 
                PolicyDocument=json.dumps(trust_relationship_policy_iam_role,indent=4) 
            ) 
            
            print ('Group: ' + groupname + '; Role arn:aws:iam::'+ str(account) +':role/' + role + ' updated') 