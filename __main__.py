import os
import base64
import boto3
import pulumi
import json
import subprocess
from decouple import config
from pulumi_gcp import storage, serviceaccount, projects
from dotenv import load_dotenv
from pulumi import Output, ResourceOptions
from pulumi_aws import ec2,rds, route53, iam, autoscaling, cloudwatch, lb, sns, dynamodb, lambda_, acm
from pulumi_random import RandomPassword

# Load environment variables from the .env file
load_dotenv()

# Load environment variables from the .env file
region = config("AWS_REGION")
availability_zones = config("AWS_AVAILABILITY_ZONES").split(",")
num_public_subnets = int(config("MY_PUBLIC_SUBNETS"))
num_private_subnets = int(config("MY_PRIVATE_SUBNETS"))
vpc_cidr_prefix = config("MY_VPC_CIDR_PREFIX")
vpc_name = config("MY_VPC_NAME")
subnet_public_name = config("MY_SUBNET_PUBLIC_NAME")
subnet_private_name = config("MY_SUBNET_PRIVATE_NAME")
public_route_table = config("MY_PUBLIC_ROUTE_TABLE")
private_route_table = config("MY_PRIVATE_ROUTE_TABLE")
public_subnet_connect = config("MY_PUBLIC_SUBNET_CONNECT")
private_subnet_connect = config("MY_PRIVATE_SUBNET_CONNECT")
internet_gateway = config("MY_INTERNET_GATEWAY")
public_route = config("MY_PUBLIC_ROUTE")
public_route_cidr_des = config("MY_PUBLIC_ROUTE_CIDR_DES")
instance_type = config("Instance_Type")
key = os.getenv("SSH_KEY")
a_record_name = config("A_RECORD_NAME")
zone_id = config("HOSTED_ZONE_ID")

#GCS
gcp_bucket_name = os.getenv("GCP_BUCKET_NAME")
gcp_bucker_location = os.getenv("GCP_BUCKER_LOCATION")
project_id = os.getenv("PROJECT_ID")

#lambda
mailgun_api_key = os.getenv("MAILGUN_API_KEY")
mailgun_domain = os.getenv("MAILGUN_DOMAIN")
mailgun_sender = os.getenv("MAILGUN_SENDER")
dynamodb_table = os.getenv("DYNAMODB_TABLE")
lambda_packages=os.getenv("LAMBDA_PACKAGES")

# Create a VPC
vpc = ec2.Vpc(
    vpc_name,
    cidr_block=vpc_cidr_prefix,
    instance_tenancy="default",
    tags={
        "Name": vpc_name,
    },
)

public_subnets = []
private_subnets = []

# Create public and private subnets
for i in range(num_public_subnets):
    subnet_name = f"{subnet_public_name}{i + 1}"
    subnet = ec2.Subnet(
        subnet_name,
        vpc_id=vpc.id,
        availability_zone=region+availability_zones[i % len(availability_zones)],  # Rotate AZs
        cidr_block=f"10.0.{i + 1}.0/24",
        map_public_ip_on_launch=True,
        tags={
            "Name": subnet_name,
        },
    )
    public_subnets.append(subnet)

for i in range(num_private_subnets):
    subnet_name = f"{subnet_private_name}{i + 1}"
    subnet = ec2.Subnet(
        subnet_name,
        vpc_id=vpc.id,
        availability_zone=region+availability_zones[i % len(availability_zones)],  # Rotate AZs
        cidr_block=f"10.0.{num_public_subnets + i + 1}.0/24",
        tags={
            "Name": subnet_name,
        },
    )
    private_subnets.append(subnet)

# Create route tables
public_route_table = ec2.RouteTable(
    public_route_table,
    vpc_id=vpc.id,
    tags={
        "Name": public_route_table,
    },
)

private_route_table = ec2.RouteTable(
    private_route_table,
    vpc_id=vpc.id,
    tags={
        "Name": private_route_table,
    },
)

public_route_table_associations = []
private_route_table_associations = []

# Associate public subnets with the public route table
for i, subnet in enumerate(public_subnets):
    association = ec2.RouteTableAssociation(
        f"{public_subnet_connect}{i + 1}",
        subnet_id=subnet.id,
        route_table_id=public_route_table.id,
    )
    public_route_table_associations.append(association)

# Associate private subnets with the private route table
for i, subnet in enumerate(private_subnets):
    association = ec2.RouteTableAssociation(
        f"{private_subnet_connect}{i + 1}",
        subnet_id=subnet.id,
        route_table_id=private_route_table.id,
    )
    private_route_table_associations.append(association)

# Create an Internet Gateway
internet_gateway = ec2.InternetGateway(
    internet_gateway,
    vpc_id=vpc.id,
    tags={
        "Name": internet_gateway,
    },
)

# Create a public route in the public route table
public_route = ec2.Route(
    public_route,
    route_table_id=public_route_table.id,
    destination_cidr_block=public_route_cidr_des,
    gateway_id=internet_gateway.id,
)

# Load Balancer Security Group
load_balancer_security_group = ec2.SecurityGroup(
    "loadBalancerSecurityGroup",
    vpc_id=vpc.id,
    ingress=[
        ec2.SecurityGroupIngressArgs(
            from_port=80,
            to_port=80,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],  # Allow TCP on port 80 from anywhere
        ),
        ec2.SecurityGroupIngressArgs(
            from_port=443,
            to_port=443,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],  # Allow TCP on port 443 from anywhere
        ),
    ],
    egress=[
        ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,  # Allow all outbound traffic
            protocol="-1",   # All protocols
            cidr_blocks=["0.0.0.0/0"],  # Allow all outbound traffic
        ),
    ],
    tags={
        "Name": "loadBalancerSecurityGroup",
    },
)

# Update App Security Group
app_security_group_ingress = [
    ec2.SecurityGroupIngressArgs(
        from_port=8000, 
        to_port=8000,  
        protocol="tcp",
        security_groups=[load_balancer_security_group.id],  # Allow application traffic from load balancer
    ),
]

app_security_group = ec2.SecurityGroup(
    "appSecurityGroup",
    vpc_id=vpc.id,
    ingress=app_security_group_ingress,
    egress=[
        ec2.SecurityGroupEgressArgs(
            from_port=0,
            to_port=0,  # Allow all outbound traffic
            protocol="-1",   # All protocols
            cidr_blocks=["0.0.0.0/0"],  # Allow all outbound traffic
        ),
    ],
    tags={
        "Name": "appSecurityGroup",
    },
)

# Create a security group for RDS instances (Database Security Group)
db_security_group = ec2.SecurityGroup(
    "dbSecurityGroup",
    vpc_id=vpc.id,
    ingress=[
        ec2.SecurityGroupIngressArgs(
            from_port=5432,  # PostgreSQL port
            to_port=5432,
            protocol="tcp",
            security_groups=[app_security_group.id],  # Allow traffic from the application security group
        ),
    ],
    tags={
        "Name": "dbSecurityGroup",
    },
)

# Create an RDS parameter group for PostgreSQL
rds_parameter_group = rds.ParameterGroup(
    "postgres-parameter-group",
    family="postgres14",  # Use the appropriate PostgreSQL version (14 for example)
    parameters=[
        rds.ParameterGroupParameterArgs(
            name="autovacuum",
            value="1",
            apply_method="immediate"
        ),
    ],
)

# Subnet Group
rds_subnet_group = rds.SubnetGroup(
    "rds-subnet-group",
    subnet_ids=[subnet.id for subnet in private_subnets],  # Assuming private_subnets is a list of subnet objects
    tags={
        "Name": "RDS Subnet Group",
    },
)

# Create an RDS instance
rds_instance = rds.Instance(
    "rds-instance",
    allocated_storage=os.getenv('ALLOCATED_STORAGE'),  # Modify the storage size as needed
    storage_type=os.getenv('STORAGE_TYPE'),
    engine=os.getenv("ENGINE"),  # Use PostgreSQL
    engine_version=os.getenv("ENGINE_VERSION"),  # Specify the PostgreSQL version
    instance_class=os.getenv("INSTANCE_CLASS"),  # Choose an appropriate instance class
    username=os.getenv("DB_USERNAME"),  # Master username
    password=os.getenv("PASSWORD"),  # Specify a strong master password
    skip_final_snapshot=True,  # Configure as needed
    vpc_security_group_ids=[db_security_group.id],  # Attach the database security group
    db_subnet_group_name=rds_subnet_group.name,  # Specify the name of your DB subnet group
    publicly_accessible=False,  # Disable public accessibility
    db_name=os.getenv("DB_NAME"),  # Specify the database name
    parameter_group_name=rds_parameter_group.name,  # Use the created parameter group
    multi_az=False, # Multi-AZ deployement
    tags={
        "Name": "RDSInstance",
    },
    
)

# Define the SNS topic
sns_topic = sns.Topic("my-sns-topic")

# User Data
user_data = Output.all(
    rds_instance.address,
    Output.from_input(os.getenv("DB_USERNAME")),
    Output.from_input(os.getenv("PASSWORD")),
    Output.from_input(os.getenv("DB_NAME")),
    region,
    sns_topic.arn
).apply(lambda values: f"""#!/bin/bash
sed -i 's/POSTGRES_USER ?= cloud/POSTGRES_USER ?= {values[1]}/g' /home/manohar/webapp/Makefile
sed -i 's/POSTGRES_PASSWORD ?= cloud/POSTGRES_PASSWORD ?= {values[2]}/g' /home/manohar/webapp/Makefile
sed -i 's/POSTGRES_HOST ?= 127.0.0.1/POSTGRES_HOST ?= {values[0]}/g' /home/manohar/webapp/Makefile
sed -i 's/POSTGRES_DB ?= cloud/POSTGRES_DB ?= {values[3]}/g' /home/manohar/webapp/Makefile
sed -i 's/AWS_REGION ?= us-east-1/AWS_REGION ?= {values[4]}/g' /home/manohar/webapp/Makefile
sed -i 's/SNS_TOPIC_ARN ?= arn/SNS_TOPIC_ARN ?= {values[5]}/g' /home/manohar/webapp/Makefile

sudo systemctl restart webapp
sudo systemctl disable postgresql
sudo systemctl stop postgresql

sudo -i -u manohar bash << EOF

sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -c file://home/manohar/webapp/packer/cloudwatch-config.json -s
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a start

EOF

""")

user_data_base64 = Output.all(user_data).apply(lambda us: base64.b64encode(us[0].encode("utf-8")).decode("utf-8"))

# Cloud watch I AM role
attach_role = iam.Role(
    "cloudwatch-role",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Effect": "Allow"
            }
        ]
    }""",
)
instance_profile = iam.InstanceProfile(
    "instance-profile",
    role=attach_role.name,
)

# Attach the policy to the CloudWatch role
iam.RolePolicyAttachment(
    "cloudwatch-policy-attachment",
    policy_arn="arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy",
    role=attach_role.name,
)

# Attach a policy that allows SNS actions
iam.RolePolicyAttachment(
    "snsPolicyAttachment",
    policy_arn="arn:aws:iam::aws:policy/AmazonSNSFullAccess", 
    role=attach_role.name
)

# Create an Application Load Balancer
load_balancer = lb.LoadBalancer(
    "myLoadBalancer",
    internal=False,
    load_balancer_type="application",
    security_groups=[load_balancer_security_group.id],
    subnets=[subnet.id for subnet in public_subnets],  # Use public subnets
)

# Create a Target Group for the Load Balancer
target_group = lb.TargetGroup(
    "appTargetGroup",
    port=8000,  # Make sure to define application_port
    protocol="HTTP",
    target_type="instance",
    vpc_id=vpc.id,
    health_check={
        "enabled": True,
        "matcher": "200",
        "path": "/healthz",  # Modify as per your application's health check endpoint
        "protocol": "HTTP",
        "interval": 30,
        "healthy_threshold": 2,  # Added parameter
        "unhealthy_threshold": 2,  # Added parameter
        "timeout": 5,  # Added parameter
        "port": "8000"
    },
    tags={
        "Name": "app-target-group",  # Modify the tag as needed
    },
)


acm_certificate = acm.get_certificate(domain=a_record_name,
    statuses=["ISSUED"])

# Create Load Balancer Listener
app_listener = lb.Listener(
    "appListener",
    load_balancer_arn=load_balancer.arn,
    port=443,
    protocol="HTTPS",
    certificate_arn=acm_certificate.arn,
    default_actions=[
        {
            "type": "forward",
            "target_group_arn": target_group.arn,
        },
    ],
)

ami = ec2.get_ami(
    executable_users=["self"],
    most_recent=True,
)

#  Auto Scaling Application Launch Template
launch_template = ec2.LaunchTemplate("webAppLaunchTemplate",
    name="webAppLaunchTemplate",
    image_id=ami.id,
    instance_type="t2.micro",
    key_name=key, 
    network_interfaces=[{
        "associate_public_ip_address": True,
        "security_groups": [app_security_group.id],
    }],
    user_data=user_data_base64, 
    iam_instance_profile={
        "arn": instance_profile.arn, 
    },
)

# Auto Scaling Group
auto_scaling_group = autoscaling.Group(
    "webAppAutoScalingGroup",
    name="webAppAutoScalingGroup",
    launch_template=autoscaling.GroupLaunchTemplateArgs(
        id=launch_template.id,
        version="$Latest",
    ),
    min_size=1,
    max_size=3,
    desired_capacity=1,
    default_cooldown=60,
    vpc_zone_identifiers=[subnet.id for subnet in public_subnets],
    tags=[
        autoscaling.GroupTagArgs(
            key="webapp",
            value="webAppAutoScalingGroup",
            propagate_at_launch=True,
        ),
    ],
)

# Create Scaling Policies
scale_up_policy = autoscaling.Policy(
    "scaleUpPolicy",
    policy_type = "SimpleScaling",
    scaling_adjustment=1,
    adjustment_type="ChangeInCapacity",
    cooldown=60,
    autoscaling_group_name=auto_scaling_group.name,
)

scale_down_policy = autoscaling.Policy(
    "scaleDownPolicy",
    policy_type = "SimpleScaling",
    scaling_adjustment=-1,
    adjustment_type="ChangeInCapacity",
    cooldown=60,
    autoscaling_group_name=auto_scaling_group.name,
)

# Create CloudWatch Alarms
cpu_utilization_high_alarm = cloudwatch.MetricAlarm(
    "cpuUtilizationHighAlarm",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=1,
    metric_name="CPUUtilization",
    namespace="AWS/EC2",
    period=60,
    threshold=5,
    statistic="Average",
    alarm_actions=[scale_up_policy.arn],
    dimensions={"AutoScalingGroupName": auto_scaling_group.name},
)

cpu_utilization_low_alarm = cloudwatch.MetricAlarm(
    "cpuUtilizationLowAlarm",
    comparison_operator="LessThanThreshold",
    evaluation_periods=1,
    metric_name="CPUUtilization",
    namespace="AWS/EC2",
    period=60,
    threshold=3,
    statistic="Average",
    alarm_actions=[scale_down_policy.arn],
    dimensions={"AutoScalingGroupName": auto_scaling_group.name},
)

# Update Auto Scaling Group to use the ALB
auto_scaling_group.attachments = [
    autoscaling.Attachment(
        autoscaling_group_name=auto_scaling_group.name,
        lb_target_group_arn=target_group.arn,  # Use the Target Group ARN of your ALB
        resource_name="AutoScale_LB",
    ),
]

# After Load Balancer is created, define Route 53 A record
a_record = pulumi.Output.concat(load_balancer.dns_name).apply(lambda dns_name: 
    route53.Record(
        "a_record",
        name=a_record_name,
        zone_id=zone_id,
        type="A",
        aliases=[{
            "name": dns_name,
            "zoneId": load_balancer.zone_id,  # Load Balancer Zone ID
            "evaluateTargetHealth": True,
        }],
    )
)

# Generate a random password for the Lambda function
password = RandomPassword("lambdaPassword", length=16, special=True)

lambda_role = iam.Role(
    "lambda_role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "lambda.amazonaws.com",
                },
                "Effect": "Allow",
                "Sid": "",
            },
        ],
    }),
)

dynamodb_policy_attachment = iam.PolicyAttachment(
    "dynamodb_policy_attachment",
    policy_arn="arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess",
    roles=[lambda_role.name],
)

# Create a DynamoDB table to track emails
email_tracking_table = dynamodb.Table(
    "email_track",
    attributes=[{"name": "id", "type": "N"}],
    billing_mode="PAY_PER_REQUEST",
    hash_key="id",
)

gcs_bucket = storage.Bucket(gcp_bucket_name, location=gcp_bucker_location)

# Create a Google Service Account
service_account = serviceaccount.Account("serviceAccount",
    account_id="lambda",
    display_name="Lambda Service Account")

# Grant write permissions to the service account on the GCS bucket
role = projects.IAMBinding("role",
    role="roles/storage.objectUser",
    project=project_id,
    members=[pulumi.Output.concat("serviceAccount:", service_account.email)])

role_viewer = projects.IAMBinding("role-viewer",
    role="roles/storage.insightsCollectorService",
    project=project_id,
    members=[pulumi.Output.concat("serviceAccount:", service_account.email)])

# Create Access Keys for the Google Service Account
access_keys = serviceaccount.Key("my-access-keys",
    service_account_id=service_account.name,

)

# lambda_environment_uppercase = {k.upper(): v for k, v in lambda_environment.items()}

# Create an AWS Lambda function
lambda_function = lambda_.Function(
    "middleware",
    runtime="python3.11",
    handler="lambda_function.lambda_handler",
    code=pulumi.AssetArchive({
        ".": pulumi.FileArchive(lambda_packages),
    }),
    environment=lambda_.FunctionEnvironmentArgs(
        variables={
            "GCS_BUCKET_NAME": gcs_bucket.name,
            "MAILGUN_API_KEY": mailgun_api_key,
            "MAILGUN_DOMAIN": mailgun_domain,
            "MAILGUN_SENDER": mailgun_sender,
            "DYNAMODB_TABLE": dynamodb_table,
            "AWS_REG": region,
            "GCP_CREDENTIALS": access_keys.private_key
        },

    ),
    role=lambda_role.arn, 
    timeout=300,
)

lambda_.Permission(
    "lambda-dynamodb-permission",
    action="lambda:InvokeFunction",
    function=lambda_function.arn,
    principal="sns.amazonaws.com",
)

# Subscribe Lambda function to the SNS topic
sns_topic_subscription = sns.TopicSubscription(
    "lambdaSubscription",
    protocol="lambda",
    endpoint=lambda_function.arn,
    topic=sns_topic.arn
)

# Export relevant information
pulumi.export("role", attach_role.name)
pulumi.export("autoScalingGroup", auto_scaling_group.name)
pulumi.export("loadBalancerSecurityGroup", load_balancer_security_group.name)
pulumi.export("loadBalancer", load_balancer.dns_name)
pulumi.export("sns_topic_arn", sns_topic.arn)
pulumi.export("lambdaFunctionArn", lambda_function.arn)
pulumi.export("cert",acm_certificate.arn)
pulumi.export("ami",ami.id)
