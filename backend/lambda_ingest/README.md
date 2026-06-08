# S3 Player Ingestion Lambda

This Lambda ingests `.json` or `.csv` player files from the Terraform-managed S3 bucket and upserts rows into the Pep.AI `players` table.

Supported JSON shapes:

```json
[
  {
    "id": "upload-1",
    "name": "Example Player",
    "position": "Center Back",
    "club": "Example FC",
    "nationality": "USA",
    "age": 22,
    "estimatedValue": "EUR 8m"
  }
]
```

or:

```json
{
  "players": []
}
```

Supported CSV columns:

```text
id,name,position,club,nationality,age,estimatedValue
```

Build the deployment zip from `backend/lambda_ingest`:

```powershell
python -m pip install -r requirements.txt -t package
Copy-Item handler.py package\
Compress-Archive -Path package\* -DestinationPath lambda_ingest.zip -Force
```

Then set `enable_s3_lambda_ingestion = true` and `lambda_ingest_zip_path` to the zip path in Terraform.
