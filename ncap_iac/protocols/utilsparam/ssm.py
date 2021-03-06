import boto3
import os

# Boto3 Resources & Clients
ssm_client = boto3.client('ssm', region_name=os.environ['REGION']) 
budgetname = "/neurocaas/budgets/{g}/{a}"

def execute_commands_on_linux_instances(commands, 
                                        instance_ids, 
                                        working_dirs,
                                        log_bucket_name,
                                        log_path):
    """Runs commands on remote linux instances
    :param commands: a list of one string,  a command to execute on the instances
    :param instance_ids: a list of instance_id strings, of the instances on which to execute the command
    :param working_dires: a list of one directory (string) where commands are executed on each instance
    :return: the response from the send_command function (check the boto3 docs for ssm client.send_command() )
    """
    return ssm_client.send_command(
        DocumentName="AWS-RunShellScript", # One of AWS' preconfigured documents
        Parameters={'commands': commands, 
                    "workingDirectory":working_dirs,
                    "executionTimeout":[os.environ['SSM_TIMEOUT'] for command in commands]},
        InstanceIds=instance_ids,
        OutputS3BucketName=log_bucket_name,
        OutputS3KeyPrefix=log_path
    )

def mount_volumes(attach_responses):
    """
    Uses an automation document to automatically mount the volume on remote with an appropriate file system. 
    Inputs: 
    attach_responses: (dict) a dictionary of dictionaries where the keys are instance ids, and the values are dictionaries of responses to the creation, attachment, and modification of volumes for them. 
    """
    ## The document is declared in the utils stack to initialize neurocaas. 
    for instance_id in attach_responses: 
        volume_id = attach_responses[instance_id]["create"]["VolumeId"]
        ## Automation assume role is generated from utils stack. TODO: make the pulling of stack resource arns automatic. 
        ssm_client.start_automation_execution(DocumentName= "NeuroCaaS AutomountDocument",Parameters = {"InstanceId":[instance_id],"VolumeId":[volume_id],"AutomationAssumeRole":["arn:aws:iam::739988523141:role/testutilsstack-MountRole-HYJ75PSR095O"]})

def put_budget_parameter(groupname,analysisname,value,overwrite = True):
    """ Assign a value to the user's budget parameter. Has the form /neurocaas/budgets/groupname/analysisname

    :param groupname: the name of the user group for which we are assigning a budget parameter.
    :param analysisname: the name of the analysis bucket for which we are assigning a budget.
    :param value: the value to assign. Must be an integer.
    :param overwrite: Whether or not to overwrite an existing budget value. Defaults to True.
    """
    assert type(value) == int
    paramname = budgetname.format(g=groupname,a =analysisname)
    response = ssm_client.put_parameter(
            Name = paramname,
            Description = "Budgeted allowance in dollars for this user group.",
            Type = "String",
            Overwrite = overwrite,
            Value = str(value)
            )

def get_budget_parameter(groupname,analysisname):
    """ Get the assigned value of the user's budget parameter. Has the form /neurocaas/budgets/groupname/analysisname

    :param groupname: the name of the user group for which we are retrieving the budget parameter.
    :param analysisname: the name of the analysis bucket for which we are retrieving a budget.
    """
    paramname = budgetname.format(g=groupname,a =analysisname)
    response = ssm_client.get_parameter(
            Name = paramname)
    return int(response["Parameter"]["Value"])
        
