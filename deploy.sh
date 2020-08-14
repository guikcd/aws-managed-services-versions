echo "[+] Build datas & index.html"
./fetch_data.py
./generate.py
echo "[+] Publish index.html to S3"
AWS_PROFILE=aws-managed-services-versions aws --region eu-west-3 s3 cp index.html s3://aws-managed-services-versions/
echo "[+] CloudFront cache purge"
sed "s/<id>/$(date +%s)/" invalidation-batch_template.json > invalidation-batch.json
aws cloudfront create-invalidation --distribution-id E3AS59ZAE6FV3Z --invalidation-batch file://invalidation-batch.json
