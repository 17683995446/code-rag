"""云服务集成配置生成器

阶段 C: 云服务集成 AWS/GCP/Azure
12 个优化点:
1. AWS ECS/Fargate 配置生成
2. AWS EKS 集群配置
3. AWS Lambda 函数配置
4. GCP Cloud Run 服务配置
5. GCP GKE 集群配置
6. GCP Cloud Functions 配置
7. Azure Container Instances 配置
8. Azure AKS 集群配置
9. Azure Functions 配置
10. 多云统一抽象层
11. 云厂商特定最佳实践
12. 成本优化配置
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from abc import ABC, abstractmethod


class CloudProvider(Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"


class AwsRegion(Enum):
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"


class GcpRegion(Enum):
    US_CENTRAL1 = "us-central1"
    US_EAST1 = "us-east1"
    EUROPE_WEST1 = "europe-west1"
    ASIA_EAST1 = "asia-east1"


class AzureRegion(Enum):
    EAST_US = "eastus"
    WEST_US_2 = "westus2"
    WEST_EUROPE = "westeurope"
    SOUTHEAST_ASIA = "southeastasia"


@dataclass
class CloudConfig:
    app_name: str = "my-app"
    image: str = "my-app:v1"
    port: int = 8000
    cpu: str = "0.5"
    memory: str = "512Mi"
    min_instances: int = 1
    max_instances: int = 10
    desired_count: int = 2
    environment: Dict[str, str] = field(default_factory=dict)
    secrets: List[str] = field(default_factory=list)
    vpc_cidr: str = "10.0.0.0/16"
    enable_autoscaling: bool = True
    enable_monitoring: bool = True
    enable_logging: bool = True
    cost_optimized: bool = True


@dataclass
class AwsConfig(CloudConfig):
    region: AwsRegion = AwsRegion.US_EAST_1
    cluster_name: str = "my-cluster"
    task_family: str = "my-task"
    execution_role: str = "ecsTaskExecutionRole"
    enable_fargate: bool = True
    spot_instances: bool = False


@dataclass
class GcpConfig(CloudConfig):
    project_id: str = "my-project"
    region: GcpRegion = GcpRegion.US_CENTRAL1
    service_name: str = "my-service"
    allow_unauthenticated: bool = False
    min_instances: int = 0
    max_instances: int = 100


@dataclass
class AzureConfig(CloudConfig):
    subscription_id: str = "my-subscription"
    resource_group: str = "my-rg"
    location: AzureRegion = AzureRegion.EAST_US
    enable_acr: bool = True
    enable_managed_identity: bool = True


class AWSECSGenerator:
    """AWS ECS/Fargate 配置生成器（优化点 1）"""
    
    def generate_task_definition(self, config: AwsConfig) -> Dict:
        return {
            "family": config.task_family,
            "cpu": str(int(float(config.cpu) * 1024)),
            "memory": str(int(config.memory.rstrip('Mi'))),
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"] if config.enable_fargate else ["EC2"],
            "containerDefinitions": [{
                "name": config.app_name,
                "image": config.image,
                "essential": True,
                "portMappings": [{"containerPort": config.port, "protocol": "tcp"}],
                "environment": [{"name": k, "value": v} for k, v in config.environment.items()],
                "secrets": [{"name": s, "valueFrom": f"arn:aws:secretsmanager:{config.region.value}:123456789:secret:{s}"} for s in config.secrets],
                "logConfiguration": {
                    "logDriver": "awslogs",
                    "options": {
                        "awslogs-group": f"/ecs/{config.app_name}",
                        "awslogs-region": config.region.value,
                        "awslogs-stream-prefix": "ecs"
                    }
                },
                "healthCheck": {
                    "command": ["CMD-SHELL", f"curl -f http://localhost:{config.port}/health || exit 1"],
                    "interval": 30,
                    "timeout": 5,
                    "retries": 3,
                    "startPeriod": 60
                }
            }],
            "executionRoleArn": f"arn:aws:iam::123456789:role/{config.execution_role}",
            "volumes": []
        }
    
    def generate_ecs_service(self, config: AwsConfig) -> Dict:
        return {
            "cluster": config.cluster_name,
            "serviceName": f"{config.app_name}-service",
            "taskDefinition": config.task_family,
            "desiredCount": config.desired_count,
            "launchType": "FARGATE",
            "platformVersion": "LATEST",
            "networkConfiguration": {
                "awsvpcConfiguration": {
                    "subnets": [f"subnet-{i}" for i in range(1, 4)],
                    "securityGroups": ["sg-12345678"],
                    "assignPublicIp": "ENABLED"
                }
            },
            "loadBalancers": [{
                "targetGroupArn": f"arn:aws:elasticloadbalancing:{config.region.value}:123456789:targetgroup/{config.app_name}/abc123",
                "containerName": config.app_name,
                "containerPort": config.port
            }],
            "enableExecuteCommand": True,
            "serviceConnectConfiguration": {
                "enabled": True,
                "namespace": f"arn:aws:servicediscovery:{config.region.value}:123456789:namespace/ns-12345678"
            }
        }
    
    def generate_autoscaling(self, config: AwsConfig) -> Dict:
        if not config.enable_autoscaling:
            return {}
        
        return {
            "cluster": config.cluster_name,
            "service": f"{config.app_name}-service",
            "scalableTarget": {
                "minCapacity": config.min_instances,
                "maxCapacity": config.max_instances,
                "resourceId": f"service/{config.cluster_name}/{config.app_name}-service",
                "roleARN": f"arn:aws:iam::123456789:role/aws-service-role/ecs.application-autoscaling.amazonaws.com/AWSServiceRoleForApplicationAutoScaling_ECSService"
            },
            "targetTrackingScalingPolicies": [{
                "policyName": "target_cpu_75",
                "targetValue": 75.0,
                "predefinedMetricType": "ECSServiceAverageCPUUtilization",
                "scaleInCooldown": 300,
                "scaleOutCooldown": 60
            }, {
                "policyName": "target_memory_80",
                "targetValue": 80.0,
                "predefinedMetricType": "ECSServiceAverageMemoryUtilization",
                "scaleInCooldown": 300,
                "scaleOutCooldown": 60
            }]
        }


class AWSEKSGenerator:
    """AWS EKS 集群配置生成器（优化点 2）"""
    
    def generate_cluster(self, config: AwsConfig) -> Dict:
        return {
            "apiVersion": "eksctl.io/v1alpha5",
            "kind": "ClusterConfig",
            "metadata": {
                "name": config.cluster_name,
                "region": config.region.value,
                "version": "1.28"
            },
            "vpc": {
                "cidr": config.vpc_cidr,
                "nat": {"gateway": "single"},
                "clusterEndpoints": {
                    "publicAccess": True,
                    "privateAccess": True
                }
            },
            "iam": {
                "withOIDC": True,
                "serviceAccounts": [{
                    "metadata": {"name": "aws-load-balancer-controller", "namespace": "kube-system"},
                    "wellKnownPolicies": {"awsLoadBalancerController": True}
                }, {
                    "metadata": {"name": "external-dns", "namespace": "kube-system"},
                    "wellKnownPolicies": {"externalDNS": True}
                }]
            },
            "addons": [{
                "name": "vpc-cni",
                "version": "latest",
                "configurationValues": "{\"enableNetworkPolicy\": \"true\"}"
            }, {
                "name": "coredns",
                "version": "latest"
            }, {
                "name": "kube-proxy",
                "version": "latest"
            }]
        }
    
    def generate_nodegroup(self, config: AwsConfig) -> Dict:
        spot_config = {}
        if config.spot_instances:
            spot_config = {
                "instanceTypes": ["m5.large", "m5.xlarge", "m5.2xlarge"],
                "spot": True,
                "minSize": 1,
                "maxSize": 10,
                "desiredCapacity": 2,
                "spotAllocationStrategy": "lowest-price"
            }
        
        return {
            "apiVersion": "eksctl.io/v1alpha5",
            "kind": "NodeGroup",
            "metadata": {
                "name": f"{config.app_name}-ng",
                "clusterName": config.cluster_name,
                "region": config.region.value
            },
            "instanceType": "m5.large",
            "labels": {"app": config.app_name, "cost": "on-demand" if not config.spot_instances else "spot"},
            "desiredCapacity": config.desired_count,
            "minSize": config.min_instances,
            "maxSize": config.max_instances,
            "volumeSize": 20,
            "volumeType": "gp3",
            "encrypted": True,
            "privateNetworking": True,
            "updateStrategy": {
                "type": "RollingUpdate",
                "rollingUpdate": {"maxUnavailable": 1}
            },
            **spot_config
        }


class AWSLambdaGenerator:
    """AWS Lambda 函数配置生成器（优化点 3）"""
    
    def generate_function(self, config: AwsConfig) -> Dict:
        return {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Transform": "AWS::Serverless-2016-10-31",
            "Description": f"{config.app_name} Lambda function",
            "Resources": {
                f"{config.app_name}Function": {
                    "Type": "AWS::Serverless::Function",
                    "Properties": {
                        "Handler": "app.handler",
                        "Runtime": "python3.11",
                        "CodeUri": f"./dist/{config.app_name}",
                        "FunctionName": config.app_name,
                        "MemorySize": int(config.memory.rstrip('Mi')),
                        "Timeout": 30,
                        "Environment": {
                            "Variables": config.environment
                        },
                        "Events": {
                            "ApiEvent": {
                                "Type": "Api",
                                "Properties": {
                                    "Path": "/{proxy+}",
                                    "Method": "ANY"
                                }
                            }
                        },
                        "Layers": [f"arn:aws:lambda:{config.region.value}:123456789:layer:common-dependencies:1"],
                        "Tracing": "Active" if config.enable_monitoring else "PassThrough"
                    }
                }
            },
            "Outputs": {
                f"{config.app_name}Function": {
                    "Description": f"{config.app_name} Lambda Function ARN",
                    "Value": {"Fn::GetAtt": [f"{config.app_name}Function", "Arn"]}
                }
            }
        }


class GCPCloudRunGenerator:
    """GCP Cloud Run 服务配置生成器（优化点 4）"""
    
    def generate_service(self, config: GcpConfig) -> Dict:
        return {
            "apiVersion": "serving.knative.dev/v1",
            "kind": "Service",
            "metadata": {
                "name": config.service_name,
                "annotations": {
                    "run.googleapis.com/ingress": "internal-and-cloud-load-balancing"
                }
            },
            "spec": {
                "template": {
                    "metadata": {
                        "annotations": {
                            "autoscaling.knative.dev/minScale": str(config.min_instances),
                            "autoscaling.knative.dev/maxScale": str(config.max_instances),
                            "run.googleapis.com/execution-environment": "gen2",
                            "run.googleapis.com/cpu-throttling": "false"
                        }
                    },
                    "spec": {
                        "containerConcurrency": 80,
                        "timeoutSeconds": 300,
                        "containers": [{
                            "image": f"gcr.io/{config.project_id}/{config.image}",
                            "ports": [{"containerPort": config.port}],
                            "env": [{"name": k, "value": v} for k, v in config.environment.items()],
                            "envFrom": [{"secretRef": {"name": s}} for s in config.secrets],
                            "resources": {
                                "limits": {
                                    "cpu": config.cpu,
                                    "memory": config.memory
                                },
                                "requests": {
                                    "cpu": str(float(config.cpu) * 0.5),
                                    "memory": str(int(config.memory.rstrip('Mi')) // 2) + "Mi"
                                }
                            },
                            "startupProbe": {
                                "httpGet": {"path": f"/health", "port": config.port},
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5,
                                "failureThreshold": 30
                            },
                            "livenessProbe": {
                                "httpGet": {"path": f"/health", "port": config.port},
                                "periodSeconds": 30,
                                "failureThreshold": 3
                            }
                        }]
                    }
                },
                "traffic": [{"percent": 100, "latestRevision": True}]
            }
        }
    
    def generate_vpc_connector(self, config: GcpConfig) -> Dict:
        return {
            "name": f"{config.app_name}-vpc-connector",
            "region": config.region.value,
            "minInstances": 2,
            "maxInstances": 10,
            "network": "default",
            "ipCidrRange": "10.8.0.0/28",
            "machineType": "e2-micro"
        }


class GCPGKEGenerator:
    """GCP GKE 集群配置生成器（优化点 5）"""
    
    def generate_cluster(self, config: GcpConfig) -> Dict:
        return {
            "apiVersion": "container.cnrm.cloud.google.com/v1beta1",
            "kind": "ContainerCluster",
            "metadata": {
                "name": f"{config.app_name}-cluster",
                "namespace": config.project_id
            },
            "spec": {
                "location": config.region.value,
                "version": "1.28",
                "network": f"projects/{config.project_id}/global/networks/default",
                "subnetwork": f"projects/{config.project_id}/regions/{config.region.value}/subnetworks/{config.app_name}",
                "privateClusterConfig": {
                    "enablePrivateNodes": True,
                    "enablePrivateEndpoint": False,
                    "masterIpv4CidrBlock": "172.16.0.0/28"
                },
                "ipAllocationPolicy": {
                    "useIpAliases": True,
                    "createSubnetwork": True
                },
                "workloadIdentityConfig": {
                    "workloadPool": f"{config.project_id}.svc.id.goog"
                },
                "nodePools": [{
                    "name": f"{config.app_name}-np",
                    "machineType": "e2-medium",
                    "nodeCount": config.desired_count,
                    "autoscaling": {
                        "enabled": config.enable_autoscaling,
                        "minNodeCount": config.min_instances,
                        "maxNodeCount": config.max_instances
                    },
                    "nodeConfig": {
                        "diskSizeGb": 20,
                        "diskType": "pd-ssd",
                        "shieldedInstanceConfig": {
                            "enableSecureBoot": True,
                            "enableIntegrityMonitoring": True
                        }
                    },
                    "management": {
                        "autoRepair": True,
                        "autoUpgrade": True
                    }
                }],
                "addonsConfig": {
                    "horizontalPodAutoscaling": {"disabled": False},
                    "networkPolicy": {"enabled": True},
                    "gcePersistentDiskCsiDriverConfig": {"enabled": True}
                },
                "meshCertificates": {
                    "enableCertificates": True
                }
            }
        }


class GCPCloudFunctionsGenerator:
    """GCP Cloud Functions 配置生成器（优化点 6）"""
    
    def generate_function(self, config: GcpConfig) -> Dict:
        return {
            "name": f"projects/{config.project_id}/locations/{config.region.value}/functions/{config.app_name}",
            "buildConfig": {
                "runtime": "python311",
                "entryPoint": "handler",
                "source": {"storageSource": {"bucket": f"{config.project_id}-functions", "object": f"{config.app_name}.zip"}}
            },
            "serviceConfig": {
                "maxInstanceCount": config.max_instances,
                "minInstanceCount": config.min_instances,
                "availableMemory": config.memory,
                "timeoutSeconds": 60,
                "environmentVariables": config.environment,
                "secretEnvironmentVariables": [{"projectId": config.project_id, "name": s, "secret": s} for s in config.secrets],
                "ingressSettings": "ALLOW_INTERNAL_AND_GCLB",
                "vpcConnector": f"projects/{config.project_id}/locations/{config.region.value}/connectors/{config.app_name}-connector",
                "vpcConnectorEgressSettings": "PRIVATE_RANGES_ONLY",
                "autonomousInstanceCount": 1 if config.enable_autoscaling else None
            }
        }


class AzureContainerInstancesGenerator:
    """Azure Container Instances 配置生成器（优化点 7）"""
    
    def generate_container_group(self, config: AzureConfig) -> Dict:
        return {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {
                "location": {"defaultValue": config.location.value, "type": "String"},
                "containerGroupName": {"defaultValue": config.app_name, "type": "String"}
            },
            "resources": [{
                "name": "[parameters('containerGroupName')]",
                "type": "Microsoft.ContainerInstance/containerGroups",
                "apiVersion": "2023-05-01",
                "location": "[parameters('location')]",
                "properties": {
                    "sku": "Standard",
                    "containerRestartPolicy": "Always",
                    "ipAddress": {
                        "type": "Public",
                        "ports": [{"protocol": "TCP", "port": config.port}]
                    },
                    "osType": "Linux",
                    "containers": [{
                        "name": config.app_name,
                        "properties": {
                            "image": f"{config.resource_group}.azurecr.io/{config.image}",
                            "resources": {
                                "requests": {
                                    "cpu": float(config.cpu),
                                    "memoryInGb": float(config.memory.rstrip('Mi')) / 1024
                                },
                                "limits": {
                                    "cpu": float(config.cpu) * 2,
                                    "memoryInGb": float(config.memory.rstrip('Mi')) / 512
                                }
                            },
                            "ports": [{"port": config.port, "protocol": "TCP"}],
                            "environmentVariables": [{"name": k, "value": v} for k, v in config.environment.items()],
                            "secureEnvironmentVariables": [{"name": s, "value": f"[parameters('{s}Secret')]"} for s in config.secrets],
                            "livenessProbe": {
                                "tcpSocket": {"port": config.port},
                                "initialDelaySeconds": 10,
                                "periodSeconds": 30,
                                "failureThreshold": 3
                            },
                            "startupProbe": {
                                "httpGet": {"path": "/health", "port": config.port},
                                "initialDelaySeconds": 5,
                                "periodSeconds": 5,
                                "failureThreshold": 30
                            }
                        }
                    }]
                },
                "identity": {"type": "SystemAssigned"} if config.enable_managed_identity else None
            }]
        }


class AzureAKSGenerator:
    """Azure AKS 集群配置生成器（优化点 8）"""
    
    def generate_cluster(self, config: AzureConfig) -> Dict:
        return {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "resources": [{
                "type": "Microsoft.ContainerService/managedClusters",
                "apiVersion": "2023-08-01",
                "name": f"{config.app_name}-aks",
                "location": config.location.value,
                "sku": {
                    "name": "Basics",
                    "tier": "Standard"
                },
                "properties": {
                    "kubernetesVersion": "1.28",
                    "enableRBAC": True,
                    "dnsPrefix": f"{config.app_name}-dns",
                    "oidcIssuerProfile": {"enabled": True},
                    "workloadAutoScalerProfile": {
                        "keda": {"enabled": True}
                    } if config.enable_autoscaling else None,
                    "networkProfile": {
                        "networkPlugin": "azure",
                        "networkPolicy": "calico",
                        "loadBalancerSku": "standard",
                        "serviceCidr": "10.0.0.0/16",
                        "dnsServiceIP": "10.0.0.10"
                    },
                    "addonProfiles": {
                        "azureKeyvaultSecretsProvider": {"enabled": True},
                        "omsagent": {"enabled": config.enable_monitoring},
                        "ingressAzureWebApplicationFirewall": {"enabled": False}
                    },
                    "identity": {
                        "type": "SystemAssigned"
                    } if config.enable_managed_identity else None
                },
                "resources": [{
                    "type": "managedClusters/agentPools",
                    "apiVersion": "2023-08-01",
                    "name": f"{config.app_name}-pool",
                    "location": config.location.value,
                    "dependsOn": [f"[resourceId('Microsoft.ContainerService/managedClusters', '{config.app_name}-aks')]"],
                    "properties": {
                        "count": config.desired_count,
                        "vmSize": "Standard_D2s_v3",
                        "enableAutoScaling": config.enable_autoscaling,
                        "minCount": config.min_instances,
                        "maxCount": config.max_instances,
                        "osType": "Linux",
                        "type": "VirtualMachineScaleSets",
                        "scaleSetPriority": "Spot" if config.cost_optimized else "Regular",
                        "scaleDownMode": "Delete",
                        "upgradeSettings": {
                            "maxSurge": "33%"
                        },
                        "nodeLabels": {"app": config.app_name},
                        "nodeTaints": ["dedicated=app:NoSchedule"]
                    }
                }]
            }]
        }


class AzureFunctionsGenerator:
    """Azure Functions 配置生成器（优化点 9）"""
    
    def generate_function(self, config: AzureConfig) -> Dict:
        return {
            "id": f"/subscriptions/{config.subscription_id}/resourceGroups/{config.resource_group}/providers/Microsoft.Web/sites/{config.app_name}",
            "name": config.app_name,
            "type": "Microsoft.Web/sites",
            "kind": "functionapp,linux",
            "location": config.location.value,
            "properties": {
                "serverFarmId": f"/subscriptions/{config.subscription_id}/resourceGroups/{config.resource_group}/providers/Microsoft.Web/serverfarms/{config.app_name}-plan",
                "siteConfig": {
                    "appSettings": [
                        {"name": "AzureWebJobsStorage", "value": "[concat('DefaultEndpointsProtocol=https;AccountName=', variables('storageAccountName'), ';EndpointSuffix=', environment().suffixes.storage)]\""},
                        {"name": "FUNCTIONS_WORKER_RUNTIME", "value": "python"},
                        {"name": "FUNCTIONS_EXTENSION_VERSION", "value": "~4"},
                        {"name": "APPINSIGHTS_INSTRUMENTATIONKEY", "value": "[reference(resourceId('microsoft.insights/components', variables('appInsightsName')), '2020-02-02').InstrumentationKey]"}
                    ] + [{"name": k, "value": v} for k, v in config.environment.items()],
                    "linuxFxVersion": "Python|3.11",
                    "minTlsVersion": "1.2",
                    "FtpsState": "Disabled",
                    "healthCheckPath": "/health"
                },
                "identity": {
                    "type": "SystemAssigned"
                } if config.enable_managed_identity else None
            }
        }


class MultiCloudAbstractionGenerator:
    """多云统一抽象层配置生成器（优化点 10）"""
    
    def generate_unified_config(self, config: CloudConfig) -> Dict:
        return {
            "version": "1.0",
            "app": {
                "name": config.app_name,
                "image": config.image,
                "port": config.port
            },
            "compute": {
                "cpu": config.cpu,
                "memory": config.memory,
                "instance_type": {
                    "aws": "t3.medium",
                    "gcp": "e2-medium",
                    "azure": "Standard_D2s_v3"
                }
            },
            "scaling": {
                "enabled": config.enable_autoscaling,
                "min": config.min_instances,
                "max": config.max_instances,
                "metrics": {
                    "cpu_threshold": 75,
                    "memory_threshold": 80,
                    "request_count_threshold": 100
                }
            },
            "networking": {
                "vpc_cidr": config.vpc_cidr,
                "enable_tls": True,
                "enable_waf": True
            },
            "observability": {
                "monitoring": config.enable_monitoring,
                "logging": config.enable_logging,
                "tracing": True
            },
            "security": {
                "secrets_management": True,
                "identity_provider": "aws-iam" if isinstance(config, AwsConfig) else "gcp-wif" if isinstance(config, GcpConfig) else "azure-ad"
            }
        }
    
    def generate_provider_specific(self, config: CloudConfig) -> Dict[str, Dict]:
        if isinstance(config, AwsConfig):
            return {"aws": self._generate_aws_specific(config)}
        elif isinstance(config, GcpConfig):
            return {"gcp": self._generate_gcp_specific(config)}
        elif isinstance(config, AzureConfig):
            return {"azure": self._generate_azure_specific(config)}
        return {}
    
    def _generate_aws_specific(self, config: AwsConfig) -> Dict:
        return {
            "provider": "aws",
            "region": config.region.value,
            "ecs": {"cluster": config.cluster_name},
            "eks": {"cluster": config.cluster_name} if not config.enable_fargate else None,
            "lambda": {"runtime": "python3.11"},
            "cost_optimization": {
                "spot_instances": config.spot_instances,
                "savings_plan": config.cost_optimized
            }
        }
    
    def _generate_gcp_specific(self, config: GcpConfig) -> Dict:
        return {
            "provider": "gcp",
            "project": config.project_id,
            "region": config.region.value,
            "cloud_run": {"service": config.service_name},
            "gke": {"cluster": f"{config.app_name}-cluster"},
            "functions": {"runtime": "python311"},
            "cost_optimization": {
                "committed_use_discounts": config.cost_optimized,
                "preemptible_instances": config.cost_optimized
            }
        }
    
    def _generate_azure_specific(self, config: AzureConfig) -> Dict:
        return {
            "provider": "azure",
            "subscription": config.subscription_id,
            "resource_group": config.resource_group,
            "location": config.location.value,
            "container_instances": {"name": config.app_name},
            "aks": {"cluster": f"{config.app_name}-aks"},
            "functions": {"runtime": "python"},
            "cost_optimization": {
                "reserved_instances": config.cost_optimized,
                "spot_instances": config.cost_optimized
            }
        }


class CloudBestPracticesGenerator:
    """云厂商特定最佳实践配置生成器（优化点 11）"""
    
    def generate_practices(self, provider: CloudProvider) -> Dict:
        practices = {
            CloudProvider.AWS: {
                "security": ["使用 IAM 角色而非访问密钥", "启用 AWS CloudTrail 审计", "使用 Security Groups 限制入站流量", "启用 EFS/S3 加密"],
                "performance": ["使用 Application Load Balancer", "启用 Amazon CloudFront CDN", "使用 ElastiCache 缓存", "配置 RDS Read Replicas"],
                "reliability": ["跨可用区部署", "启用 Auto Scaling", "配置 S3 版本控制", "使用 CloudWatch 警报"]
            },
            CloudProvider.GCP: {
                "security": ["使用 Workload Identity", "启用 VPC Service Controls", "使用 Cloud Armor", "配置 Binary Authorization"],
                "performance": ["使用 Cloud CDN", "配置 Memorystore 缓存", "使用 Cloud Load Balancing", "配置全球负载均衡"],
                "reliability": ["跨区域部署", "启用 Cloud Monitoring", "配置故障转移", "使用 Cloud Storage 多区域存储"]
            },
            CloudProvider.AZURE: {
                "security": ["使用 Managed Identity", "启用 Azure AD 条件访问", "使用 Azure Firewall", "配置 Network Security Groups"],
                "performance": ["使用 Azure CDN", "配置 Azure Cache for Redis", "使用 Application Gateway", "配置 Traffic Manager"],
                "reliability": ["跨可用性区域部署", "启用 Azure Monitor", "配置自动故障转移", "使用 GRS 存储"]
            }
        }
        return practices.get(provider, {})


class CostOptimizationGenerator:
    """成本优化配置生成器（优化点 12）"""
    
    def generate_optimization(self, config: CloudConfig) -> Dict:
        return {
            "right_sizing": {
                "enabled": config.cost_optimized,
                "recommendations": True,
                "auto_adjust": True,
                "schedule": {"start": "09:00", "end": "18:00", "timezone": "UTC"}
            },
            "reserved_capacity": {
                "enabled": config.cost_optimized,
                "term": "1_year",
                "payment_option": "Partial_Upfront"
            },
            "spot_preemptible": {
                "enabled": config.cost_optimized,
                "fallback_on_demand": True,
                "max_spot_percentage": 80
            },
            "scheduled_scaling": {
                "enabled": True,
                "timezone": "UTC",
                "rules": [
                    {"cron": "0 18 * * 1-5", "action": "scale_to_min"},
                    {"cron": "0 9 * * 1-5", "action": "scale_to_peak"}
                ]
            },
            "storage_tiering": {
                "enabled": True,
                "hot_to_warm_days": 30,
                "warm_to_cold_days": 90
            },
            "monitoring": {
                "budget_alerts": True,
                "daily_limit": 100.00,
                "anomaly_detection": True
            }
        }


class CloudConfigGenerator:
    """完整的云服务配置生成器"""
    
    def __init__(self):
        self.ecs_gen = AWSECSGenerator()
        self.eks_gen = AWSEKSGenerator()
        self.lambda_gen = AWSLambdaGenerator()
        self.cloudrun_gen = GCPCloudRunGenerator()
        self.gke_gen = GCPGKEGenerator()
        self.gcf_gen = GCPCloudFunctionsGenerator()
        self.aci_gen = AzureContainerInstancesGenerator()
        self.aks_gen = AzureAKSGenerator()
        self.functions_gen = AzureFunctionsGenerator()
        self.multi_cloud_gen = MultiCloudAbstractionGenerator()
        self.practices_gen = CloudBestPracticesGenerator()
        self.cost_gen = CostOptimizationGenerator()
    
    def generate_aws_configs(self, config: AwsConfig) -> Dict[str, any]:
        return {
            "ecs-task-definition.json": self.ecs_gen.generate_task_definition(config),
            "ecs-service.json": self.ecs_gen.generate_ecs_service(config),
            "ecs-autoscaling.json": self.ecs_gen.generate_autoscaling(config),
            "eks-cluster.yaml": self.eks_gen.generate_cluster(config),
            "eks-nodegroup.yaml": self.eks_gen.generate_nodegroup(config),
            "lambda-template.yaml": self.lambda_gen.generate_function(config),
            "multi-cloud-unified.yaml": self.multi_cloud_gen.generate_unified_config(config),
            "cloud-best-practices.json": self.practices_gen.generate_practices(CloudProvider.AWS),
            "cost-optimization.json": self.cost_gen.generate_optimization(config)
        }
    
    def generate_gcp_configs(self, config: GcpConfig) -> Dict[str, any]:
        return {
            "cloudrun-service.yaml": self.cloudrun_gen.generate_service(config),
            "cloudrun-vpc-connector.json": self.cloudrun_gen.generate_vpc_connector(config),
            "gke-cluster.yaml": self.gke_gen.generate_cluster(config),
            "cloud-function.json": self.gcf_gen.generate_function(config),
            "multi-cloud-unified.yaml": self.multi_cloud_gen.generate_unified_config(config),
            "cloud-best-practices.json": self.practices_gen.generate_practices(CloudProvider.GCP),
            "cost-optimization.json": self.cost_gen.generate_optimization(config)
        }
    
    def generate_azure_configs(self, config: AzureConfig) -> Dict[str, any]:
        return {
            "aci-template.json": self.aci_gen.generate_container_group(config),
            "aks-cluster.json": self.aks_gen.generate_cluster(config),
            "functions-app.json": self.functions_gen.generate_function(config),
            "multi-cloud-unified.yaml": self.multi_cloud_gen.generate_unified_config(config),
            "cloud-best-practices.json": self.practices_gen.generate_practices(CloudProvider.AZURE),
            "cost-optimization.json": self.cost_gen.generate_optimization(config)
        }
    
    def generate_all(self, cloud_config: CloudConfig) -> Dict[str, any]:
        if isinstance(cloud_config, AwsConfig):
            return self.generate_aws_configs(cloud_config)
        elif isinstance(cloud_config, GcpConfig):
            return self.generate_gcp_configs(cloud_config)
        elif isinstance(cloud_config, AzureConfig):
            return self.generate_azure_configs(cloud_config)
        return {}
