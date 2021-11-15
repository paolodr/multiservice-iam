from github import Github 
from github.GithubException import UnknownObjectException 
import yaml, json, string, glob, os 
from email.mime.text import MIMEText 
from email.mime.multipart import MIMEMultipart 
import smtplib 

GIT_TOKEN = os.environ.get('GIT_TOKEN') 
SMTP_USER = os.environ.get('SMTP_USER') 
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD') 

g = Github(base_url="https://github.domain.com/api/v3", login_or_token = GIT_TOKEN) 
org = g.get_organization(organization-name) 

def landing_function(): 
    path = 'groups' 
    non_github_users_email_ids = [] 
    non_github_users_to_email = [] 
    non_github_users_email = [] 
    email_list = [] 

    for filename in glob.glob(os.path.join(path, '*.yaml')): 
        with open(os.path.join(os.getcwd(), filename), 'r') as stream: 
            out = yaml.load(stream, Loader=yaml.FullLoader) 
            accounts = out['aws']['accounts'] 
            emails = out['members'] 
            users = [ i.replace("@domain.com",'').replace('.','-') for i in emails ] 
            roles = out['aws']['roles'] 
            groupname = out['name'] 

            if out.get('jfrog'): 
                jfrog_permissions = out['jfrog']['permissions'] 

        team_details = create_team(groupname) 
        remove_members(team_details, users)  
        non_github_users_email = add_members(team_details, users) 

        if not non_github_users_email: 
           pass 

        else: 
           email_list.append({"Group_name":groupname,"email_id":non_github_users_email}) 

    send_email(email_list)    

def create_team(groupname):         
    try: 
        team_details = org.get_team_by_slug(groupname) 
    except UnknownObjectException as e: 
        if "Not Found" in str(e): 
            print("Team name: {} is not found, hence creating".format(groupname)) 
            team_details = org.create_team(name=groupname, permission='pull', privacy='closed', description="This GitHub team is for {}".format(groupname)) 
            print("Team: {}  Created".format(groupname)) 
        else: 
            raise Exception("Unknown Exception, {}".format(str(e))) 

    return team_details 

  

def remove_members(team_details, users): 
    members_to_remove = [] 
    git_team_members = [] 
    members = team_details.get_members() 
    git_team_members = [i.login for i in list(members)] 

    if 'service-account' in  git_team_members: 
        git_team_members.remove('service-account') 
        team_details.remove_from_members(g.get_user('service-account')) 

    if git_team_members: 
        members_to_remove = list(set(git_team_members).difference(set(users))) 
        if members_to_remove: 
            for member_to_remove in members_to_remove: 
                member_obj_to_remove = g.get_user(member_to_remove)             
                team_details.remove_from_members(member_obj_to_remove) 
 
def add_members(team_details, users): 
    non_github_members = [] 
    non_github_users_email = [] 
    team_members = team_details.get_members() 
    team_members_git_name = [i.login for i in list(team_members)] 
    members_to_add = list(set(users).difference(set(team_members_git_name))) 

    if members_to_add: 
        for yaml_user in members_to_add: 
            try: 
                user_details = g.get_user(yaml_user) 
                hi = team_details.add_to_members(g.get_user(yaml_user)) 
            except UnknownObjectException as e: 

                if "Not Found" in str(e): 
                    non_github_members.append(yaml_user) 
                    non_github_users_email = [ i.replace('-','.')+"@domain.com" for i in non_github_members ] 

                else: 
                    raise Exception("Unknown Exception, {}".format(str(e))) 

    return non_github_users_email 

  

  

def send_email(email_address): 

    if not email_address: 
       return 
    to_email_address = "qwerty@domain.com" 
    text_part = MIMEText('text', "html") 
    message_string = """ 

Hi Team, <br> <br> Below users are not in github.domain.com, hence not able to add the user into the github teams. Please verify the user existense on <b>github.domain.com</b> 

    """ 

    for data in email_address: 
        if data: 
           msg = "<br><b>Github teams</b>: {} and the <b>members</b> are {}".format(data['Group_name'],', '.join(data['email_id'])) 
           message_string += msg  

    text_part.set_payload(message_string) 
    msg = MIMEMultipart() 
    msg.attach(text_part) 
    msg['Subject'] = "GitOps Notification" 
    msg['From'] = 'qwerty@domain.com' 
    msg['To'] = to_email_address 
    smtp = None 

    try: 

        print("Sending email") 
        smtp = smtplib.SMTP('smtp-email.domain.com', 587) 
        smtp.starttls() 
        smtp.login(SMTP_USER, SMTP_PASSWORD) 
        smtp.sendmail(msg['From'], to_email_address.split(','), msg.as_string()) 

    except Exception as e: 
        print (str(e)) 

    finally: 
        if smtp: 
            smtp.quit() 

if __name__ == "__main__": 
    landing_function()