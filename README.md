# cloud-armor-tools
A collection of helpful scripts to make lives easier (WIP)

* [protected_resource_count_by_project.py](https://github.com/mikehansen20/cloud-armor-tools/blob/main/protected_resource_count_by_project.py) - Quickly find the amount of potential Protected Resources that Cloud Armor Enterprise would cover.
  * How to run: `python3 protected_resource_count_by_project.py`
  * Uses the current project set in Cloud Shell. If no project is set, run `gcloud config set project PROJECT_ID` first and set your project ID.
* [protected_resource_count_by_org.py](https://github.com/mikehansen20/cloud-armor-tools/blob/main/protected_resource_count_by_org.py) - Counts Protected Resources across all projects within an Organization.
  * How to run: `python3 protected_resource_count_by_project.py ORG_ID`
  * E.g., `python3 protected_resource_count_by_project.py 1234567890`
  * Requires org-level permissions to run (see script instructions at the top for details)
