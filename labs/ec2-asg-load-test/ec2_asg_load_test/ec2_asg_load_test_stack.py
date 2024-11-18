from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    CfnOutput,
    aws_ec2 as ec2,
    aws_autoscaling as autoscaling,
    Tags as tags,  # Import Tags
)
from constructs import Construct


class Ec2AsgLoadTestStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        tags.of(self).add("Environment", "Development")
        tags.of(self).add("Project", "WebApp")

        # Create VPC
        vpc = ec2.Vpc(
            self,
            "MyVPC",
            max_azs=2,  # Use 2 Availability Zones
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
            ],
        )

        # Add specific tags to VPC
        tags.of(vpc).add("Name", "CDKVPC")
        tags.of(vpc).add("ResourceType", "Network")

        # Create Security Group for Web Servers
        web_security_group = ec2.SecurityGroup(
            self,
            "WebServerSG",
            vpc=vpc,
            description="Security group for web servers",
            allow_all_outbound=True,
        )
        # Add tags to web security group
        tags.of(web_security_group).add("Name", "WebServerSG")
        tags.of(web_security_group).add("ResourceType", "SecurityGroup")

        web_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(80),
            description="Allow HTTP traffic",
        )

        # Create Security Group for Bastion Host
        bastion_security_group = ec2.SecurityGroup(
            self,
            "BastionSG",
            vpc=vpc,
            description="Security group for bastion host",
            allow_all_outbound=True,
        )
        # Add tags to bastion security group
        tags.of(bastion_security_group).add("Name", "BastionSG")
        tags.of(bastion_security_group).add("ResourceType", "SecurityGroup")

        bastion_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description="Allow SSH access",
        )

        web_security_group.add_ingress_rule(
            peer=bastion_security_group,
            connection=ec2.Port.tcp(22),
            description="Allow SSH from bastion",
        )

        # Create User Data script to install and start Nginx
        web_user_data = ec2.UserData.for_linux()
        web_user_data.add_commands(
            "yum update -y",
            # "yum install -y nginx",
            "amazon-linux-extras install nginx1",
            "systemctl start nginx",
            "systemctl enable nginx",
        )

        # Create Launch Template
        launch_template = ec2.LaunchTemplate(
            self,
            "ASG-LaunchTemplate",
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            ),
            user_data=web_user_data,
            security_group=web_security_group,
        )

        # Add tags to launch template
        tags.of(launch_template).add("Name", "WebServerLT")
        tags.of(launch_template).add("ResourceType", "LaunchTemplate")

        # Create Auto Scaling Group
        asg = autoscaling.AutoScalingGroup(
            self,
            "MyASG",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            launch_template=launch_template,
            min_capacity=0,
            max_capacity=4,
            desired_capacity=1,
        )

        # Add tags to ASG and its instances
        tags.of(asg).add("Name", "WebServerASG")
        tags.of(asg).add("ResourceType", "AutoScalingGroup")
        tags.of(asg).add("DevOpsGuru", "enabled")

        # Create User Data script to install and start Nginx
        bastion_user_data = ec2.UserData.for_linux()
        bastion_user_data.add_commands("yum update -y", "yum install httpd-tools")

        # Create Bastion Host
        bastion_host = ec2.Instance(
            self,
            "BastionHost",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.C5, ec2.InstanceSize.XLARGE
            ),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
            ),
            security_group=bastion_security_group,
            user_data=bastion_user_data,
            # key_name="your-key-pair-name"  # Replace with your EC2 key pair name
        )

        # Add tags to bastion host
        tags.of(bastion_host).add("Name", "BastionHost")
        tags.of(bastion_host).add("ResourceType", "EC2")

        # Output the VPC ID
        CfnOutput(self, "VPCId", value=vpc.vpc_id, description="VPC ID")

        CfnOutput(
            self,
            "BastionID",
            value=bastion_host.instance_id,
            description="Bastion Host ID",
        )
