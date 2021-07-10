Spec
----

* fetch datas from managed services:
  * Amazon Elasticsearch Service
  * Amazon RDS
  * Amazon DocumentDB (MongoDB)
  * Amazon Elasticache
  * AWS Elastic Beanstalk
  * Amazon EKS
  * AWS Lambda
  * Amazon MQ (ActiveMQ)
  * Amazon MSK (Kafka)
  * AWS OpsWorks (Puppet & Chef)
* Generate a single index.html page (use bootstrap); you can search all fields, thanks to jQuery

Visualize on-line
-----------------

Live on: https://aws-versions.iroqwa.org/

How to launch manually
----------------------

* Authenticate on an AWS account (only describe/list actions, AWS managed policy `ReadOnlyAccess` is OK)
* Install dependencies (virtualenv + requirements.txt)
* Generate the html page:

```
$ bash ./test_lambda.sh
```
* Point your browser to `index2.html`
