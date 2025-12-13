# /Users/Mikiyas/Desktop/Open_Source/osdp-team6/src/ai_adapter/README.md
# AI Adapter

## Overview
`ai_adapter` provides integration between AI services (like Claude) and the ticketing system. It translates natural language commands into structured ticket operations and executes them through the `TicketServiceAPI`.

## Purpose
- Parse natural language input from users
- Communicate with AI services to determine intent and extract data
- Execute ticket operations based on AI-interpreted commands
- Return structured responses to the user

## Architecture

### Component Design
The adapter acts as a bridge between:
1. AI Service (Claude) - for natural language understanding
2. Ticket Service API - for ticket operations

### Flow