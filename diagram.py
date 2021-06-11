from diagrams import Cluster, Diagram, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.integration import SNS
from diagrams.aws.storage import S3
from diagrams.aws.network import CloudFront
from diagrams.aws.management import CloudwatchEventTimeBased
from diagrams.generic.device import Mobile, Tablet


with Diagram("AWS managed versions", show=False):
    cron = CloudwatchEventTimeBased("CloudWatch Event rule")
    lambda_func = Lambda("Lambda Function")
    cloudfront = CloudFront("https://aws-versions.iroqwa.org/")
    s3 = S3("S3")
    sns = SNS("SNS")
    email = Mobile("Email")
    user = Tablet("User")

    user >> Edge(label="4 - query") >> cloudfront >>  Edge(label="3 - get") >> s3 << Edge(label="2 - generate & store index") << lambda_func << Edge(label="1 - daily schedule") << cron
    lambda_func >> Edge(label="dead letter events", style="dotted") >> sns >> Edge(label="notify") >> email
