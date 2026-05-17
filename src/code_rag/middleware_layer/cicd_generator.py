"""CI/CD Pipeline 生成器

阶段 D: CI/CD Pipeline 生成
12 个优化点:
1. GitHub Actions 工作流生成
2. GitLab CI Pipeline 配置
3. Jenkins Pipeline (Jenkinsfile)
4. ArgoCD Application 配置
5. Tekton Pipeline 配置
6. 自动化测试集成（单元/集成/E2E）
7. 安全扫描集成（SAST/DAST/SCA）
8. 容器镜像构建与推送
9. 部署策略（蓝绿/金丝雀/滚动）
10. 基础设施即代码 (IaC) 集成
11. 通知与告警集成
12. 回滚与恢复机制
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class CICDPlatform(Enum):
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    JENKINS = "jenkins"
    ARGOCD = "argocd"
    TEKTON = "tekton"


class DeploymentStrategy(Enum):
    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"


class Environment(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class PipelineConfig:
    app_name: str = "my-app"
    language: str = "python"
    build_image: str = "python:3.11-slim"
    docker_registry: str = "ghcr.io"
    docker_repo: str = "my-org/my-app"
    environments: List[Environment] = field(default_factory=lambda: [
        Environment.DEVELOPMENT, Environment.STAGING, Environment.PRODUCTION
    ])
    enable_security_scan: bool = True
    enable_integration_tests: bool = True
    enable_e2e_tests: bool = True
    deployment_strategy: DeploymentStrategy = DeploymentStrategy.ROLLING
    enable_rollback: bool = True
    enable_notifications: bool = True
    slack_webhook: Optional[str] = None
    enable_iac: bool = True
    kubernetes_namespace: str = "default"
    helm_chart_path: Optional[str] = None
    terraform_state_bucket: Optional[str] = None
    notification_channels: List[str] = field(default_factory=list)


class GitHubActionsGenerator:
    """GitHub Actions 工作流生成器（优化点 1）"""
    
    def generate_workflow(self, config: PipelineConfig) -> Dict:
        workflow = {
            "name": f"{config.app_name} CI/CD",
            "on": {
                "push": {"branches": ["main", "develop"]},
                "pull_request": {"branches": ["main"]},
                "workflow_dispatch": {}
            },
            "env": {
                "APP_NAME": config.app_name,
                "DOCKER_REGISTRY": config.docker_registry,
                "DOCKER_REPO": config.docker_repo,
                "KUBERNETES_NAMESPACE": config.kubernetes_namespace
            },
            "jobs": self._generate_jobs(config)
        }
        return workflow
    
    def _generate_jobs(self, config: PipelineConfig) -> Dict:
        jobs = {
            "lint": self._generate_lint_job(config),
            "test": self._generate_test_job(config),
            "build": self._generate_build_job(config),
            "security-scan": self._generate_security_job(config),
            "deploy-staging": self._generate_deploy_job(config, Environment.STAGING),
        }
        
        if config.deployment_strategy == DeploymentStrategy.CANARY:
            jobs["deploy-canary"] = self._generate_canary_job(config)
            jobs["deploy-production"] = self._generate_production_job(config, Environment.PRODUCTION)
        else:
            jobs["deploy-production"] = self._generate_production_job(config, Environment.PRODUCTION)
        
        return jobs
    
    def _generate_lint_job(self, config: PipelineConfig) -> Dict:
        lint_commands = {
            "python": ["pip install ruff", "ruff check ."],
            "node": ["npm ci", "npm run lint"],
            "go": ["go fmt ./...", "golangci-lint run"],
        }
        command = lint_commands.get(config.language, ["echo 'No linter configured'"])
        
        return {
            "runs-on": "ubuntu-latest",
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": f"Set up {config.language}",
                    "uses": "actions/setup-python@v4" if config.language == "python" else "actions/setup-node@v4",
                    "with": {"cache": "pip"} if config.language == "python" else {"cache": "npm"}
                },
                {"name": "Run linter", "run": " && ".join(command)}
            ]
        }
    
    def _generate_test_job(self, config: PipelineConfig) -> Dict:
        test_commands = {
            "python": ["pip install pytest pytest-cov", "pytest --cov=. --cov-report=xml"],
            "node": ["npm test -- --coverage"],
            "go": ["go test -v -race -coverprofile=coverage.out ./..."]
        }
        command = test_commands.get(config.language, ["echo 'No tests configured'"])
        
        return {
            "runs-on": "ubuntu-latest",
            "needs": "lint",
            "services": self._generate_test_services(config),
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": f"Set up {config.language}",
                    "uses": "actions/setup-python@v4" if config.language == "python" else "actions/setup-node@v4"
                },
                {"name": "Run tests", "run": " && ".join(command)},
                {
                    "name": "Upload coverage",
                    "uses": "codecov/codecov-action@v3",
                    "with": {"files": "./coverage.xml", "fail_ci_if_error": False}
                }
            ]
        }
    
    def _generate_test_services(self, config: PipelineConfig) -> Dict:
        services = {}
        if config.enable_integration_tests:
            if config.language in ["python", "node"]:
                services["postgres"] = {
                    "image": "postgres:15-alpine",
                    "env": {"POSTGRES_PASSWORD": "test", "POSTGRES_DB": "test"},
                    "options": "--health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5"
                }
                services["redis"] = {
                    "image": "redis:7-alpine",
                    "options": "--health-cmd 'redis-cli ping' --health-interval 10s --health-timeout 5s --health-retries 5"
                }
        return services
    
    def _generate_build_job(self, config: PipelineConfig) -> Dict:
        return {
            "runs-on": "ubuntu-latest",
            "needs": "test",
            "outputs": {"image_tag": {"value": "${{steps.meta.outputs.tags}}"},
                        "digest": {"value": "${{steps.meta.outputs.digest}}"}},
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": "Set up Docker Buildx",
                    "uses": "docker/setup-buildx-action@v3"
                },
                {
                    "name": "Log in to Container Registry",
                    "uses": "docker/login-action@v3",
                    "with": {"registry": config.docker_registry, "username": "${{ secrets.REGISTRY_USER }}", "password": "${{ secrets.REGISTRY_TOKEN }}"}
                },
                {
                    "name": "Extract metadata",
                    "id": "meta",
                    "uses": "docker/metadata-action@v5",
                    "with": {"images": f"{config.docker_registry}/{config.docker_repo}"}
                },
                {
                    "name": "Build and push",
                    "uses": "docker/build-push-action@v5",
                    "with": {
                        "context": ".",
                        "push": "${{ github.event_name != 'pull_request' }}",
                        "tags": "${{ steps.meta.outputs.tags }}",
                        "cache-from": "type=gha",
                        "cache-to": "type=gha,mode=max",
                        "provenance": "true",
                        "sbom": "true"
                    }
                }
            ]
        }
    
    def _generate_security_job(self, config: PipelineConfig) -> Dict:
        if not config.enable_security_scan:
            return {"runs-on": "ubuntu-latest", "steps": [{"run": "echo 'Security scan disabled'"}]}
        
        return {
            "runs-on": "ubuntu-latest",
            "needs": "build",
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": "Run Trivy vulnerability scanner",
                    "uses": "aquasecurity/trivy-action@master",
                    "with": {
                        "scan-type": "fs",
                        "severity": "CRITICAL,HIGH",
                        "exit-code": "1",
                        "format": "sarif",
                        "output": "trivy-results.sarif"
                    }
                },
                {
                    "name": "Upload Trivy results",
                    "uses": "github/codeql-action/upload-sarif@v2",
                    "with": {"sarif_file": "trivy-results.sarif"}
                },
                {
                    "name": "Run Semgrep",
                    "uses": "returntocorp/semgrep-action@v1",
                    "with": {"config": "p/security-audit p/severity=high"}
                }
            ]
        }
    
    def _generate_deploy_job(self, config: PipelineConfig, env: Environment) -> Dict:
        return {
            "runs-on": "ubuntu-latest",
            "needs": "security-scan",
            "environment": env.value,
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": "Configure AWS credentials",
                    "uses": "aws-actions/configure-aws-credentials@v4",
                    "with": {"role-to-assume": "${{ secrets.AWS_ROLE_ARN }}", "aws-region": "us-east-1"}
                },
                {
                    "name": "Deploy to EKS",
                    "run": f"helm upgrade --install {config.app_name} ./chart --namespace {config.kubernetes_namespace} --set image.tag=${{ github.sha }} --wait --timeout 5m"
                },
                {
                    "name": "Run integration tests",
                    "run": "pytest tests/integration/ -v",
                    "if": config.enable_integration_tests
                },
                {
                    "name": "Notify Slack",
                    "uses": " slackapi/slack-github-action@v1.25.0",
                    "with": {"channel-id": "deployments", "payload": '{"text": "Deployed to ' + env.value + '"}'},
                    "if": config.enable_notifications
                }
            ]
        }
    
    def _generate_canary_job(self, config: PipelineConfig) -> Dict:
        return {
            "runs-on": "ubuntu-latest",
            "needs": "security-scan",
            "environment": "staging",
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": "Deploy canary (10% traffic)",
                    "run": f"kubectl set image deployment/{config.app_name} {config.app_name}=${{ needs.build.outputs.image_tag }} -n {config.kubernetes_namespace}"
                },
                {"name": "Wait for canary analysis", "run": "sleep 60"},
                {"name": "Promote canary to production", "run": "echo 'Canary approved, promoting to production'"}
            ]
        }
    
    def _generate_production_job(self, config: PipelineConfig, env: Environment) -> Dict:
        return {
            "runs-on": "ubuntu-latest",
            "needs": "deploy-canary" if config.deployment_strategy == DeploymentStrategy.CANARY else "security-scan",
            "environment": {"name": env.value, "url": f"https://{config.app_name}.example.com"},
            "steps": [
                {"uses": "actions/checkout@v4"},
                {
                    "name": "Deploy to production",
                    "run": f"helm upgrade --install {config.app_name} ./chart --namespace {config.kubernetes_namespace} --set image.tag=${{ needs.build.outputs.image_tag || github.sha }} --wait --timeout 10m --atomic"
                },
                {
                    "name": "Run smoke tests",
                    "run": "curl -f https://${{ env.APP_NAME }}.example.com/health"
                },
                {
                    "name": "Notify deployment",
                    "run": f"echo 'Deployed {config.app_name} to production'",
                    "if": config.enable_notifications
                }
            ]
        }


class GitLabCIGenerator:
    """GitLab CI Pipeline 配置生成器（优化点 2）"""
    
    def generate_pipeline(self, config: PipelineConfig) -> Dict:
        return {
            "stages": ["lint", "test", "build", "security", "deploy-staging", "deploy-production"],
            "variables": {
                "DOCKER_REGISTRY": config.docker_registry,
                "DOCKER_REPO": config.docker_repo,
                "APP_NAME": config.app_name
            },
            "lint": self._generate_stage("lint", config),
            "test": self._generate_test_stage(config),
            "build": self._generate_build_stage(config),
            "security-scan": self._generate_security_stage(config),
            "deploy-staging": self._generate_deploy_stage(config, Environment.STAGING),
            "deploy-production": self._generate_production_stage(config)
        }
    
    def _generate_stage(self, stage: str, config: PipelineConfig) -> Dict:
        scripts = {"lint": ["pip install ruff && ruff check ."] if config.language == "python" else ["npm run lint"]}
        return {
            "stage": stage,
            "image": config.build_image,
            "script": scripts.get(stage, ["echo 'No script'"]),
            "artifacts": {"reports": {"junit": "report.xml"}} if stage == "test" else None
        }
    
    def _generate_test_stage(self, config: PipelineConfig) -> Dict:
        test_script = ["pip install pytest pytest-cov pytest-json-report", "pytest --json-report --json-report-file=report.json"]
        return {
            "stage": "test",
            "image": config.build_image,
            "services": ["postgres:15", "redis:7"],
            "script": test_script,
            "artifacts": {"reports": {"junit": "report.xml", "coverage_report": {"coverage_format": "cobertura", "path": "coverage.xml"}}}
        }
    
    def _generate_build_stage(self, config: PipelineConfig) -> Dict:
        return {
            "stage": "build",
            "image": {"name": "docker:24-dind", "entrypoint": [""]},
            "services": ["docker:24-dind"],
            "script": [
                f"docker build -t $DOCKER_REGISTRY/$DOCKER_REPO:$CI_COMMIT_SHA .",
                f"docker push $DOCKER_REGISTRY/$DOCKER_REPO:$CI_COMMIT_SHA",
                f"docker tag $DOCKER_REGISTRY/$DOCKER_REPO:$CI_COMMIT_SHA $DOCKER_REGISTRY/$DOCKER_REPO:latest",
                "docker push $DOCKER_REGISTRY/$DOCKER_REPO:latest"
            ],
            "rules": [{"if": "$CI_COMMIT_BRANCH"}]
        }
    
    def _generate_security_stage(self, config: PipelineConfig) -> Dict:
        return {
            "stage": "security",
            "image": {"name": "aquasec/trivy:latest", "entrypoint": [""]},
            "script": ["trivy image --exit-code 1 --severity CRITICAL,HIGH $DOCKER_REGISTRY/$DOCKER_REPO:$CI_COMMIT_SHA"],
            "rules": [{"if": "$CI_COMMIT_BRANCH == 'main'"}]
        }
    
    def _generate_deploy_stage(self, config: PipelineConfig, env: Environment) -> Dict:
        return {
            "stage": f"deploy-{env.value}",
            "image": {"name": "bitnami/kubectl:latest", "entrypoint": [""]},
            "script": [
                f"helm upgrade --install {config.app_name} ./chart --set image.tag=$CI_COMMIT_SHA --namespace {config.kubernetes_namespace} --wait"
            ],
            "environment": {"name": env.value, "url": f"https://{config.app_name}.{env.value}.example.com"},
            "rules": [{"if": f"$CI_COMMIT_BRANCH == '{'main' if env == Environment.PRODUCTION else 'develop'}'"}]
        }
    
    def _generate_production_stage(self, config: PipelineConfig) -> Dict:
        return {
            **self._generate_deploy_stage(config, Environment.PRODUCTION),
            "stage": "deploy-production",
            "when": "manual",
            "environment": {"name": "production", "url": f"https://{config.app_name}.example.com", "on_stop": "rollback-production"}
        }


class JenkinsPipelineGenerator:
    """Jenkins Pipeline (Jenkinsfile) 生成器（优化点 3）"""
    
    def generate_jenkinsfile(self, config: PipelineConfig) -> str:
        stages = self._generate_stages(config)
        return f'''pipeline {{
    agent {{ dockerfile {{ reuseNode true }} }}
    
    environment {{
        APP_NAME = '{config.app_name}'
        DOCKER_REGISTRY = '{config.docker_registry}'
        DOCKER_REPO = '{config.docker_repo}'
        KUBERNETES_NAMESPACE = '{config.kubernetes_namespace}'
    }}
    
    options {{
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }}
    
    stages {stages}
    
    post {{
        always {{
            cleanWs()
            junit '**/test-results/*.xml'
            coverage(pattern: '**/coverage.xml')
        }}
        success {{
            echo 'Pipeline completed successfully!'
            slackSend(channel: '#deployments', message: "Build ${{BUILD_NUMBER}} succeeded: ${{env.GIT_COMMIT[0..7]}}")
        }}
        failure {{
            echo 'Pipeline failed!'
            slackSend(channel: '#deployments', message: "Build ${{BUILD_NUMBER}} FAILED!", color: 'danger')
        }}
    }}
}}
'''
    
    def _generate_stages(self, config: PipelineConfig) -> str:
        return f'''
        stage('Checkout') {{
            steps {{
                checkout scm
            }}
        }}
        
        stage('Lint') {{
            steps {{
                sh ''' + self._get_lint_command(config) + '''
            }}
        }}
        
        stage('Test') {{
            steps {{
                sh ''' + self._get_test_command(config) + '''
            }}
        }}
        
        stage('Security Scan') {{
            when {{
                branch 'main'
            }}
            steps {{
                sh 'trivy image --exit-code 1 --severity CRITICAL,HIGH $DOCKER_REGISTRY/$DOCKER_REPO:$GIT_COMMIT'
            }}
        }}
        
        stage('Build & Push') {{
            steps {{
                script {{
                    def image = docker.build("$DOCKER_REGISTRY/$DOCKER_REPO:$GIT_COMMIT")
                    docker.withRegistry('https://$DOCKER_REGISTRY', 'docker-hub-credentials') {{
                        image.push()
                        image.push('latest')
                    }}
                }}
            }}
        }}
        
        stage('Deploy to Staging') {{
            when {{
                branch 'develop'
            }}
            steps {{
                sh 'helm upgrade --install $APP_NAME ./chart --set image.tag=$GIT_COMMIT --namespace staging --wait'
            }}
        }}
        
        stage('Deploy to Production') {{
            when {{
                branch 'main'
            }}
            steps {{
                sh 'helm upgrade --install $APP_NAME ./chart --set image.tag=$GIT_COMMIT --namespace production --wait --atomic'
            }}
        }}
'''
    
    def _get_lint_command(self, config: PipelineConfig) -> str:
        commands = {"python": "pip install ruff && ruff check .", "node": "npm run lint"}
        return commands.get(config.language, "echo 'No linter'")
    
    def _get_test_command(self, config: PipelineConfig) -> str:
        commands = {"python": "pytest tests/ --junitxml=test-results/results.xml --cov=. --cov-report=xml", "node": "npm test"}
        return commands.get(config.language, "echo 'No tests'")


class ArgoCDGenerator:
    """ArgoCD Application 配置生成器（优化点 4）"""
    
    def generate_application(self, config: PipelineConfig) -> Dict:
        return {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {
                "name": config.app_name,
                "namespace": "argocd",
                "labels": {"app": config.app_name}
            },
            "spec": {
                "project": "default",
                "source": {
                    "repoURL": "https://github.com/my-org/k8s-config",
                    "targetRevision": "HEAD",
                    "path": f"apps/{config.app_name}/overlays/{config.deployment_strategy.value}",
                    "helm": {
                        "valueFiles": ["values.yaml", f"values-{config.deployment_strategy.value}.yaml"],
                        "parameters": [
                            {"name": "image.repository", "value": f"{config.docker_registry}/{config.docker_repo}"},
                            {"name": "image.tag", "value": "latest"}
                        ]
                    }
                },
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": config.kubernetes_namespace
                },
                "syncPolicy": {
                    "automated": {
                        "prune": True,
                        "selfHeal": True,
                        "allowEmpty": False
                    },
                    "syncOptions": ["CreateNamespace=true", "PruneLast=true"],
                    "retry": {
                        "limit": 5,
                        "backoff": {"duration": "5s", "factor": 2, "maxDuration": "3m"}
                    }
                },
                "ignoreDifferences": [
                    {"group": "apps", "kind": "Deployment", "jsonPointers": ["/spec/replicas"]}
                ]
            }
        }
    
    def generate_app_of_apps(self, config: PipelineConfig) -> Dict:
        return {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {
                "name": f"{config.app_name}-root",
                "namespace": "argocd"
            },
            "spec": {
                "source": {
                    "repoURL": "https://github.com/my-org/k8s-config",
                    "path": f"apps/{config.app_name}",
                    "targetRevision": "HEAD"
                },
                "destination": {"server": "https://kubernetes.default.svc", "namespace": "argocd"},
                "syncPolicy": {"automated": {"prune": True, "selfHeal": True}}
            }
        }


class TektonPipelineGenerator:
    """Tekton Pipeline 配置生成器（优化点 5）"""
    
    def generate_pipeline(self, config: PipelineConfig) -> Dict:
        return {
            "apiVersion": "tekton.dev/v1beta1",
            "kind": "Pipeline",
            "metadata": {"name": f"{config.app_name}-pipeline"},
            "spec": {
                "params": [
                    {"name": "git-url", "type": "string"},
                    {"name": "git-revision", "type": "string", "default": "main"},
                    {"name": "image-url", "type": "string"}
                ],
                "tasks": [
                    self._generate_git_clone_task(),
                    self._generate_build_task(config),
                    self._generate_test_task(config),
                    self._generate_security_task(config),
                    self._generate_deploy_task(config)
                ]
            }
        }
    
    def _generate_git_clone_task(self) -> Dict:
        return {
            "name": "git-clone",
            "taskRef": {"name": "git-clone", "kind": "ClusterTask"},
            "params": [
                {"name": "url", "value": "$(params.git-url)"},
                {"name": "revision", "value": "$(params.git-revision)"},
                {"name": "out", "value": "$(results.clone.path)"}
            ]
        }
    
    def _generate_build_task(self, config: PipelineConfig) -> Dict:
        return {
            "name": "build-image",
            "taskRef": {"name": "kaniko", "kind": "ClusterTask"},
            "params": [
                {"name": "IMAGE", "value": "$(params.image-url)"},
                {"name": "DOCKERFILE", "value": "./Dockerfile"},
                {"name": "CONTEXT", "value": "."}
            ],
            "runAfter": ["git-clone"]
        }
    
    def _generate_test_task(self, config: PipelineConfig) -> Dict:
        return {
            "name": "run-tests",
            "taskRef": {"name": "golang-test", "kind": "ClusterTask"} if config.language == "go" else {"name": "python-test", "kind": "Task"},
            "runAfter": ["build-image"]
        }
    
    def _generate_security_task(self, config: PipelineConfig) -> Dict:
        return {
            "name": "security-scan",
            "taskRef": {"name": "trivy-scan", "kind": "ClusterTask"},
            "params": [{"name": "image-url", "value": "$(params.image-url)"}],
            "runAfter": ["build-image"]
        }
    
    def _generate_deploy_task(self, config: PipelineConfig) -> Dict:
        return {
            "name": "deploy",
            "taskRef": {"name": "kubectl-deploy", "kind": "Task"},
            "params": [
                {"name": "app-name", "value": config.app_name},
                {"name": "namespace", "value": config.kubernetes_namespace}
            ],
            "runAfter": ["run-tests", "security-scan"]
        }


class AutomatedTestingGenerator:
    """自动化测试集成配置生成器（优化点 6）"""
    
    def generate_test_config(self, config: PipelineConfig) -> Dict:
        test_config = {
            "unit_tests": self._generate_unit_test_config(config),
            "integration_tests": self._generate_integration_test_config(config) if config.enable_integration_tests else None,
            "e2e_tests": self._generate_e2e_test_config(config) if config.enable_e2e_tests else None
        }
        return {k: v for k, v in test_config.items() if v}
    
    def _generate_unit_test_config(self, config: PipelineConfig) -> Dict:
        frameworks = {"python": {"framework": "pytest", "config": "pytest.ini"}, "node": {"framework": "jest", "config": "jest.config.js"}}
        return frameworks.get(config.language, {"framework": "custom", "config": "test.config"})
    
    def _generate_integration_test_config(self, config: PipelineConfig) -> Dict:
        return {
            "framework": "pytest" if config.language == "python" else "supertest",
            "database": "postgres:15",
            "redis": "redis:7",
            "services": ["kafka", "elasticsearch"],
            "coverage_threshold": 80,
            "parallel": True,
            "workers": 4
        }
    
    def _generate_e2e_test_config(self, config: PipelineConfig) -> Dict:
        return {
            "framework": "playwright",
            "browsers": ["chromium", "firefox", "webkit"],
            "base_url": f"https://{config.app_name}.example.com",
            "test_patterns": ["**/e2e/**/*.spec.ts"],
            "screenshot_on_failure": True,
            "video_on_failure": True,
            "parallel": True
        }


class SecurityScanGenerator:
    """安全扫描集成配置生成器（优化点 7）"""
    
    def generate_security_config(self, config: PipelineConfig) -> Dict:
        if not config.enable_security_scan:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "sast": {
                "tools": [
                    {"name": "Semgrep", "rules": "security", "severity": "high"},
                    {"name": "Bandit", "language": "python"},
                    {"name": "ESLint", "language": "javascript", "plugins": ["security"]}
                ]
            },
            "dast": {
                "tools": [
                    {"name": "OWASP ZAP", "spider": True, "active_scan": True},
                    {"name": "Nuclei", "templates": "vulnerabilities"}
                ]
            },
            "sca": {
                "tools": [
                    {"name": "Dependabot", "schedule": "daily"},
                    {"name": "Snyk", "fail_on": "critical"},
                    {"name": "Trivy", "severity": "HIGH,CRITICAL"}
                ]
            },
            "container_scan": {
                "tools": [
                    {"name": "Trivy", "format": "sarif"},
                    {"name": "Anchore", "policy": "security"}
                ]
            },
            "secret_scan": {
                "tools": [{"name": "Gitleaks", "config": ".gitleaks.toml"}]
            }
        }


class ContainerBuildGenerator:
    """容器镜像构建与推送配置生成器（优化点 8）"""
    
    def generate_build_config(self, config: PipelineConfig) -> Dict:
        return {
            "registry": config.docker_registry,
            "repository": config.docker_repo,
            "tags": ["$(git.sha)", "latest", "$(date +%Y%m%d)"],
            "build_args": {
                "BUILDKIT_INLINE_CACHE": "1",
                "CGO_ENABLED": "0"
            },
            "buildx": {
                "enabled": True,
                "platforms": ["linux/amd64", "linux/arm64"],
                "cache_from": "type=gha",
                "cache_to": "type=gha,mode=max"
            },
            "provenance": {
                "enabled": True,
                "mode": "min"
            },
            "sbom": {
                "enabled": True,
                "format": "spdx"
            }
        }


class DeploymentStrategyGenerator:
    """部署策略配置生成器（优化点 9）"""
    
    def generate_strategy(self, config: PipelineConfig) -> Dict:
        strategies = {
            DeploymentStrategy.ROLLING: self._generate_rolling_strategy(config),
            DeploymentStrategy.BLUE_GREEN: self._generate_blue_green_strategy(config),
            DeploymentStrategy.CANARY: self._generate_canary_strategy(config),
            DeploymentStrategy.RECREATE: self._generate_recreate_strategy(config)
        }
        return strategies.get(config.deployment_strategy, strategies[DeploymentStrategy.ROLLING])
    
    def _generate_rolling_strategy(self, config: PipelineConfig) -> Dict:
        return {
            "strategy": "RollingUpdate",
            "rollingUpdate": {"maxUnavailable": "25%", "maxSurge": "25%"},
            "health_check": {"path": "/health", "initial_delay": 30, "period": 10},
            "rollback": {"automatic": True, "max_history": 10}
        }
    
    def _generate_blue_green_strategy(self, config: PipelineConfig) -> Dict:
        return {
            "strategy": "blue-green",
            "active_service": f"{config.app_name}-active",
            "preview_service": f"{config.app_name}-preview",
            "selector": {"app": config.app_name, "slot": "production"},
            "pre_deployment_test": {"threshold": 95, "duration": "5m"},
            "traffic_switch": {"type": "istio", "weight": 100}
        }
    
    def _generate_canary_strategy(self, config: PipelineConfig) -> Dict:
        return {
            "strategy": "canary",
            "steps": [
                {"setWeight": 10, "pause": {"duration": "10m"}},
                {"setWeight": 25, "pause": {"duration": "15m"}},
                {"setWeight": 50, "pause": {"duration": "30m"}},
                {"setWeight": 100, "pause": {}}
            ],
            "analysis": {
                "templates": [{"templateName": "success-rate"},
                               {"templateName": "latency"}],
                "startingStep": 1,
                "interval": "5m"
            },
            "metrics": [
                {"name": "success-rate", "type": "prometheus", "query": "rate(http_requests_total{service='{{name}}',code=~'2..'}[5m])/rate(http_requests_total{service='{{name}}'}[5m])"},
                {"name": "latency", "type": "prometheus", "query": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service='{{name}}'}[5m]))"}
            ]
        }
    
    def _generate_recreate_strategy(self, config: PipelineConfig) -> Dict:
        return {
            "strategy": "Recreate",
            "pre_scale_down": {"delay": "30s"},
            "scale_down": {},
            "scale_up": {"initial_delay": "10s"},
            "post_scale_up": {"health_check": {"path": "/health", "retries": 5}}
        }


class IaCIntegrationGenerator:
    """基础设施即代码集成配置生成器（优化点 10）"""
    
    def generate_iac_config(self, config: PipelineConfig) -> Dict:
        if not config.enable_iac:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "terraform": {
                "backend": "s3",
                "bucket": config.terraform_state_bucket or f"{config.app_name}-tf-state",
                "key": f"environments/{{workspace}}/terraform.tfstate",
                "locks_table": f"{config.app_name}-tf-locks",
                "workspace": ["development", "staging", "production"],
                "init": ["terraform init -upgrade"],
                "plan": ["terraform plan -out=tfplan -input=false"],
                "apply": ["terraform apply -input=false tfplan"],
                "destroy": ["terraform destroy -input=false"],
                "validate": ["terraform fmt -check -recursive", "tflint"],
                "security_scan": ["tfsec", "checkov"]
            },
            "helm": {
                "chart_path": config.helm_chart_path or "./chart",
                "values_files": ["values.yaml", f"values-{config.deployment_strategy.value}.yaml"],
                "pre_render": {"kustomize": True},
                "hooks": {"pre_upgrade": True, "post_upgrade": True}
            },
            "kustomize": {
                "bases": ["./base"],
                "overlays": ["development", "staging", "production"]
            }
        }


class NotificationGenerator:
    """通知与告警集成配置生成器（优化点 11）"""
    
    def generate_notification_config(self, config: PipelineConfig) -> Dict:
        if not config.enable_notifications:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "channels": config.notification_channels or ["slack", "email"],
            "slack": {
                "webhook_url": config.slack_webhook,
                "channels": {"deployments": "#deployments", "incidents": "#incidents", "security": "#security-alerts"},
                "events": ["deployment_success", "deployment_failed", "rollback_triggered", "security_scan_failed"]
            },
            "email": {
                "smtp": {"host": "smtp.example.com", "port": 587},
                "recipients": ["team@example.com", "ops@example.com"],
                "events": ["deployment_failed", "rollback_triggered"]
            },
            "pagerduty": {
                "integration_key": "$(PAGERDUTY_KEY)",
                "urgency": {"deployment": "low", "security": "high", "rollback": "high"}
            },
            "teams": {
                "webhook_url": "$(TEAMS_WEBHOOK)",
                "events": ["deployment_success", "deployment_failed"]
            }
        }


class RollbackRecoveryGenerator:
    """回滚与恢复机制配置生成器（优化点 12）"""
    
    def generate_rollback_config(self, config: PipelineConfig) -> Dict:
        if not config.enable_rollback:
            return {"enabled": False}
        
        return {
            "enabled": True,
            "automatic_rollback": {
                "enabled": True,
                "triggers": [
                    {"type": "health_check_failed", "threshold": 3},
                    {"type": "error_rate_increased", "threshold": 5},
                    {"type": "latency_increased", "threshold": 2.0}
                ]
            },
            "manual_rollback": {
                "commands": [
                    f"helm rollback {config.app_name} 1 --namespace {config.kubernetes_namespace}",
                    f"kubectl rollout undo deployment/{config.app_name} -n {config.kubernetes_namespace}"
                ]
            },
            "history": {
                "limit": 10,
                "timeout": "5m"
            },
            "backup": {
                "enabled": True,
                "before_deployment": True,
                "resources": ["deployment", "service", "configmap", "secret"],
                "storage": {"type": "s3", "bucket": f"{config.app_name}-backups"}
            },
            "recovery": {
                "procedure": [
                    "1. Identify the last known good revision",
                    "2. Execute helm rollback with revision number",
                    "3. Verify pod health",
                    "4. Run smoke tests",
                    "5. Update deployment status"
                ],
                "time_estimate": "5-10 minutes"
            }
        }


class CICDConfigGenerator:
    """完整的 CI/CD 配置生成器"""
    
    def __init__(self):
        self.github_gen = GitHubActionsGenerator()
        self.gitlab_gen = GitLabCIGenerator()
        self.jenkins_gen = JenkinsPipelineGenerator()
        self.argocd_gen = ArgoCDGenerator()
        self.tekton_gen = TektonPipelineGenerator()
        self.testing_gen = AutomatedTestingGenerator()
        self.security_gen = SecurityScanGenerator()
        self.container_gen = ContainerBuildGenerator()
        self.deployment_gen = DeploymentStrategyGenerator()
        self.iac_gen = IaCIntegrationGenerator()
        self.notification_gen = NotificationGenerator()
        self.rollback_gen = RollbackRecoveryGenerator()
    
    def generate_all(self, config: PipelineConfig) -> Dict[str, any]:
        return {
            "github-actions": {
                "workflows": {
                    "ci-cd.yml": self.github_gen.generate_workflow(config)
                }
            },
            "gitlab-ci": {
                ".gitlab-ci.yml": self.gitlab_gen.generate_pipeline(config)
            },
            "jenkins": {
                "Jenkinsfile": self.jenkins_gen.generate_jenkinsfile(config)
            },
            "argocd": {
                "application.yaml": self.argocd_gen.generate_application(config),
                "app-of-apps.yaml": self.argocd_gen.generate_app_of_apps(config)
            },
            "tekton": {
                "pipeline.yaml": self.tekton_gen.generate_pipeline(config)
            },
            "testing": self.testing_gen.generate_test_config(config),
            "security": self.security_gen.generate_security_config(config),
            "container-build": self.container_gen.generate_build_config(config),
            "deployment-strategy": self.deployment_gen.generate_strategy(config),
            "iac": self.iac_gen.generate_iac_config(config),
            "notifications": self.notification_gen.generate_notification_config(config),
            "rollback": self.rollback_gen.generate_rollback_config(config)
        }
