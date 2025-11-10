#!/usr/bin/env python3

"""
Cloud Armor Enterprise Protected Resource Count Script - ORGANIZATION LEVEL
Counts resources that can be protected by Cloud Armor Enterprise across an entire organization

INSTRUCTIONS: 
Run this in Cloud Shell via `python3 protected_resource_count_by_org.py ORG-ID`
E.g., `python3 protected_resource_count_by_org.py 123456789`

REQUIRED PERMISSIONS:
  At the organization level, you need:
  - cloudasset.assets.searchAllResources
  - cloudasset.assets.listAssets
  - resourcemanager.organizations.get (optional)

RECOMMENDED IAM ROLE:
  roles/cloudasset.viewer (Cloud Asset Viewer)
"""

import sys
import json
from google.cloud import asset_v1

def print_usage():
    print("Usage: ./pr_org.py <ORGANIZATION_ID>")
    print("Example: ./pr_org.py 123456789012")
    print()
    print("To find your org ID, run: gcloud organizations list")
    sys.exit(1)

# Get organization ID from command line
if len(sys.argv) != 2:
    print("ERROR: Organization ID is required")
    print_usage()

ORG_ID = sys.argv[1]

# Validate org ID format (should be numeric)
if not ORG_ID.isdigit():
    print(f"ERROR: Invalid organization ID: {ORG_ID}")
    print("Organization ID should be numeric (e.g., 123456789012)")
    print_usage()

print("=" * 60)
print("Cloud Armor Enterprise - Protected Resources (Organization)")
print("=" * 60)
print(f"Organization ID: {ORG_ID}")
print()

# ============================================
# COUNT PROTECTED RESOURCES
# ============================================

def count_assets(asset_type):
    """Count assets using Asset Inventory API"""
    client = asset_v1.AssetServiceClient()
    request = asset_v1.SearchAllResourcesRequest(
        scope=f"organizations/{ORG_ID}",
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
print("  (This may take a while for large organizations...)")

# The Asset Search API doesn't provide detailed network config
# We need to use the full Asset API with read_mask to get network details
from google.cloud.asset_v1 import ContentType

client = asset_v1.AssetServiceClient()

# List all VM assets with full resource data
parent = f"organizations/{ORG_ID}"
content_type = ContentType.RESOURCE

vms_with_public_ips = 0
total_vms_checked = 0

# Use ListAssets instead of SearchAllResources to get full resource data
request = asset_v1.ListAssetsRequest(
    parent=parent,
    asset_types=["compute.googleapis.com/Instance"],
    content_type=content_type,
)

page_result = client.list_assets(request=request)

for asset in page_result:
    total_vms_checked += 1

    # Check if resource has network interfaces with external IPs
    if asset.resource and asset.resource.data:
        resource_data = dict(asset.resource.data)
        network_interfaces = resource_data.get('networkInterfaces', [])

        has_external_ip = False
        for interface in network_interfaces:
            access_configs = interface.get('accessConfigs', [])
            for config in access_configs:
                # Check for natIP (external IP)
                if config.get('natIP'):
                    has_external_ip = True
                    break
            if has_external_ip:
                break

        if has_external_ip:
            vms_with_public_ips += 1

print(f"  {vms_with_public_ips} found (out of {total_vms_checked} total VMs)")

total_resources = backend_services + backend_buckets + target_pools + target_instances + vms_with_public_ips

# ============================================
# SUMMARY
# ============================================

print()
print("=" * 60)
print("SUMMARY BY RESOURCE TYPE")
print("=" * 60)
print(f"Backend Services:       {backend_services:>6}")
print(f"Backend Buckets:        {backend_buckets:>6}")
print(f"Target Pools:           {target_pools:>6}")
print(f"Target Instances:       {target_instances:>6}")
print(f"VMs with Public IPs:    {vms_with_public_ips:>6}")
print("-" * 60)
print(f"TOTAL:                  {total_resources:>6}")
print("=" * 60)
print()
print("Notes:")
print("- Requires 'cloudasset.assets.searchAllResources' permission at org level")
print("- For data processing costs, refer to your billing report")
print("- VM counting may take several minutes for large organizations")
print("=" * 60)
