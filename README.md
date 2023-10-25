# iac-pulumi

Pulumi is an Infrastructure as Code (IaC) tool designed to help manage and provision cloud resources and infrastructure. Pulumi provides a robust set of libraries, integrations with popular CI/CD tools. 
Pulumi allows you to automate the provisioning and management of cloud infrastructure. You can define your infrastructure in code, and Pulumi will create, update, or delete cloud resources to match the desired state, reducing the manual and error-prone tasks involved in setting up and maintaining infrastructure.


### Requirements
- Python 3.x
- Pulumi 3.x.x
- .env file 
- AWS Account

### Environment variables:
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

### Installation 
https://www.pulumi.com/docs/install
```bash
$ brew install pulumi/tap/pulumi
```
https://www.pulumi.com/docs/install
https://www.pulumi.com/docs/languages-sdks/python

### License
This project is licensed under the MIT License.