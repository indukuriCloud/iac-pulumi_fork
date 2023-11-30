# iac-pulumi

Pulumi is an Infrastructure as Code (IaC) tool designed to help manage and provision cloud resources and infrastructure. Pulumi provides a robust set of libraries, integrations with popular CI/CD tools. 
Pulumi allows you to automate the provisioning and management of cloud infrastructure. You can define your infrastructure in code, and Pulumi will create, update, or delete cloud resources to match the desired state, reducing the manual and error-prone tasks involved in setting up and maintaining infrastructure.


### Requirements

- Python 3.x
- Pulumi 3.x.x
- .env file 
- AWS Account


### Installation 
https://www.pulumi.com/docs/install
```bash
$ brew install pulumi/tap/pulumi
```
https://www.pulumi.com/docs/languages-sdks/python

### Create Instance
```bash
$ pulumi up --config aws:profile= Your_Admin_IAM_User
```

### Destroy Stack
Once Everything is checked, delete the instance by:
```bash
$ pulumi destroy
```

# Lambda Packages
```
https://github.com/indukuriCloud/test/raw/main/my_deployment_package.zip
```

### Environment variables:
```
AWS_REGION=YOUR_NEAREST_REGION

AWS_AVAILABILITY_ZONES=AVAILABLE_REGION

MY_PUBLIC_SUBNETS=YOUR_CHOICE

MY_PRIVATE_SUBNETS=YOUR_CHOICE

MY_VPC_CIDR_PREFIX=x.x.x.x/xx(ex:10.0.0.1/16)

MY_VPC_NAME=CHOICE_OF_NAME

MY_SUBNET_PUBLIC_NAME=pulumi-public-subnet-

MY_SUBNET_PRIVATE_NAME=pulumi-private-subnet-

MY_PUBLIC_ROUTE_TABLE=publicRouteTable

MY_PRIVATE_ROUTE_TABLE=privateRouteTable

MY_PUBLIC_SUBNET_CONNECT=public-subnet-connect-

MY_PRIVATE_SUBNET_CONNECT=private-subnet-connect-

MY_INTERNET_GATEWAY=pulumi-internetGateway

MY_PUBLIC_ROUTE=publicRoute

MY_PUBLIC_ROUTE_CIDR_DES=0.0.0.0/0

Instance_Type=t2.micro

AMI=ami-id
```

### RDS Instance Variables
```
export ALLOCATED_STORAGE='10'

export STORAGE_TYPE="gp2"

export ENGINE="Postgres"

export ENGINE_VERSION=""

export INSTANCE_CLASS="db.t3.micro"

export NAME=""

export USERNAME=""

export PASSWORD=""

export DB_NAME=""
```

### GCP 
```
GCP_BUCKET_NAME=

GCP_BUCKER_LOCATION=

PROJECT_ID=
```
### AWS Lambda
```
MAILGUN_API_KEY=

MAILGUN_DOMAIN=

MAILGUN_SENDER=

DYNAMODB_TABLE=

LAMBDA_PACKAGES=

```
### License
This project is licensed under the MIT License.
