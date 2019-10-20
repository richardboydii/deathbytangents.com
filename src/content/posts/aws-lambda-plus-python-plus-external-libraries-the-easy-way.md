+++
title = "AWS Lambda + Python + External Libraries the Easy Way"
description = "A quick tutorial on conducting Lambda development locally with external Python packages then deploying them to AWS."
date = 2018-02-18T10:01:11-06:00
draft = false
toc = true
categories = ["development"]
tags = ["python", "aws", "lambda", "docker"]
+++
As a ~~systems administrator~~ ~~systems engineeer~~ ~~devops engineer~~ SRE? 
I've come to love AWS Lambda. Even though there are limitations (duration and 
resource caps) most of the server-side daemon code you end up developing can be 
ported over without too much hassle. There is one hitch that can make your 
serverless life painful: external libraries.

# Why External Libraries
The Python standard library has just about everything you need to write 
elegant software that can do just about everything. But sometimes you just want
to do things the simple way and incorporate the work some genius engineer has 
done so that getting the job done takes less code and less time. 

This is where most people (including me) hit a wall with AWS Lambda. If you 
take a look at [the documentation on the AWS Lambda execution environment](https://docs.aws.amazon.com/lambda/latest/dg/current-supported-versions.html) 
you'll see that you have very few tools to play with. For Python developers 
this means you have Python 2.7 or 3.6 and [Boto3](https://boto3.readthedocs.io/en/latest/) 
(the AWS SDK for Python) library and that's about it. If you need to take 
advantage of other libraries, Lambda can be unforgiving. 

# How External Libraries are Used
When you want to integrate an external library with your Lambda code, you'll 
need to build a virtual environment, install your libraries, then package them 
together with your Python code. Unfortunately there are a few gotchas that you 
need to look out for when you're doing this.

* **lib and lib64:** In your virtual environment, you'll often have two 
different library paths, lib and lib64. As a good rule of thumb, you need to 
grab *site-packages* out of both library paths.
* **compiled code:** If external libraries require native compilation (the 
[pymssql libary](http://www.pymssql.org/en/stable/) is a godo example) you have 
to install the libary on an OS that is compatible with Amazon Linux.

# The Workaround: Docker
[LambCI](https://github.com/lambci/lambci) is a Continuous Integration service 
built on top of AWS Lambda. While the project is pretty neat, waht they've done 
one the Docker side of the house is of direct benefit to those of us that are 
in the position of needed to use (and compile) external libraries. Take a look 
at the [LambCI Docker Hub registry](https://github.com/lambci/docker-lambda). 
They've created several containers that mimic the runtime environment of AWS 
Lambda. Using these containers, you can easily install and package your 
external libraries knowing that they'll be 100% compatible when uploaded to AWS
Lambda.

## A Quick Example
I recently had to create a Lambda to generate Confluence pages based on a 
CloudWatch event. In order to make life easier I decided to use the 
[Requests library](http://docs.python-requests.org/en/master/) (which is 
fantastic if you're doing anything with HTTP in Python). Unfortunately this 
meant that I had to go through the process of adding external libraries to my 
code.

1. To start off, create a `requiremnts.txt` file in the root of your project. 
List any external libraries you'll need (this is also good practice no matter 
what you're doing with Python). In addition to any external libraries, it's 
reccomended that you update boto3 by adding it into your package list.

    Example `requirements.txt`:

    {{< highlight go "linenos=table,linenostart=1" >}}
boto3
requests {{< / highlight >}}

2. We need to get an image from LambCI that matches our execution environment. 
For my example I'm using Python 3.6 so the image I want to get is the 
`build-python3.6` image. 
    
    ```
    docker pull lambci/lambda:build-python3.6
    ```

3. Once I have the image locally we need to `cd` to the root of our project and 
run the container in interactive mode. In this example I'm going to fire up 
the container and drop into a BASH shell.
   
    ```
    docker run -v "$PWD":/var/task -it lambci/lambda:build-python3.6 bash
    ```

    * `-v "$PWD":/var/task`: We're creating a mount from the current directory 
    to the `/var/task` directory on the container. This mirrors the location 
    where your code will run in an AWS Lambda ~~container~~ execution 
    environment
    * `-it`: This combination of flags starts the container in interactive mode 
    with a pseudo-TTY. 
    * `lambci/lambda:build-python3.6 bash`: The first part of this just tells 
    Docker which image we want to run. The `bash` at the end starts a shell 
    session. Paired with the `it` flag we're dropped into a shell on the 
    running container.

4. Start up a virtual environment **inside your container**. If there is a 
pre-existing virtual environment in your project root, create a new one. As a 
general rule, I name them `venv` (when doing local development) and `aws` if 
using Docker. Create the virtual environment, activate it, and install your 
external libraries.

    ```
    virtualenv aws
    . ./aws/bin/activate
    pip install -r requirements.txt
    ```

5. At this point you can start working on your Lambda code inside the 
container. Since we've mounted our project directory to the container, we can 
use our favorite editor to write with while executing inside the container to 
make sure everything works. 

6. When your code is doing all the neat things you want it to do, we need to 
zip up all the external libraries (and thier dependencies) and package it 
together with our existing code. One thing that will get you is that some 
libraries may be 32-bit or 64-bit only. The libraries for a virtual environment 
are located in the `venv/lib/python3.6/site-packages` and 
`venv/lib/python3.6/site-packages` folders. In order to make sure you have all 
of the code you'll need, make sure to get `site-packages` from both the **lib** 
and **lib64** directories then exit your conatiner.

    ```
    cd venv/lib/python3.6/site-packages
    zip -r ../../../../name_of_project.zip *
    cd ../../../lib64/python3.6/site-packages
    zip -r ../../../../name_of_project.zip *
    exit
    ```

7. Add your lambda code to the zip file then upload it to AWS Lambda via the 
console or the `aws cli` command. The only downside is that you will no longer 
be able to edit your code inline in the console.

    ```
    zip name_of_project.zip name_of_project.py
    ```

# Closing
I hope this blog post helps others who find themselves in the same situation. 
AWS Lambda can be fun to work with but making complex code with external 
libraries can cause a few headaches. After reading this article you should be 
able to avoid the learning curve that I had in figuring this out.