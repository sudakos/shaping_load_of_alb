# shaping_load_of_alb
You can reduce the load of access from the internet on the main target with the lamda function  using weighted routing of Applicatin Load Balancer.

<img src="./architecture.png" whdth=500>

# Construction procedure

## Premise
* WEB servers and ALB that you want to protect have been built.
* The ALB is called "ALB-SLOA-LimitingLoad"
* The TargetGroup to the servers is caled "TG-SLOA-ToServersToProtect"

## Summary of procedure
1. Create the TargetGroup having no instances : "TG-SLOA-NoInstances"
1. Set the some values to Parameter Store 
2. Create the role for the lambda function : "RoleSLOAforLambda"
3. Build the lambda function : Lambda-SLOA-TuneWeight
4. Set CloudWatch Event to run the lambda function every 1 miutes


