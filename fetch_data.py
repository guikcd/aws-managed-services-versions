#!/usr/bin/env python3
"""
Fetch versions data from AWS managed services
"""
import json
import boto3

def write_json(data, output_file):
    """ Write json file """
    print("Writting {}...".format(output_file))
    with open(output_file, 'w') as written_file:
        json.dump(data, written_file)

elasticsearch = boto3.client('es')
write_json(elasticsearch.list_elasticsearch_versions(), "elasticsearch.json")

rds = boto3.client('rds')
write_json(rds.describe_db_engine_versions(), "rds.json")

elasticache = boto3.client('elasticache')
write_json(elasticache.describe_cache_engine_versions(), "elasticache.json")

elasticbeanstalk = boto3.client('elasticbeanstalk')
write_json(elasticbeanstalk.list_available_solution_stacks(), "elasticbeanstalk.json")

mq = boto3.client('mq')
write_json(mq.describe_broker_engine_types(), "mq.json")
