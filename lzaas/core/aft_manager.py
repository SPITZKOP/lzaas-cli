"""
AFT Manager - Core AWS Account Factory operations
Handles DynamoDB operations, GitHub integration, and AFT pipeline management
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
import yaml
from botocore.exceptions import ClientError, NoCredentialsError

from lzaas.core.models import AccountRequest, AFTStatus


class AFTManager:
    """Manages AFT operations and DynamoDB interactions"""

    def __init__(self, profile: str = "default", region: str = "eu-west-3"):
        self.profile = profile
        self.region = region
        self.table_name = "lzaas-account-requests"

        # Initialize AWS clients
        try:
            session = boto3.Session(profile_name=profile, region_name=region)
            self.dynamodb = session.resource("dynamodb")
            self.codepipeline = session.client("codepipeline")
            self.stepfunctions = session.client("stepfunctions")
            self.s3 = session.client("s3")
        except (NoCredentialsError, ClientError) as e:
            raise Exception(f"AWS authentication failed: {str(e)}")

    def _get_table(self):
        """Get or create DynamoDB table"""
        try:
            table = self.dynamodb.Table(self.table_name)
            # Test table access
            table.load()
            return table
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                # Table doesn't exist, create it
                return self._create_table()
            else:
                raise Exception(f"DynamoDB error: {str(e)}")

    def _create_table(self):
        """Create DynamoDB table for account requests"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[{"AttributeName": "request_id", "KeyType": "HASH"}],
                AttributeDefinitions=[
                    {"AttributeName": "request_id", "AttributeType": "S"},
                    {"AttributeName": "client_id", "AttributeType": "S"},
                    {"AttributeName": "status", "AttributeType": "S"},
                ],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "client-status-index",
                        "KeySchema": [
                            {"AttributeName": "client_id", "KeyType": "HASH"},
                            {"AttributeName": "status", "KeyType": "RANGE"},
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "BillingMode": "PAY_PER_REQUEST",
                    }
                ],
                BillingMode="PAY_PER_REQUEST",
            )

            # Wait for table to be created
            table.wait_until_exists()
            return table

        except ClientError as e:
            raise Exception(f"Failed to create DynamoDB table: {str(e)}")

    def create_account_request(self, account_request: AccountRequest) -> Dict[str, Any]:
        """Create a new account request"""
        try:
            table = self._get_table()

            # Store in DynamoDB
            table.put_item(Item=account_request.to_dict())

            # TODO: Create GitHub repository files for AFT
            # This would involve:
            # 1. Creating account request YAML file
            # 2. Committing to aft-account-request repository
            # 3. Triggering AFT pipeline

            return {
                "success": True,
                "request_id": account_request.request_id,
                "message": "Account request created successfully",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_account_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get account request by ID"""
        try:
            table = self._get_table()
            response = table.get_item(Key={"request_id": request_id})
            return response.get("Item")
        except Exception as e:
            raise Exception(f"Failed to get account request: {str(e)}")

    def list_account_requests(
        self,
        client_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """List account requests with optional filters"""
        try:
            table = self._get_table()

            if client_id and status:
                # Use GSI for client_id and status filter
                response = table.query(
                    IndexName="client-status-index",
                    KeyConditionExpression="client_id = :client_id AND #status = :status",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":client_id": client_id,
                        ":status": status,
                    },
                    Limit=limit,
                )
                return response.get("Items", [])
            elif client_id:
                # Use GSI for client_id filter only
                response = table.query(
                    IndexName="client-status-index",
                    KeyConditionExpression="client_id = :client_id",
                    ExpressionAttributeValues={":client_id": client_id},
                    Limit=limit,
                )
                return response.get("Items", [])
            else:
                # Scan table (less efficient but works for all cases)
                scan_kwargs = {"Limit": limit}

                if status:
                    scan_kwargs["FilterExpression"] = "#status = :status"
                    scan_kwargs["ExpressionAttributeNames"] = {"#status": "status"}
                    scan_kwargs["ExpressionAttributeValues"] = {":status": status}

                response = table.scan(**scan_kwargs)
                return response.get("Items", [])

        except Exception as e:
            raise Exception(f"Failed to list account requests: {str(e)}")

    def update_account_request(
        self, request_id: str, updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update account request"""
        try:
            table = self._get_table()

            # Add updated timestamp
            updates["updated_date"] = datetime.utcnow().isoformat()

            # Build update expression
            update_expression: str = "SET "
            expression_values: Dict[str, Any] = {}
            expression_names: Dict[str, str] = {}

            for key, value in updates.items():
                if key == "status":
                    # Status is a reserved word in DynamoDB
                    update_expression += "#status = :status, "
                    expression_names["#status"] = "status"
                    expression_values[":status"] = value
                else:
                    update_expression += f"{key} = :{key}, "
                    expression_values[f":{key}"] = value

            # Remove trailing comma and space
            update_expression = update_expression.rstrip(", ")

            kwargs = {
                "Key": {"request_id": request_id},
                "UpdateExpression": update_expression,
                "ExpressionAttributeValues": expression_values,
                "ReturnValues": "ALL_NEW",
            }

            if expression_names:
                kwargs["ExpressionAttributeNames"] = expression_names

            response = table.update_item(**kwargs)

            return {"success": True, "updated_item": response.get("Attributes")}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def delete_account_request(self, request_id: str) -> Dict[str, Any]:
        """Delete account request"""
        try:
            table = self._get_table()
            table.delete_item(Key={"request_id": request_id})

            return {"success": True, "message": f"Account request {request_id} deleted"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_aft_status(self, request_id: str) -> Optional[AFTStatus]:
        """Get AFT pipeline status for a request"""
        try:
            # This would query AFT's DynamoDB tables or Step Functions
            # For now, return mock status based on our request
            request = self.get_account_request(request_id)
            if not request:
                return None

            # Mock AFT status - in real implementation, this would query AFT resources
            return AFTStatus(
                request_id=request_id,
                pipeline_status=str(request.get("status", "unknown")),
                account_id=(
                    str(request.get("account_id"))
                    if request.get("account_id")
                    else None
                ),
                last_updated=(
                    str(request.get("updated_date"))
                    if request.get("updated_date")
                    else None
                ),
            )

        except Exception as e:
            raise Exception(f"Failed to get AFT status: {str(e)}")

    def create_aft_repository_files(
        self, account_request: AccountRequest
    ) -> Dict[str, Any]:
        """Create AFT repository files for account request"""
        try:
            # Generate AFT-compatible YAML
            aft_request = account_request.to_aft_request()

            # Create account request file content
            account_file_content = yaml.dump(aft_request, default_flow_style=False)

            # TODO: Implement GitHub API integration to:
            # 1. Create/update file in aft-account-request repository
            # 2. Commit changes
            # 3. Trigger AFT pipeline

            return {
                "success": True,
                "file_content": account_file_content,
                "message": "AFT repository files prepared (GitHub integration pending)",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def list_aft_pipelines(self) -> List[Dict[str, Any]]:
        """List AFT CodePipeline executions"""
        try:
            # Get AFT-related pipelines
            pipelines = []

            response = self.codepipeline.list_pipelines()
            for pipeline in response.get("pipelines", []):
                pipeline_name = pipeline["name"]
                if "aft" in pipeline_name.lower():
                    # Get pipeline execution history
                    executions = self.codepipeline.list_pipeline_executions(
                        pipelineName=pipeline_name, maxResults=5
                    )

                    pipelines.append(
                        {
                            "name": pipeline_name,
                            "executions": executions.get(
                                "pipelineExecutionSummaries", []
                            ),
                        }
                    )

            return pipelines

        except Exception as e:
            raise Exception(f"Failed to list AFT pipelines: {str(e)}")
