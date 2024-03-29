aws-managed-services-versions
=============================

[![Actions Status](https://github.com/guikcd/aws-managed-services-versions/workflows/Deploy%20to%20live/badge.svg)](https://github.com/guikcd/aws-managed-services-versions/actions)

Spec
----

* fetch datas from managed services:
  * Amazon OpenSearch Service
  * Amazon RDS
  * Amazon DocumentDB (MongoDB)
  * Amazon ElastiCache (Redis & Memcached)
  * AWS Elastic Beanstalk
  * Amazon Elastic Kubernetes Service (EKS)
  * AWS Lambda
  * Amazon MQ (ActiveMQ & RabbitMQ)
  * Amazon Managed Streaming for Apache Kafka (MSK)
  * Amazon Lightsail
  * Amazon Keyspaces (for Apache Cassandra)
* Generate a single `index.html` page (use bootstrap); you can search all fields, thanks to jQuery

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
