# check_job_status

A tool for checking the status of asynchronous jobs.

**Functionality**

If a tool or API endpoint response includes a job id, this tool can be used to query for the progress of said job.
See https://developer.alation.com/dev/reference/jobs-apis for more details.

**Input Parameters**

- ` job_id ` (int): The identifier of the asychronous job.

**Returns**

- JSON-formatted response of the job details
