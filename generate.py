#!/usr/bin/env python3
# pylint: disable=line-too-long
"""
Fetch AWS managed services versions and generate an html page
"""
import re
import os
import datetime
import logging
import boto3
from jinja2 import Template
import requests
from bs4 import BeautifulSoup

GENERATION_DATE = datetime.datetime.now()
VERSION = '0.3'

ELASTICACHE_ENGINES = ['memcached', 'redis']

VERSION_URL_DETAIL = {
    'elasticsearch': 'https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/what-is-amazon-elasticsearch-service.html#aes-choosing-version',
    'redis': 'https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/supported-engine-versions.html',
    'memcached': 'https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/supported-engine-versions.html',
    'kafka': 'https://docs.aws.amazon.com/msk/latest/developerguide/what-is-msk.html',
    'kubernetes': 'https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html',
    'lambda': 'https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html',
    'postgres': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html',
    'aurora-postgresql': 'https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraPostgreSQL.Updates.20180305.html',
    'aurora': 'https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Updates.html',
    'aurora-mysql': 'https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/AuroraMySQL.Updates.html',
    'neptune': 'https://docs.aws.amazon.com/neptune/latest/userguide/engine-releases.html',
    'docdb': 'https://aws.amazon.com/documentdb/faqs/',
    'mariadb' : 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_MariaDB.html',
    'mysql': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_MySQL.html',
    'oracle-ee': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Oracle.html',
    'oracle-se': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Oracle.html',
    'oracle-se1': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Oracle.html',
    'oracle-se2': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Oracle.html',
    'sqlserver-ee': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_SQLServer.html',
    'sqlserver-ex': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_SQLServer.html',
    'sqlserver-se': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_SQLServer.html',
    'sqlserver-web': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_SQLServer.html',
    'mq': 'https://docs.aws.amazon.com/amazon-mq/latest/developer-guide/supported-engine-versions.html',
    'cassandra': 'https://docs.aws.amazon.com/keyspaces/latest/devguide/keyspaces-vs-cassandra.html',
}

OUTPUT_BUCKET = os.getenv('OUTPUT_BUCKET')
OUTPUT_FILE = os.getenv('OUTPUT_FILE')
LOCAL_DEBUG = os.getenv('LOCAL_DEBUG')

# distribution to invalidate for frontend
CLOUDFRONT_TAGS = {'Key': 'project', 'Value': 'aws-managed-services-versions'}

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def rds_engines(data=None):
    """
    RDS
    """
    all_engines = []
    if 'DBEngineVersions' in data:
        for engine in data['DBEngineVersions']:
            all_engines.append(engine['Engine'])

    return list(set(all_engines))

def elasticsearch_versions(data=None):
    """
    ES
    """
    logging.info("Fetching ElasticSearch")
    return test_versions(data['ElasticsearchVersions'])

def mq_versions(engine=None, data=None):
    """
    MQ
    """
    logging.info("Fetching MQ")
    versions = []
    for supported_engine in data['BrokerEngineTypes']:
        if supported_engine['EngineType'] == engine:
            for version in supported_engine['EngineVersions']:
                versions.append(version['Name'])
    return test_versions(versions)

def engines_versions(engine=None, data=None):
    """
    RDS/Elasticache engines
    """
    logging.info("Fetching RDS/Elasticache '%s'", engine)
    if engine in rds_engines(data=data):
        first_key = 'DBEngineVersions'
    if engine in ELASTICACHE_ENGINES:
        first_key = 'CacheEngineVersions'

    versions = []
    for version in data[first_key]:
        if version['Engine'] == engine:
            versions.append(version['EngineVersion'])
    # thx https://stackoverflow.com/a/2574090
    # but version may contain letter :(
    #versions.sort(key=lambda s: list(map(int, s.split('.'))))
    versions.sort()
    versions.reverse()
    return test_versions(versions)

def elasticbeanstalk_versions(platform=None, data=None):
    """
    ElasticBeanstalk
    """
    logging.info("Fetching ElasticBeanstalk '%s'", platform)
    versions = []
    for solution in data['SolutionStacks']:
        if platform in solution:
            beanstalk_version = re.compile('running {}(.+)'.format(platform))
            versions.append(beanstalk_version.search(solution).group(1))
    return test_versions(list(set(versions)))

def version_table_row(service, version, engine=None):
    """
    generate a row for a table
    """
    url = '#'
    if engine is not None:
        if VERSION_URL_DETAIL.get(engine) is not None:
            url = VERSION_URL_DETAIL[engine]
    return "<tr>\n<td>{}</td>\n<td><a href='{}'>{}</a></td>\n</tr>\n".format(service, url, version)

def msk_versions():
    """
    MSK
    """
    logging.info("Fetching MSK")
    # root url: https://docs.aws.amazon.com/msk/latest/developerguide/what-is-msk.html
    req = requests.get(VERSION_URL_DETAIL["kafka"])
    # Apache Kafka version 1.1.1, 2.2.1, 2.3.1, or 2.4.1.
    version_text = re.findall("Apache Kafka version (.*)", req.text)
    versions = []
    for msk_version in version_text[0].split(', '):
        versions.append(msk_version.replace("or ", "").replace(". ", ""))
    return test_versions(versions)

def eks_versions():
    """
    EKS
    """
    logging.info("Fetching EKS")
    req = requests.get(VERSION_URL_DETAIL["kubernetes"])
    soup = BeautifulSoup(req.text, 'html.parser')
    # <div class="itemizedlist">
    # <ul class="itemizedlist" type="disc">
    # <li class="listitem">
    # <p>1.14.6</p>
    # </li>
    html_versions = soup.find("div", attrs={"class": "itemizedlist"}).find("ul", attrs={"class": "itemizedlist"}).find_all("li", attrs={"class": "listitem"})
    versions = []
    for eks_version in html_versions:
        versions.append(eks_version.contents[1].contents[0])
    return test_versions(versions)

def lambda_versions():
    """
    Lambda
    """
    logging.info("Fetching Lambda")
    req = requests.get(VERSION_URL_DETAIL["lambda"])
    soup = BeautifulSoup(req.text, 'html.parser')
    # <div class="itemizedlist">
    runtimes = soup.find_all("div", attrs={"class": "awsui-util-container"})

    output_rows = []
    for runtime in runtimes:
        for table_row in runtime.findAll('tr'):
            columns = table_row.findAll('td')
            output_row = []
            for column in columns:
                output_row.append(column.text)
            output_rows.append(output_row)

    versions = []
    for element in output_rows:
        if len(element) > 1:
            versions.append(element[0].replace('\n', ''))

    return test_versions(versions)

def cassandra_versions():
    """
    Cassandra
    """
    req = requests.get(VERSION_URL_DETAIL["cassandra"])
    soup = BeautifulSoup(req.text, 'html.parser')
    html_versions = soup.find("div", attrs={"id": "main-col-body"}).find("p")
    versions = []
    versions.append(re.findall(r"clients that are compatible with Apache Cassandra ([\d.]+).  Amazon Keyspaces supports", html_versions.text)[0])
    return test_versions(versions)

def test_versions(versions):
    """
    test versions veracity
    """
    # verify that list is not empty
    if len(versions) == 0:
        raise ValueError('versions list empty!')
    return versions

def cloudfront_invalidation():
    """
    Invalidate CloudFront OUTPUT_FILE
    """
    cloudfront = boto3.client('cloudfront')
    cloudfront_distributions = cloudfront.list_distributions()
    distribution_invalidation_id = ""
    # if many distributions returned, use a paginator
    for distribution in cloudfront_distributions['DistributionList']['Items']:
        tags = cloudfront.list_tags_for_resource(Resource=distribution['ARN'])
        for tag in tags['Tags']['Items']:
            if CLOUDFRONT_TAGS['Key'] == tag['Key'] and CLOUDFRONT_TAGS['Value'] == tag['Value']:
                distribution_invalidation_id = distribution['Id']
    cloudfront.create_invalidation(
        DistributionId=distribution_invalidation_id,
        InvalidationBatch={
            'Paths': {
                "Quantity": 1,
                'Items': ["/{}".format(OUTPUT_FILE)]
            },
            'CallerReference': 'aws-managed-services-versions-invalidation-{}'.format(datetime.datetime.now().timestamp())
        }
    )
    logging.info("CloudFront invalidation successfull")


def lambda_handler(event, context): # pylint: disable=too-many-locals,unused-argument,too-many-branches
    """
    Lambda entry point
    """
    elasticsearch = boto3.client('es')
    rds = boto3.client('rds')
    elasticache = boto3.client('elasticache')
    elasticbeanstalk = boto3.client('elasticbeanstalk')
    amazon_mq = boto3.client('mq')

    versions = ""

    for version in mq_versions(engine="ACTIVEMQ", data=amazon_mq.describe_broker_engine_types()):
        versions += version_table_row("Amazon MQ for Apache ActiveMQ", version, "mq")
    for version in mq_versions(engine="RABBITMQ", data=amazon_mq.describe_broker_engine_types()):
        versions += version_table_row("Amazon MQ for RabbitMQ", version, "mq")

    for version in elasticsearch_versions(data=elasticsearch.list_elasticsearch_versions()):
        versions += version_table_row("Amazon ElasticSearch Service", version, "elasticsearch")

    paginator = rds.get_paginator('describe_db_engine_versions')
    engines = []
    all_engines = {}
    for page in paginator.paginate():
        for version in page['DBEngineVersions']:
            engines.append(version)
    all_engines['DBEngineVersions'] = engines
    for rds_version in rds_engines(data=all_engines):
        for version in engines_versions(engine=rds_version, data=all_engines):
            versions += version_table_row("Amazon Relational Database Service (RDS) " + rds_version, version, rds_version)

    for version in cassandra_versions():
        versions += version_table_row("Amazon Keyspaces (for Apache Cassandra)", version, "cassandra")

    for version in engines_versions(engine='memcached', data=elasticache.describe_cache_engine_versions()):
        versions += version_table_row("Amazon ElastiCache memcached", version, "memcached")
    for version in engines_versions(engine='redis', data=elasticache.describe_cache_engine_versions()):
        versions += version_table_row("Amazon ElastiCache redis", version, "redis")
    for beanstalk in ['PHP ', 'Tomcat ', 'Multi-container Docker ', 'Ruby ', 'Python ', 'IIS ', 'Go ']:
        for version in elasticbeanstalk_versions(platform=beanstalk, data=elasticbeanstalk.list_available_solution_stacks()):
            versions += "<tr><td>AWS Elastic Beanstalk " + beanstalk + "</td><td><a href='https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/platforms-support-policy.html'>" + version + "</a></td></tr>"


    for version in msk_versions():
        versions += version_table_row("Amazon Managed Streaming for Apache Kafka (MSK)", version, 'kafka')

    for version in eks_versions():
        versions += version_table_row("Amazon Elastic Kubernetes Service (Amazon EKS)", version, "kubernetes")
    for version in lambda_versions():
        versions += version_table_row("AWS Lambda Runtimes", version, "lambda")

    with open('index.template.html') as html:
        template = Template(html.read())
    output = template.render(my_cels=versions, date=GENERATION_DATE, version=VERSION)

    if LOCAL_DEBUG == 'true':
        with open(OUTPUT_FILE, 'w') as html_output:
            write = html_output.write(output)

    s3client = boto3.client('s3')
    s3client.put_object(Body=output, Bucket=OUTPUT_BUCKET, Key=OUTPUT_FILE, ContentType='text/html')
    logging.info("Successfully pushed to s3://%s/%s", OUTPUT_BUCKET, OUTPUT_FILE)
    cloudfront_invalidation()

if __name__ == "__main__":
    lambda_handler({'event': 1}, '')
