import aws_cdk as core
import aws_cdk.assertions as assertions

from ec2_asg_load_test.ec2_asg_load_test_stack import Ec2AsgLoadTestStack

# example tests. To run these tests, uncomment this file along with the example
# resource in ec2_asg_load_test/ec2_asg_load_test_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Ec2AsgLoadTestStack(app, "ec2-asg-load-test")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
