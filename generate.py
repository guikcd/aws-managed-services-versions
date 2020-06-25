#!/usr/bin/env python3
import json
import re
import datetime
from jinja2 import Template
import requests
from bs4 import BeautifulSoup

GENERATION_DATE = datetime.datetime.now()
VERSION = '0.1'

ELASTICACHE_ENGINES = ['memcached', 'redis']

VERSION_URL_DETAIL = {
    'elasticsearch': 'https://docs.aws.amazon.com/elasticsearch-service/latest/developerguide/what-is-amazon-elasticsearch-service.html#aes-choosing-version',
    'redis': 'https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/supported-engine-versions.html',
    'memcached': 'https://docs.aws.amazon.com/AmazonElastiCache/latest/mem-ug/supported-engine-versions.html',
    'kafka': 'https://docs.aws.amazon.com/msk/latest/developerguide/what-is-msk.html',
    'kubernetes': 'https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html',
    'lambda': 'https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html',
    'postgresql': 'https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html',
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
    'mq': 'https://aws.amazon.com/amazon-mq/faqs/',
}

def rds_engines():
    all_engines = []
    with open('rds.json') as rds_engines:
        engines_json = json.loads(rds_engines.read())
        # print(engines_json['DBEngineVersions'])
        for engine in engines_json['DBEngineVersions']:
            all_engines.append(engine['Engine'])

    return(list(set(all_engines)))

def elasticsearch_versions():
    with open("elasticsearch.json") as json_file:
        data = json.load(json_file)
        return test_versions(data['ElasticsearchVersions'])

def mq_versions(engine=None):
    with open("mq.json") as json_file:
        data = json.load(json_file)
        versions = []
        for supported_engine in data['BrokerEngineTypes']:
           if supported_engine['EngineType'] == engine:
               for version in supported_engine['EngineVersions']:
                   versions.append(version['Name'])
        return test_versions(versions)

def engines_versions(engine=None):
    if engine in rds_engines():
        data_file = 'rds.json'
        first_key = 'DBEngineVersions'
    if engine in ELASTICACHE_ENGINES:
        data_file = 'elasticache.json'
        first_key = 'CacheEngineVersions'
    with open(data_file) as json_file:
        data = json.load(json_file)
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

def elasticbeanstalk_versions(platform=None):
    with open("elasticbeanstalk.json") as json_file:
        data = json.load(json_file)
        versions = []
        for solution in data['SolutionStacks']:
           if platform in solution:
              beanstalk_version = re.compile('running {}(.+)'.format(platform))
              versions.append(beanstalk_version.search(solution).group(1))
        return test_versions(list(set(versions)))

def version_table_row(service, version, engine=None):
    url = '#'
    if engine is not None:
           if engine in VERSION_URL_DETAIL:
              url = VERSION_URL_DETAIL[engine]
    return "<tr>\n<td>{}</td>\n<td><a href='{}'>{}</a></td>\n</tr>\n".format(service, url, version)

def msk_versions():
    # root url: https://docs.aws.amazon.com/msk/latest/developerguide/what-is-msk.html
    req = requests.get(VERSION_URL_DETAIL["kafka"])
    # Apache Kafka version 1.1.1, 2.2.1, and 2.3.1.
    version_text = re.findall("Apache Kafka version (.*)", req.text)
    versions = []
    for msk_version in version_text[0].split(', '):
        versions.append(msk_version.replace("or ", ""))
    return test_versions(versions)

def eks_versions():
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

def lambda_versions(runtime=None):
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

def test_versions(versions):
    # verify that list is not empty
    if len(versions) == 0:
        raise ValueError('versions list empty!')
    return versions

versions = ""

for version in mq_versions(engine="ACTIVEMQ"):
    versions += version_table_row("Amazon MQ for Apache ActiveMQ", version, "mq")

for version in elasticsearch_versions():
    versions += version_table_row("Amazon ElasticSearch Service", version, "elasticsearch")

for rds in rds_engines():
     for version in engines_versions(engine=rds):
        versions += version_table_row("Amazon Relational Database Service (RDS) " + rds, version, rds)
for version in engines_versions(engine='memcached'):
    versions += version_table_row("Amazon ElastiCache memcached", version, "memcached")
for version in engines_versions(engine='redis'):
    versions += version_table_row("Amazon ElastiCache redis", version, "redis")
for beanstalk in ['PHP ', 'Tomcat ', 'Multi-container Docker ', 'Ruby ', 'Python ', 'IIS ', 'Go ']:
    for version in elasticbeanstalk_versions(platform=beanstalk):
        versions += "<tr><td>AWS Elastic Beanstalk " + beanstalk + "</td><td><a href='https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/platforms-support-policy.html'>" + version + "</a></td></tr>"


for version in msk_versions():
    versions += version_table_row("Amazon Managed Streaming for Apache Kafka (MSK)", version, 'kafka')

for version in eks_versions():
    versions += version_table_row("Amazon Elastic Kubernetes Service (Amazon EKS)", version, "kubernetes")
for version in lambda_versions():
    versions += version_table_row("AWS Lambda Runtimes", version, "lambda")

with open('index.template.html') as html:
    tm = Template(html.read())
output = tm.render(my_cels=versions, date=GENERATION_DATE, version=VERSION)

with open("index.html", 'w') as html:
    html.write(output)
