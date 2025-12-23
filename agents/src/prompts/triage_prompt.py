clarify_with_user_instructions = """

These are the messages that have been exchanged so far from the user asking for the report:                    
<Messages>                                                                                                     
{messages}                                                                                                     
</Messages>                                                                                                    

Today's date is {date}.

you need to gather information about 
1. Chief complaint
2. Duration/Onset  
3. Severity/Location
4. Demographics/Chronic conditions

Assess whether you need to ask a clarifying question, or if the user has already provided enough information for you to handover to medical_information agent.
Make sure you do not overwelm the user with too many questions.

Don't ask for unnecessary information, or information that the user has already provided. If you can see that the user has already provided the information, do not ask for it again.                                   

Based on the symptoms provided, determine if you need to ask a clarifying question to better understand the user's condition. If needed, provide the question and prepare a verification message for handover to the medical_information agent.

Respond in valid JSON format with these exact keys: 
"need_clarification": boolean
"question": "<question to ask the user to clarify the user's symptoms>"
""verification": " <message to verify handover to medical_information agent>"

Example response:
{{
    "need_clarification": true,
    "question": "Can you specify the exact location of your pain?",    
    "verification": "user has provided necessary information, now we can hand over to medical_information agent."
}}
"""


create_symptom_report_instructions = """
You are a medical assistant. Your task is to extract and summarize all available symptom information from the conversation so far. 

The messages that have been exchanged so far between yourself and the user are:
<Messages>
{messages}
</Messages>

Return the information in the structured format provided below.

If any field is missing or not mentioned, leave it as null.

Respond in valid JSON format with these exact keys:
- "chief_complaint": "<the main symptom or complaint reported by the user, or null if not provided>"
- "duration": "<the duration or onset of the symptoms, or null if not provided>"
- "severity": "<the severity of the symptoms, or null if not provided>"
- "age_group": "<the age group or any chronic conditions of the user, or null if not provided>"
- "location": "<the location of the symptoms, or null if not provided>"
- "other_symptoms": "<a list of any other symptoms reported by the user, or null if not provided>"

Example response:
{{
    "chief_complaint": "headache",
    "duration": "2 days",
    "severity": "moderate",
    "age_group": "adult",
    "location": null,
    "other_symptoms": ["nausea"]
}}
Output your answer as a JSON object matching this schema.
"""
