# -*- coding: utf-8 -*-

# This sample demonstrates handling intents from an Alexa skill using the Alexa Skills Kit SDK for Python.
# Please visit https://alexa.design/cookbook for additional examples on implementing slots, dialog management,
# session persistence, api calls, and more.
# This sample is built using the handler classes approach in skill builder.
import logging
import ask_sdk_core.utils as ask_utils

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# library for time calculations
from datetime import datetime

# libraries for dynamodb and persistence
import json
from ask_sdk_model.interfaces.alexa.presentation.apl import (
    RenderDocumentDirective)

import os
import boto3

from ask_sdk.standard import StandardSkillBuilder
from ask_sdk_dynamodb.adapter import DynamoDbAdapter
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.dispatch_components import AbstractResponseInterceptor

# launch request handler, for when skill awakens from launch request
class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool

        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        session_attributes = handler_input.attributes_manager.session_attributes
        
        if session_attributes["isClockedIn"] is None:
            speak_output = "Welcome to Timesheet Assistant, your solution to voice-activated Timesheets. Clock in to get started."
        elif session_attributes["isClockedIn"]:
            clockInTime = datetime.strptime(session_attributes["clockInTime"], '%y-%m-%d %H:%M:%S.%f')
            now = datetime.now()
            days, hours, minutes, seconds = timeDifference(clockInTime, now)
            speak_output = f"Welcome back to your Timesheet. You've been clocked in for {minutes} minutes and {seconds} seconds."
        elif not session_attributes["isClockedIn"]:
            speak_output = "Your Timesheet Assistant is open. Clock in to get started."
        else:
            speak_output = "There was a problem with the database."
        
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


## Clocking in and Clocking out

class ClockInIntentHandler(AbstractRequestHandler):
    ## clock in intent handler
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ClockInIntent")(handler_input)

    def handle(self, handler_input):
        
        session_attributes = handler_input.attributes_manager.session_attributes
        
        # get session attribute for isClockedIn
        isClockedIn = session_attributes["isClockedIn"]
        
        # if clocked in is false, allow clock in and return
        if not isClockedIn:
            # get current time
            clockInTime = datetime.now()
            
            # set clock in time in session attributes
            session_attributes["clockInTime"] = clockInTime.strftime('%y-%m-%d %H:%M:%S.%f')
            session_attributes["isClockedIn"] = True
            
            speak_output = "All set. Remember to clock out!"
            
            # else still clocked in
        elif isClockedIn:
            
            speak_output = "You are already clocked in."
            
            #else error
        else:
            speak_output = "Your status is undefined."
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .set_should_end_session(False)
                .response
        )

def timeDifference(timeIn, timeOut):
    timeDelta = timeOut - timeIn
    totalSeconds = int(timeDelta.total_seconds())
    
    days = totalSeconds // 86400
    totalSeconds = totalSeconds % 86400
    
    hours = totalSeconds // 3600
    totalSeconds = totalSeconds % 3600
    
    minutes = totalSeconds // 60 
    totalSeconds = totalSeconds % 60
    
    seconds = totalSeconds
    
    return (days, hours, minutes, seconds)

class ClockOutIntentHandler(AbstractRequestHandler):
    ## clock in intent handler
    def can_handle(self, handler_input):
        return ask_utils.is_intent_name("ClockOutIntent")(handler_input)

    def handle(self, handler_input):
        
        session_attributes = handler_input.attributes_manager.session_attributes
        
        # get session attribute for isClockedIn
        isClockedIn = session_attributes["isClockedIn"]
        
        # if currently clocked in, allow clock out procedure
        if isClockedIn:
            
            # get current time
            clockOutTime = datetime.now()
            
            # retrieve clock in time
            clockInTime = datetime.strptime(session_attributes["clockInTime"], '%y-%m-%d %H:%M:%S.%f')
            session_attributes["isClockedIn"] = False
            
            # timedelta object stores only days, seconds, and microseconds
            days, hours, minutes, seconds = timeDifference(clockInTime, clockOutTime)
            
            speak_output = f"You worked for {hours} hours, {minutes} minutes, and {seconds} seconds."
            
            # else if not clocked in
        elif not isClockedIn:
            
            speak_output = "You are not currently clocked in."
            
            return (
            handler_input.response_builder
                .speak(speak_output)
                .set_should_end_session(False)
                .response
            )
            
            # else errors
        else:
            
            speak_output = "Your clocked in status is undefined."
            
            return (
            handler_input.response_builder
                .speak(speak_output)
                .set_should_end_session(False)
                .response
            )
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )


class HelloWorldIntentHandler(AbstractRequestHandler):
    """Handler for Hello World Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("HelloWorldIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Hello World!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "You can say hello to me! How can I help?"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "Goodbye!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, I'm not sure. You can say Hello or Help. What would you like to do?"
        reprompt = "I didn't catch that. What can I help you with?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response

        # Any cleanup logic goes here.

        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """The intent reflector is used for interaction model testing and debugging.
    It will simply repeat the intent the user said. You can create custom handlers
    for your intents by defining them above, then also adding them to the request
    handler chain below.
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Generic error handling to capture any syntax or routing errors. If you receive an error
    stating the request handler chain is not found, you have not implemented a handler for
    the intent being invoked or included it in the skill builder below.
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speak_output = "Sorry, I had trouble doing what you asked. Please try again."

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class LoadDataInterceptor(AbstractRequestInterceptor):
    """Check if user is invoking skill for first time and initialize preset."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        persistent_attributes = handler_input.attributes_manager.persistent_attributes
        session_attributes = handler_input.attributes_manager.session_attributes
        
        # ensure important variables are initialized so they're used more easily in handlers.
        # This makes sure they're ready to go and makes the handler code a little more readable
        if 'isClockedIn' not in session_attributes:
            session_attributes["isClockedIn"] = False
            
        if 'isClockedIn' not in session_attributes:
            persistent_attributes["isClockedIn"] = False
            
        if 'clockInTime' not in session_attributes:
            session_attributes["clockInTime"] = None
            
        if 'clockInTime' not in persistent_attributes:
            persistent_attributes["clockInTime"] = None
            
        # if you're tracking past_celebs between sessions, use the persistent value
        # set the visits value (either 0 for new, or the persistent value)
        session_attributes["isClockedIn"] = persistent_attributes["isClockedIn"] if 'isClockedIn' in persistent_attributes else False
        session_attributes["clockInTime"] = persistent_attributes["clockInTime"] if 'clockInTime' in persistent_attributes and session_attributes["isClockedIn"] else None

class LoggingRequestInterceptor(AbstractRequestInterceptor):
    """Log the alexa requests."""
    def process(self, handler_input):
        # type: (HandlerInput) -> None
        logger.debug('----- REQUEST -----')
        logger.debug("{}".format(
            handler_input.request_envelope.request))

class SaveDataInterceptor(AbstractResponseInterceptor):
    """Save persistence attributes before sending response to user."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        persistent_attributes = handler_input.attributes_manager.persistent_attributes
        session_attributes = handler_input.attributes_manager.session_attributes
        
        persistent_attributes["isClockedIn"] = session_attributes["isClockedIn"]
        persistent_attributes["clockInTime"] = session_attributes["clockInTime"] if session_attributes["isClockedIn"] else None
        
        handler_input.attributes_manager.save_persistent_attributes()

class LoggingResponseInterceptor(AbstractResponseInterceptor):
    """Log the alexa responses."""
    def process(self, handler_input, response):
        # type: (HandlerInput, Response) -> None
        logger.debug('----- RESPONSE -----')
        logger.debug("{}".format(response))

# The SkillBuilder object acts as the entry point for your skill, routing all request and response
# payloads to the handlers above. Make sure any new handlers or interceptors you've
# defined are included below. The order matters - they're processed top to bottom.


sb = StandardSkillBuilder(
    table_name=os.environ.get("DYNAMODB_PERSISTENCE_TABLE_NAME"), auto_create_table=False)

sb.add_request_handler(LaunchRequestHandler())

sb.add_request_handler(ClockInIntentHandler())
sb.add_request_handler(ClockOutIntentHandler())

sb.add_request_handler(HelloWorldIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # make sure IntentReflectorHandler is last so it doesn't override your custom intent handlers

sb.add_exception_handler(CatchAllExceptionHandler())

# Interceptors
sb.add_global_request_interceptor(LoadDataInterceptor())
sb.add_global_request_interceptor(LoggingRequestInterceptor())

sb.add_global_response_interceptor(SaveDataInterceptor())
sb.add_global_response_interceptor(LoggingResponseInterceptor())

lambda_handler = sb.lambda_handler()