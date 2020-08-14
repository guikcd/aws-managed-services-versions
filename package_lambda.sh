#!/bin/bash
set -e
rm -rf lambda.dist lambda.zip
cp -a lambda lambda.dist
pip install --target ./lambda.dist -r lambda.dist/requirements.txt
cd lambda.dist
zip -r ../lambda.zip .
cd ..
aws s3 cp lambda.zip s3://aws-managed-services-versions/
aws lambda update-function-code --function-name aws-managed-services-versions-generation --s3-bucket aws-managed-services-versions --s3-key lambda.zip
