#!/usr/bin/env python3

"""
Cloud Armor Enterprise Protected Resource Count Script
Counts resources that can be protected by Cloud Armor Enterprise

INSTRUCTIONS: 
Run this in Cloud Shell via `python3 protected_resource_count_by_project.py` 
The script will attempt to use the current project ID set in Cloud Shell. 
If no project ID is set, run the `gcloud config set project PROJECT_ID` command.
"""

import sys
from google.cloud import asset_v1

# Get current project
import subprocess
result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                       capture_output=True, text=True)
PROJECT_ID = result.stdout.strip()

if not PROJECT_ID:
    print("ERROR: No project is currently set.")
    print("Use 'gcloud config set project PROJECT_ID' to set one.")
    sys.exit(1)

print("=" * 50)
print("Cloud Armor Enterprise - Protected Resources")
print("=" * 50)
print(f"Project: {PROJECT_ID}")
print()

# ============================================
# COUNT PROTECTED RESOURCES
# ============================================

def count_assets(asset_type):
    """Count assets using Asset Inventory API"""
    client = asset_v1.AssetServiceClient()
    request = asset_v1.SearchAllResourcesRequest(
        scope=f"projects/{PROJECT_ID}",
        asset_types=[asset_type],
    )
    
    count = 0
    for resource in client.search_all_resources(request=request):
        count += 1
    return count

print("Counting Backend Services...")
backend_services = count_assets("compute.googleapis.com/BackendService")
print(f"  {backend_services} found")

print("Counting Backend Buckets...")
backend_buckets = count_assets("compute.googleapis.com/BackendBucket")
print(f"  {backend_buckets} found")

print("Counting Target Pools...")
target_pools = count_assets("compute.googleapis.com/TargetPool")
print(f"  {target_pools} found")

print("Counting Target Instances...")
target_instances = count_assets("compute.googleapis.com/TargetInstance")
print(f"  {target_instances} found")

print("Counting VMs with Public IPs...")
# For VMs we need to use gcloud since we need to filter by external IP
result = subprocess.run([
    'gcloud', 'compute', 'instances', 'list',
    f'--project={PROJECT_ID}',
    '--filter=networkInterfaces.accessConfigs[0].natIP:*',
    '--format=value(name)'
], capture_output=True, text=True)
vms_with_public_ips = len([line for line in result.stdout.strip().split('\n') if line])
print(f"  {vms_with_public_ips} found")

total_resources = backend_services + backend_buckets + target_pools + target_instances + vms_with_public_ips

# ============================================
# SUMMARY
# ============================================

print()
print("=" * 50)
print(f"Total Protected Resources: {total_resources}")
print("=" * 50)
print()
print("Note: For data processing costs, refer to your billing")
print("report for actual Cloud Armor data processing charges.")
print("=" * 50)
