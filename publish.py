#!/usr/bin/env python3

import os
from subprocess import call
import boto3
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool


OUTPUTDIR = "src/build"
BUCKET = "deathbytangents.com"
S3 = boto3.resource("s3")

def upload_file(src_dest):
    """Use boto3 to upload a file to S3."""
    extension = src_dest[0].split(".")[-1]
    if extension.endswith(("htm", "html", "xml", "css")):
        c_type = "text/%s" % extension
    elif extension.endswith(("jpeg", "jpg", "jpe", "png", "gif")):
        c_type = "image/%s" % extension
    elif extension.endswith(("json", "js")):
        c_type = "application/%s" % extension
    else:
        c_type = "binary/octet"
    extra_args = {"ContentType": c_type}
    S3.meta.client.upload_file(src_dest[0], BUCKET, src_dest[1],
                               ExtraArgs=extra_args)

def publish():
    """Clear the S3 bucket, uploads files."""
    S3.Bucket(BUCKET).objects.delete()
    files = []
    for root, directories, filenames in os.walk(OUTPUTDIR):
        for filename in filenames:
            source = os.path.join(root, filename)
            dest = source.replace(OUTPUTDIR + "/", "")
            files.append([source, dest])
    pool = ThreadPool()
    results = pool.map(upload_file, files)
    pool.close()
    pool.join()

if __name__ == "__main__":
    publish()