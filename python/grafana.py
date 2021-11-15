from github import Github 
from github.GithubException import UnknownObjectException 
import yaml, json, string, glob, os 
from grafana_api.grafana_face import GrafanaFace 
from grafana_api.grafana_api import GrafanaServerError, GrafanaClientError 
from password_generator import PasswordGenerator 

GIT_TOKEN = os.environ.get('GIT_TOKEN') 
GRAFANA_USER = os.environ.get('GRAFANA_USER') 
GRAFANA_PASSWORD = os.environ.get('GRAFANA_PASSWORD') 

pwo = PasswordGenerator() 
pwo.generate() 
grafana_api = GrafanaFace(auth=(GRAFANA_USER, GRAFANA_PASSWORD),host='grafana-host', port=443, protocol='https') 

g = Github(base_url="https://github.domain.com/api/v3", login_or_token= GIT_TOKEN) 
org = g.get_organization(git-org) 

def landing_function(): 

    path = 'groups' 
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
        team_id = get_team_id(groupname) 
        grafana_git_diff = get_diff_gitgrafana(team_id, users) 
        delete_members_frm_grafana(grafana_git_diff) 
        remove_members_from_team(team_id)  
        add_user_to_grafana(users) 
        user_ids =  get_user_id(users) 
        add_members_teams(team_id, user_ids) 

def create_team(groupname): 

    team_details = grafana_api.teams.get_team_by_name(groupname) 
    if not team_details: 
        team = grafana_api.teams.add_team({"name":groupname}) 
    return team_details 

def get_team_id(groupname): 
    team = grafana_api.teams.get_team_by_name(groupname) 
    team_id = team[0]['id'] 
    return team_id 

  

def get_diff_gitgrafana(team_id, users): 

    grafana_list = [] 
    github_members = [] 
    github_list = [] 
    grafana_team_members = grafana_api.teams.get_team_members(team_id) 

    for grafana_members in grafana_team_members: 
        grafana_list.append(grafana_members['name']) 

    for u in users: 
        try:         
            github_members = g.get_user(u).login 

        except UnknownObjectException as e: 
            if "Not Found" in str(e): 
                github_list.append(u)  

            else: 
                raise Exception("Unknown Exception, {}".format(str(e)))  

    grafana_git_diff  = [d for d in github_list if not d in grafana_list] 

    return grafana_git_diff 

def delete_members_frm_grafana(grafana_git_diff): 

    if not grafana_git_diff: 
        pass 

    else: 
        userid_to_be_removed = get_user_id(grafana_git_diff) 
        for userid_to_be_removed in userid_to_be_removed: 
            try: 
                grafana_api.organization.delete_user_current_organization(userid_to_be_removed) 

            except GrafanaServerError as e: 
                if 'Failed to remove user' in str(e): 
                    pass 
                else: 
                    raise Exception("Unknown Exception, {}".format(str(e)))           

def remove_members_from_team(team_id):    

    team_members =  grafana_api.teams.get_team_members(team_id) 
    for members in team_members:            
        grafana_api.teams.remove_team_member(team_id, members['userId']) 

def add_user_to_grafana(users): 

    non_github_members = [] 
    for u in users: 
        try: 
            github_users = g.get_user(u).login 

        except UnknownObjectException as e: 
            if "Not Found" in str(e): 
                print("user {} not found in github".format(u)) 
                non_github_members.append(u) 
                non_github_users_email = [ i.replace('-','.')+"@domain.com" for i in non_github_members ] 

        else: 
            try: 
                grafana_api.users.find_user(u) 

            except GrafanaClientError as e: 
                if 'User not found' in str(e): 
                    email_id = u.replace('-','.')+"@domain.com" 
                    randompassword = pwo.shuffle_password('Grafana@.0123456789', 10) 
                    grafana_api.admin.create_user({"name": u, "email": email_id, "login": u, "password": randompassword, "OrgId": 1})             

def get_user_id(users): 

    user_ids = [] 
    for user in users: 
        try: 
            user_details = grafana_api.users.find_user(user) 
            user_id = user_details.get('id') 
            user_ids.append(user_id)  

        except GrafanaClientError as e: 
            if 'User not found' in str(e): 
                pass 

            else: 
                raise Exception("Unknown Exception, {}".format(str(e))) 

    return user_ids 

def add_members_teams(team_id, user_ids): 

    for yaml_user in user_ids: 
        added_members = grafana_api.teams.add_team_member(team_id, yaml_user) 

if __name__ == "__main__": 
    landing_function() 