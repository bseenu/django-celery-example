# Django Celery Example on Kubernetes

Example used in the blog post [How to Use Celery and RabbitMQ with Django](https://simpleisbetterthancomplex.com/tutorial/2017/08/20/how-to-use-celery-with-django.html?utm_source=github&utm_medium=repository)

### Build and publish the docker images needed [ django & celery ]
```https://hub.docker.com/u/bseenu/```

### Ensure to create the secrets in EC2 parameter store and give the kubernetes node role
read access to the secrets

### Create the kubernetes cluster using kops
#### Install kops, my environment is mac
```bash 
brew install kops
```
#### Create the S3 bucket to store the kops state
```bash
aws s3 mb <<bucketname>>
```
```bash
export KOPS_STATE_STORE=s3://<<bucketname>>
```
```bash
kops create -f k8s-templates/cluster.yaml
kops create secret --name srini.cluster.k8s.local sshpublickey admin -i ~/.ssh/id_rsa.pub
kops update cluster srini.cluster.k8s.local --yes
```
The above command will create kubernetes cluster with one master and two nodes [ Master: t2.medium, Nodes: t2.micro ]
and will generally take around 7-8 mins

#### Create an EFS Fileshare to be used as data volume
```bash
aws efs create-file-system --creation-token <<clusterfs-name>>
```
Make sure the efs is in the same vpc as the kubernetes cluster and whitelist the node security groups so that they 
can mount the efs file system

### Kubernetes deployment
#### Set up the persistent volume claim
```bash
kubectl create -f k8s-templates/sqlite-configmap.yaml
kubectl create -f k8s-templates/sqlite-storage.yaml
kubectl create -f k8s-templates/sqlite-pv.yaml
kubectl create -f k8s-templates/sqlite-pvc.yaml
```
The above sets up the EFS filesystem as persistent volume which can be mounted by containers

#### Django deployment
```bash
kubectl create -f k8s-templates/django-deployment.yaml 
```
The above sets up the django containers, you can verify by checking the command `kubectl get pods` you should be seeing them
in the running state
```bash
kubectl create -f k8s-templates/django-service.yaml
```
The above exposes the django deployment via ingress load balancer, you can get the ingress load balancer name by running 
the command `kubectl describe svc/django-service`, you should be able to point to the name on port 8000 and see the django
page

#### Celery deployment
```bash
kubectl create -f k8s-templates/celery-deployment.yaml
```
The above sets up celery workers which refers to the same broker url as django and also uses the same data volume for writing
to sqlite3 as django app reads from

#### Doing an upgrade
```bash
kubectl set image deployments/django-deployment django-web=<<docker-image>>
```
The above will bring up the new containers with the new images and terminates the old ones, and the rollout will be done in 
a controlled way ensuring your app is not down, In this example lets say if you have 4 containers it will do 2 at a time

#### Rollback an upgrade
```bash
kubectl rollout undo deployments/django-deployment
```
The above will rollback the recent django deployment, if you want to rollback to a specific revision you need to use the 
revision at the end of the command, you can use the kubectl rollout history deployments/django-deployment to see the
revisions, Please not you need to use --record in your deployments for this

#### Deleting the cluster
```bash
kops delete cluster <<cluster-name>> --yes
