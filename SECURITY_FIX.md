# Security Fix: Hardcoded AWS Credentials Removal

## Issue
Both `insecure-app.yaml` and `workload-security-evaluator.yaml` contained hardcoded AWS credentials as plaintext environment variable values. This exposed the credentials to:
- Anyone with repository access
- Anyone able to read Kubernetes Deployment specifications
- Any compromised process within the pods
- Version control history

## Changes Made

### 1. Created aws-credentials-secret.yaml
- Defines Kubernetes Secret resources for both namespaces
- Contains placeholder values with instructions for proper credential management
- Includes comments recommending modern alternatives (IRSA, Workload Identity, External Secrets Operator)

### 2. Updated insecure-app.yaml
- Replaced hardcoded `value` fields with `valueFrom.secretKeyRef` references
- AWS_ACCESS_KEY_ID now references secret key `aws-access-key-id`
- AWS_SECRET_ACCESS_KEY now references secret key `aws-secret-access-key`

### 3. Updated workload-security-evaluator.yaml
- Applied identical changes as insecure-app.yaml
- Both deployments now reference the `aws-credentials` Secret in their respective namespaces

### 4. Updated README.md
- Added step 2 in deployment instructions for creating AWS credentials secrets
- Updated configuration issues description to reflect Secret-based credential management

## Security Improvements

1. **Credentials removed from version control**: No plaintext credentials in repository
2. **Separation of concerns**: Credentials managed independently from deployment configuration
3. **Access control**: Kubernetes RBAC can control who can read Secrets
4. **Rotation capability**: Credentials can be rotated without modifying Deployment manifests
5. **Audit trail**: Secret access can be monitored separately

## Deployment Requirements

Operators must now create the `aws-credentials` Secret in both namespaces before deploying:

```bash
kubectl create secret generic aws-credentials \
  --from-literal=aws-access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=aws-secret-access-key=YOUR_SECRET_ACCESS_KEY \
  -n insecure-app

kubectl create secret generic aws-credentials \
  --from-literal=aws-access-key-id=YOUR_ACCESS_KEY_ID \
  --from-literal=aws-secret-access-key=YOUR_SECRET_ACCESS_KEY \
  -n workload-security-evaluator
```

## Recommendations for Production

For production environments, consider:
- AWS IAM Roles for Service Accounts (IRSA) for EKS clusters
- Workload Identity for GKE clusters
- External Secrets Operator with AWS Secrets Manager or Parameter Store
- HashiCorp Vault integration
- Avoid long-lived static credentials when possible
