from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.handlers.interaction_handler import InteractionHandler
from app.handlers.command_handler import CommandHandler
from app.utils.block_builder import BlockBuilder
from app.config import get_settings
import json
import hmac
import hashlib
import time
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/slack", tags=["slack"])
settings = get_settings()


def verify_slack_signature(request: Request, body: bytes) -> bool:
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    slack_signature = request.headers.get("X-Slack-Signature", "")
    
    # Prevent replay attacks
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False
    
    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    my_signature = 'v0=' + hmac.new(
        settings.slack_signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(my_signature, slack_signature)


@router.post("/events")
async def handle_events(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    
    # Verify signature
    if not verify_slack_signature(request, body):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    payload = await request.json()
    
    # Handle URL verification
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}
    
    # Handle events
    event = payload.get("event", {})
    
    # Log event for debugging
    logger.info(f"Received event: {event.get('type')}")
    
    return JSONResponse(content={"status": "ok"})


@router.post("/interactions")
async def handle_interactions(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    
    # Verify signature
    if not verify_slack_signature(request, body):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Parse payload
    form_data = await request.form()
    payload = json.loads(form_data.get("payload", "{}"))
    
    interaction_type = payload.get("type")
    
    # Handle different interaction types
    if interaction_type == "block_actions":
        handler = InteractionHandler(db)
        response = await handler.handle_interaction(payload)
        return JSONResponse(content=response)
    
    elif interaction_type == "view_submission":
        # Handle modal submission
        handler = InteractionHandler(db)
        response = await handler.handle_interaction(payload)
        return JSONResponse(content=response)
    
    return JSONResponse(content={"status": "ok"})


# @router.post("/commands/timesheet")
# async def handle_timesheet_command(request: Request, db: Session = Depends(get_db)):
#     body = await request.body()
    
#     # Verify signature
#     if not verify_slack_signature(request, body):
#         raise HTTPException(status_code=403, detail="Invalid signature")
    
#     form_data = await request.form()
#     payload = {
#         "user_id": form_data.get("user_id"),
#         "channel_id": form_data.get("channel_id"),
#         "text": form_data.get("text", "")
#     }
    
#     handler = CommandHandler(db)
#     response = await handler.handle_timesheet_command(payload)
    
#     logger.info(body)
#     logger.info(payload)
#     logger.info(response)
    
#     return JSONResponse(content=response)

@router.post("/commands/postTimesheetWeekly")
async def handle_weekly_timesheet(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    if not verify_slack_signature(request, body):
        raise HTTPException(status_code=403, detail="Invalid signature")

    form_data = await request.form()
    payload = {
        "user_id": form_data.get("user_id"),
        "channel_id": form_data.get("channel_id"),
        "text": form_data.get("text", "Weekly Timesheet submitted Successfully."),
        "trigger_id": form_data.get("trigger_id"),
    }

    handler = CommandHandler(db)
    response = await handler.handle_timesheet_weekly_command(payload)

    logger.info(body)
    logger.info(payload)
    logger.info(response)

    return JSONResponse(content=response)

@router.post("/commands/postTimesheetMonthly")
async def handle_monthly_timesheet(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    if not verify_slack_signature(request, body):
        raise HTTPException(status_code=403, detail="Invalid signature")

    form_data = await request.form()
    payload = {
        "user_id": form_data.get("user_id"),
        "channel_id": form_data.get("channel_id"),
        "text": form_data.get("text", "Monthly Timesheet submitted Successfully."),
        "trigger_id": form_data.get("trigger_id"),
    }

    handler = CommandHandler(db)
    response = await handler.handle_timesheet_monthly_command(payload)

    logger.info(body)
    logger.info(payload)
    logger.info(response)

    return JSONResponse(content=response)

@router.post("/commands/getTimesheetWeeklyReport")
async def handle_weekly_report(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    
    # Verify signature
    if not verify_slack_signature(request, body):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    form_data = await request.form()
    payload = {
        "user_id": form_data.get("user_id"),
        "channel_id": form_data.get("channel_id")
    }
    
    handler = CommandHandler(db)
    response = await handler.handle_weekly_report(payload)
    
    return JSONResponse(content=response)


@router.post("/commands/getTimesheetMonthlyReport")
async def handle_monthly_report(request: Request, db: Session = Depends(get_db)):
    body = await request.body()
    
    # Verify signature
    if not verify_slack_signature(request, body):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    form_data = await request.form()
    payload = {
        "user_id": form_data.get("user_id"),
        "channel_id": form_data.get("channel_id")
    }
    
    handler = CommandHandler(db)
    response = await handler.handle_monthly_report(payload)
    
    return JSONResponse(content=response)

@router.post("/commands/edit_timesheet")
async def handle_edit_timesheet(request: Request, db: Session = Depends(get_db)):
    """Handle the /edit_timesheet command."""
    body = await request.body()
    
    if not verify_slack_signature(request, body):
        raise HTTPException(status_code=403, detail="Invalid signature")
    
    form_data = await request.form()
    trigger_id = form_data.get("trigger_id")
    
    if not trigger_id:
        return JSONResponse(content={
            "response_type": "ephemeral",
            "text": "Error: Unable to process command. Please try again."
        })
    
    logger.info(f"Edit timesheet command received with trigger_id: {trigger_id}")
    
    payload = {
        "user_id": form_data.get("user_id"),
        "channel_id": form_data.get("channel_id"),
        "trigger_id": trigger_id,
        "text": form_data.get("text", "")
    }
    
    handler = CommandHandler(db)
    response = await handler.handle_edit_timesheet_command(payload)
    
    return JSONResponse(content=response)