#!/usr/bin/env python3
# pylint: disable=line-too-long
"""
Fetch AWS managed services versions and generate a full html page
"""
import datetime
import logging
import os
import re

import boto3
import requests
from bs4 import BeautifulSoup
from jinja2 import Template

GENERATION_DATE = datetime.datetime.now()
VERSION = "0.7.2"

ELASTICACHE_ENGINES = ["memcached", "redis"]

VERSION_URL_DETAIL = {
    "opensearch": "https://docs.aws.amazon.com/opensearch-service/latest/developerguide/what-is.html#aes-choosing-version",
    "redis": "https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/supported-engine-versions.html",
    "memcached": "https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/supported-engine-versions-mc.html",
    "kafka": "https://docs.aws.amazon.com/msk/latest/developerguide/kafka-versions.html",
    "kubernetes": "https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html",
    "lambda": "https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html",
    "postgres": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html",
    "aurora-postgresql": "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Updates.20180305.html",
    "aurora": "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Updates.html",
    "aurora-mysql": "https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Updates.html",
    "neptune": "https://docs.aws.amazon.com/neptune/latest/userguide/engine-releases.html",
    "docdb": "https://aws.amazon.com/documentdb/faqs/",
    "mariadb": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_MariaDB.html",
    "mysql": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_MySQL.html",
    "oracle-ee": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Oracle.html",
    "oracle-se": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Oracle.html",
    "oracle-se1": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Oracle.html",
    "oracle-se2": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Oracle.html",
    "sqlserver-ee": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_SQLServer.html",
    "sqlserver-ex": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_SQLServer.html",
    "sqlserver-se": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_SQLServer.html",
    "sqlserver-web": "https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_SQLServer.html",
    "activemq": "https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/activemq-version-management.html",
    "rabbitmq": "https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/rabbitmq-version-management.html",
    "cassandra": "https://docs.aws.amazon.com/keyspaces/latest/devguide/keyspaces-vs-cassandra.html",
    "lightsail_app": "https://lightsail.aws.amazon.com/ls/docs/en_us/articles/compare-options-choose-lightsail-instance-image",
    "lightsail_database": "https://lightsail.aws.amazon.com/ls/docs/en_us/articles/amazon-lightsail-choosing-a-database",
}

OUTPUT_BUCKET = os.getenv("OUTPUT_BUCKET")
LOCAL_DEBUG = os.getenv("LOCAL_DEBUG")

# distribution to invalidate for frontend
CLOUDFRONT_TAGS = {"Key": "project", "Value": "aws-managed-services-versions"}

logger = logging.getLogger()
logger.setLevel(logging.INFO)

logging.info("Fetching ElasticBeanstalk solutions stacks")
elasticbeanstalk = boto3.client("elasticbeanstalk")
EBS_SOLUTIONS_STACKS = elasticbeanstalk.list_available_solution_stacks()[
    "SolutionStacks"
]

logging.info("Fetching MQ engine types")
amazon_mq = boto3.client("mq")
MQ_ENGINE_TYPES = amazon_mq.describe_broker_engine_types()["BrokerEngineTypes"]

logging.info("Fetching ElastiCache engine versions")
elasticache = boto3.client("elasticache")
ELASTICACHE_ENGINE_VERSIONS = elasticache.describe_cache_engine_versions()

logging.info("Fetching RDS engine versions")
rds = boto3.client("rds")
paginator = rds.get_paginator("describe_db_engine_versions")
engines = []
ALL_ENGINES = {}
for page in paginator.paginate():
    for rds_engine_version in page["DBEngineVersions"]:
        engines.append(rds_engine_version)
ALL_ENGINES["DBEngineVersions"] = engines


def check_urls():
    """
    test that versions urls to service documentation has not changed
    """
    # want to get the service
    for service, url in VERSION_URL_DETAIL.items():
        response = requests.get(url, allow_redirects=False)
        if response.status_code != 200:
            logging.warning(
                "Service %s URL return %s instead of 200 (%s)",
                service,
                response.status_code,
                url,
            )


def rds_engines(data=None):
    """
    RDS
    """
    all_engines = []
    if "DBEngineVersions" in data:
        for engine in data["DBEngineVersions"]:
            all_engines.append(engine["Engine"])

    return list(set(all_engines))


def opensearch_versions():
    """
    ES
    """
    logging.info("Fetching OpenSearch")
    opensearch = boto3.client("opensearch")
    return test_versions(opensearch.list_versions()["Versions"])


def mq_versions(engine=None):
    """
    MQ
    """
    logging.info("Fetching MQ %s", engine)

    versions = []
    for supported_engine in MQ_ENGINE_TYPES:
        if supported_engine["EngineType"] == engine:
            for mq_version in supported_engine["EngineVersions"]:
                versions.append(mq_version["Name"])
    return test_versions(versions)


def engines_versions(engine=None, data=None):
    """
    RDS/Elasticache engines
    """
    logging.info("Fetching RDS/Elasticache '%s'", engine)
    if engine in rds_engines(data=data):
        first_key = "DBEngineVersions"
    if engine in ELASTICACHE_ENGINES:
        first_key = "CacheEngineVersions"

    versions = []
    for version in data[first_key]:
        if version["Engine"] == engine:
            versions.append(version["EngineVersion"])
    # thx https://stackoverflow.com/a/2574090
    # but version may contain letter :(
    # versions.sort(key=lambda s: list(map(int, s.split('.'))))
    versions.sort()
    versions.reverse()
    return test_versions(versions)


def elasticbeanstalk_versions(platform=None):
    """
    ElasticBeanstalk
    """
    logging.info("Fetching ElasticBeanstalk '%s'", platform)
    versions = []
    # for solution in elasticbeanstalk_list_available_solutions_stacks():
    for solution in EBS_SOLUTIONS_STACKS:
        if platform in solution:
            beanstalk_version = re.compile("running {}(.+)".format(platform))
            versions.append(beanstalk_version.search(solution).group(1))
    return test_versions(list(set(versions)))


def version_table_row(service, version, engine=None):
    """
    generate a row for a table
    """
    url = "#"
    if engine is not None:
        if VERSION_URL_DETAIL.get(engine) is not None:
            url = VERSION_URL_DETAIL[engine]
    return "<tr>\n<td>{}</td>\n<td><a href='{}'>{}</a></td>\n</tr>\n".format(
        service, url, version
    )


def msk_versions():
    """
    MSK
    """
    logging.info("Fetching MSK")
    msk = boto3.client("kafka")
    active_versions = []
    for version in msk.list_kafka_versions()["KafkaVersions"]:
        if version["Status"] == "ACTIVE":
            active_versions.append(version["Version"])
    active_versions.sort()
    active_versions.reverse()
    return test_versions(active_versions)


def eks_versions():
    """
    EKS
    """
    logging.info("Fetching EKS")
    req = requests.get(VERSION_URL_DETAIL["kubernetes"])
    soup = BeautifulSoup(req.text, "html.parser")
    # <div class="itemizedlist">
    # <ul class="itemizedlist" type="disc">
    # <li class="listitem">
    # <p><code class="code">1.14.6</code></p>
    # </li>
    html_versions = (
        soup.find("div", attrs={"class": "itemizedlist"})
        .find("ul", attrs={"class": "itemizedlist"})
        .find_all("li", attrs={"class": "listitem"})
    )
    versions = []
    for eks_version in html_versions:
        versions.append(eks_version.contents[1].contents[0].get_text())
    return test_versions(versions)


def lambda_versions():
    """
    Lambda
    """
    logging.info("Fetching Lambda")
    req = requests.get(VERSION_URL_DETAIL["lambda"])
    soup = BeautifulSoup(req.text, "html.parser")
    # <div class="itemizedlist">
    runtimes = soup.find_all("div", attrs={"class": "awsui-util-container"})

    output_rows = []
    for runtime in runtimes:
        for table_row in runtime.findAll("tr"):
            columns = table_row.findAll("td")
            output_row = []
            for column in columns:
                output_row.append(column.text)
            output_rows.append(output_row)

    versions = []
    for element in output_rows:
        if len(element) > 1:
            versions.append(element[0].replace("\n", ""))

    return test_versions(versions)


def cassandra_versions():
    """
    Cassandra
    """
    req = requests.get(VERSION_URL_DETAIL["cassandra"])
    soup = BeautifulSoup(req.text, "html.parser")
    html_versions = soup.find("div", attrs={"id": "main-col-body"}).find("p")
    versions = []
    versions.append(
        re.findall(
            r"clients that are compatible with Apache Cassandra ([\d.]+).  Amazon Keyspaces supports",
            html_versions.text,
        )[0]
    )
    return test_versions(versions)


def lightsail_versions(blueprint_type=None):
    """
    Lightsail
    """

    versions = []
    logging.info("Fetching Lightsail")
    lightsail = boto3.client("lightsail")

    if blueprint_type == "app":
        blueprints = lightsail.get_blueprints()["blueprints"]
        for blueprint in blueprints:
            if blueprint["type"] == blueprint_type:
                versions.append(blueprint["name"] + " " + blueprint["version"])

    if blueprint_type == "database":
        databases = lightsail.get_relational_database_blueprints()["blueprints"]
        for database in databases:
            versions.append(database["engineVersionDescription"])

    return test_versions(versions)


def test_versions(versions):
    """
    test versions veracity
    """
    # verify that list is not empty
    if len(versions) == 0:
        raise ValueError("versions list empty!")
    return versions


def cloudfront_invalidation(item=None):
    """
    Invalidate CloudFront item
    """
    cloudfront = boto3.client("cloudfront")
    cloudfront_distributions = cloudfront.list_distributions()
    distribution_invalidation_id = ""
    # if many distributions returned, use a paginator
    for distribution in cloudfront_distributions["DistributionList"]["Items"]:
        tags = cloudfront.list_tags_for_resource(Resource=distribution["ARN"])
        for tag in tags["Tags"]["Items"]:
            if (
                CLOUDFRONT_TAGS["Key"] == tag["Key"]
                and CLOUDFRONT_TAGS["Value"] == tag["Value"]
            ):
                distribution_invalidation_id = distribution["Id"]
    cloudfront.create_invalidation(
        DistributionId=distribution_invalidation_id,
        InvalidationBatch={
            "Paths": {"Quantity": 1, "Items": ["/{}".format(item)]},
            "CallerReference": "aws-managed-services-versions-invalidation-{}".format(
                datetime.datetime.now().timestamp()
            ),
        },
    )
    logging.info("CloudFront invalidation successfull")


def lambda_handler(
    event, context
):  # pylint: disable=too-many-locals,unused-argument,too-many-branches
    """
    Lambda entry point
    """

    output_file = os.getenv("OUTPUT_FILE")
    if "output_file" in event:
        logging.info(
            "Overriding OUTPUT_FILE env variable with '%s' value", event["output_file"]
        )
        output_file = event["output_file"]

    versions = ""

    for version in lightsail_versions(blueprint_type="app"):
        versions += version_table_row(
            "Amazon Lightsail blueprints", version, "lightsail_app"
        )

    for version in lightsail_versions(blueprint_type="database"):
        versions += version_table_row(
            "Amazon Lightsail databases", version, "lightsail_database"
        )

    for version in mq_versions(engine="ACTIVEMQ"):
        versions += version_table_row(
            "Amazon MQ for Apache ActiveMQ", version, "activemq"
        )
    for version in mq_versions(engine="RABBITMQ"):
        versions += version_table_row("Amazon MQ for RabbitMQ", version, "rabbitmq")

    for version in opensearch_versions():
        versions += version_table_row(
            "Amazon OpenSearch Service", version, "opensearch"
        )

    for rds_version in rds_engines(data=ALL_ENGINES):
        for version in engines_versions(engine=rds_version, data=ALL_ENGINES):
            versions += version_table_row(
                "Amazon Relational Database Service (RDS) " + rds_version,
                version,
                rds_version,
            )

    for version in cassandra_versions():
        versions += version_table_row(
            "Amazon Keyspaces (for Apache Cassandra)", version, "cassandra"
        )

    for version in engines_versions(
        engine="memcached", data=ELASTICACHE_ENGINE_VERSIONS
    ):
        versions += version_table_row(
            "Amazon ElastiCache memcached", version, "memcached"
        )
    for version in engines_versions(engine="redis", data=ELASTICACHE_ENGINE_VERSIONS):
        versions += version_table_row("Amazon ElastiCache redis", version, "redis")
    for beanstalk in [
        "PHP ",
        "Tomcat ",
        "Ruby ",
        "Python ",
        "IIS ",
        "Go ",
        "Node.js ",
    ]:
        for version in elasticbeanstalk_versions(platform=beanstalk):
            versions += (
                "<tr><td>AWS Elastic Beanstalk "
                + beanstalk
                + "</td><td><a href='https://docs.aws.amazon.com/elasticbeanstalk/latest/platforms/platforms-supported.html'>"
                + version
                + "</a></td></tr>"
            )

    for version in msk_versions():
        versions += version_table_row(
            "Amazon Managed Streaming for Apache Kafka (MSK)", version, "kafka"
        )

    for version in eks_versions():
        versions += version_table_row(
            "Amazon Elastic Kubernetes Service (Amazon EKS)", version, "kubernetes"
        )
    for version in lambda_versions():
        versions += version_table_row("AWS Lambda Runtimes", version, "lambda")

    with open("index.template.html") as html:
        template = Template(html.read())
    output = template.render(my_cels=versions, date=GENERATION_DATE, version=VERSION)

    if LOCAL_DEBUG == "true":
        with open(output_file, "w") as html_output:
            html_output.write(output)

    s3client = boto3.client("s3")
    s3client.put_object(
        Body=output,
        Bucket=OUTPUT_BUCKET,
        Key=output_file,
        ContentType="text/html",
        StorageClass="STANDARD_IA",
    )
    logging.info("Successfully pushed to s3://%s/%s", OUTPUT_BUCKET, output_file)
    cloudfront_invalidation(item=output_file)


if __name__ == "__main__":
    check_urls()
    lambda_handler({"event": 1}, "")
