# cloud-armor-tools
A collection of helpful scripts to make lives easier (WIP)

* [protected_resource_count_by_project.sh](https://github.com/mikehansen20/cloud-armor-tools/blob/main/protected_resource_count_by_project.sh) - Quickly find the amount of potential Protected Resources that Cloud Armor Enterprise would cover at the project level across multiple projects.
  * How to run:
    * Pass in space-separated project-ID's as a one-liner
      * `bash protected_resource_count_by_project.sh project-id-1 project-id-2`
    * Have the script read from a text file with project-IDs separated by new lines:
      * `bash protected_resource_count_by_project.sh -f project_list.txt`
        
* [protected_resource_count_by_org.py](https://github.com/mikehansen20/cloud-armor-tools/blob/main/protected_resource_count_by_org.py) - Counts Protected Resources across all projects within an Organization.
  * How to run: `python3 protected_resource_count_by_project.py ORG_ID`
  * E.g., `python3 protected_resource_count_by_project.py 1234567890`
  * Requires org-level permissions to run (see script instructions at the top for details)
