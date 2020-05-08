import json
import boto3
import base64
import logging
import datetime
from datetime import datetime
from datetime import timedelta

region_name = boto3.session.Session().region_name
ssm = boto3.client('ssm', region_name=region_name)
clientELB = boto3.client('elbv2')
clientCloudWatch = boto3.client('cloudwatch')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# main lambda function
def lambda_handler(event, context):
    
    threthold=int( get_param('/SLOA/threthold') )
    newConnections=getValue_NewConnections()

    print("## #NewConnections : ",newConnections)

    if(threthold>=newConnections):
        print("## clear rate()")
        response=clearRate()
    else:
        rate=int(threthold*100/(newConnections))
        print("## change rate()",rate)
        response=changeRate(rate)

    print(response)
    return response

# return the value about the number of new connections
def getValue_NewConnections():   
    try:
        valueOfDimentions=get_param('/SLOA/valueOfDimentions')

        current_time = datetime.utcnow()
        start_time = current_time - timedelta(minutes=5)
        end_time = current_time
        period = 60
    
        response= clientCloudWatch.get_metric_data(
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
        print("## values[] : ", values)

        if not values:
            maxValues=0
        else:
            maxValues=max(values)

        return maxValues
    
    except Exception as e:
        logger.error('fail to modify_listener')
        logger.error(e)
        raise e


# change the weight of forwarding to main target group to 100%
def clearRate():

    try:
        listenerArn=get_param('/SLOA/listenerArn')
        mainTargetGroupArn=get_param('/SLOA/mainTargetGroupArn')
        nullTargetGroupArn=get_param('/SLOA/nullTargetGroupArn')

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


# change the weight of forwarding to main target group to "rateToMain"
def changeRate(rateToMain):

    try:
        listenerArn=get_param('/SLOA/listenerArn')
        mainTargetGroupArn=get_param('/SLOA/mainTargetGroupArn')
        nullTargetGroupArn=get_param('/SLOA/nullTargetGroupArn')

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

# return the value associated by key from ParameterStore
def get_param(key: str) -> str:
    global ssm
    try:
        return ssm.get_parameter(Name=key)['Parameter']['Value']
    except Exception as e:
        logger.error('fail to get_param(key: str) ')
        logger.error(e)
        raise e
     
event={}
context=""

response=lambda_handler(event,context)

print(response)
