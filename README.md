aws-managed-services-versions
=============================

[![Actions Status](https://github.com/guikcd/aws-managed-services-versions/workflows/Deploy%20to%20live/badge.svg)](https://github.com/guikcd/aws-managed-services-versions/actions)

Spec
----

* fetch datas from managed services:
  * Amazon Elasticsearch Service
  * Amazon RDS
  * Amazon DocumentDB (MongoDB)
  * Amazon ElastiCache
  * AWS Elastic Beanstalk
  * Amazon EKS
  * AWS Lambda
  * Amazon MQ (ActiveMQ)
  * Amazon MSK (Kafka)
  * Amazon LightSail
  * Amazon Keyspaces (pour Apache Cassandra)
* Generate a single index.html page (use bootstrap); you can search all fields, thanks to jQuery

Visualize on-line
-----------------

Live on: <https://aws-versions.iroqwa.org/>

How to launch manually
----------------------

* Authenticate on an AWS account (only describe/list actions, AWS managed policy `ReadOnlyAccess` is OK)
* Install dependencies (virtualenv + requirements.txt)
* Generate the HTML page:

```bash
$ bash ./test_lambda.sh
...
```
* Point your browser to `index2.html`
