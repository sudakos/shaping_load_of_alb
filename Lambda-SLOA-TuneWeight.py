import json
import boto3
import base64
import logging
import datetime
from datetime import datetime
from datetime import timedelta

region_name = boto3.session.Session().region_name
#ssm = boto3.client('ssm', region_name=region_name)
clientELB = boto3.client('elbv2')
clientCloudWatch = boto3.client('cloudwatch')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

listenerArn='arn:aws:elasticloadbalancing:us-east-1:404506830242:listener/app/ALB-SLOA-LimitingLoad/feeba4c459681324/cf6499dadc8053d3'
mainTargetGroupArn='arn:aws:elasticloadbalancing:us-east-1:404506830242:targetgroup/TG-SLOA-ToServersToProtect/cd57a363e3d95583'
nullTargetGroupArn='"arn:aws:elasticloadbalancing:us-east-1:404506830242:targetgroup/TG-SLOA-NoInstances/4a5ada26de8936f5"'
valueOfDimentions='app/ALBforArtifactToRateLimit/a6ef3e91e8ada08e'

threthold=50

def lambda_handler(event, context):
    
    newConnections=getValue_NewConnections()

    if(threthold>=newConnections):
        print("## clear rate()")
        response=clearRate()
    else:
        rate=int(threthold*100/(newConnections))
        print("## change rate()",rate)
        response=changeRate(rate)

    print(response)
    return response

def getValue_NewConnections():   
    try:
        current_time = datetime.utcnow()
        start_time = current_time - timedelta(minutes=5)
        end_time = current_time
        period = 60
    
        response=response = clientCloudWatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'id1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/ApplicationELB',
                            'MetricName': 'NewConnectionCount',
                            'Dimensions': [
                                {
                                    'Name': 'LoadBalancer',
                                    'Value': valueOfDimentions
                                }
                            ]
                        },
                        'Period': period,
                        'Stat': 'Average'
                    },
                    'ReturnData': True
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
        )
    
    
        values=response['MetricDataResults'][0]['Values']

        if not values:
            maxValues=0
        else:
            maxValues=max(values)

        return maxValues
    
    except Exception as e:
        logger.error('fail to modify_listener')
        logger.error(e)
        raise e



def clearRate():

    try:
        response = clientELB.modify_listener(
            ListenerArn=listenerArn,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'Order': 1,
                    'ForwardConfig': {
                        'TargetGroups': [
                            {
                                'TargetGroupArn': mainTargetGroupArn,
                                'Weight': 100
                            }
                        ]
                    }
                }
            ]
        )

#        confirming_time = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        
        return response

    except Exception as e:
        logger.error('fail to clearRate')
        logger.error(e)
        raise e



def changeRate(rateToMain):

    try:
        rateToSub=100-rateToMain

        response = clientELB.modify_listener(
            ListenerArn=listenerArn,
            DefaultActions=[
                {
                    'Type': 'forward',
                    'Order': 1,
                    'ForwardConfig': {
                        'TargetGroups': [
                            {
                                'TargetGroupArn': mainTargetGroupArn,
                                'Weight': rateToMain
                            },
                            {
                               'TargetGroupArn': nullTargetGroupArn,
                                'Weight': rateToSub
                            }
                        ]
                    }
                }
            ]
        )

        return response

    except Exception as e:
        logger.error('fail to changeRate')
        logger.error(e)
        raise e

event={}
context=""

response=lambda_handler(event,context)

print(response)
