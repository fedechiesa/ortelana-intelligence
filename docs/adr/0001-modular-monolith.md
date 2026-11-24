# ADR 0001: modular monolith and two orchestration layers

Status: accepted.

The supplied dataset is small, and the central problem is consistency across analysis, persistence and human decisions. A modular FastAPI application gives clear boundaries without premature microservices.

LangGraph owns typed internal analysis dependencies, parallel work, checkpointing and interruption. n8n owns external triggers and integration routing. FastAPI owns calculations and authorization. This avoids duplicated business policy and competing human-approval state machines.

Trade-off: synchronous API processing and one worker are sufficient here but not a throughput architecture. A durable worker queue is the appropriate next extension for larger datasets.
