# Paper-to-Product Mapping

## What the paper specifies clearly

The paper gives a strong high-level architecture:

- patient vitals should be monitored remotely
- ambient conditions should be monitored for safety
- a secured medicine box should log access attempts
- an IoT cloud server should collect data and produce alerts
- GSM and email should support notifications

## What the paper leaves open

Several implementation details are still incomplete in the paper:

- "Our Contributions" is marked "To be Written"
- "Data Handling and Transmission" is marked "To be written"
- evaluation tables contain placeholder values
- the paper does not define a concrete backend API or software module layout

## How this repository fills the gap

This codebase makes those implicit layers explicit:

- A typed REST API defines the cloud ingestion contract
- Persistent models define how devices, telemetry, alerts, and notification attempts are stored
- A rule engine translates raw sensor data into clinician-facing alerts
- A live dashboard visualizes the same data the paper says should be sent to cloud and mobile interfaces
- A simulator makes the repository demonstrable without the original hardware

## Scope note

This repository is best understood as a professional reference implementation of the paper's software platform. It is not a claim that the original authors used this exact code.
