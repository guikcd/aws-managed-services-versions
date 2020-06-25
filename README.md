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
* Generate a single index.html page (use bootstrap); you can search all fields, thaks to jQuery

How to launch
-------------

* Authenticate on an AWS account (only describe/list actions, AWS managed policy `ReadOnlyAccess` is OK)
* Populate somes metadata from AWS managed services:

```
$ ./fetch_data.py
```

* Install dependencies (virtualenv + requirements.txt)
* Generate the html page:

```
python ./generate.py
```
* Point your brower to `index.html`
