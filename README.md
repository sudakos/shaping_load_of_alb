# shaping_load_of_alb
You can reduce the load of access from the internet on the main target with the lamda function  using weighted routing of Applicatin Load Balancer.

<img src="./architecture.png" whdth=500>

# Construction procedure

## Premise
* WEB servers and ALB that you want to protect have been built.
* The ALB is called "ALB-SLOA-LimitingLoad"
* The TargetGroup to the servers is caled "TG-SLOA-ToServersToProtect"

## Summary of the construction procedure
1. Create the TargetGroup having no instances : "TG-SLOA-NoInstances"
2. Set the some values to Parameter Store 
3. Create the role for the lambda function : "RoleSLOAforLambda"
4. Build the lambda function : Lambda-SLOA-TuneWeight
5. Set CloudWatch Event to run the lambda function every 1 miutes

## Detail of the construction procedure

### 1. Create the TargetGroup having no instances : "TG-SLOA-NoInstances"

Check the follow value:
* VPC ID where the system is build

```shell
aws elbv2 create-target-group --name "TG-SLOA-NoInstances" --protocol HTTP --port 80 --vpc-id <VPC where the system is build>
```
Make a note the ARN of TargetGroup "TG-SLOA-NoInstances"

### 2. Set the some values to Parameter Store 

Check the follow value:
* the ARN of listener of the ALB
* the ARN of the TargetGroup to the servers is caled "TG-SLOA-ToServersToProtect"
* the ARN of TargetGroup "TG-SLOA-NoInstances"
* the value of dimensions to specify the ALB

Decide the follow value:
* the threthold of the number of new connections

```shell
aws ssm put-parameter --name '/SLOA/listenerArn' --value <the ARN of listener of the ALB> --type String --overwrite
aws ssm put-parameter --name '/SLOA/mainTargetGroupArn' --value <the ARN of the TargetGroup to the servers is caled "TG-SLOA-ToServersToProtect"> --type String --overwrite
aws ssm put-parameter --name '/SLOA/nullTargetGroupArn' --value <the ARN of TargetGroup "TG-SLOA-NoInstances"> --type String --overwrite
aws ssm put-parameter --name '/SLOA/valueOfDimentions' --value <the value of dimensions to specify the ALB> --type String --overwrite
aws ssm put-parameter --name '/SLOA/threthold' --value <the threthold of the number of new connections> --type String --overwrite
```

### 3. Create the role for the lambda function : "RoleSLOAforLambda"

```shell
aws iam create-role --role-name "RoleSLOAforLambda" --assume-role-policy-document file://lambda_role.json
aws iam attach-role-policy --role-name "RoleSLOAforLambda" --policy-arn "arn:aws:iam::aws:policy/RoleSLOAforLambda ElasticLoadBalancingFullAccess"
aws iam attach-role-policy --role-name "RoleSLOAforLambda" --policy-arn "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess"
aws iam attach-role-policy --role-name "RoleSLOAforLambda" --policy-arn "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
```

Make a note the ARN of the lambda function

### 4. Build the lambda function : Lambda-SLOA-TuneWeight

```shell
zip temp.zip Lambda-SLOA-TuneWeight.py
aws lambda create-function --function-name "Lambda-SLOA-TuneWeight" \
      --runtime "python3.8" --role "RoleSLOAforLambda" \
      --handler Lambda-SLOA-TuneWeight.lambda_handler \
      --timeout 60 --zip-file fileb://temp.zip
```

### 5. Set CloudWatch Event to run the lambda function every 1 miutes

Check the follow value:
* the name of the lambda function
* the ARN of the lambda function

Decide the follow value:
* the name of CloudWatch Rules
* the ARN of CloudWatch Rules

```shell
aws lambda add-permission \
--function-name <the name of the lambda function> \
--statement-id events-access \
--action 'lambda:InvokeFunction' \
--principal events.amazonaws.com \
--source-arn <the ARN of CloudWatch Rules>
aws events put-rule --name <the name of CloudWatch Rules> --schedule-expression "rate(1 minute)" --state ENABLED
aws events put-targets --rule <the name of CloudWatch Rules> --targets Arn=<the ARN of the lambda function>,Id=1
```
