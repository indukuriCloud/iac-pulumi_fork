import pulumi
import pulumi_aws as aws

# Creating a VPC
main = aws.ec2.Vpc("pulumi01",
    cidr_block="10.0.0.0/16",
    instance_tenancy="default",
    tags={
        "Name": "pulumi01"
    })

# Defining the availability zones used
availability_zones = [
    "us-east-1a",
    "us-east-1b",
    "us-east-1c"
]

public_subnets = []
private_subnets = []

# Creating 3 public and 3 private subnets in different availability zones
for i in range(3):
    subnet_name = f"pulumi-public-subnet-{i + 1}"
    subnet = aws.ec2.Subnet(subnet_name,
        vpc_id=main.id,
        availability_zone=availability_zones[i],
        cidr_block=f"10.0.{i + 1}.0/24",
        tags={
            "Name": subnet_name
        })
    public_subnets.append(subnet)

for i in range(3):
    subnet_name = f"pulumi-private-subnet-{i + 1}"
    subnet = aws.ec2.Subnet(subnet_name,
        vpc_id=main.id,
        availability_zone=availability_zones[i],
        cidr_block=f"10.0.{i + 4}.0/24",
        tags={
            "Name": subnet_name
        })
    private_subnets.append(subnet)

# Creating route tables
public_route_table = aws.ec2.RouteTable("publicRouteTable",
    vpc_id=main.id,
    tags={
        "Name": "PublicRouteTable"
    })

private_route_table = aws.ec2.RouteTable("privateRouteTable",
    vpc_id=main.id,
    tags={
        "Name": "PrivateRouteTable"
    })

public_route_table_associations = []
private_route_table_associations = []

# Associating public subnets with the public route table
y = 0
for public_subnet in public_subnets:
    association = aws.ec2.RouteTableAssociation(f"public-subnet-connect-{y + 1}",
        subnet_id=public_subnet.id,
        route_table_id=public_route_table.id)
    y += 1
    public_route_table_associations.append(association)

# Associating private subnets with the private route table
k = 0
for private_subnet in private_subnets:
    association = aws.ec2.RouteTableAssociation(f"private-subnet-connect-{k + 1}",
        subnet_id=private_subnet.id,
        route_table_id=private_route_table.id)
    k += 1
    private_route_table_associations.append(association)

# Creating an Internet Gateway
internet_gateway = aws.ec2.InternetGateway("internetGateway",
    vpc_id=main.id,
    tags={
        "Name": "pulumi-igw"
    })

# Creating a public route in the public route table
public_route = aws.ec2.Route("publicRoute",
    route_table_id=public_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    gateway_id=internet_gateway.id)
