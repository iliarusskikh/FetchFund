#agent1q20850rnurygmuuu5v3ryzhxl2mrfnwler8gzc0h4u4xp4xxuruljj54rwp agentverse

from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context, Model

import os
import logging
from logging import Logger
import sys
import requests
import atexit


# Import the necessary components of the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    StartSessionContent,
    TextContent,
    chat_protocol_spec,
)
# Initialise agent2
agent2 = Agent()


# AI Agent Address for structured output processing
AI_AGENT_ADDRESS = 'agent1q2gmk0r2vwk6lcr0pvxp8glvtrdzdej890cuxgegrrg86ue9cahk5nfaf3c'
if not AI_AGENT_ADDRESS:
    raise ValueError("AI_AGENT_ADDRESS not set")

def create_text_chat(text: str, end_session: bool = True) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    if end_session:
        content.append(EndSessionContent(type="end-session"))
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
    )
# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)
struct_output_client_proto = Protocol(
    name="StructuredOutputClientProtocol", version="0.1.0"
)


class ContextPrompt(Model):
    context: str
    text: str
 
class Response(Model):
    text: str


class HeartbeatRequest(Model):
    hbdata: str = Field(
        description="heartbeat data sent by user",
    )

class HeartbeatResponse(Model):
    status: str = Field(
        description="stop or continue",
    )


class StructuredOutputPrompt(Model):
    prompt: str
    output_schema: dict[str, Any]

class StructuredOutputResponse(Model):
    output: dict[str, Any]



# Startup Handler - Print agent details
@agent2.on_event("startup")
async def startup_handler(ctx: Context):
    # Print agent details
    ctx.logger.info(f"My name is {ctx.agent.name} and my address is {ctx.agent.address}")


# Message Handler - Process received messages and send acknowledgements
@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    ctx.logger.info(f"Got a message from {sender}: {msg}")
    ctx.storage.set(str(ctx.session), sender)
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id),
    )

    for item in msg.content:
        if isinstance(item, StartSessionContent):
            ctx.logger.info(f"Got a start session message from {sender}")
            continue
        elif isinstance(item, TextContent):
            ctx.logger.info(f"Got a message from {sender}: {item.text}")
            ctx.storage.set(str(ctx.session), sender)
            prompt = f'''Analyse the data which contains heart beat as "value" and its timestamp within past 2 hours. Evaluate if any value is greater than 100, then return "stop" if true. Otherwise, return "continue". Again, only return one word "stop" or "continue". This is the data provided: {item.text}. If no data found in the query, insert <UNKNOWN> in the output schema. '''
            await ctx.send(
                AI_AGENT_ADDRESS,
                StructuredOutputPrompt(
                    prompt=prompt, output_schema=HeartbeatResponse.schema()
                ),
            )
        else:
            ctx.logger.info(f"Got unexpected content from {sender}")



# Acknowledgement Handler - Process received acknowledgements
@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")


@struct_output_client_proto.on_message(StructuredOutputResponse)
async def handle_structured_output_response(
    ctx: Context, sender: str, msg: StructuredOutputResponse
):
    session_sender = ctx.storage.get(str(ctx.session))
    if session_sender is None:
        ctx.logger.error(
            "Discarding message because no session sender found in storage"
        )
        return

    if "<UNKNOWN>" in str(msg.output):
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't process your request. Please include a valid heartbeat data."
            ),
        )
        return

    try:
        # Parse the structured output to get the address
       heartbeat_response = HeartbeatResponse.parse_obj(msg.output)
       hb = heartbeat_response.status
        
       if not hb:
           await ctx.send(session_sender,create_text_chat("Sorry, I couldn't find a valid heartbeat data in your query."),)
           return

       await ctx.send(session_sender, create_text_chat(str(hb)))

        
    except Exception as err:
        ctx.logger.error(err)
        await ctx.send(
            session_sender,
            create_text_chat(
                "Sorry, I couldn't check the heartbeat data provided. Please try again later."
            ),
        )
        return


# Include the protocol in the agent to enable the chat functionality
# This allows the agent to send/receive messages and handle acknowledgements using the chat protocol
agent2.include(chat_proto, publish_manifest=True)
agent2.include(struct_output_client_proto, publish_manifest=True)


@agent2.on_message(HeartbeatRequest, replies={ContextPrompt})
async def handle_request(ctx: Context, sender: str, msg: HeartbeatRequest):
    ctx.logger.info(f"Heartbeat data received: {msg.hbdata}")

    ctx.storage.set("sender_address", sender)

    prompt = f'''This is the data provided: {msg.hbdata}'''
    try:
        await ctx.send(AI_AGENT_ADDRESS,ContextPrompt(context="Analyse the data which contains heart beat as VALUE and its timestamp within past 2 hours. Evaluate if any value is greater than 100, then return stop if true. Otherwise, return continue. Again, only return one word stop or continue.", text=prompt))
    except Exception as e:
        agent._logger.info(f"Error sending data to agent: {e}")


@agent2.on_message(Response, replies={HeartbeatResponse})
async def handle_request(ctx: Context, sender: str, msg: Response):
    ctx.logger.info(f"This is the ASI analysed decision: {msg.text}")
    useraddress = ctx.storage.get("sender_address")

    try:
        await ctx.send(useraddress,HeartbeatResponse(status=msg.text))
    except Exception as e:
        agent._logger.info(f"Error sending data to agent: {e}")




if __name__ == '__main__':
    agent2.run()
