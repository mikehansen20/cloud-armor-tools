#!/bin/bash

# Initialize grand totals
GRAND_BACKEND_SERVICES=0
GRAND_BACKEND_BUCKETS=0
GRAND_TARGET_POOLS=0
GRAND_TARGET_INSTANCES=0
GRAND_VMS_PUBLIC_IPS=0
GRAND_TOTAL=0
PROJECT_COUNT=0
FAILED_PROJECTS=0

# Function to check if Cloud Asset API is enabled and accessible
check_api_access() {
  local PROJECT_ID=$1
  local temp_error=$(mktemp)
  
  # Try a simple Asset API call to test access
  gcloud asset search-all-resources \
    --scope=projects/$PROJECT_ID \
    --asset-types=compute.googleapis.com/BackendService \
    --page-size=1 \
    --format="value(name)" 2>"$temp_error" >/dev/null
  
  local exit_code=$?
  local error_msg=$(cat "$temp_error")
  rm -f "$temp_error"
  
  # Check for common errors
  if [ $exit_code -ne 0 ]; then
    if echo "$error_msg" | grep -q "Cloud Asset API has not been used"; then
      echo "ERROR: Cloud Asset API is not enabled for project $PROJECT_ID"
      echo "Enable it with: gcloud services enable cloudasset.googleapis.com --project=$PROJECT_ID"
      return 1
    elif echo "$error_msg" | grep -q "PERMISSION_DENIED"; then
      echo "ERROR: Permission denied for project $PROJECT_ID"
      echo "Required permissions: cloudasset.assets.searchAllResources or roles/cloudasset.viewer"
      return 1
    elif echo "$error_msg" | grep -q "NOT_FOUND\|does not exist"; then
      echo "ERROR: Project $PROJECT_ID not found or does not exist"
      return 1
    elif echo "$error_msg" | grep -q "UNAUTHENTICATED"; then
      echo "ERROR: Not authenticated. Run: gcloud auth login"
      return 1
    else
      echo "ERROR: Unable to access Cloud Asset API for project $PROJECT_ID"
      echo "Error details: $error_msg"
      return 1
    fi
  fi
  
  return 0
}

# Function to count resources for a single project
count_resources() {
  local PROJECT_ID=$1
  
  echo "========================================"
  echo "=== Cloud Armor Protected Resources ==="
  echo "=== Project: $PROJECT_ID"
  echo "========================================"
  echo ""
  
  # Check API access first
  if ! check_api_access "$PROJECT_ID"; then
    echo ""
    FAILED_PROJECTS=$((FAILED_PROJECTS + 1))
    return 1
  fi

  # 1. Backend Services
  echo "Backend Services:"
  backend_services=$(gcloud asset search-all-resources \
    --scope=projects/$PROJECT_ID \
    --asset-types=compute.googleapis.com/BackendService \
    --format="value(name)" 2>/dev/null | wc -l)
  echo "  Total: $backend_services"
  GRAND_BACKEND_SERVICES=$((GRAND_BACKEND_SERVICES + backend_services))

  # 2. Backend Buckets
  echo "Backend Buckets:"
  backend_buckets=$(gcloud asset search-all-resources \
    --scope=projects/$PROJECT_ID \
    --asset-types=compute.googleapis.com/BackendBucket \
    --format="value(name)" 2>/dev/null | wc -l)
  echo "  Total: $backend_buckets"
  GRAND_BACKEND_BUCKETS=$((GRAND_BACKEND_BUCKETS + backend_buckets))

  # 3. Target Pools
  echo "Target Pools:"
  target_pools=$(gcloud asset search-all-resources \
    --scope=projects/$PROJECT_ID \
    --asset-types=compute.googleapis.com/TargetPool \
    --format="value(name)" 2>/dev/null | wc -l)
  echo "  Total: $target_pools"
  GRAND_TARGET_POOLS=$((GRAND_TARGET_POOLS + target_pools))

  # 4. Target Instances
  echo "Target Instances:"
  target_instances=$(gcloud asset search-all-resources \
    --scope=projects/$PROJECT_ID \
    --asset-types=compute.googleapis.com/TargetInstance \
    --format="value(name)" 2>/dev/null | wc -l)
  echo "  Total: $target_instances"
  GRAND_TARGET_INSTANCES=$((GRAND_TARGET_INSTANCES + target_instances))

  # 5. VMs with External IPs
  echo "VMs with Public IPs:"
  vms_with_public_ips=$(gcloud compute instances list \
    --project=$PROJECT_ID \
    --filter="networkInterfaces.accessConfigs[0].natIP:*" \
    --format="value(name)" 2>/dev/null | wc -l)
  echo "  Total: $vms_with_public_ips"
  GRAND_VMS_PUBLIC_IPS=$((GRAND_VMS_PUBLIC_IPS + vms_with_public_ips))

  # Calculate total for this project
  total=$((backend_services + backend_buckets + target_pools + target_instances + vms_with_public_ips))
  GRAND_TOTAL=$((GRAND_TOTAL + total))
  PROJECT_COUNT=$((PROJECT_COUNT + 1))
  
  echo ""
  echo "=== TOTAL PROTECTED RESOURCES: $total ==="
  echo ""
}

# Function to display grand totals
display_grand_totals() {
  if [ $PROJECT_COUNT -gt 1 ]; then
    echo ""
    echo "========================================"
    echo "===   GRAND TOTAL ACROSS ALL PROJECTS   ==="
    echo "========================================"
    echo "Projects Analyzed: $PROJECT_COUNT"
    if [ $FAILED_PROJECTS -gt 0 ]; then
      echo "Projects Failed: $FAILED_PROJECTS"
    fi
    echo ""
    echo "Backend Services: $GRAND_BACKEND_SERVICES"
    echo "Backend Buckets: $GRAND_BACKEND_BUCKETS"
    echo "Target Pools: $GRAND_TARGET_POOLS"
    echo "Target Instances: $GRAND_TARGET_INSTANCES"
    echo "VMs with Public IPs: $GRAND_VMS_PUBLIC_IPS"
    echo ""
    echo "========================================="
    echo "=== GRAND TOTAL PROTECTED RESOURCES: $GRAND_TOTAL ==="
    echo "========================================="
  elif [ $FAILED_PROJECTS -gt 0 ]; then
    echo ""
    echo "Script completed with errors. See messages above."
  fi
}

# Main script
if [ $# -eq 0 ]; then
  # No arguments provided, use current project
  PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
  if [ -z "$PROJECT_ID" ]; then
    echo "Error: No project ID specified and no default project configured."
    echo "Usage: $0 [PROJECT_ID1 PROJECT_ID2 ...] or $0 -f PROJECT_LIST_FILE"
    exit 1
  fi
  count_resources "$PROJECT_ID"
elif [ "$1" == "-f" ]; then
  # Read from file
  if [ -z "$2" ]; then
    echo "Error: Please specify a file containing project IDs"
    echo "Usage: $0 -f PROJECT_LIST_FILE"
    exit 1
  fi
  
  if [ ! -f "$2" ]; then
    echo "Error: File $2 not found"
    exit 1
  fi
  
  while IFS= read -r project || [ -n "$project" ]; do
    # Skip empty lines and comments
    [[ -z "$project" || "$project" =~ ^[[:space:]]*# ]] && continue
    count_resources "$project"
  done < "$2"
else
  # Process command line arguments
  for project in "$@"; do
    count_resources "$project"
  done
fi

# Display grand totals if multiple projects were processed
display_grand_totals

# Exit with error code if any projects failed
if [ $FAILED_PROJECTS -gt 0 ]; then
  exit 1
fi