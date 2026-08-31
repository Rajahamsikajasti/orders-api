# Serverless E-Commerce Order API

A serverless order management API built with **AWS Lambda (Python 3.12)**,
**Amazon API Gateway**, and **Amazon DynamoDB**, deployed with the **AWS SAM**
(Serverless Application Model) CLI.

## Architecture

```
                 ┌────────────────┐
   HTTPS  ─────► │  API Gateway    │
                 │  (REST API)     │
                 └───────┬─────────┘
                         │
        ┌────────────────┼─────────────────┐
        ▼                ▼                 ▼
 ┌─────────────┐  ┌───────────────┐  ┌─────────────────┐
 │ create_order │  │  get_orders   │  │ update_status    │
 │  (Lambda)    │  │   (Lambda)    │  │   (Lambda)       │
 └──────┬───────┘  └───────┬───────┘  └────────┬─────────┘
        │                  │                   │
        └──────────────────┼───────────────────┘
                            ▼
                  ┌───────────────────┐
                  │   DynamoDB Table   │
                  │  PK: CustomerId    │
                  │  SK: OrderId       │
                  │  GSI: OrderIndex   │
                  └───────────────────┘
```

### DynamoDB key design

| Attribute | Role | Example |
|---|---|---|
| `PK` | Partition key | `CUSTOMER#cust-123` |
| `SK` | Sort key | `ORDER#3f2a...` |
| `OrderId` | GSI (`OrderIndex`) hash key | `3f2a...` |

Storing `CustomerId` as the partition key means "all orders for a customer"
is a single, efficient `Query` on the partition key — no table scan
required. The `OrderIndex` GSI keeps direct order-id lookups available for
future endpoints without needing the customer id up front.

## Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/orders` | Create a new order |
| `GET` | `/orders/{customerId}` | List all orders for a customer (supports `?status=`, `?limit=`, `?nextToken=`) |
| `GET` | `/orders/{customerId}/{orderId}` | Get a single order |
| `PUT` | `/orders/{customerId}/{orderId}` | Update an order's status |

### Create an order

```bash
curl -X POST "$API_URL/orders" \
  -H "Content-Type: application/json" \
  -d '{
        "customerId": "cust-123",
        "items": [
          {"sku": "SKU-1", "name": "Widget", "quantity": 2, "price": 9.99}
        ],
        "shippingAddress": {
          "line1": "123 Main St", "city": "Franklin", "state": "TN", "zip": "37064"
        }
      }'
```

Response `201`:

```json
{
  "orderId": "3f2a1c4e-...",
  "customerId": "cust-123",
  "status": "PENDING",
  "totalAmount": 19.98,
  "createdAt": "2026-08-30T12:00:00+00:00",
  "updatedAt": "2026-08-30T12:00:00+00:00",
  "items": [{"sku": "SKU-1", "name": "Widget", "quantity": 2, "price": 9.99}],
  "shippingAddress": {"line1": "123 Main St", "city": "Franklin", "state": "TN", "zip": "37064"}
}
```

### List a customer's orders

```bash
curl "$API_URL/orders/cust-123?status=PENDING&limit=10"
```

### Get a single order

```bash
curl "$API_URL/orders/cust-123/3f2a1c4e-..."
```

### Update order status

```bash
curl -X PUT "$API_URL/orders/cust-123/3f2a1c4e-..." \
  -H "Content-Type: application/json" \
  -d '{"status": "SHIPPED"}'
```

Valid status values: `PENDING`, `CONFIRMED`, `PROCESSING`, `SHIPPED`,
`DELIVERED`, `CANCELLED`.

## Project structure

```
order-api/
├── template.yaml              # SAM/CloudFormation template
├── samconfig.toml             # SAM CLI deploy defaults
├── requirements.txt           # Runtime deps (boto3)
├── requirements-dev.txt       # Test deps (pytest, moto)
├── src/
│   ├── common/
│   │   ├── db.py              # DynamoDB table/key helpers
│   │   └── utils.py           # HTTP responses, JSON encoding, validation
│   └── handlers/
│       ├── create_order.py    # POST /orders
│       ├── get_orders.py      # GET /orders/{customerId}[/{orderId}]
│       └── update_status.py   # PUT /orders/{customerId}/{orderId}
├── events/                    # Sample events for `sam local invoke`
├── tests/                     # pytest unit tests (mocked DynamoDB via moto)
└── terraform/                 # Terraform equivalent of template.yaml (see below)
    ├── versions.tf
    ├── variables.tf
    ├── dynamodb.tf
    ├── iam.tf
    ├── lambda.tf
    ├── api_gateway.tf
    ├── cors.tf
    ├── outputs.tf
    └── terraform.tfvars.example
```

## Prerequisites

- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), configured with credentials (`aws configure`)
- [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)
- [Docker](https://www.docker.com/) (only needed for `sam local` commands)
- Python 3.12

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Run the unit tests

Tests mock DynamoDB with `moto`, so no AWS account or network access is
required:

```bash
pytest -v
```

## Run a function locally (requires Docker + SAM CLI)

```bash
sam build
sam local invoke CreateOrderFunction --event events/create_order_event.json
sam local invoke GetOrdersByCustomerFunction --event events/get_orders_event.json
sam local invoke UpdateOrderStatusFunction --event events/update_status_event.json
```

Or run the whole API locally on `http://127.0.0.1:3000`:

```bash
sam local start-api
```

## Deploy to AWS

```bash
sam build
sam deploy --guided   # first time: walks through stack name, region, etc.
# subsequent deploys:
sam deploy
```

After deploy, SAM prints the `ApiUrl` output — the base URL for the
endpoints above.

## Tear down

```bash
sam delete
```

## Alternative: deploy with Terraform instead of SAM

A Terraform equivalent of `template.yaml` lives in `terraform/`. It deploys
the exact same architecture (API Gateway REST API, 3 Lambda functions, the
DynamoDB table + GSI, IAM role/policy, CloudWatch log groups, and CORS)
without requiring the SAM CLI. Both point at the same `src/` code — use
one or the other, not both, for a given deployment.

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

Terraform zips `src/` itself via the `archive_file` data source, so there's
no separate build step. Customize the deployment by copying
`terraform.tfvars.example` to `terraform.tfvars` and editing values
(region, project name, stage name, memory/timeout, tags).

After `apply`, the `api_url` output is the base URL for the same endpoints
documented above.

Tear down with:

```bash
terraform destroy
```

See `terraform/*.tf` for the full resource breakdown — each file is
scoped to one concern (`dynamodb.tf`, `iam.tf`, `lambda.tf`,
`api_gateway.tf`, `cors.tf`, `outputs.tf`).

## Notes / production hardening ideas

- Add authentication/authorization (Amazon Cognito authorizer or a custom
  Lambda authorizer on API Gateway) — this project ships with open endpoints
  for simplicity.
- Add request validation at the API Gateway layer (JSON Schema models) in
  addition to the in-Lambda validation already present.
- Add an idempotency key on order creation to safely handle client retries.
- Wire up CloudWatch Alarms on Lambda errors/throttles and DynamoDB
  throttled requests.
- Consider DynamoDB Streams + a downstream Lambda for order-event
  side effects (emails, inventory decrement, etc.).
