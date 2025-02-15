# Brand Graph Crew: Agentic Flow Overview

This project leverages an agentic architecture to build a complete pipeline for gathering and processing brand information. The pipeline is structured around multiple specialized agents and tasks that work together seamlessly to produce enriched brand data. This document explains the roles of each agent, how tasks are defined, and the overall workflow.

## Overview

The pipeline is designed using CrewAI’s framework where individual agents perform well-defined responsibilities. The agents are coordinated by tasks and an overall crew structure, which determines the flow based on the input mode. There are two primary modes:

- **Category Mode:** Discover a list of brands from a given category and product type.
- **Brand Mode:** Directly process a specific brand to extract detailed information.

The flow ensures that each brand is thoroughly enriched through attribute extraction and variation generation before being processed further by subsequent systems.

## Agents

The pipeline is built on three core agents:

### 1. Brand Discovery Agent

**Purpose:**  
The Brand Discovery Agent is responsible for searching online for relevant brand names based on a provided category and product type. Its goal is to produce a clean list of brand names with minimal noise.

**Key Characteristics:**

- **Goal:**  
  It receives inputs such as a category (e.g., "Footwear") and product type (e.g., "Running Shoes") and is instructed to output a JSON array of brand names, each on a new line.
  
- **Backstory:**  
  Designed as an expert researcher, this agent is adept at scanning various online sources and identifying potential brand names using heuristic rules or LLM-generated insights.
  
- **Operation:**  
  The agent uses an LLM prompt with clear instructions to avoid extra commentary and produce strictly JSON output.

### 2. Attribute Extraction Agent

**Purpose:**  
For any given brand and product type, the Attribute Extraction Agent gathers product-specific attributes. This includes information such as available colors, sizes, or other relevant characteristics.

**Key Characteristics:**

- **Goal:**  
  The agent is prompted with the brand name and product type, and it must extract detailed attributes in a structured JSON format (e.g., `{"Color": ["Red", "Blue"], "Size": ["8", "9", "10"]}`).
  
- **Backstory:**  
  This agent is built to be an expert in data extraction—scraping and summarizing detailed product information from various online sources.
  
- **Operation:**  
  It is instructed to return only the required information in JSON, ensuring that no extraneous text is included. This guarantees that downstream tasks can reliably parse the output.

### 3. Brand Variation Agent

**Purpose:**  
The Brand Variation Agent generates alternative versions of a brand’s name, including potential misspellings or knock-off variations. This is crucial for scenarios where slight variations might indicate counterfeit or alias names.

**Key Characteristics:**

- **Goal:**  
  Given a brand name, the agent is tasked with generating a list of variations. The output should be a strict JSON array (e.g., `["BrandX", "Br4ndX"]`).
  
- **Backstory:**  
  With a keen eye for detail, this agent leverages LLM capabilities to detect subtle changes in brand naming that could be important for further analysis.
  
- **Operation:**  
  The agent is provided with clear prompt instructions to ensure that the output is strictly in JSON format without additional commentary.

## Tasks

Each agent is associated with a task that formalizes the instructions and expected output. The tasks are defined with explicit instructions and sample outputs:

- **Brand Discovery Task:**  
  Uses the Brand Discovery Agent to search for brands based on category and product type. It demands a JSON array of brand names.
  
- **Attribute Extraction Task:**  
  Uses the Attribute Extraction Agent to extract product-specific attributes for a given brand. The expected output is a JSON object mapping attribute names to arrays of possible values.
  
- **Variation Generation Task:**  
  Uses the Brand Variation Agent to generate a list of name variations for a given brand. It expects a JSON array as output.

Each task is designed to provide a clear, structured response that downstream processes can consume without additional processing.

## Agentic Workflow

The overall crew is orchestrated based on the input mode:

- **In Category Mode:**  
  1. The **Brand Discovery Task** is executed first to produce a list of brand names.
  2. After this task completes, the workflow dynamically iterates over each discovered brand.  
     For each brand:
     - The **Attribute Extraction Task** is invoked with that brand and its associated product type.
     - The **Variation Generation Task** is similarly invoked to produce possible name variations.
  3. The outputs from these tasks provide enriched brand data for subsequent processing.

- **In Brand Mode:**  
  The pipeline directly runs the **Attribute Extraction Task** and **Variation Generation Task** for the provided brand, bypassing the discovery phase.

The agents are coordinated in a sequential process, ensuring that each step’s output informs the next. This modular approach allows for easy updates to individual agents or tasks without affecting the overall flow.

## Conclusion

This agentic architecture demonstrates a robust and modular approach to collecting and processing brand data. By defining clear responsibilities for each agent and setting strict output formats in each task, the pipeline ensures reliable, structured data that can be used for further analysis. The separation into distinct agents and tasks facilitates easy maintenance, testing, and future enhancements.

Feel free to explore and extend the agents or add additional tasks as needed to further enrich the data collection process!

--- 
