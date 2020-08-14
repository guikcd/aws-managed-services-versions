#!/bin/bash
set -e
rm -rf lambda lambda.zip && mkdir lambda
cp generate.py index.template.html __init__.py lambda
pip install --target ./lambda -r requirements.txt
cd lambda
zip -r ../lambda.zip .
cd ..
aws s3 cp lambda.zip s3://aws-managed-services-versions/
aws lambda update-function-code --function-name aws-managed-services-versions-fetch --s3-bucket aws-managed-services-versions --s3-key lambda.zip
